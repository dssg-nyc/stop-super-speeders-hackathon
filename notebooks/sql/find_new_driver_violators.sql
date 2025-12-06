-- ============================================================================
-- FIND NEW DRIVER VIOLATORS (Traffic Violations - Points Based)
-- ============================================================================
-- This query expects two tables to be registered:
--   - historical_data (license_id, violation_year, violation_month, violation_code, points, county)
--   - test_data (license_id, violation_year, violation_month, violation_code, points, county)
--
-- Returns drivers (license_id) that NEWLY crossed the 11+ points threshold
-- when test_data is added to historical_data.
--
-- IMPORTANT: Uses the SAME reference date for both baseline and combined
-- calculations to ensure we identify drivers who crossed the threshold
-- specifically due to violations in the new test data.
--
-- Threshold: 11+ violation points within trailing 24 months
-- Reference: NY Bill A.2299/S.4045
-- ============================================================================

-- Combined: historical + test
WITH combined_data AS (
    SELECT
        license_id,
        violation_year,
        violation_month,
        violation_code,
        points,
        county
    FROM historical_data
    UNION ALL
    SELECT
        license_id,
        violation_year,
        violation_month,
        violation_code,
        points,
        county
    FROM test_data
),

-- Deduplicate by unique violation (same violation should only count once)
-- A violation is unique by: license_id + year + month + violation_code
combined_deduped AS (
    SELECT DISTINCT ON (license_id, violation_year, violation_month, violation_code)
        license_id,
        violation_year,
        violation_month,
        violation_code,
        points,
        county
    FROM combined_data
    WHERE license_id IS NOT NULL
    ORDER BY license_id, violation_year, violation_month, violation_code
),

-- Reference month: use the most recent violation month from COMBINED data
-- This is the "as of" date for our analysis
reference_month AS (
    SELECT MAX(violation_year * 12 + violation_month) as ref_month FROM combined_deduped
),

-- CURRENT violators (historical + test data)
-- Sum points in trailing 24-month window from the reference date
current_violators AS (
    SELECT
        d.license_id,
        SUM(d.points) as total_points,
        COUNT(*) as violation_count,
        STRING_AGG(DISTINCT d.county, ', ' ORDER BY d.county) as counties,
        MIN(d.violation_year * 100 + d.violation_month) as first_violation_ym,
        MAX(d.violation_year * 100 + d.violation_month) as last_violation_ym,
        r.ref_month as reference_month
    FROM combined_deduped d, reference_month r
    WHERE (d.violation_year * 12 + d.violation_month) >= r.ref_month - 24
    GROUP BY d.license_id, r.ref_month
    HAVING SUM(d.points) >= 11
),

-- Deduplicate historical data only
historical_deduped AS (
    SELECT DISTINCT ON (license_id, violation_year, violation_month, violation_code)
        license_id,
        violation_year,
        violation_month,
        violation_code,
        points,
        county
    FROM historical_data
    WHERE license_id IS NOT NULL
    ORDER BY license_id, violation_year, violation_month, violation_code
),

-- BASELINE violators (historical only, but using SAME reference date)
-- This ensures we compare the same 24-month window
baseline_violators AS (
    SELECT
        h.license_id,
        SUM(h.points) as total_points
    FROM historical_deduped h, reference_month r
    WHERE (h.violation_year * 12 + h.violation_month) >= r.ref_month - 24
    GROUP BY h.license_id
    HAVING SUM(h.points) >= 11
),

-- NEW violators = current - baseline
-- These are drivers that crossed the threshold specifically due to new test data
new_violators AS (
    SELECT
        c.license_id,
        c.total_points,
        c.violation_count,
        c.counties,
        -- Convert YYYYMM back to readable format
        CONCAT(c.first_violation_ym // 100, '-', LPAD((c.first_violation_ym % 100)::VARCHAR, 2, '0')) as first_violation,
        CONCAT(c.last_violation_ym // 100, '-', LPAD((c.last_violation_ym % 100)::VARCHAR, 2, '0')) as last_violation,
        c.reference_month,
        'LICENSE_POINTS' as threshold_type,
        '11+ points in 24 months' as threshold_description
    FROM current_violators c
    LEFT JOIN baseline_violators b
        ON c.license_id = b.license_id
    WHERE b.license_id IS NULL
)

SELECT
    license_id,
    total_points,
    violation_count,
    counties,
    first_violation,
    last_violation,
    threshold_type,
    threshold_description
FROM new_violators
ORDER BY total_points DESC, violation_count DESC;
