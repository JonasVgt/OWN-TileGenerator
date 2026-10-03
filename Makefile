PLANETILER_VERSION := 1.0.0-SNAPSHOT
PLANETILER_JAR := ./planetiler-nautical/target/planetiler-nauticaltiles-$(PLANETILER_VERSION)-with-deps.jar

all: build-tiles

# Extract shapefile from zip
./build/shapefile/ne_10m_admin_0_countries.shp: 
	unzip -o ./build/sources/ne_10m_admin_0_countries.zip -d ./build/shapefile

# Extract continent GEOJSONs
./build/continents/extract.json: ./build/shapefile/ne_10m_admin_0_countries.shp
	python tools/extract_continent_boundaries.py -i ./build/shapefile/ne_10m_admin_0_countries.shp -o ./build/continents

# Extract continent osm.pbf
extract_continents: ./build/continents/extract.json ./build/sources/planet-260622.osm.pbf
	echo "Extracting continents..."
	osmium extract --config "./build/continents/extract.json" "./build/sources/planet-260622.osm.pbf" --fsync --overwrite

# Extract country GEOJSONs
./build/country/extract.json: ./build/shapefile/ne_10m_admin_0_countries.shp
	python tools/extract_country_boundaries.py -i ./build/shapefile/ne_10m_admin_0_countries.shp -o ./build/countries

# Extract countries osm.pbf
extract_countries: ./build/country/extract.json ./build/continents/Africa.osm.pbf
	echo "Extracting countries..."
	osmium extract --config "./build/countries/Africa-extract-2.json" "./build/continents/Africa.osm.pbf" --fsync --overwrite

# Initialize Planetiler
$(PLANETILER_JAR):
	cd ./planetiler-nautical && \
	./mvnw clean package

# Build tiles
build-tiles: $(PLANETILER_JAR)
	echo "Building tiles..."
	java \
	-Xmx20g \
	-XX:MaxHeapFreeRatio=40 \
	-jar "$(PLANETILER_JAR)" \
	--fetch-wikidata \
	--download \
	--osm-path="./build/countries/Ethiopia.osm.pbf" \
	--output="./build/result/test.pmtiles" \
	--nodemap-type=sparsearray --storage=ram \
	--download_dir="./build/sources" \
	--tmpdir="./build/tmp" \
	--force

clean:
	rm -rf build