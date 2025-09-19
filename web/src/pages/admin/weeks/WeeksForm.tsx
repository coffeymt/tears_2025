import React, { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

type Props = {
  initial?: { id?: number; week_number?: number; lock_time?: string };
  onClose: () => void;
};

export default function WeeksForm({ initial, onClose }: Props) {
  const queryClient = useQueryClient();
  const [weekNumber, setWeekNumber] = useState<string>(initial?.week_number?.toString() ?? '');
  const [lockTime, setLockTime] = useState<string>(initial?.lock_time ?? '');
  const [loading, setLoading] = useState(false);
  const isEdit = Boolean(initial?.id);

  useEffect(() => {
    setWeekNumber(initial?.week_number?.toString() ?? '');
    setLockTime(initial?.lock_time ?? '');
  }, [initial]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const parsedWeek = parseInt(weekNumber, 10);
    if (isNaN(parsedWeek) || parsedWeek < 0) {
      alert('Week number must be a non-negative integer');
      return;
    }
    setLoading(true);
    try {
      if (isEdit && initial?.id) {
        await fetch(`/api/admin/weeks/${initial.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ week_number: parsedWeek, lock_time: lockTime }),
        });
      } else {
        await fetch('/api/admin/weeks', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ week_number: parsedWeek, lock_time: lockTime }),
        });
      }

      // Invalidate cache so WeeksList refetches
  await queryClient.invalidateQueries({ queryKey: ['admin', 'weeks'] });
      onClose();
    } catch (err) {
      console.error('Failed to save week', err);
      alert('Failed to save week');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div role="dialog" aria-modal="true" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <form onSubmit={handleSubmit} className="bg-white rounded p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold mb-4">{isEdit ? 'Edit Week' : 'Add Week'}</h3>

        <label className="block mb-2">
          <div className="text-sm">Week number</div>
          <input
            type="number"
            value={weekNumber}
            onChange={(e) => setWeekNumber(e.target.value)}
            className="border rounded p-2 mt-1 w-full"
            min={0}
            required
          />
        </label>

        <label className="block mb-4">
          <div className="text-sm">Lock time</div>
          <input
            type="datetime-local"
            value={lockTime}
            onChange={(e) => setLockTime(e.target.value)}
            className="border rounded p-2 mt-1 w-full"
          />
        </label>

        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="px-3 py-1 border rounded" disabled={loading}>
            Cancel
          </button>
          <button type="submit" className="px-3 py-1 bg-blue-600 text-white rounded" disabled={loading}>
            {loading ? 'Saving...' : 'Save'}
          </button>
        </div>
      </form>
    </div>
  );
}
