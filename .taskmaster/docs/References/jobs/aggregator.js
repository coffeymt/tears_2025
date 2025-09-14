const { syncFromEspn } = require('../services/espnScoreboard');
const { updatePickStatusesForWeek } = require('../services/pickStatus');
const { writeSnapshotToGcs, readSnapshotFromGcs } = require('../utils/gcs');

// Build a compact reveal snapshot payload for a week id.
// This produces a small JSON containing only the pieces the frontend Reveal needs
// (counts distribution, games, and KPIs). We intentionally omit the full picks array
// to keep the snapshot small; detailed picks remain available from /api/weeks/:id/picks or grid endpoints.
async function buildRevealSnapshot(weekId) {
  const models = require('../models');
  const week = await models.weeks.findById(weekId);
  if (!week) throw Object.assign(new Error('WEEK_NOT_FOUND'), { code: 'WEEK_NOT_FOUND' });

  // Check if this is the current week and if it's locked
  const current = await models.weeks.findCurrent();
  const isCurrentWeek = current && current.id === week.id;
  const now = new Date();
  const lockTime = week.lock_time ? new Date(week.lock_time) : null;
  const isLocked = !!(lockTime && now >= lockTime);
  
  // Debug logging for lock time checking
  if (isCurrentWeek) {
    console.log(`[aggregator] Current week ${week.id} (${week.season_year} W${week.week_number})`);
    console.log(`[aggregator] Lock time: ${lockTime ? lockTime.toISOString() : 'null'}`);
    console.log(`[aggregator] Current time: ${now.toISOString()}`);
    console.log(`[aggregator] Is locked: ${isLocked}`);
  }
  
  // For current week before lock time, return minimal data with defaults
  if (isCurrentWeek && !isLocked) {
    console.log(`[aggregator] Returning minimal data for unlocked current week ${week.id}`);
    return {
      week: {
        id: week.id,
        season_year: week.season_year,
        week_number: week.week_number,
        lock_time: week.lock_time
      },
      games: [], // Empty games array before lock
      counts: {}, // Empty pick distribution before lock
      kpis: { wins: 0, losses: 0, tbd: 0, total: 0, alive_count: 0, no_pick_count: 0 },
      leaderboard: [], // Empty leaderboard before lock
      alive_count: 0,
      generated_at: new Date().toISOString()
    };
  }

  // For locked weeks or non-current weeks, proceed with full data aggregation
  const [games, picks, entries, users] = await Promise.all([
    models.games.findByWeek(week.id),
    models.picks.findByWeek(week.id),
    models.entries.findAll(),
    models.users.findAll()
  ]);

  const teamsFile = await Promise.resolve().then(() => {
    try { return require('../data/nfl_teams.json'); } catch { return { teams: [] }; }
  });

  const entryById = new Map((entries || []).map(e => [e.id, e]));
  const userById = new Map((users || []).map(u => [u.id, u]));
  const teamByAbbr = new Map((teamsFile.teams || []).map(t => [t.abbreviation, t]));

  // Build a map of team -> game result (win/loss/tbd)
  const gameResultByTeam = new Map();
  for (const g of games || []) {
    if (!g || !g.home_team_abbr || !g.away_team_abbr) continue;
    const isFinal = g.status === 'final' && typeof g.home_score === 'number' && typeof g.away_score === 'number';
    if (isFinal) {
      if (g.home_score === g.away_score) {
        gameResultByTeam.set(g.home_team_abbr, 'loss');
        gameResultByTeam.set(g.away_team_abbr, 'loss');
      } else {
        const homeWon = g.home_score > g.away_score;
        const winner = homeWon ? g.home_team_abbr : g.away_team_abbr;
        const loser = homeWon ? g.away_team_abbr : g.home_team_abbr;
        if (winner) gameResultByTeam.set(winner, 'win');
        if (loser) gameResultByTeam.set(loser, 'loss');
      }
    } else {
      // future or in-progress -> mark as tbd if not already set
      if (!gameResultByTeam.has(g.home_team_abbr)) gameResultByTeam.set(g.home_team_abbr, 'tbd');
      if (!gameResultByTeam.has(g.away_team_abbr)) gameResultByTeam.set(g.away_team_abbr, 'tbd');
    }
  }

  // Distribution counts by team abbr (only count actual picks with a team)
  const counts = {};
  for (const p of picks || []) {
    if (!p || !p.team_abbr) continue;
    counts[p.team_abbr] = (counts[p.team_abbr] || 0) + 1;
  }

  // KPIs: compute wins/losses/tbd by using pick status directly
  let wins = 0, losses = 0, tbd = 0;
  for (const p of picks || []) {
    if (!p) continue;
    // Use pick status directly since it's already calculated
    if (p.status === 'win') wins += 1;
    else if (p.status === 'loss') losses += 1;
    else tbd += 1; // includes 'tbd', 'no_pick', and any other statuses
  }
  const total = wins + losses + tbd;

  // alive_count = picks not eliminated
  const alive_count = (picks || []).filter(p => p && p.status !== 'loss' && p.status !== 'eliminated').length;
  const no_pick_count = (picks || []).filter(p => p && (p.status === 'no_pick' || !p.team_abbr)).length;

  // Optional light leaderboard: aggregate wins/losses by user for quick display
  const leaderboardByUser = new Map();
  for (const p of picks || []) {
    if (!p || !p.entry_id) continue;
    const entry = entryById.get(p.entry_id) || {};
    const user = userById.get(entry.user_id) || {};
    const uid = user.id || entry.user_id || 'unknown';
    if (!leaderboardByUser.has(uid)) leaderboardByUser.set(uid, { user_id: uid, user_name: (user.first_name || user.last_name) ? `${(user.first_name || '').trim()} ${(user.last_name || '').trim()}`.trim() : (user.email || ''), wins: 0, losses: 0, tbd: 0 });
    const rec = leaderboardByUser.get(uid);
    const res = gameResultByTeam.get(p.team_abbr) || 'tbd';
    if (res === 'win') rec.wins += 1; else if (res === 'loss') rec.losses += 1; else rec.tbd += 1;
  }
  const leaderboard = Array.from(leaderboardByUser.values()).sort((a, b) => (b.wins - a.wins) || (a.user_name || '').localeCompare(b.user_name || ''));

  const snapshot = {
    week: {
      id: week.id,
      season_year: week.season_year,
      week_number: week.week_number,
      lock_time: week.lock_time
    },
    games: games || [],
    // Small distribution map used by the Dashboard pick distribution
    counts,
    // KPIs helpful to render Wins/Losses/TBD/Total without fetching picks client-side
    kpis: { wins, losses, tbd, total, alive_count, no_pick_count },
    // Lightweight leaderboard summary for the Grid/summary pages
    leaderboard,
    // Keep alive_count at top level for backward compatibility with frontend fallback
    alive_count,
    generated_at: new Date().toISOString()
  };

  return snapshot;
}

