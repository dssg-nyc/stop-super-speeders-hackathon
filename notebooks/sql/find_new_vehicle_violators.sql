-- ============================================================================
-- FIND NEW SPEED CAMERA VIOLATORS
-- ============================================================================
-- This query expects two tables to be registered:
--   - historical_data (plate, state, summons_number, issue_date)
--   - test_data (plate, state, summons_number, issue_date)
--
-- Returns plates that NEWLY crossed the 16+ ticket threshold when
-- test_data is added to historical_data.
--
-- Threshold: 16+ speed camera tickets within 12 months
-- ============================================================================

-- Combined: historical + test
WITH combined_data AS (
    SELECT * FROM historical_data
    UNION ALL
    SELECT * FROM test_data
),

-- Deduplicate by summons_number
deduplicated AS (
    SELECT DISTINCT ON (summons_number)
        issue_date,
        plate,
        summons_number,
        state
    FROM combined_data
    WHERE summons_number IS NOT NULL
    ORDER BY summons_number, issue_date
),

-- Reference date from combined data
reference_date_combined AS (
    SELECT MAX(issue_date) as ref_date FROM deduplicated
),

-- CURRENT violators (historical + test data)
current_violators AS (
    SELECT
        d.plate,
        d.state,
        COUNT(*) as ticket_count,
        MIN(d.issue_date) as first_violation,
        MAX(d.issue_date) as last_violation
    FROM deduplicated d, reference_date_combined r
    WHERE d.issue_date >= r.ref_date - INTERVAL '12 months'
    GROUP BY d.plate, d.state
    HAVING COUNT(*) >= 16
),

-- BASELINE violators (historical only)
reference_date_historical AS (
    SELECT MAX(issue_date) as ref_date FROM historical_data
),

baseline_violators AS (
    SELECT
        h.plate,
        h.state
    FROM historical_data h, reference_date_historical r
    WHERE h.issue_date >= r.ref_date - INTERVAL '12 months'
    GROUP BY h.plate, h.state
    HAVING COUNT(*) >= 16
),

-- NEW violators = current - baseline
new_violators AS (
    SELECT
        c.plate,
        c.state,
        c.ticket_count,
        c.first_violation,
        c.last_violation
    FROM current_violators c
    LEFT JOIN baseline_violators b
        ON c.plate = b.plate AND c.state = b.state
    WHERE b.plate IS NULL
)

SELECT
    plate,
    state,
    ticket_count,
    first_violation,
    last_violation
FROM new_violators
ORDER BY ticket_count DESC;
