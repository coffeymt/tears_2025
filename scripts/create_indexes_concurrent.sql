-- Production index creation using CONCURRENTLY (run outside a transaction)
-- This file uses DO blocks to check for existing indexes and then executes
-- CREATE INDEX CONCURRENTLY when necessary. Run it with psql (not inside a transaction):
-- Example (PowerShell): $env:DATABASE_URL='postgresql://...'; psql $env:DATABASE_URL -f scripts/create_indexes_concurrent.sql

DO $$
BEGIN
	IF NOT EXISTS (
		SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
		WHERE c.relkind = 'i' AND c.relname = 'idx_games_home_team_id'
	) THEN
		EXECUTE 'CREATE INDEX CONCURRENTLY idx_games_home_team_id ON games(home_team_id)';
	END IF;
END$$;

DO $$
BEGIN
	IF NOT EXISTS (
		SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
		WHERE c.relkind = 'i' AND c.relname = 'idx_games_away_team_id'
	) THEN
		EXECUTE 'CREATE INDEX CONCURRENTLY idx_games_away_team_id ON games(away_team_id)';
	END IF;
END$$;

DO $$
BEGIN
	IF NOT EXISTS (
		SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
		WHERE c.relkind = 'i' AND c.relname = 'idx_picks_team_id'
	) THEN
		EXECUTE 'CREATE INDEX CONCURRENTLY idx_picks_team_id ON picks(team_id)';
	END IF;
END$$;
