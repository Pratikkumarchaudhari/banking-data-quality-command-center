-- Executable with SQLite; reference pattern for Snowflake/dbt adaptation.
-- Import data/institutions.csv as institutions first. Never silently deduplicate.
SELECT institution_id, COUNT(*) AS occurrences
FROM institutions GROUP BY institution_id HAVING COUNT(*) > 1;

SELECT bureau, COUNT(*) AS record_count,
       SUM(CASE WHEN TRIM(COALESCE(name,'')) = '' THEN 1 ELSE 0 END) AS missing_names
FROM institutions GROUP BY bureau;

-- Use a fixed evaluation date so published sample results are reproducible.
SELECT institution_id, last_verified FROM institutions
WHERE julianday('2026-09-30') - julianday(last_verified) > 90
   OR julianday(last_verified) > julianday('2026-09-30')
   OR julianday(last_verified) IS NULL;
