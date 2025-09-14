const express = require('express');
const bodyParser = require('body-parser');
const { runAggregator, persistHistoryMatrixToGcs } = require('./aggregator');

const app = express();
app.use(bodyParser.json());

app.get('/internal/health', (req, res) => res.json({ ok: true }));

// Optional trigger endpoint to run aggregator on-demand (protected via SCHEDULER_AUTH_TOKEN)
app.post('/internal/run-aggregator', async (req, res) => {
  try {
    const rawAuth = req.headers['authorization'] || req.headers['Authorization'] || '';
    const auth = String(rawAuth || '').trim();
    const token = auth.startsWith('Bearer ') ? auth.slice(7).trim() : '';
    const expected = process.env.SCHEDULER_AUTH_TOKEN ? String(process.env.SCHEDULER_AUTH_TOKEN) : '';
    if (!expected || !token || token !== expected) return res.status(401).json({ error: 'Unauthorized' });
    const { season_year, week_number, runSync } = req.body || {};
    const result = await runAggregator({ seasonYear: season_year, weekNumber: week_number, runSync: !!runSync });
    res.json({ ok: true, result });
  } catch (e) {
    if (e && e.code === 'WEEK_NOT_FOUND') return res.status(404).json({ error: 'Week not found' });
    res.status(500).json({ error: 'Aggregator failed', message: e && e.message });
  }
});

// Endpoint to persist history matrix (protected by auth token)
app.post('/internal/persist-matrix', async (req, res) => {
  try {
    const rawAuth = req.headers['authorization'] || req.headers['Authorization'] || '';
    const auth = String(rawAuth || '').trim();
    const token = auth.startsWith('Bearer ') ? auth.slice(7).trim() : '';
    const expected = process.env.SCHEDULER_AUTH_TOKEN ? String(process.env.SCHEDULER_AUTH_TOKEN) : '';
    if (!expected || !token || token !== expected) return res.status(401).json({ error: 'Unauthorized' });
    const { season_year } = req.body || {};
    const result = await persistHistoryMatrixToGcs(season_year);
    res.json({ ok: true, result });
  } catch (e) {
    res.status(500).json({ error: 'Matrix persist failed', message: e && e.message });
  }
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`Aggregator runner listening on ${PORT}`);
});
