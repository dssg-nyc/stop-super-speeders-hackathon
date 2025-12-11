
-- ============ SEQUENCES (define before tables) ============

CREATE SEQUENCE IF NOT EXISTS seq_violation_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_camera_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_location_id START 1;

-- ============ FACT TABLES ============

-- Core violations fact table (combines speed cameras + traffic violations)
CREATE TABLE IF NOT EXISTS fct_violations (
    violation_id BIGINT PRIMARY KEY DEFAULT nextval('seq_violation_id'),
    
    -- Identity
    summons_number BIGINT,
    driver_id VARCHAR,
    driver_age INTEGER,
    
    -- Violation Details
    violation_code VARCHAR NOT NULL,
    violation_description VARCHAR,
    points_assessed INTEGER DEFAULT 0,
    
    -- Location
    county VARCHAR,
    precinct INTEGER,
    street_name VARCHAR,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    
    -- Temporal
    violation_date DATE NOT NULL,
    violation_year INTEGER,
    violation_month INTEGER,
    violation_day_of_week VARCHAR,
    violation_hour INTEGER,
    
    -- Financial
    fine_amount DECIMAL(10,2) DEFAULT 0.00,
    penalty_amount DECIMAL(10,2) DEFAULT 0.00,
    payment_amount DECIMAL(10,2) DEFAULT 0.00,
    interest_amount DECIMAL(10,2) DEFAULT 0.00,
    
    -- Status
    violation_status VARCHAR DEFAULT 'UNKNOWN',
    judgment_date DATE,
    
    -- Metadata
    data_source VARCHAR,
    ingested_at TIMESTAMP DEFAULT now(),
    
    CONSTRAINT chk_fine_positive CHECK (fine_amount >= 0),
    CONSTRAINT chk_year_valid CHECK (violation_year >= 2000 AND violation_year <= year(now()) + 1),
    CONSTRAINT chk_month_valid CHECK (violation_month >= 1 AND violation_month <= 12),
    CONSTRAINT chk_age_valid CHECK (driver_age IS NULL OR (driver_age >= 16 AND driver_age <= 120))
);

-- Speed camera specific facts
CREATE TABLE IF NOT EXISTS fct_speed_cameras (
    camera_id BIGINT PRIMARY KEY DEFAULT nextval('seq_camera_id'),
    
    -- Location
    camera_name VARCHAR,
    street_name VARCHAR NOT NULL,
    county VARCHAR,
    precinct INTEGER,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    
    -- Activity
    total_violations_recorded BIGINT DEFAULT 0,
    first_violation_date DATE,
    last_violation_date DATE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    deployment_date DATE,
    deactivation_date DATE,
    
    -- Metadata
    ingested_at TIMESTAMP DEFAULT now()
);

-- ============ DIMENSION TABLES ============

-- Geographic dimension
CREATE TABLE IF NOT EXISTS dim_location (
    location_id BIGINT PRIMARY KEY DEFAULT nextval('seq_location_id'),
    
    street_name VARCHAR,
    cross_street VARCHAR,
    precinct INTEGER,
    county VARCHAR,
    borough VARCHAR,
    
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    
    community_board VARCHAR,
    police_district VARCHAR,
    
    -- Computed metrics
    risk_score_current DECIMAL(5,2),
    violations_last_30_days BIGINT DEFAULT 0,
    violations_last_90_days BIGINT DEFAULT 0,
    violations_all_time BIGINT DEFAULT 0,
    
    last_updated TIMESTAMP DEFAULT now()
);

-- Violation type dimension
CREATE TABLE IF NOT EXISTS dim_violation_type (
    violation_code VARCHAR PRIMARY KEY,
    
    violation_description VARCHAR NOT NULL,
    violation_category VARCHAR,
    severity_level VARCHAR,  -- HIGH, MEDIUM, LOW
    
    default_fine_amount DECIMAL(10,2),
    default_points INTEGER,
    
    is_speed_related BOOLEAN DEFAULT FALSE
);

