-- FloatChat PostgreSQL + PostGIS Schema Definition
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS floats (
    float_id INT PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    status VARCHAR(20) NOT NULL,
    max_depth DOUBLE PRECISION NOT NULL,
    region VARCHAR(50),
    geom geometry(Point, 4326)
);

CREATE TABLE IF NOT EXISTS profiles (
    profile_id VARCHAR(50) PRIMARY KEY,
    float_id INT REFERENCES floats(float_id),
    timestamp TIMESTAMP NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geom geometry(Point, 4326)
);

CREATE TABLE IF NOT EXISTS measurements (
    id SERIAL PRIMARY KEY,
    profile_id VARCHAR(50) REFERENCES profiles(profile_id),
    depth DOUBLE PRECISION NOT NULL,
    pressure DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    salinity DOUBLE PRECISION,
    oxygen DOUBLE PRECISION,
    chlorophyll DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_floats_spatial ON floats USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_measurements_depth ON measurements(depth);
