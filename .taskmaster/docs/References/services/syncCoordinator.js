const { syncFromEspn } = require('./espnScoreboard');
const { runAggregator, persistHistoryMatrixToGcs } = require('../jobs/aggregator');

// Coordinate an ESPN sync followed immediately by aggregation.
// If sync fails, aggregation will still attempt to run using best-effort week detection.
async function runSyncAndAggregate(options = {}) {
  let syncResult = null;
  try {
    syncResult = await syncFromEspn(options);
  } catch (e) {
    // Keep error info but don't throw - aggregation should still be attempted
    syncResult = { error: true, message: e && e.message, details: e && e.details, code: e && e.code };
  }

  // Prefer season/week from the sync result, fall back to provided options
  const seasonYear = (syncResult && Number.isInteger(syncResult.season_year)) ? syncResult.season_year : (Number.isInteger(options.seasonYear) ? options.seasonYear : undefined);
  const weekNumber = (syncResult && Number.isInteger(syncResult.week_number)) ? syncResult.week_number : (Number.isInteger(options.weekNumber) ? options.weekNumber : undefined);

  let aggregatorResult = null;
  try {
    const aggOpts = {};
    if (typeof seasonYear === 'number') aggOpts.seasonYear = seasonYear;
    if (typeof weekNumber === 'number') aggOpts.weekNumber = weekNumber;
    // Don't re-run the sync inside the aggregator since we already attempted it
    aggOpts.runSync = false;
    const res = await runAggregator(aggOpts);
    aggregatorResult = { ok: true, ...res };
  } catch (e) {
    aggregatorResult = { error: true, message: e && e.message };
  }

  // Also persist the history matrix for the season (best effort - don't fail if this errors)
  let matrixResult = null;
  if (typeof seasonYear === 'number') {
    try {
      const matRes = await persistHistoryMatrixToGcs(seasonYear);
      matrixResult = { ok: true, ...matRes };
    } catch (e) {
      matrixResult = { error: true, message: e && e.message };
      console.warn('Failed to persist history matrix:', e && e.message);
    }
  }

  return { sync: syncResult, aggregator: aggregatorResult, matrix: matrixResult };
}

module.exports = { runSyncAndAggregate };
