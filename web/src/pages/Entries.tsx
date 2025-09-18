import React, { useEffect, useState } from 'react';
import NewEntryModal from '../components/NewEntryModal'
import EntryItem from '../components/EntryItem'

type Entry = {
  id: number;
  title: string;
  created_at?: string;
};

export default function Entries() {
  const [entries, setEntries] = useState<Entry[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    let mounted = true;

    const fetchEntries = async () => {
      setLoading(true);
      setError(null);
      try {
        const origin = typeof window !== 'undefined' && window.location?.origin ? window.location.origin : '';
        const res = await fetch(origin + '/api/entries');
        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        const data = await res.json();
        if (mounted) setEntries(Array.isArray(data) ? data : []);
      } catch (err: any) {
        if (mounted) setError(err?.message ?? 'Unknown error');
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchEntries();

    return () => {
      mounted = false;
    };
  }, []);

  if (loading) return <div data-testid="entries-loading">Loading entries…</div>;
  if (error) return <div data-testid="entries-error">Error: {error}</div>;
  if (!entries || entries.length === 0) return <div data-testid="entries-empty">No entries found.</div>;

  return (
    <div data-testid="entries-list">
      <h1 className="text-xl font-bold mb-4">Your Entries</h1>
      <div className="mb-4">
        <button onClick={() => setModalOpen(true)} className="px-3 py-1 bg-green-600 text-white rounded" data-testid="open-new-entry">
          Add Entry
        </button>
      </div>
      <ul>
        {entries.map((e) => (
          <li key={e.id}>
            <EntryItem
              entry={e}
              onUpdated={(updated) => setEntries((s) => (s ? s.map((it) => (it.id === updated.id ? updated : it)) : [updated]))}
              onDeleted={(id) => setEntries((s) => (s ? s.filter((it) => it.id !== id) : []))}
            />
          </li>
        ))}
      </ul>
      <NewEntryModal
        isOpen={isModalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={(entry) => setEntries((s) => (s ? [entry, ...s] : [entry]))}
      />
    </div>
  );
}
