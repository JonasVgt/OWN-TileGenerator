let
  pkgs = import <nixpkgs> {};

  python = pkgs.python3;

  mapbox-vector-tile = python.pkgs.buildPythonPackage rec {
    pname = "mapbox_vector_tile";
    version = "2.2.0";

    src = pkgs.fetchPypi {
      inherit pname version;
      hash = "sha256-n78ulIkEKcza+OBHAZ3MrdnesD9bKum1xVYdJ6IKDrM=";
    };

    pyproject = true;

    build-system = [
      python.pkgs.poetry-core
    ];

    dependencies = [
      python.pkgs.shapely
      python.pkgs.protobuf6
      python.pkgs.numpy
      python.pkgs.pyclipper
    ];

    doCheck = false;
  };

  pmtiles = python.pkgs.buildPythonPackage rec {
    pname = "pmtiles";
    version = "3.8.1";

    src = pkgs.fetchPypi {
      inherit pname version;
      hash = "sha256-D1lKYbN/ygOfBhYkKHgfdqQjP1vuqUREcC8NxB8g8Ac=";
    };

    pyproject = true;

    build-system = [
      python.pkgs.setuptools
    ];

    dependencies = [
    ];

    doCheck = false;
  };
in
  pkgs.mkShell {
    packages = [
      (python.withPackages (python-pkgs: [
        python-pkgs.geopandas
        mapbox-vector-tile
        pmtiles
      ]))
      pkgs.osmium-tool
      pkgs.zip
    ];
  }
