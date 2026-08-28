-- FloatChat PostgreSQL + PostGIS Schema Definition
CREATE EXTENSION IF NOT EXISTS postgis;
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION
    WHEN undefined_file THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS floats (
    float_id INT PRIMARY KEY,
    platform_number VARCHAR(32),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    status VARCHAR(20) NOT NULL,
    max_depth DOUBLE PRECISION NOT NULL,
    region VARCHAR(50),
    geom geometry(Point, 4326),
    source_file TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS profiles (
    profile_id VARCHAR(50) PRIMARY KEY,
    float_id INT REFERENCES floats(float_id),
    timestamp TIMESTAMP NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geom geometry(Point, 4326),
    profile_direction VARCHAR(20),
    source_file TEXT
);

CREATE TABLE IF NOT EXISTS measurements (
    id SERIAL PRIMARY KEY,
    profile_id VARCHAR(50) REFERENCES profiles(profile_id),
    depth DOUBLE PRECISION NOT NULL,
    pressure DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    salinity DOUBLE PRECISION,
    oxygen DOUBLE PRECISION,
    chlorophyll DOUBLE PRECISION,
    bbp700 DOUBLE PRECISION,
    nitrate DOUBLE PRECISION,
    ph DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_floats_spatial ON floats USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_profiles_spatial ON profiles USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_profiles_timestamp ON profiles(timestamp);
CREATE INDEX IF NOT EXISTS idx_measurements_float ON measurements(profile_id);
CREATE INDEX IF NOT EXISTS idx_measurements_depth ON measurements(depth);
