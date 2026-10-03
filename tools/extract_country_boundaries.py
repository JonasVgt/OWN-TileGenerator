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


def generate_country_geojsons(gdf, output_dir):
    name_column = determine_name_column(gdf)

    for continent, group in gdf.groupby("CONTINENT"):

        extracts_countries = []
        for _, row in group.iterrows():
            country_name = row[name_column]
            filename = output_dir / f"{safe_filename(country_name)}.geojson"

            single = gpd.GeoDataFrame(
                [{"geometry": row.geometry}],
                geometry="geometry",
                crs=gdf.crs,
            )

            single.to_file(filename, driver="GeoJSON")

            extracts_countries.append(
                {
                    "output": f"{safe_filename(country_name)}.osm.pbf",
                    "polygon": {"file_name": str(filename), "file_type": "geojson"},
                }
            )

        config = {"directory": str(output_dir), "extracts": extracts_countries}

        with open(
            output_dir / f"{safe_filename(continent)}-extract.json",
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

    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Reading '{input_path}'...")
    gdf = gpd.read_file(input_path)

    print("Generating country geojsons...")
    generate_country_geojsons(gdf, output_dir)


if __name__ == "__main__":
    main()
