#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import re
import os

def safe_filename(name):
    name = name.strip()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "_", name)
    return name


def determine_name_column(gdf):
    possible_columns = [
        "NAME_EN",
        "ADMIN",
        "NAME",
        "SOVEREIGNT",
    ]

    name_column = next(
        (c for c in possible_columns if c in gdf.columns),
        None,
    )

    if name_column is None:
        raise RuntimeError(
            f"Could not determine country name column.\nColumns: {list(gdf.columns)}"
        )

    return name_column


def generate_datasets(input_dir: Path, output_file):
    datasets = []
    for file in input_dir.iterdir():
        if not file.is_file:
            continue

        if file.suffix != ".region":
            continue

        with open(file, "rb") as f:
            hash_digest = hashlib.file_digest(f, "sha256")

        hash = hash_digest.hexdigest()
        size = os.path.getsize(file)
        date = int(os.path.getctime(file))
        id = file.stem

        with open(f"./build/countries/{id}.geojson", 'r') as f:
            name = json.load(f)["name"]

        datasets.append(
            {
                "id": id,
                "name": name,
                "file": str(file.relative_to(output_file.parent)),
                "sha256": hash,
                "size": size,
                "date": date,
            }
        )
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(datasets, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Extract Natural Earth continents into individual GeoJSON files."
    )

    parser.add_argument(
        "-i",
        "--input",
        default=".",
        help="Input directory.",
    )

    parser.add_argument(
        "-o",
        "--output",
        default="datasets.json",
        help="Output file (default: datasets.json).",
    )

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_path = Path(args.output)

    print(f"Generating '{str(output_path)}'...")
    generate_datasets(input_dir, output_path)


if __name__ == "__main__":
    main()
