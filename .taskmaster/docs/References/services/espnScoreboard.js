// Minimal ESPN scoreboard integration for MVP
// Fetches games from ESPN's public scoreboard and maps to our Games schema

const models = require('../models');
const teamsFile = require('../data/nfl_teams.json');

async function httpGet(url) {
  if (typeof fetch === 'function') {
    return fetch(url, { headers: { Accept: 'application/json' } });
  }
  // Fallback for Node versions without global fetch
  return new Promise((resolve, reject) => {
    try {
      const u = new URL(url);
      const lib = u.protocol === 'https:' ? require('https') : require('http');
      const req = lib.request(url, { method: 'GET', headers: { Accept: 'application/json' } }, (res) => {
        const chunks = [];
        res.on('data', (c) => chunks.push(c));
        res.on('end', () => {
          const body = Buffer.concat(chunks).toString('utf8');
          resolve({
            ok: res.statusCode >= 200 && res.statusCode < 300,
            status: res.statusCode,
            statusText: res.statusMessage,
            // Minimal headers shim
            headers: {
              get: (name) => {
                name = String(name || '').toLowerCase();
                const raw = res.headers[name];
                if (Array.isArray(raw)) return raw.join(', ');
                return raw || '';
              }
            },
            text: async () => body,
            json: async () => {
              try { return JSON.parse(body); } catch { return {}; }
            }
          });
        });
      });
      req.on('error', reject);
      req.end();
    } catch (e) {
      reject(e);
    }
  });
}

// Normalize common ESPN abbreviation mismatches to our internal 2-3 letter codes
function normalizeAbbr(abbr) {
  if (!abbr) return abbr;
  const map = {
  WSH: 'WAS', // Washington Commanders legacy
  // Normalize any ESPN variant for the Jaguars to our canonical 'JAX'
  JAX: 'JAX', // ESPN may send JAX
  JAC: 'JAX', // or JAC - coerce to JAX
  LA: 'LAR', // Ensure Rams use LAR
  };
  return map[abbr] || abbr;
}

function mapStatus(espnState) {
  switch (String(espnState || '').toLowerCase()) {
    case 'pre':
      return 'scheduled';
    case 'in':
      return 'in_progress';
    case 'post':
      return 'final';
    default:
      return 'scheduled';
  }
}

// Transform ESPN scoreboard JSON to an array of game objects (without ids) conforming to our schema
function transformScoreboardToGames(scoreboardJson, weekId) {
  const events = Array.isArray(scoreboardJson && scoreboardJson.events) ? scoreboardJson.events : [];
  const games = [];
  for (const ev of events) {
    try {
      const competitions = Array.isArray(ev.competitions) ? ev.competitions : [];
      const comp = competitions[0] || {};
      const comps = Array.isArray(comp.competitors) ? comp.competitors : [];
      const home = comps.find((c) => c && c.homeAway === 'home') || {};
      const away = comps.find((c) => c && c.homeAway === 'away') || {};
      const homeAbbr = String(normalizeAbbr(home.team && home.team.abbreviation || '')).toUpperCase().trim();
      const awayAbbr = String(normalizeAbbr(away.team && away.team.abbreviation || '')).toUpperCase().trim();
      if (!homeAbbr || !awayAbbr) continue; // skip malformed
      if (homeAbbr.length < 2 || homeAbbr.length > 3 || awayAbbr.length < 2 || awayAbbr.length > 3) continue;

      const status = mapStatus(ev.status && ev.status.type && ev.status.type.state);
      const startTime = ev.date; // ISO-ish string from ESPN (UTC)
      if (!startTime || isNaN(Date.parse(startTime))) continue;
      // Normalize to strict RFC3339 with seconds for AJV date-time validation
      const startTimeISO = new Date(startTime).toISOString();
      const homeScore = Number.isFinite(Number(home.score)) ? parseInt(home.score, 10) : 0;
      const awayScore = Number.isFinite(Number(away.score)) ? parseInt(away.score, 10) : 0;

      games.push({
        week_id: weekId,
        home_team_abbr: homeAbbr,
        away_team_abbr: awayAbbr,
        start_time: startTimeISO,
        status,
        home_score: homeScore,
        away_score: awayScore,
      });
    } catch {
      // skip any problematic event
    }
  }
  return games;
}

// Find an existing game by composite key within a week's games
function findExistingByComposite(existingWeekGames, g) {
  return (
    (existingWeekGames || []).find(
      (x) =>
        x &&
        x.week_id === g.week_id &&
        x.home_team_abbr === g.home_team_abbr &&
        x.away_team_abbr === g.away_team_abbr &&
        x.start_time === g.start_time,
    ) || null
  );
}

// Return true if the given ISO datetime falls on a Thursday in US/Eastern time
function isThursdayEastern(iso) {
  try {
    const d = new Date(iso);
    // Get weekday name in America/New_York
    const day = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', weekday: 'short' }).format(d);
    return String(day).toLowerCase().startsWith('thu');
  } catch {
    return false;
  }
}

// Map any internal game abbr to the roster file abbr used elsewhere (no-op for JAX)
function toRosterAbbr(abbr) {
  const map = { /* legacy mapping if needed */ };
  return map[abbr] || abbr;
}