// Run aggregator for a given week (optionally runs syncFromEspn first)
async function runAggregator({ seasonYear, weekNumber, runSync = false } = {}) {
  // If seasonYear/weekNumber not provided, attempt to detect current week
  const models = require('../models');
  let week = null;
  if (Number.isInteger(seasonYear) && Number.isInteger(weekNumber)) {
    const weeks = await models.weeks.findAll();
    week = (weeks || []).find(w => w.season_year === seasonYear && w.week_number === weekNumber) || null;
  } else {
    week = await models.weeks.findCurrent();
  }
  if (!week) throw Object.assign(new Error('Week not found'), { code: 'WEEK_NOT_FOUND' });

  // Check if this is the current week and if it's locked
  const current = await models.weeks.findCurrent();
  const isCurrentWeek = current && current.id === week.id;
  const now = new Date();
  const lockTime = week.lock_time ? new Date(week.lock_time) : null;
  const isLocked = !!(lockTime && now >= lockTime);

  // Debug logging for lock time checking
  if (isCurrentWeek) {
    console.log(`[runAggregator] Current week ${week.id} (${week.season_year} W${week.week_number})`);
    console.log(`[runAggregator] Lock time: ${lockTime ? lockTime.toISOString() : 'null'}`);
    console.log(`[runAggregator] Current time: ${now.toISOString()}`);
    console.log(`[runAggregator] Is locked: ${isLocked}`);
  }

  // Only run sync and pick status updates for locked weeks or non-current weeks
  if (!isCurrentWeek || isLocked) {
    if (runSync) {
      try {
        await syncFromEspn({ seasonYear: week.season_year, weekNumber: week.week_number });
      } catch (e) {
        // continue even if sync fails; aggregator can still build snapshot from existing data
        console.warn('aggregator: syncFromEspn failed:', e && e.message);
      }
    }

    // Ensure pick statuses are up-to-date before snapshot
    try {
      await updatePickStatusesForWeek(week.id);
    } catch (e) {
      console.warn('aggregator: updatePickStatusesForWeek failed:', e && e.message);
    }
  } else {
    console.log(`aggregator: skipping sync/status updates for unlocked current week ${week.id} (${week.season_year} week ${week.week_number})`);
  }

  const snapshot = await buildRevealSnapshot(week.id);

  // Persist snapshot to GCS
  const bucket = process.env.GCS_BUCKET;
  const prefix = process.env.GCS_PREFIX || '';
  if (!bucket) throw new Error('GCS_BUCKET env var not set');
  const key = `${prefix}snapshots/week-${week.id}-reveal-snapshot.json`;
  await writeSnapshotToGcs(bucket, key, JSON.stringify(snapshot));

  return { ok: true, week_id: week.id, gcs_key: key };
}

