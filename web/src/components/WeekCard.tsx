import React from 'react';
import useSiteTime from '../hooks/useSiteTime';

type WeekCardProps = {
  weekNumber: number;
  lock_time: string; // ISO string
};

function formatDuration(ms: number) {
  if (ms <= 0) return 'Locked';
  const totalSeconds = Math.floor(ms / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${days}d ${hours}h ${minutes}m ${seconds}s`;
}

export default function WeekCard({ weekNumber, lock_time }: WeekCardProps) {
  const { now, isLoading } = useSiteTime({ pollIntervalMs: 15000 });
  const lockMs = React.useMemo(() => new Date(lock_time).getTime(), [lock_time]);
  const remaining = React.useMemo(() => {
    if (!now) return Infinity;
    return lockMs - now.getTime();
  }, [now, lockMs]);

  return (
    <div data-testid="week-card" className="p-4 border rounded shadow-sm bg-white">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Week {weekNumber}</h3>
        <div className="text-sm text-gray-600">{isLoading ? 'Syncing time...' : 'Server time synced'}</div>
      </div>
      <div className="mt-3">
        <div className="text-xs text-gray-500">Lock time</div>
        <div className="text-xl font-mono" data-testid="week-lock-countdown">
          {formatDuration(remaining)}
        </div>
      </div>
    </div>
  );
}