-- Time dimension
CREATE TABLE IF NOT EXISTS dim_time (
    date_key DATE PRIMARY KEY,
    
    year INTEGER,
    month INTEGER,
    day_of_month INTEGER,
    day_of_week VARCHAR,
    week_of_year INTEGER,
    
    is_weekend BOOLEAN,
    is_holiday BOOLEAN DEFAULT FALSE,
    
    quarter INTEGER,
    fiscal_period VARCHAR
);

-- Driver/License dimension
CREATE TABLE IF NOT EXISTS dim_driver (
    driver_id VARCHAR PRIMARY KEY,
    
    -- Demographics
    estimated_age_at_first_violation INTEGER,
    
    -- Violation History
    total_violations BIGINT DEFAULT 0,
    total_points_accumulated INTEGER DEFAULT 0,
    first_violation_date DATE,
    last_violation_date DATE,
    
    -- Recidivism
    is_repeat_offender BOOLEAN DEFAULT FALSE,
    violations_last_year BIGINT DEFAULT 0,
    violations_last_month BIGINT DEFAULT 0,
    
    -- Most common
    most_common_violation_code VARCHAR,
    
    last_updated TIMESTAMP DEFAULT now()
);

-- ============ AGGREGATE TABLES ============

-- Risk scores by location (for enforcement prioritization)
CREATE TABLE IF NOT EXISTS agg_risk_scores_by_location (
    location_id BIGINT PRIMARY KEY,
    
    street_name VARCHAR,
    county VARCHAR,
    borough VARCHAR,
    precinct INTEGER,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    
    -- Metrics
    violations_last_30_days BIGINT,
    violations_last_90_days BIGINT,
    violations_all_time BIGINT,
    
    -- Risk Score (0-100)
    risk_score DECIMAL(5,2),
    risk_tier VARCHAR,  -- CRITICAL, HIGH, MEDIUM, LOW
    
    -- Context
    violation_types_count INTEGER,
    avg_fine DECIMAL(10,2),
    avg_points DECIMAL(5,2),
    
    computed_date DATE DEFAULT today()
);

-- Trends over time by borough/precinct
CREATE TABLE IF NOT EXISTS agg_violations_by_time_borough (
    time_key DATE,
    borough VARCHAR,
    precinct INTEGER,
    day_of_week VARCHAR,
    violation_hour INTEGER,
    
    violation_count BIGINT,
    avg_fine DECIMAL(10,2),
    avg_points DECIMAL(5,2),
    
    PRIMARY KEY (time_key, borough, precinct, day_of_week, violation_hour)
);

-- Top repeat offenders
CREATE TABLE IF NOT EXISTS agg_repeat_offenders (
    driver_id VARCHAR PRIMARY KEY,
    
    violation_count BIGINT,
    total_points BIGINT,
    estimated_avg_age INTEGER,
    
    first_violation_date DATE,
    last_violation_date DATE,
    
    offender_tier VARCHAR,  -- CRITICAL, HIGH, MEDIUM
    violations_last_year BIGINT,
    
    most_common_violation_code VARCHAR,
    most_common_county VARCHAR,
    
    computed_date DATE DEFAULT today()
);

-- ============ INDEXES ============

CREATE INDEX IF NOT EXISTS idx_violations_date ON fct_violations(violation_date);
CREATE INDEX IF NOT EXISTS idx_violations_precinct ON fct_violations(precinct);
CREATE INDEX IF NOT EXISTS idx_violations_county ON fct_violations(county);
CREATE INDEX IF NOT EXISTS idx_violations_driver ON fct_violations(driver_id);
CREATE INDEX IF NOT EXISTS idx_violations_source ON fct_violations(data_source);

CREATE INDEX IF NOT EXISTS idx_cameras_location ON fct_speed_cameras(county, precinct);
CREATE INDEX IF NOT EXISTS idx_cameras_active ON fct_speed_cameras(is_active);