// Build a season-level history matrix (same shape as /api/history/matrix)
async function buildHistoryMatrix(seasonYear) {
  const models = require('../models');
  const weeks = await models.weeks.findAll();
  if (!weeks || weeks.length === 0) return { season_year: null, weeks: [], entries: [] };

  const current = await models.weeks.findCurrent();
  // Determine seasonYear if not provided
  const season = Number.isInteger(seasonYear)
    ? seasonYear
    : (current && typeof current.season_year === 'number')
      ? current.season_year
      : weeks.reduce((max, w) => (typeof w.season_year === 'number' && w.season_year > max ? w.season_year : max), -Infinity);

  // Filter season weeks and sort by week_number
  const seasonWeeks = (weeks || []).filter(w => w.season_year === season)
    .sort((a, b) => (a.week_number || 0) - (b.week_number || 0));

  // Helper to decide if a week should be visible (after lock OR prior to current week in same season)
  const visibleWeeks = [];
  for (const w of seasonWeeks) {
    const afterLock = !!(w && w.lock_time && (new Date() >= new Date(w.lock_time)));
    const priorInSeason = !!(current && w.season_year === current.season_year && typeof w.week_number === 'number' && typeof current.week_number === 'number' && w.week_number < current.week_number);
    if (afterLock || priorInSeason) visibleWeeks.push(w);
  }

  // Preload games and results per week
  const winnersByWeek = new Map(); // weekId -> Set of team_abbr that won
  const losersByWeek = new Map(); // weekId -> Set of team_abbr that lost
  for (const w of visibleWeeks) {
    const games = await models.games.findByWeek(w.id);
    const winners = new Set();
    const losers = new Set();
    for (const g of games || []) {
      if (g && g.status === 'final' && typeof g.home_score === 'number' && typeof g.away_score === 'number') {
        if (g.home_score === g.away_score) {
          if (g.home_team_abbr) losers.add(g.home_team_abbr);
          if (g.away_team_abbr) losers.add(g.away_team_abbr);
        } else {
          const homeWon = g.home_score > g.away_score;
          const winner = homeWon ? g.home_team_abbr : g.away_team_abbr;
          const loser = homeWon ? g.away_team_abbr : g.home_team_abbr;
          if (winner) winners.add(winner);
          if (loser) losers.add(loser);
        }
      }
    }
    winnersByWeek.set(w.id, winners);
    losersByWeek.set(w.id, losers);
  }

  // Load entries and users
  const [entriesAll, users] = await Promise.all([
    models.entries.findAll(),
    models.users.findAll()
  ]);
  const userById = new Map((users || []).map(u => [u.id, u]));
  const entries = (entriesAll || []).filter(e => !!e).map(e => ({
    id: e.id,
    name: e.name,
    user_id: e.user_id,
    user_name: (() => {
      const u = userById.get(e.user_id) || {};
      const full = `${(u.first_name || '').trim()} ${(u.last_name || '').trim()}`.trim();
      return full || u.email || e.user_id;
    })(),
    is_eliminated: !!e.is_eliminated
  }));

  // Build picks map: entryId -> week_number -> { team_abbr, result }
  const byEntry = new Map();
  for (const w of visibleWeeks) {
    const picks = await models.picks.findByWeek(w.id);
    const winners = winnersByWeek.get(w.id) || new Set();
    const losers = losersByWeek.get(w.id) || new Set();
    for (const p of picks || []) {
      if (!p || !p.entry_id) continue;
      const team = p.team_abbr;
      const result = winners.has(team) ? 'win' : (losers.has(team) ? 'loss' : 'tbd');
      if (!byEntry.has(p.entry_id)) byEntry.set(p.entry_id, new Map());
      byEntry.get(p.entry_id).set(w.week_number, { team_abbr: team, result });
    }
  }

  const matrixEntries = entries.map(e => {
    const map = byEntry.get(e.id) || new Map();
    // Determine eliminated week: first loss
    let eliminated_week = null;
    for (const w of visibleWeeks) {
      const cell = map.get(w.week_number);
      if (cell && cell.result === 'loss') { eliminated_week = w.week_number; break; }
    }
    // Serialize picks by week number
    const picks = {};
    for (const w of visibleWeeks) {
      const cell = map.get(w.week_number);
      if (cell) picks[w.week_number] = cell;
    }
    return {
      id: e.id,
      name: e.name,
      user_name: e.user_name,
      eliminated_week,
      picks
    };
  });

  const payload = {
    season_year: season,
    weeks: visibleWeeks.map(w => ({ id: w.id, week_number: w.week_number, lock_time: w.lock_time })),
    entries: matrixEntries
  };
  return payload;
}

