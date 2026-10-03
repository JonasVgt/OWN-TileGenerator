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


def generate_country_geojsons(gdf, output_dir, extracts_per_file):
    name_column = determine_name_column(gdf)

    for continent, group in gdf.groupby("CONTINENT"):
        num_files = 0
        extracts_countries = []
        for _, row in group.iterrows():
            country_name = row[name_column]
            filename = f"{safe_filename(country_name)}.geojson"

            single = gpd.GeoDataFrame(
                [{"geometry": row.geometry}],
                geometry="geometry",
                crs=gdf.crs,
            )

            single.to_file(output_dir / filename, driver="GeoJSON")

            extracts_countries.append(
                {
                    "output": f"{safe_filename(country_name)}.osm.pbf",
                    "polygon": {"file_name": str(filename), "file_type": "geojson"},
                }
            )

            if len(extracts_countries) >= extracts_per_file:
                config = {"directory": str(output_dir), "extracts": extracts_countries}
                with open(
                    output_dir / f"{safe_filename(continent)}-extract-{num_files+1}.json",
                    "w",
                    encoding="utf-8",
                ) as f:
                    json.dump(config, f, indent=2)
                num_files += 1
                extracts_countries = []

        if(len(extracts_countries) > 0):
            config = {"directory": str(output_dir), "extracts": extracts_countries}

            with open(
                output_dir / f"{safe_filename(continent)}-extract-{num_files+1}.json",
                "w",
                encoding="utf-8",
            ) as f:
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
        default="countries",
        help="Output folder for GeoJSON files (default: countries).",
    )

    parser.add_argument(
        "-n",
        "--extracts-per-file",
        default="6",
        help="Number of files per osmium extract to reduce memory usage (default: 6).",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Reading '{input_path}'...")
    gdf = gpd.read_file(input_path)

    print("Generating country geojsons...")
    generate_country_geojsons(gdf, output_dir, args.extracts_per_file)


if __name__ == "__main__":
    main()
