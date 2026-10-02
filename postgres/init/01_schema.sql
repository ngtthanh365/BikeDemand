CREATE TABLE IF NOT EXISTS trips (
    ride_id VARCHAR(100) PRIMARY KEY,

    rideable_type VARCHAR(30),

    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP NOT NULL,

    start_station_name VARCHAR(255),
    start_station_id VARCHAR(50),

    end_station_name VARCHAR(255),
    end_station_id VARCHAR(50),

    start_lat DOUBLE PRECISION,
    start_lng DOUBLE PRECISION,

    end_lat DOUBLE PRECISION,
    end_lng DOUBLE PRECISION,

    member_casual VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS hourly_demand (
    id BIGSERIAL PRIMARY KEY,

    timestamp TIMESTAMP NOT NULL UNIQUE,

    date DATE NOT NULL,
    hour INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    month INTEGER NOT NULL,

    is_weekend BOOLEAN NOT NULL,

    member_count INTEGER NOT NULL,
    casual_count INTEGER NOT NULL,

    electric_count INTEGER NOT NULL,
    classic_count INTEGER NOT NULL,

    demand INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,

    prediction_time TIMESTAMP NOT NULL,
    target_time TIMESTAMP NOT NULL,

    predicted_demand DOUBLE PRECISION NOT NULL,

    actual_demand INTEGER,

    model_name VARCHAR(100),
    model_version VARCHAR(50)
);