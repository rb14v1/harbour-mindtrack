import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { MoodTrendPoint } from "../../types";

export function MoodTrendChart({ points }: { points: MoodTrendPoint[] }) {
  if (points.length === 0) {
    return <p>No journal entries in this window yet.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={points} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="entry_date" tick={{ fontSize: 11 }} />
        <YAxis domain={[0, 10]} allowDecimals={false} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="score" name="Mood score" stroke="#4f46e5" connectNulls strokeWidth={2} />
        <Line type="monotone" dataKey="energy_level" name="Energy" stroke="#059669" connectNulls strokeWidth={1.5} />
      </LineChart>
    </ResponsiveContainer>
  );
}
