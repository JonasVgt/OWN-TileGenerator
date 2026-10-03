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


def generate_continent_geojsons(gdf, output_dir):
    extracts_continents = []

    for continent, group in gdf.groupby("CONTINENT"):
        # Merge all country polygons into a single geometry
        merged = group.dissolve(by="CONTINENT")

        merged = merged.make_valid()

        filename = continent.replace(" ", "_") + ".geojson"

        merged.to_file(output_dir / filename, driver="GeoJSON")

        extracts_continents.append(
            {
                "output": f"{safe_filename(continent)}.osm.pbf",
                "polygon": {"file_name": str(filename), "file_type": "geojson"},
            }
        )

    config = {"directory": str(output_dir), "extracts": extracts_continents}
    with open(output_dir / "extract.json", "w", encoding="utf-8") as f:
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
        default="continents",
        help="Output folder for GeoJSON files (default: continents).",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Reading '{input_path}'...")
    gdf = gpd.read_file(input_path)

    print("Generating continent geojsons...")
    generate_continent_geojsons(gdf, output_dir)


if __name__ == "__main__":
    main()
