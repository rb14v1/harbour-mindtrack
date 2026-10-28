import { useEffect, useState } from "react";

import { fetchMoodTrend } from "../../api/analytics";
import { extractErrorMessage } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import type { MoodTrendResponse } from "../../types";
import { MoodTrendChart } from "./MoodTrendChart";

export function MoodTrendsPage() {
  const { user } = useAuth();
  const [days, setDays] = useState(30);
  const [data, setData] = useState<MoodTrendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    fetchMoodTrend(user.id, days)
      .then((res) => setData(res.data))
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [user, days]);

  return (
    <div className="page">
      <h1>My mood trend</h1>
      <div className="toolbar">
        <label>
          Window:{" "}
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={7}>7 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
          </select>
        </label>
        {data?.mean_score != null && <span className="mean-score">Mean: {data.mean_score}</span>}
      </div>
      {error && <div className="form-error">{error}</div>}
      {loading ? <div className="page-loading">Loading...</div> : <MoodTrendChart points={data?.points ?? []} />}
    </div>
  );
}
