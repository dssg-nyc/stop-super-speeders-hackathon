-- ============================================================================
-- FIND NEW DRIVER VIOLATORS (Traffic Violations - Points Based)
-- ============================================================================
-- This query expects two tables to be registered:
--   - historical_data (license_id, issue_date, points)
--   - test_data (license_id, issue_date, points)
--
-- Returns drivers (license_id) that NEWLY crossed the 11+ points threshold
-- when test_data is added to historical_data.
--
-- Threshold: 11+ points within 24 months
-- ============================================================================

-- Combined: historical + test
WITH combined_data AS (
    SELECT * FROM historical_data
    UNION ALL
    SELECT * FROM test_data
),

-- Reference date from combined data
reference_date_combined AS (
    SELECT MAX(issue_date) as ref_date FROM combined_data
),

-- CURRENT violators (historical + test data)
current_violators AS (
    SELECT
        c.license_id,
        SUM(c.points) as total_points,
        COUNT(*) as violation_count,
        MIN(c.issue_date) as first_violation,
        MAX(c.issue_date) as last_violation
    FROM combined_data c, reference_date_combined r
    WHERE c.issue_date >= r.ref_date - INTERVAL '24 months'
      AND c.license_id IS NOT NULL
    GROUP BY c.license_id
    HAVING SUM(c.points) >= 11
),

-- BASELINE violators (historical only)
reference_date_historical AS (
    SELECT MAX(issue_date) as ref_date FROM historical_data
),

baseline_violators AS (
    SELECT
        h.license_id
    FROM historical_data h, reference_date_historical r
    WHERE h.issue_date >= r.ref_date - INTERVAL '24 months'
      AND h.license_id IS NOT NULL
    GROUP BY h.license_id
    HAVING SUM(h.points) >= 11
),

-- NEW violators = current - baseline
new_violators AS (
    SELECT
        c.license_id,
        c.total_points,
        c.violation_count,
        c.first_violation,
        c.last_violation
    FROM current_violators c
    LEFT JOIN baseline_violators b
        ON c.license_id = b.license_id
    WHERE b.license_id IS NULL
)

SELECT
    license_id,
    total_points,
    violation_count,
    first_violation,
    last_violation
FROM new_violators
ORDER BY total_points DESC;
