"""Integration smoke against a pinned, real refractiveindex.info snapshot.

This script requires network access for the initial download. It runs against
actual published YAML, never synthetic optical constants, and leaves source
files and DB in ignored data/ directories.
"""

from pathlib import Path

from packages.material_data.importer import SNAPSHOT, import_pilots
from packages.material_data.store import dataset_details, evaluate_constants, list_datasets


def main() -> None:
    database = Path("data/processed/s1-integration.sqlite")
    imported = import_pilots(database, cache_dir="data/raw/refractiveindex-info")
    assert imported == 4
    datasets = list_datasets(database)
    assert len(datasets) == 4
    assert all(record["source_commit"] == SNAPSHOT for record in datasets)
    for record in datasets:
        assert record["source_sha256"]
        assert record["references"]
        assert dataset_details(database, record["id"])["sections"]
    for dataset_id in ("main:Cu:nk:Johnson", "main:Al:nk:Rakic", "main:SiO2:nk:Gao"):
        result = evaluate_constants(database, dataset_id, 532, require_nk=True)
        assert result["n"] >= 0
        assert result["k"] is not None and result["k"] >= 0
        assert result["complete_for_tmm"]
        print(f"{dataset_id} at 532 nm: n={result['n']:.6g}, k={result['k']:.6g}")
    silica = evaluate_constants(database, "main:SiO2:nk:Malitson", 532)
    assert 1.460 < silica["n"] < 1.462
    assert silica["k"] is None
    assert not silica["complete_for_tmm"]
    print("Silica Malitson n(532nm):", silica["n"], "k: missing, correctly flagged")
    print("PASS: 4 real source-backed datasets, provenance and wavelength evaluation")


if __name__ == "__main__":
    main()
