#!/usr/bin/env python3
import argparse
import geopandas as gpd
import json
from pathlib import Path
import re


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


def generate_config(gdf, output_file):
    name_column = determine_name_column(gdf)
    extracts_countries = []

    for continent, group in gdf.groupby("CONTINENT"):
        # Merge all country polygons into a single geometry
        merged = group.dissolve(by="CONTINENT")

        merged = merged.make_valid()

        for _, row in group.iterrows():
            country_name = row[name_column]

            extracts_countries.append(
                {"name": f"{safe_filename(country_name)}", "type": "country"}
            )

    config = {"extracts": extracts_countries}
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Extract Natural Earth continents into individual GeoJSON files."
    )

    parser.add_argument(
        "-i",
        "--input",
        default="ne_10m_admin_0_countries.shp",
        help="Input shapefile (default: ne_10m_admin_0_countries.shp).",
    )

    parser.add_argument(
        "-o",
        "--output",
        default="config.json",
        help="Output file (default: config.json).",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    print(f"Reading '{input_path}'...")
    gdf = gpd.read_file(input_path)

    print("Generating config file...")
    generate_config(gdf, output_path)


if __name__ == "__main__":
    main()
