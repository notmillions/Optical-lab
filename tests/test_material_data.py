"""S1 tests use declared SYNTHETIC fixtures; never imply they are measurements."""

from pathlib import Path

import pytest

from packages.material_data.importer import scan_catalog, write_coverage_report
from packages.material_data.parser import DataFormatError, inspect_source, parse_dataset
from packages.material_data.store import (
    MissingDatasetError,
    SpectralDomainError,
    dataset_details,
    evaluate_constants,
    import_datasets,
    list_datasets,
    list_materials,
    list_source_records,
)

SNAPSHOT = "e6d15e364f70de1cad8a96a20f75689f2fba8b21"
FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures"


def fixture_record(filename: str, material: str = "SiO2"):
    name = filename.removeprefix("s1_synthetic_").removesuffix(".yml")
    return parse_dataset(
        f"database/data/main/{material}/nk/{name}.yml",
        (FIXTURES / filename).read_bytes(),
        SNAPSHOT,
    )


@pytest.fixture
def database(tmp_path):
    db = tmp_path / "materials.sqlite"
    import_datasets(
        db,
        [
            fixture_record("s1_synthetic_nk.yml"),
            fixture_record("s1_synthetic_n_only.yml"),
        ],
    )
    return db


def test_parsing_micrometres_to_nm_and_provenance():
    record = fixture_record("s1_synthetic_nk.yml")
    assert record.sections[0].rows[0] == (400.0, 1.5, 0.1)
    assert record.min_nm == pytest.approx(400.0)
    assert record.max_nm == pytest.approx(600.0)
    assert record.has_n and record.has_k
    assert len(record.source_sha256) == 64
    assert record.source_commit == SNAPSHOT


def test_sqlite_search_and_source_metadata(database):
    assert list_materials(database)[0]["id"] == "SiO2"
    assert len(list_datasets(database, "SiO2")) == 2
    detail = dataset_details(database, "main:SiO2:nk:nk")
    assert detail["has_n"] is True
    assert detail["has_k"] is True
    assert detail["sections"][0]["points"] == 3
    assert detail["source_commit"] == SNAPSHOT


def test_linear_interpolation_is_explicit(database):
    result = evaluate_constants(database, "main:SiO2:nk:nk", 450)
    assert result["n"] == pytest.approx(1.55)
    assert result["k"] == pytest.approx(0.15)
    assert result["complete_for_tmm"]


def test_missing_k_not_misrepresented_as_zero(database):
    result = evaluate_constants(database, "main:SiO2:nk:n_only", 450)
    assert result["k"] is None
    assert result["complete_for_tmm"] is False
    with pytest.raises(SpectralDomainError, match="k missing"):
        evaluate_constants(database, "main:SiO2:nk:n_only", 450, require_nk=True)


def test_no_extrapolation(database):
    for wavelength in (399, 601):
        with pytest.raises(SpectralDomainError):
            evaluate_constants(database, "main:SiO2:nk:nk", wavelength)


def test_missing_dataset(database):
    with pytest.raises(MissingDatasetError):
        evaluate_constants(database, "does-not-exist", 450)


def test_rejects_bad_tabulation():
    data = b"REFERENCES: Synthetic\nDATA:\n  - type: tabulated nk\n    data: '0.4 1.5 0.0\\n0.3 1.6 0.2'\n"
    with pytest.raises(DataFormatError):
        parse_dataset("database/data/main/Cu/nk/failure.yml", data, SNAPSHOT)


@pytest.mark.parametrize("value", [0, -1.0])
def test_rejects_nonpositive_refractive_index(value):
    data = f"""REFERENCES: Synthetic\nDATA:\n  - type: tabulated nk\n    data: |\n      0.4 {value} 0.1\n      0.6 1.5 0.1\n""".encode()
    with pytest.raises(DataFormatError, match="n must be positive"):
        parse_dataset("database/data/main/Cu/nk/failure.yml", data, SNAPSHOT)


