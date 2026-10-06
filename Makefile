PLANETILER_VERSION := 1.0.0-SNAPSHOT
PLANETILER_JAR := ./planetiler-nautical/target/planetiler-nauticaltiles-$(PLANETILER_VERSION)-with-deps.jar
include config.mk

all: $(TARGETS) ./build/result/datasets.json

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
extract-country-boundaries: ./build/shapefile/ne_10m_admin_0_countries.shp
	python tools/extract_country_boundaries.py -i $< -o ./build/countries

# Extract countries osm.pbf
extract-countries: extract-country-boundaries
	for dir in ./build/countries/*/; do \
		continent=$$(basename "$$dir"); \
		for file in $${dir}extract-*.json; do \
			echo "$$file"; \
			osmium extract --config "$$file" "./build/continents/$${continent}.osm.pbf" --fsync --overwrite; \
		done; \
	done

# Initialize Planetiler
$(PLANETILER_JAR):
	cd ./planetiler-nautical && \
	./mvnw clean package

# Build tiles
./build/result/%.pmtiles: ./build/countries/%.osm.pbf $(PLANETILER_JAR) 
	echo "Building tiles..."
	java \
	-Xmx20g \
	-XX:MaxHeapFreeRatio=40 \
	-jar "$(PLANETILER_JAR)" \
	--fetch-wikidata \
	--download \
	--osm-path="$<" \
	--output="$@" \
	--nodemap-type=sparsearray --storage=ram \
	--download_dir="./build/sources" \
	--tmpdir="./build/tmp" \
	--force

build-tiles: build/result/Western_Sahara.pmtiles

./build/result/datasets.json:
	python tools/generate_datasets_json.py -i ./build/result/ -o $@

configure: ./build/shapefile/ne_10m_admin_0_countries.shp
	python tools/generate_config.py -i "$<" -o "config.mk"

clean:
	rm -rf build