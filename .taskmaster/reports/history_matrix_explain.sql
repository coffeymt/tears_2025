-- EXPLAIN SQL for the history matrix raw query
-- Replace {{YEAR}} before running, or use the accompanying Python runner to substitute automatically.

SELECT
  e.id         AS entry_id,
  e.name       AS entry_name,
  w.week_number,
  p.team_id
FROM picks p
JOIN entries e ON p.entry_id = e.id
JOIN weeks w   ON p.week_id = w.id
WHERE w.season_year = {{YEAR}}
ORDER BY e.id, w.week_number;
