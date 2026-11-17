"""Strict ingestion of refractiveindex.info YAML records.

Dataset identities correspond to a *single original YAML file*. The data file's
DATA sections remain separate, and no optical constants are borrowed from
unrelated publications. Original wavelengths are in micrometres; all internal
wavelengths and API inputs are nanometres.

Supported in S1: tabulated n, tabulated k, tabulated nk, and formula 1
(Sellmeier). Unknown sections are rejected rather than misinterpreted.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import isfinite
from pathlib import PurePosixPath
import json
import re

import yaml


class DataFormatError(ValueError):
    """The source record cannot be interpreted safely by this importer."""


@dataclass(frozen=True)
class ParsedSection:
    ordinal: int
    kind: str
    min_nm: float
    max_nm: float
    rows: tuple[tuple[float, float | None, float | None], ...] = ()
    coefficients: tuple[float, ...] = ()


@dataclass(frozen=True)
class ParsedDataset:
    id: str
    material_id: str
    page: str
    source_path: str
    source_sha256: str
    source_commit: str
    references: str
    doi_urls: tuple[str, ...]
    notes: str
    conditions_json: str
    sections: tuple[ParsedSection, ...]
    min_nm: float
    max_nm: float
    has_n: bool
    has_k: bool


def _finite(value: object, label: str) -> float:
    try:
        v = float(value)
    except (ValueError, TypeError) as exc:
        raise DataFormatError(f"Invalid {label}: {value!r}") from exc
    if not isfinite(v):
        raise DataFormatError(f"Non-finite {label}: {value!r}")
    return v


def _words(value: object, label: str) -> tuple[float, ...]:
    if not isinstance(value, str):
        raise DataFormatError(f"{label} must be a whitespace-separated string")
    return tuple(_finite(v, label) for v in value.split())


def _path_identity(source_path: str) -> tuple[str, str, str]:
    p = PurePosixPath(source_path)
    parts = p.parts
    if (
        len(parts) != 6
        or parts[:2] != ("database", "data")
        or parts[4] not in ("nk",)
        or not parts[5].endswith(".yml")
        or any(segment in (".", "..") for segment in parts)
    ):
        raise DataFormatError(f"Unexpected optical-record path: {source_path}")
    shelf, material, page = parts[2], parts[3], p.stem
    if not all(re.fullmatch(r"[a-zA-Z0-9_.+-]+", value) for value in (shelf, material, page)):
        raise DataFormatError(f"Unsafe dataset identifier: {source_path}")
    return shelf, material, page


def _tabulated(raw: object, kind: str, ordinal: int) -> ParsedSection:
    if not isinstance(raw, str):
        raise DataFormatError(f"{kind}: tabular data must be text")
    columns = {"tabulated n": 2, "tabulated k": 2, "tabulated nk": 3}[kind]
    rows: list[tuple[float, float | None, float | None]] = []
    for line_num, line in enumerate(raw.splitlines(), start=1):
        parts = line.split()
        if not parts:
            continue
        if len(parts) != columns:
            raise DataFormatError(f"{kind} row {line_num}: expected {columns} columns")
        values = [_finite(word, f"{kind} row {line_num}") for word in parts]
        wavelength_um = values[0]
        if wavelength_um <= 0:
            raise DataFormatError("Wavelength must be positive")
        if kind == "tabulated n":
            n, k = values[1], None
        elif kind == "tabulated k":
            n, k = None, values[1]
        else:
            n, k = values[1], values[2]
        if k is not None and k < 0:
            raise DataFormatError("A passive-medium extinction coefficient cannot be negative")
        wavelength_nm = wavelength_um * 1000.0
        if rows and wavelength_nm <= rows[-1][0]:
            raise DataFormatError("Tabulated wavelengths must be strictly increasing")
        rows.append((wavelength_nm, n, k))
    if not rows:
        raise DataFormatError("Empty tabulated dataset")
    return ParsedSection(ordinal, kind, rows[0][0], rows[-1][0], tuple(rows))


def _formula_1(raw: dict, ordinal: int) -> ParsedSection:
    limits = _words(raw.get("wavelength_range"), "wavelength_range")
    coefficients = _words(raw.get("coefficients"), "coefficients")
    if len(limits) != 2 or not (0 < limits[0] < limits[1]):
        raise DataFormatError("Invalid formula 1 wavelength_range")
    if len(coefficients) < 3 or len(coefficients) % 2 != 1:
        raise DataFormatError("Formula 1 requires c0 plus B,C coefficient pairs")
    return ParsedSection(
        ordinal, "formula 1", limits[0] * 1000, limits[1] * 1000,
        coefficients=coefficients,
    )


def parse_dataset(source_path: str, content: bytes, commit: str) -> ParsedDataset:
    """Parse a single original YAML record with traceable source identifiers."""
    shelf, material, page = _path_identity(source_path)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise DataFormatError("Snapshot commit must be a pinned 40-character SHA")
    try:
        doc = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise DataFormatError(f"Invalid YAML: {source_path}") from exc
    if not isinstance(doc, dict) or not isinstance(doc.get("DATA"), list):
        raise DataFormatError(f"Record is missing DATA: {source_path}")
    references = str(doc.get("REFERENCES") or "")
    if not references.strip():
        raise DataFormatError(f"Record has no REFERENCES: {source_path}")
    notes = str(doc.get("NOTES") or doc.get("COMMENTS") or "")
    conditions = doc.get("CONDITIONS") or {}
    if not isinstance(conditions, dict):
        raise DataFormatError("CONDITIONS must be a map")
    sections: list[ParsedSection] = []
    for ordinal, item in enumerate(doc["DATA"]):
        if not isinstance(item, dict):
            raise DataFormatError(f"DATA section {ordinal} must be a map")
        kind = item.get("type")
        if kind in ("tabulated n", "tabulated k", "tabulated nk"):
            sections.append(_tabulated(item.get("data"), kind, ordinal))
        elif kind == "formula 1":
            sections.append(_formula_1(item, ordinal))
        else:
            raise DataFormatError(f"Unsupported source section type: {kind!r} in {source_path}")
    if not sections:
        raise DataFormatError("Record has no optical DATA sections")
    has_n = any(s.kind in ("tabulated n", "tabulated nk", "formula 1") for s in sections)
    has_k = any(s.kind in ("tabulated k", "tabulated nk") for s in sections)
    doi_urls = tuple(dict.fromkeys(
        match.rstrip(".,);")
        for match in re.findall(r"https?://doi\.org/[^\s\"<>]+", references, re.I)
    ))
    return ParsedDataset(
        id=f"{shelf}:{material}:nk:{page}",
        material_id=material,
        page=page,
        source_path=source_path,
        source_sha256=sha256(content).hexdigest(),
        source_commit=commit,
        references=references,
        doi_urls=doi_urls,
        notes=notes,
        conditions_json=json.dumps(conditions, ensure_ascii=False, sort_keys=True),
        sections=tuple(sections),
        min_nm=min(s.min_nm for s in sections),
        max_nm=max(s.max_nm for s in sections),
        has_n=has_n,
        has_k=has_k,
    )
