all: ./build/shapefile/ne_10m_admin_0_countries.shp

# Extract shapefile from zip
./build/shapefile/ne_10m_admin_0_countries.shp: 
	unzip -o ./build/sources/ne_10m_admin_0_countries.zip -d ./build/shapefile
