import React, { useEffect, useState } from 'react';

type Team = { id: number; name: string; abbr?: string };
type Game = {
  id: number;
  home_team_id: number | null;
  away_team_id: number | null;
  start_time: string | null;
};

type Props = {
  weekId: string | number;
};

export default function GamesTableEditor({ weekId }: Props) {
  const [games, setGames] = useState<Game[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchInitial();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [weekId]);

  async function fetchInitial() {
    setLoading(true);
    setError(null);
    try {
      const [gRes, tRes] = await Promise.all([
        fetch(`/api/admin/weeks/${weekId}/games`),
        fetch(`/api/teams`),
      ]);
      if (!gRes.ok) throw new Error('Failed to fetch games');
      if (!tRes.ok) throw new Error('Failed to fetch teams');
      const gJson = await gRes.json();
      const tJson = await tRes.json();
      setGames(gJson || []);
      setTeams(tJson || []);
    } catch (err: any) {
      setError(err?.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    const payload = { home_team_id: null, away_team_id: null, start_time: null };
    const res = await fetch(`/api/admin/weeks/${weekId}/games`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      setError('Failed to create game');
      return;
    }
    const created = await res.json();
    setGames((s) => [...s, created]);
  }

  async function handleUpdate(id: number, patch: Partial<Game>) {
    const res = await fetch(`/api/admin/games/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    });
    if (!res.ok) {
      setError('Failed to update game');
      return;
    }
    const updated = await res.json();
    setGames((s) => s.map((g) => (g.id === id ? updated : g)));
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this game?')) return;
    const res = await fetch(`/api/admin/games/${id}`, { method: 'DELETE' });
    if (!res.ok) {
      setError('Failed to delete game');
      return;
    }
    setGames((s) => s.filter((g) => g.id !== id));
  }

  if (loading) return <div>Loading games…</div>;
  if (error) return <div className="text-red-600">{error}</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-medium">Games</h3>
        <div className="space-x-2">
          <button className="btn" onClick={handleCreate} data-testid="create-game">
            Add Game
          </button>
        </div>
      </div>

      <table className="w-full table-auto">
        <thead>
          <tr>
            <th className="text-left">Home</th>
            <th className="text-left">Away</th>
            <th className="text-left">Start Time</th>
            <th className="text-left">Actions</th>
          </tr>
        </thead>
        <tbody>
          {games.map((g) => (
            <tr key={g.id} className="border-t">
              <td>
                <select
                  value={g.home_team_id ?? ''}
                  onChange={(e) => handleUpdate(g.id, { home_team_id: Number(e.target.value) || null })}
                >
                  <option value="">--</option>
                  {teams.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </td>
              <td>
                <select
                  value={g.away_team_id ?? ''}
                  onChange={(e) => handleUpdate(g.id, { away_team_id: Number(e.target.value) || null })}
                >
                  <option value="">--</option>
                  {teams.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </td>
              <td>
                <input
                  type="datetime-local"
                  value={g.start_time ? new Date(g.start_time).toISOString().slice(0, 16) : ''}
                  onChange={(e) => handleUpdate(g.id, { start_time: e.target.value || null })}
                />
              </td>
              <td>
                <button className="btn-danger" onClick={() => handleDelete(g.id)} data-testid={`delete-${g.id}`}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
          {games.length === 0 && (
            <tr>
              <td colSpan={4} className="py-4 text-center text-gray-500">
                No games yet
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
