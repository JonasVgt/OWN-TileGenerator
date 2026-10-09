#!/usr/bin/env python3

import argparse
import json
import os
import sqlite3
from pathlib import Path

import mapbox_vector_tile

from pmtiles.reader import MmapSource, Reader, all_tiles
from pmtiles.writer import Writer
from pmtiles.tile import (
    Compression,
    TileType,
    zxy_to_tileid,
)

import gzip


METADATA_LAYER = "metadata_beacon_buoy"
METADATA_ZOOM = 14


def create_database(path: str):
    conn = sqlite3.connect(path)

    conn.execute("""
        CREATE TABLE metadata (
            id          INTEGER PRIMARY KEY,
            properties  TEXT NOT NULL
        )
    """)

    return conn


def process_tile(tile_data, z, x, y, db, writer):
    """
    Process one MVT tile.

    - Extract metadata features at z14 into SQLite.
    - Remove the metadata layer.
    - Write the remaining tile to the output PMTiles.
    """

    # Only z14 contains metadata.
    if z != METADATA_ZOOM:
        writer.write_tile(
            zxy_to_tileid(z, x, y),
            tile_data,
        )
        return

    decoded = mapbox_vector_tile.decode(
        gzip.decompress(tile_data),
        default_options={
            "geojson": False,
        },
    )

    metadata = decoded.pop(METADATA_LAYER, None)

    if metadata is not None:
        for feature in metadata["features"]:
            feature_id = feature.get("id")

            if feature_id is None:
                raise ValueError(
                    f"Metadata feature without id in "
                    f"{z}/{x}/{y}"
                )

            properties = feature.get("properties", {})
            db.execute(
                """
                INSERT OR IGNORE INTO metadata (
                    id,
                    properties
                )
                VALUES (?, ?)
                """,
                (
                    feature_id,
                    json.dumps(
                        properties,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ),
                ),
            )

    # Re-encode the tile without the metadata layer.
    #
    # If the tile contained only the metadata layer, there is
    # nothing to write to the output archive.
    if decoded:
        new_tile = mapbox_vector_tile.encode(
            [
                {
                    "name": layer_name,
                    **layer,
                }
                for layer_name, layer in decoded.items()
            ]
        )

        writer.write_tile(
            zxy_to_tileid(z, x, y),
            gzip.compress(new_tile),
        )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Extract a PMTiles metadata layer into SQLite "
            "and remove that layer from the PMTiles archive."
        )
    )

    parser.add_argument(
        "-i",
        "--input",
        default="tiles.pmtiles",
        help="Input PMTiles file",
    )

    parser.add_argument(
        "-o",
        "--output",
        default="out.pmtiles",
        help="Output PMTiles file without the metadata layer",
    )

    parser.add_argument(
        "-d",
        "--database",
        default="metadata.db",
        help="SQLite database to create",
    )

    parser.add_argument(
        "--metadata-layer",
        default=METADATA_LAYER,
        help=f"Metadata layer name (default: {METADATA_LAYER})",
    )

    parser.add_argument(
        "--metadata-zoom",
        type=int,
        default=METADATA_ZOOM,
        help=f"Metadata zoom (default: {METADATA_ZOOM})",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    database_path = Path(args.database)

    if not input_path.exists():
        raise SystemExit(f"Input does not exist: {input_path}")

    if output_path.exists():
        raise SystemExit(f"Output already exists: {output_path}")

    if database_path.exists():
        raise SystemExit(f"Database already exists: {database_path}")

    # Use a temporary output so an interrupted run doesn't leave
    # a seemingly valid PMTiles file at the final destination.
    temp_output = output_path.with_suffix(
        output_path.suffix + ".tmp"
    )

    if temp_output.exists():
        temp_output.unlink()

    print(f"Reading:  {input_path}")
    print(f"Writing:  {output_path}")
    print(f"Database: {database_path}")

    with open(input_path, "rb") as input_file:

        source = MmapSource(input_file)
        reader = Reader(source)

        header = reader.header()
        archive_metadata = reader.metadata()

        # Create SQLite database.
        db = create_database(str(database_path))

        try:
            with open(temp_output, "wb") as output_file:

                writer = Writer(output_file)

                tile_count = 0
                metadata_count = 0

                # Iterate through every tile in the PMTiles archive.
                for (z, x, y), tile_data in all_tiles(source):

                    process_tile(
                        tile_data,
                        z,
                        x,
                        y,
                        db,
                        writer,
                    )

                    tile_count += 1

                    if tile_count % 10000 == 0:
                        print(
                            f"Processed {tile_count:,} tiles..."
                        )

                # Commit SQLite data before finalizing the archive.
                db.commit()

                # Preserve the original PMTiles metadata/header
                # where possible, while changing the tile type/
                # compression information to match the generated
                # tiles.
                writer.finalize(
                    {
                        "tile_type": TileType.MVT,
                        "tile_compression": Compression.GZIP,
                        "min_zoom": header["min_zoom"],
                        "max_zoom": header["max_zoom"],
                        "min_lon_e7": header["min_lon_e7"],
                        "min_lat_e7": header["min_lat_e7"],
                        "max_lon_e7": header["max_lon_e7"],
                        "max_lat_e7": header["max_lat_e7"],
                        "center_zoom": header["center_zoom"],
                        "center_lon_e7": header["center_lon_e7"],
                        "center_lat_e7": header["center_lat_e7"],
                    },
                    archive_metadata,
                )

                print(f"Processed {tile_count:,} tiles.")

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    # Atomic-ish replacement of the temporary PMTiles.
    os.replace(temp_output, output_path)

    print()
    print("Done.")
    print(f"PMTiles: {output_path}")
    print(f"SQLite:  {database_path}")


if __name__ == "__main__":
    main()
