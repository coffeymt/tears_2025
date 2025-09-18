-- Recommended index statements for history matrix query profiling (Postgres / Supabase)
-- Run these against your Supabase database if EXPLAIN ANALYZE shows sequential scans on these columns.

-- Indexes on picks to support joins and filtering by entry/week
CREATE INDEX IF NOT EXISTS idx_picks_entry_id ON picks (entry_id);
CREATE INDEX IF NOT EXISTS idx_picks_week_id  ON picks (week_id);
-- Composite index that may help the ordering/grouping by entry then week
CREATE INDEX IF NOT EXISTS idx_picks_entry_week ON picks (entry_id, week_id);

-- Index on weeks for season_year filtering and ordering
CREATE INDEX IF NOT EXISTS idx_weeks_season_year_week_number ON weeks (season_year, week_number);

-- Optional: If you frequently filter by season_year in other queries, an index on games.week_id -> weeks may be helpful but is not created here.