// Fetch ESPN scoreboard (optionally for a specific week) and upsert into our Games store.
// Options: { weekNumber?: number, seasonYear?: number }
async function syncFromEspn(options = {}) {
  const { weekNumber, seasonYear } = options;
  // Prefer HTTPS to avoid outbound HTTP restrictions in some environments
  const base = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard';

  // Prefer explicit weekNumber; otherwise fall back to the app's current week to ensure
  // we always query a concrete week with '?week=' per ESPN API expectations.
  let inferredWeekNumber = null;
  if (!Number.isInteger(weekNumber)) {
    try {
      const current = await models.weeks.findCurrent();
      if (current && Number.isInteger(current.week_number)) {
        inferredWeekNumber = current.week_number;
      }
    } catch {}
  }
  const effectiveWeekNumber = Number.isInteger(weekNumber) ? weekNumber : inferredWeekNumber;
  const url = Number.isInteger(effectiveWeekNumber) ? `${base}?week=${effectiveWeekNumber}` : base;

  const resp = await httpGet(url);
  if (!resp.ok) {
    const text = await (async () => {
      try {
        return await resp.text();
      } catch {
        return '';
      }
    })();
    const err = new Error(`ESPN fetch failed: ${resp.status} ${resp.statusText}`);
    err.espnUrl = url;
    err.details = text.slice(0, 500);
    throw err;
  }
  const json = await resp.json();

  // Determine target season/week
  // Resolve season/year and week:
  // - Prefer explicit options
  // - Fall back to ESPN payload
  // - Finally, fall back to the app's current week metadata (if available)
  let espnSeasonYear = Number.isInteger(seasonYear) ? seasonYear : ((json && json.season && json.season.year) || null);
  let espnWeekNumber = Number.isInteger(weekNumber) ? weekNumber : ((json && json.week && json.week.number) || null);
  if (!Number.isInteger(espnWeekNumber) && Number.isInteger(effectiveWeekNumber)) {
    espnWeekNumber = effectiveWeekNumber;
  }
  if (!Number.isInteger(espnSeasonYear)) {
    try {
      const current = await models.weeks.findCurrent();
      if (current && Number.isInteger(current.season_year)) {
        espnSeasonYear = current.season_year;
      }
    } catch {}
  }
  if (!Number.isInteger(espnSeasonYear) || !Number.isInteger(espnWeekNumber)) {
    const e = new Error('Unable to determine seasonYear/weekNumber from ESPN data');
    e.espnUrl = url;
    throw e;
  }

  const week = await models.weeks.findByWeekNumber(espnWeekNumber, espnSeasonYear);
  if (!week) {
    const e = new Error(`Week not found for season ${espnSeasonYear} week ${espnWeekNumber}`);
    e.code = 'WEEK_NOT_FOUND';
    throw e;
  }

  const incoming = transformScoreboardToGames(json, week.id)
    .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
  const existing = await models.games.findByWeek(week.id);

  // Overwrite semantics: remove all existing week games, then insert fresh
  for (const g of existing || []) {
    try { await models.games.delete(g.id); } catch {}
  }
  let created = 0;
  for (const g of incoming) {
    await models.games.create(g);
    created += 1;
  }
  const updated = 0;

  // Auto-manage ineligible teams for this week based on the synced slate
  try {
    const allTeams = new Set((teamsFile.teams || []).map(t => String(t.abbreviation).toUpperCase()));
    // Teams playing this week, normalized to roster abbreviations
    const playing = new Set();
    const thursdayTeams = new Set();
    for (const g of incoming) {
      const home = toRosterAbbr(String(g.home_team_abbr).toUpperCase());
      const away = toRosterAbbr(String(g.away_team_abbr).toUpperCase());
      playing.add(home);
      playing.add(away);
      if (isThursdayEastern(g.start_time)) {
        thursdayTeams.add(home);
        thursdayTeams.add(away);
      }
    }
    const nonPlaying = new Set();
    for (const abbr of allTeams) {
      if (!playing.has(abbr)) nonPlaying.add(abbr);
    }
    // Union with any existing ineligible_teams
    const nextIneligible = new Set([
      ...Array.from(nonPlaying),
      ...Array.from(thursdayTeams),
      ...Array.isArray(week.ineligible_teams) ? week.ineligible_teams.map(s => String(s).toUpperCase()) : []
    ]);
    const nextArr = Array.from(nextIneligible);
    // Only persist if changed to avoid unnecessary writes
    const prev = Array.isArray(week.ineligible_teams) ? week.ineligible_teams.map(s => String(s).toUpperCase()) : [];
    const same = prev.length === nextArr.length && prev.every(v => nextIneligible.has(v));
    if (!same) {
      await models.weeks.update(week.id, { ineligible_teams: nextArr });
    }
  } catch (e) {
    // Non-fatal: log and continue
    try { console.warn('Failed to auto-update ineligible_teams:', e && e.message); } catch {}
  }

  return {
    season_year: espnSeasonYear,
    week_number: espnWeekNumber,
    week_id: week.id,
  counts: { created, updated, total: incoming.length },
  source_url: url,
  };
}

module.exports = {
  syncFromEspn,
};
