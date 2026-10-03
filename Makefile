all: ./build/continents/extract.json

# Extract shapefile from zip
./build/shapefile/ne_10m_admin_0_countries.shp: 
	unzip -o ./build/sources/ne_10m_admin_0_countries.zip -d ./build/shapefile

# Extract continent GEOJSONs
./build/continents/extract.json: ./build/shapefile/ne_10m_admin_0_countries.shp
	python tools/extract_continent_boundaries.py -i ./build/shapefile/ne_10m_admin_0_countries.shp -o ./build/continents
