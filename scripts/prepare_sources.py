"""Create deterministic patient and operation extracts for the SSIS staging load."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PATIENT_COLUMNS = ["source_id", "Name", "Age", "Gender", "Blood Type"]
OPERATION_COLUMNS = [
    "source_id",
    "Medical Condition",
    "Date of Admission",
    "Discharge Date",
    "Doctor",
    "Hospital",
    "Insurance Provider",
    "Billing Amount",
    "Room Number",
    "Admission Type",
    "Medication",
    "Test Results",
]
PATIENT_ID_COLUMNS = ["Name", "Gender", "Blood Type"]


def prepare_sources(input_path: Path, output_dir: Path) -> tuple[Path, Path]:
    """Split the raw admission data into patient and operation CSV files."""
    frame = pd.read_csv(input_path)
    required = set(PATIENT_COLUMNS[1:] + OPERATION_COLUMNS[1:])
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    for column in ("Date of Admission", "Discharge Date"):
        frame[column] = pd.to_datetime(frame[column], errors="raise")

    frame["source_id"] = frame.groupby(
        PATIENT_ID_COLUMNS, sort=False, dropna=False
    ).ngroup() + 1

    patients = (
        frame.sort_values("Date of Admission")
        .drop_duplicates("source_id", keep="last")[PATIENT_COLUMNS]
        .sort_values("source_id")
    )
    operations = frame[OPERATION_COLUMNS]

    output_dir.mkdir(parents=True, exist_ok=True)
    patient_path = output_dir / "patient_source.csv"
    operation_path = output_dir / "operation_source.csv"
    patients.to_csv(patient_path, index=False, date_format="%Y-%m-%d")
    operations.to_csv(operation_path, index=False, date_format="%Y-%m-%d")

    validate_sources(patients, operations)
    return patient_path, operation_path


def validate_sources(patients: pd.DataFrame, operations: pd.DataFrame) -> None:
    """Fail when extract keys or admission dates violate the staging contract."""
    if patients["source_id"].duplicated().any():
        raise ValueError("patient_source.csv contains duplicate source_id values")
    if not operations["source_id"].isin(patients["source_id"]).all():
        raise ValueError("operation_source.csv contains unknown source_id values")
    if (operations["Discharge Date"] < operations["Date of Admission"]).any():
        raise ValueError("Discharge Date cannot precede Date of Admission")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Raw healthcare CSV")
    parser.add_argument(
        "--output-dir", type=Path, required=True, help="Directory for generated CSVs"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    patient_path, operation_path = prepare_sources(args.input, args.output_dir)
    print(f"Created {patient_path}")
    print(f"Created {operation_path}")


if __name__ == "__main__":
    main()
