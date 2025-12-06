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
-- IMPORTANT: Uses the SAME reference date for both baseline and combined
-- calculations to ensure we identify plates that crossed the threshold
-- specifically due to tickets in the new test data.
--
-- Threshold: 16+ speed camera tickets within trailing 12 months
-- Reference: NY Bill A.2299/S.4045
-- ============================================================================

-- Combined: historical + test
WITH combined_data AS (
    SELECT
        issue_date,
        UPPER(plate) as plate,
        summons_number,
        state
    FROM historical_data
    UNION ALL
    SELECT
        issue_date,
        UPPER(plate) as plate,
        summons_number,
        state
    FROM test_data
),

-- Deduplicate by summons_number (same ticket should only count once)
combined_deduped AS (
    SELECT DISTINCT ON (summons_number)
        issue_date,
        plate,
        summons_number,
        state
    FROM combined_data
    WHERE summons_number IS NOT NULL
    ORDER BY summons_number, issue_date DESC
),

-- Reference date: use the most recent ticket date from COMBINED data
-- This is the "as of" date for our analysis
reference_date AS (
    SELECT MAX(issue_date) as ref_date FROM combined_deduped
),

-- CURRENT violators (historical + test data)
-- Count tickets in trailing 12-month window from the reference date
current_violators AS (
    SELECT
        d.plate,
        d.state,
        COUNT(*) as ticket_count,
        MIN(d.issue_date) as first_violation,
        MAX(d.issue_date) as last_violation,
        r.ref_date as reference_date
    FROM combined_deduped d, reference_date r
    WHERE d.issue_date >= r.ref_date - INTERVAL '12 months'
    GROUP BY d.plate, d.state, r.ref_date
    HAVING COUNT(*) >= 16
),

-- Normalize and deduplicate historical data only
historical_deduped AS (
    SELECT DISTINCT ON (summons_number)
        issue_date,
        UPPER(plate) as plate,
        summons_number,
        state
    FROM historical_data
    WHERE summons_number IS NOT NULL
    ORDER BY summons_number, issue_date DESC
),

-- BASELINE violators (historical only, but using SAME reference date)
-- This ensures we compare the same 12-month window
baseline_violators AS (
    SELECT
        h.plate,
        h.state
    FROM historical_deduped h, reference_date r
    WHERE h.issue_date >= r.ref_date - INTERVAL '12 months'
    GROUP BY h.plate, h.state
    HAVING COUNT(*) >= 16
),

-- NEW violators = current - baseline
-- These are plates that crossed the threshold specifically due to new test data
new_violators AS (
    SELECT
        c.plate,
        c.state,
        c.ticket_count,
        c.first_violation,
        c.last_violation,
        c.reference_date,
        'SPEED_CAMERA' as threshold_type,
        '16+ tickets in 12 months' as threshold_description
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
    last_violation,
    reference_date,
    threshold_type,
    threshold_description
FROM new_violators
ORDER BY ticket_count DESC, last_violation DESC;