def test_reimport_is_idempotent(database):
    original = len(list_datasets(database))
    assert import_datasets(database, [fixture_record("s1_synthetic_nk.yml")]) == 1
    assert len(list_datasets(database)) == original


def test_formula_1_malitson_reference():
    # Formula and coefficients reproduced from Malitson (1965), RefractiveIndex.INFO.
    # This is an analytical reference test, not a replacement for provenance storage.
    data = b"""REFERENCES: "I. H. Malitson (1965)"
DATA:
  - type: formula 1
    wavelength_range: 0.21 6.7
    coefficients: 0 0.6961663 0.0684043 0.4079426 0.1162414 0.8974794 9.896161
"""
    record = parse_dataset("database/data/main/SiO2/nk/Malitson.yml", data, SNAPSHOT)
    assert record.has_n and not record.has_k
    from packages.material_data.store import _sellmeier_1

    n = _sellmeier_1(list(record.sections[0].coefficients), 532)
    assert n == pytest.approx(1.4607, abs=0.0002)


def test_unsupported_formula_rejected():
    data = b"REFERENCES: Synthetic\nDATA:\n  - type: formula 2\n    coefficients: '0 1 2'\n"
    with pytest.raises(DataFormatError, match="Unsupported"):
        parse_dataset("database/data/main/Cu/nk/unsupported.yml", data, SNAPSHOT)


def test_catalog_inspection_marks_unsupported_section_without_interpreting_it():
    data = b"""REFERENCES: Synthetic
DATA:
  - type: tabulated nk
    data: |
      0.4 1.5 0.1
      0.6 1.6 0.2
  - type: formula 9
    data: never interpret this
"""
    inspection = inspect_source("database/data/main/Cu/nk/mixed.yml", data, SNAPSHOT)
    assert inspection.status == "partial"
    assert inspection.dataset is not None
    assert len(inspection.dataset.sections) == 1
    assert inspection.unsupported_sections[0].source_type == "formula 9"
    assert inspection.dataset.sections[0].rows[0] == (400.0, 1.5, 0.1)


def test_catalog_scan_reports_every_file_and_persists_manifest(tmp_path):
    root = tmp_path / "source"
    nk = root / "database/data/main/Cu/nk"
    nk.mkdir(parents=True)
    (nk / "supported.yml").write_bytes(
        b"""REFERENCES: Synthetic
DATA:
  - type: tabulated nk
    data: |
      0.4 1.5 0.1
      0.6 1.6 0.2
"""
    )
    (nk / "unsupported.yml").write_bytes(
        b"""REFERENCES: Synthetic
DATA:
  - type: formula 9
    data: unknown
"""
    )

    report = scan_catalog(root)
    assert report.discovered_files == 2
    assert report.importable_datasets == 1
    assert report.fully_supported_datasets == 1
    assert report.unsupported_files == 1
    assert report.unsupported_sections == 1

    database = tmp_path / "catalog.sqlite"
    from packages.material_data.store import import_datasets

    import_datasets(
        database,
        [item.dataset for item in report.records if item.dataset is not None],
        source_records=list(report.records),
    )
    manifest = list_source_records(database)
    assert [row["status"] for row in manifest] == ["imported", "unsupported"]
    assert manifest[1]["unsupported_sections"][0]["source_type"] == "formula 9"

    markdown = tmp_path / "coverage.md"
    write_coverage_report(report, markdown)
    assert "Importable datasets: **1**" in markdown.read_text()


def test_catalog_scan_accepts_nested_material_paths(tmp_path):
    root = tmp_path / "source"
    nk = root / "database/data/main/organic/Example/nk"
    nk.mkdir(parents=True)
    path = nk / "record.yml"
    path.write_bytes(
        b"""REFERENCES: Synthetic
DATA:
  - type: tabulated n
    data: |
      0.4 1.5
      0.6 1.6
"""
    )
    report = scan_catalog(root)
    assert report.records[0].dataset is not None
    assert report.records[0].dataset.material_id == "organic/Example"
