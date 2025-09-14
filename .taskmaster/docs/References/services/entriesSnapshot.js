let Storage = null;
try {
  Storage = require('@google-cloud/storage').Storage;
} catch (e) {
  console.warn('Google Cloud Storage not available:', e.message);
}
const models = require('../models');

const GCS_BUCKET = process.env.GCS_BUCKET || null;
const GCS_PREFIX = process.env.GCS_PREFIX || '';

// GCS helpers
async function readUserSnapshotFromGcs(userId) {
  if (!GCS_BUCKET || process.env.NODE_ENV === 'test' || !Storage) return null;
  try {
    const storage = new Storage();
    const key = `${GCS_PREFIX}snapshots/user-${userId}-entries-with-picks.json`;
    const file = storage.bucket(GCS_BUCKET).file(key);
    const [exists] = await file.exists();
    if (!exists) return null;
    const [contents] = await file.download();
    try { return JSON.parse(contents.toString()); } catch { return null; }
  } catch (e) {
    console.warn('Failed to read user snapshot from GCS:', e && e.message);
    return null;
  }
}

async function writeUserSnapshotToGcs(userId, payload) {
  if (!GCS_BUCKET || process.env.NODE_ENV === 'test' || !Storage) return;
  try {
    const storage = new Storage();
    const key = `${GCS_PREFIX}snapshots/user-${userId}-entries-with-picks.json`;
    const file = storage.bucket(GCS_BUCKET).file(key);
    await file.save(JSON.stringify(payload), { contentType: 'application/json' });
  } catch (e) {
    console.warn('Failed to write user snapshot to GCS:', e && e.message);
  }
}

// Build per-user entries-with-picks payload
async function buildEntriesWithPicksPayload(userId) {
  const entries = await models.entries.findByUser(userId);
  if (!entries || entries.length === 0) return { entries: [], picks_by_entry: {} };
  const picksByEntryPromises = entries.map(async (entry) => {
    try {
      const picks = await models.picks.findByEntry(entry.id);
      return { entryId: entry.id, picks: picks || [] };
    } catch (error) {
      console.warn(`Failed to load picks for entry ${entry.id}:`, error && error.message);
      return { entryId: entry.id, picks: [] };
    }
  });
  const picksByEntryResults = await Promise.all(picksByEntryPromises);
  const picksByEntry = {};
  for (const result of picksByEntryResults) picksByEntry[result.entryId] = result.picks;
  return { entries, picks_by_entry: picksByEntry };
}

async function generateAndWriteUserSnapshot(userId) {
  try {
    const payload = await buildEntriesWithPicksPayload(userId);
    await writeUserSnapshotToGcs(userId, payload);
  } catch (e) {
    console.warn('Failed to generate/write user snapshot:', e && e.message);
  }
}

module.exports = {
  readUserSnapshotFromGcs,
  writeUserSnapshotToGcs,
  buildEntriesWithPicksPayload,
  generateAndWriteUserSnapshot
};
