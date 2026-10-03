all: extract_countries

# Extract shapefile from zip
./build/shapefile/ne_10m_admin_0_countries.shp: 
	unzip -o ./build/sources/ne_10m_admin_0_countries.zip -d ./build/shapefile

# Extract continent GEOJSONs
./build/continents/extract.json: ./build/shapefile/ne_10m_admin_0_countries.shp
	python tools/extract_continent_boundaries.py -i ./build/shapefile/ne_10m_admin_0_countries.shp -o ./build/continents

# Extract continent osm.pbf
extract_continents: ./build/continents/extract.json ./build/sources/planet-260622.osm.pbf
	echo "Extracting continents..."
	osmium extract --config "./build/continents/extract.json" "./build/sources/planet-260622.osm.pbf" --fsync

# Extract country GEOJSONs
./build/country/extract.json: ./build/shapefile/ne_10m_admin_0_countries.shp
	python tools/extract_country_boundaries.py -i ./build/shapefile/ne_10m_admin_0_countries.shp -o ./build/countries

# Extract countries osm.pbf
extract_countries: ./build/country/extract.json extract_continents ./build/continents/Africa.osm.pbf
	echo "Extracting countries..."
	osmium extract --config "./build/countries/Africa-extract.json" "./build/continents/Africa.osm.pbf" --fsync

clean:
	rm -rf build