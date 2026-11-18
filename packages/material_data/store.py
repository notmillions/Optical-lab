"""SQLite persistence and safe wavelength-domain evaluation.

The importer retains independent YAML records as independent datasets. A
missing k stays None. Evaluating n and k from different publications requires
an explicit future composition model and is not done here.
"""

from __future__ import annotations

import json
import sqlite3
from bisect import bisect_left
from collections.abc import Iterator
from contextlib import contextmanager
from math import isclose, isfinite, sqrt
from pathlib import Path

from packages.material_data.parser import ParsedDataset, SourceInspection, UnsupportedSection


class MissingDatasetError(LookupError):
    """No such imported record exists."""


class SpectralDomainError(ValueError):
    """The wavelength is invalid, unsupported, or not defined by this dataset."""


SCHEMA_VERSION = 2
SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS snapshots (
    commit_sha TEXT PRIMARY KEY,
    repository_url TEXT NOT NULL,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS materials (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS datasets (
    id TEXT PRIMARY KEY,
    material_id TEXT NOT NULL REFERENCES materials(id),
    page TEXT NOT NULL,
    source_commit TEXT NOT NULL REFERENCES snapshots(commit_sha),
    source_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    references_text TEXT NOT NULL,
    dois_json TEXT NOT NULL,
    notes TEXT NOT NULL,
    conditions_json TEXT NOT NULL,
    min_nm REAL NOT NULL,
    max_nm REAL NOT NULL,
    has_n INTEGER NOT NULL,
    has_k INTEGER NOT NULL,
    UNIQUE(source_commit, source_path)
);
CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY,
    dataset_id TEXT NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    kind TEXT NOT NULL,
    min_nm REAL NOT NULL,
    max_nm REAL NOT NULL,
    coefficients_json TEXT NOT NULL,
    UNIQUE(dataset_id, ordinal)
);
CREATE TABLE IF NOT EXISTS sample_points (
    section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    wavelength_nm REAL NOT NULL,
    n REAL,
    k REAL,
    PRIMARY KEY(section_id, wavelength_nm)
);
CREATE INDEX IF NOT EXISTS ix_datasets_material ON datasets(material_id);
CREATE INDEX IF NOT EXISTS ix_sections_dataset ON sections(dataset_id);
CREATE TABLE IF NOT EXISTS source_records (
    source_commit TEXT NOT NULL,
    source_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('imported', 'partial', 'unsupported', 'invalid')),
    dataset_id TEXT REFERENCES datasets(id) ON DELETE SET NULL,
    unsupported_sections_json TEXT NOT NULL,
    error TEXT,
    PRIMARY KEY(source_commit, source_path)
);
CREATE INDEX IF NOT EXISTS ix_source_records_status ON source_records(status);
"""


@contextmanager
def connect(database: str | Path) -> Iterator[sqlite3.Connection]:
    """Open and always close a connection with transactional writes."""
    conn = sqlite3.connect(str(database))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(database: str | Path) -> None:
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1, SCHEMA_VERSION):
            raise RuntimeError(f"Unsupported SQLite schema version: {version}")
        conn.executescript(SCHEMA)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def _assert_initialized(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version != SCHEMA_VERSION:
        raise RuntimeError("Material database is missing or has a different schema; import first")


def _unsupported_json(sections: tuple[UnsupportedSection, ...]) -> str:
    return json.dumps(
        [
            {"ordinal": item.ordinal, "source_type": item.source_type, "reason": item.reason}
            for item in sections
        ],
        ensure_ascii=False,
        sort_keys=True,
    )


def _upsert_source_record(conn: sqlite3.Connection, inspection: SourceInspection) -> None:
    dataset_id = inspection.dataset.id if inspection.dataset is not None else None
    conn.execute(
        """INSERT INTO source_records(
            source_commit, source_path, source_sha256, status, dataset_id,
            unsupported_sections_json, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_commit, source_path) DO UPDATE SET
            source_sha256=excluded.source_sha256,
            status=excluded.status,
            dataset_id=excluded.dataset_id,
            unsupported_sections_json=excluded.unsupported_sections_json,
            error=excluded.error""",
        (
            inspection.source_commit,
            inspection.source_path,
            inspection.source_sha256,
            inspection.status,
            dataset_id,
            _unsupported_json(inspection.unsupported_sections),
            inspection.error,
        ),
    )


def import_datasets(
    database: str | Path,
    records: list[ParsedDataset],
    *,
    source_records: list[SourceInspection] | None = None,
) -> int:
    """Replace records atomically, without blending their original authors/sources."""
    if len({r.id for r in records}) != len(records):
        raise ValueError("Duplicate dataset IDs in ingestion batch")
    init_database(database)
    with connect(database) as conn:
        for record in records:
            conn.execute(
                """INSERT OR IGNORE INTO snapshots(commit_sha, repository_url)
                   VALUES (?, ?)""",
                (record.source_commit, "https://github.com/polyanskiy/refractiveindex.info-database"),
            )
            material_name = {"Cu": "Copper", "Al": "Aluminium", "SiO2": "Fused silica / silica"}.get(
                record.material_id, record.material_id
            )
            conn.execute(
                "INSERT OR IGNORE INTO materials(id, name) VALUES (?, ?)",
                (record.material_id, material_name),
            )
            conn.execute("DELETE FROM datasets WHERE id = ?", (record.id,))
            conn.execute(
                """INSERT INTO datasets(
                    id, material_id, page, source_commit, source_path, source_sha256,
                    references_text, dois_json, notes, conditions_json, min_nm, max_nm,
                    has_n, has_k
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.id, record.material_id, record.page, record.source_commit,
                    record.source_path, record.source_sha256, record.references,
                    json.dumps(record.doi_urls), record.notes, record.conditions_json,
                    record.min_nm, record.max_nm, int(record.has_n), int(record.has_k),
                ),
            )
            for section in record.sections:
                cur = conn.execute(
                    """INSERT INTO sections(dataset_id, ordinal, kind, min_nm, max_nm, coefficients_json)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        record.id, section.ordinal, section.kind,
                        section.min_nm, section.max_nm, json.dumps(section.coefficients),
                    ),
                )
                conn.executemany(
                    """INSERT INTO sample_points(section_id, wavelength_nm, n, k)
                       VALUES (?, ?, ?, ?)""",
                    [(cur.lastrowid, *row) for row in section.rows],
                )
        if source_records is not None:
            for inspection in source_records:
                _upsert_source_record(conn, inspection)
    return len(records)


def list_source_records(
    database: str | Path,
    *,
    status: str | None = None,
) -> list[dict]:
    """Return the complete source manifest, including unsupported files."""
    with connect(database) as conn:
        _assert_initialized(conn)
        if status is None:
            rows = conn.execute(
                "SELECT * FROM source_records ORDER BY source_path"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM source_records WHERE status = ? ORDER BY source_path",
                (status,),
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["unsupported_sections"] = json.loads(item.pop("unsupported_sections_json"))
            result.append(item)
        return result


def list_materials(database: str | Path, query: str = "") -> list[dict]:
    with connect(database) as conn:
        _assert_initialized(conn)
        rows = conn.execute(
            """SELECT m.id, m.name, COUNT(d.id) AS dataset_count
               FROM materials m JOIN datasets d ON d.material_id = m.id
               WHERE m.id LIKE ? OR m.name LIKE ?
               GROUP BY m.id, m.name ORDER BY m.name""",
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
        return [dict(row) for row in rows]


def list_datasets(database: str | Path, material_id: str | None = None) -> list[dict]:
    with connect(database) as conn:
        _assert_initialized(conn)
        if material_id is None:
            rows = conn.execute("SELECT * FROM datasets ORDER BY material_id, page").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM datasets WHERE material_id = ? ORDER BY page", (material_id,)
            ).fetchall()
        return [_dataset_row(row) for row in rows]


def _dataset_row(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["has_n"] = bool(data["has_n"])
    data["has_k"] = bool(data["has_k"])
    data["doi_urls"] = json.loads(data.pop("dois_json"))
    data["conditions"] = json.loads(data.pop("conditions_json"))
    data["references"] = data.pop("references_text")
    return data


def dataset_details(database: str | Path, dataset_id: str) -> dict:
    with connect(database) as conn:
        _assert_initialized(conn)
        row = conn.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,)).fetchone()
        if row is None:
            raise MissingDatasetError(dataset_id)
        sections = conn.execute(
            """SELECT id, ordinal, kind, min_nm, max_nm,
                      (SELECT COUNT(*) FROM sample_points WHERE section_id = sections.id) AS points
               FROM sections WHERE dataset_id = ? ORDER BY ordinal""",
            (dataset_id,),
        ).fetchall()
        return {**_dataset_row(row), "sections": [dict(item) for item in sections]}


def _interpolate(points: list[sqlite3.Row], wavelength_nm: float, column: str) -> float:
    xs = [row["wavelength_nm"] for row in points]
    i = bisect_left(xs, wavelength_nm)
    if i < len(xs) and isclose(xs[i], wavelength_nm, rel_tol=0, abs_tol=1e-8):
        value = points[i][column]
        if value is None:
            raise SpectralDomainError(f"{column} absent from this tabulated section")
        return float(value)
    if i <= 0 or i >= len(points):
        raise SpectralDomainError("Extrapolation beyond tabulated wavelengths is forbidden")
    left, right = points[i - 1], points[i]
    a, b = left[column], right[column]
    if a is None or b is None:
        raise SpectralDomainError(f"{column} absent from this tabulated section")
    ratio = (wavelength_nm - left["wavelength_nm"]) / (
        right["wavelength_nm"] - left["wavelength_nm"]
    )
    return float(a + ratio * (b - a))


def _sellmeier_1(coefficients: list[float], wavelength_nm: float) -> float:
    wavelength_um = wavelength_nm / 1000.0
    squared = wavelength_um * wavelength_um
    n_squared = 1.0 + coefficients[0]
    for j in range(1, len(coefficients), 2):
        b, c = coefficients[j], coefficients[j + 1]
        denominator = squared - c * c
        if isclose(denominator, 0.0, rel_tol=0, abs_tol=1e-14):
            raise SpectralDomainError("Wavelength lies on a Sellmeier pole")
        n_squared += b * squared / denominator
    if not isfinite(n_squared) or n_squared < 0:
        raise SpectralDomainError("Invalid Sellmeier n² value")
    return sqrt(n_squared)


def _resolve_unique(values: list[float], label: str) -> float | None:
    if not values:
        return None
    if not all(isclose(values[0], value, abs_tol=1e-7, rel_tol=1e-6) for value in values[1:]):
        raise SpectralDomainError(f"Ambiguous overlapping {label} sections")
    return values[0]


def evaluate_constants(
    database: str | Path,
    dataset_id: str,
    wavelength_nm: float,
    *,
    require_nk: bool = False,
) -> dict:
    """Return n and k from one original record, with explicit missingness."""
    if not isfinite(wavelength_nm) or wavelength_nm <= 0:
        raise SpectralDomainError("Wavelength must be positive and finite")
    with connect(database) as conn:
        _assert_initialized(conn)
        record = conn.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,)).fetchone()
        if record is None:
            raise MissingDatasetError(dataset_id)
        sections = conn.execute(
            "SELECT * FROM sections WHERE dataset_id = ? ORDER BY ordinal", (dataset_id,)
        ).fetchall()
        n_values: list[float] = []
        k_values: list[float] = []
        for section in sections:
            if not (section["min_nm"] - 1e-8 <= wavelength_nm <= section["max_nm"] + 1e-8):
                continue
            kind = section["kind"]
            if kind == "formula 1":
                n_values.append(
                    _sellmeier_1(json.loads(section["coefficients_json"]), wavelength_nm)
                )
            elif kind in ("tabulated n", "tabulated k", "tabulated nk"):
                points = conn.execute(
                    "SELECT wavelength_nm, n, k FROM sample_points WHERE section_id = ? "
                    "ORDER BY wavelength_nm", (section["id"],)
                ).fetchall()
                if kind in ("tabulated n", "tabulated nk"):
                    n_values.append(_interpolate(points, wavelength_nm, "n"))
                if kind in ("tabulated k", "tabulated nk"):
                    k_values.append(_interpolate(points, wavelength_nm, "k"))
            else:
                raise SpectralDomainError(f"Unsupported stored section: {kind}")
        n = _resolve_unique(n_values, "n")
        k = _resolve_unique(k_values, "k")
        if n is None:
            raise SpectralDomainError("No n defined at this wavelength in the selected record")
        if require_nk and k is None:
            raise SpectralDomainError("k missing: this record cannot be used alone for TMM")
        return {
            "dataset_id": dataset_id,
            "source_commit": record["source_commit"],
            "source_sha256": record["source_sha256"],
            "wavelength_nm": wavelength_nm,
            "n": n,
            "k": k,
            "complete_for_tmm": k is not None,
            "warning": None if k is not None else "k is not provided by this reference",
            "interpolation": "linear (tabulated) or formula 1 (Sellmeier)",
        }
