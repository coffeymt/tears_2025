const models = require('../models');

// Compute winners and losers for a given week based on game records.
// Ties count as losses for both teams; track in-progress teams too.
async function computeWeekWinnersLosers(weekId) {
  const games = await models.games.findByWeek(weekId);
  const winners = new Set();
  const losers = new Set();
  const inProgressTeams = new Set();
  for (const g of games || []) {
    try {
      if (!g) continue;
      if (g.status === 'in_progress') {
        if (g.home_team_abbr) inProgressTeams.add(g.home_team_abbr);
        if (g.away_team_abbr) inProgressTeams.add(g.away_team_abbr);
      }
      if (g.status !== 'final') continue;
      const hs = typeof g.home_score === 'number' ? g.home_score : null;
      const as = typeof g.away_score === 'number' ? g.away_score : null;
      if (hs == null || as == null) continue;
      if (hs === as) {
        if (g.home_team_abbr) losers.add(g.home_team_abbr);
        if (g.away_team_abbr) losers.add(g.away_team_abbr);
      } else {
        const homeWon = hs > as;
        const winner = homeWon ? g.home_team_abbr : g.away_team_abbr;
        const loser = homeWon ? g.away_team_abbr : g.home_team_abbr;
        if (winner) winners.add(winner);
        if (loser) losers.add(loser);
      }
    } catch {}
  }
  return { winners, losers, inProgressTeams };
}

// Update pick.status for all picks in a week and eliminate entries on losses.
// Status values: 'win' | 'loss' | 'in_progress' | 'tbd'.
// Returns counts summary including eliminated entries.
async function updatePickStatusesForWeek(weekId) {
  if (!weekId) return { win: 0, loss: 0, in_progress: 0, tbd: 0, eliminated: 0 };
  const { winners, losers, inProgressTeams } = await computeWeekWinnersLosers(weekId);
  const picks = await models.picks.findByWeek(weekId);
  let counts = { win: 0, loss: 0, in_progress: 0, tbd: 0, eliminated: 0 };
  const nowISO = new Date().toISOString();

  for (const p of picks || []) {
    try {
      if (!p || !p.team_abbr) { counts.tbd++; continue; }
      let status = 'tbd';
      if (winners.has(p.team_abbr)) status = 'win';
      else if (losers.has(p.team_abbr)) status = 'loss';
      else if (inProgressTeams.has(p.team_abbr)) status = 'in_progress';

      // Persist pick fields only if needed
      const next = {};
      if (p.status !== status) next.status = status;
      if (status === 'win' || status === 'loss') {
        if (!p.result_at) next.result_at = nowISO;
      } else if (p.result_at) {
        // If status rolled back from final to non-final, clear result timestamp
        next.result_at = null;
      }
      if (Object.keys(next).length) {
        await models.picks.update(p.id, next);
      }

      // On loss, eliminate entry if not already
      if (status === 'loss' && p.entry_id) {
        try {
          const entry = await models.entries.findById(p.entry_id);
          if (entry && !entry.is_eliminated) {
              await models.entries.update(entry.id, { is_eliminated: true });
            counts.eliminated++;
          }
        } catch {}
      }
      counts[status] += 1;
    } catch {}
  }
  return counts;
}

module.exports = { computeWeekWinnersLosers, updatePickStatusesForWeek };