// Persist season matrix to GCS
async function persistHistoryMatrixToGcs(seasonYear) {
  const bucket = process.env.GCS_BUCKET;
  const prefix = process.env.GCS_PREFIX || '';
  if (!bucket) throw new Error('GCS_BUCKET env var not set');
  const matrix = await buildHistoryMatrix(seasonYear);
  const key = `${prefix}snapshots/season-${seasonYear || matrix.season_year}-matrix.json`;
  await writeSnapshotToGcs(bucket, key, JSON.stringify(matrix));
  return { ok: true, season_year: seasonYear || matrix.season_year, gcs_key: key };
}

// Create snapshots for old (locked) weeks to speed up retrieval
async function generateSnapshotsForOldWeeks(options = {}) {
  const { seasonYear = null, force = false, daysThreshold = 7 } = options;
  const models = require('../models');
  
  // Find weeks that are locked and older than the threshold
  const allWeeks = await models.weeks.findAll();
  const cutoffDate = new Date(Date.now() - (daysThreshold * 24 * 60 * 60 * 1000));
  
  const oldWeeks = (allWeeks || []).filter(w => {
    if (!w || !w.lock_time) return false;
    if (seasonYear && w.season_year !== seasonYear) return false;
    
    const lockTime = new Date(w.lock_time);
    return lockTime < cutoffDate; // Week is locked and older than threshold
  });
  
  if (oldWeeks.length === 0) {
    return { ok: true, message: 'No old weeks found to snapshot', snapshots_created: 0 };
  }
  
  const bucket = process.env.GCS_BUCKET;
  const prefix = process.env.GCS_PREFIX || '';
  if (!bucket) throw new Error('GCS_BUCKET env var not set');
  
  const results = [];
  let created = 0;
  
  for (const week of oldWeeks) {
    try {
      const snapshotKey = `${prefix}snapshots/week-${week.id}-reveal-snapshot.json`;
      
      // Check if snapshot already exists (unless forcing)
      if (!force) {
        try {
          await readSnapshotFromGcs(bucket, snapshotKey);
          console.log(`Snapshot for week ${week.id} already exists, skipping`);
          continue;
        } catch (e) {
          // Snapshot doesn't exist, continue to create it
        }
      }
      
      // Generate and persist snapshot
      const snapshot = await buildRevealSnapshot(week.id);
      await writeSnapshotToGcs(bucket, snapshotKey, JSON.stringify(snapshot));
      
      console.log(`Created snapshot for week ${week.id} (${week.season_year} week ${week.week_number})`);
      results.push({
        week_id: week.id,
        season_year: week.season_year,
        week_number: week.week_number,
        gcs_key: snapshotKey,
        status: 'created'
      });
      created++;
      
    } catch (error) {
      console.warn(`Failed to create snapshot for week ${week.id}:`, error.message);
      results.push({
        week_id: week.id,
        season_year: week.season_year,
        week_number: week.week_number,
        status: 'failed',
        error: error.message
      });
    }
  }

  return {
    ok: true,
    message: `Processed ${oldWeeks.length} old weeks, created ${created} snapshots`,
    snapshots_created: created,
    results
  };
}

module.exports = { 
  runAggregator, 
  buildRevealSnapshot, 
  buildHistoryMatrix, 
  persistHistoryMatrixToGcs,
  generateSnapshotsForOldWeeks
};
