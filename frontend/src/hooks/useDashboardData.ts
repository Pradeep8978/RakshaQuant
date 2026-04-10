import { useState, useEffect } from 'react';
import axios from 'axios';
import { SummaryData, Trade, Lesson } from '../types';

const API_BASE = 'http://127.0.0.1:8000/api/dashboard';

export function useDashboardData() {
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [summaryRes, tradesRes, lessonsRes] = await Promise.all([
        axios.get(`${API_BASE}/summary`).catch(() => ({ data: null })),
        axios.get(`${API_BASE}/trades`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE}/lessons`).catch(() => ({ data: [] }))
      ]);

      if (summaryRes.data && !summaryRes.data.error) setSummary(summaryRes.data);
      if (tradesRes.data) setTrades(tradesRes.data);
      if (lessonsRes.data) setLessons(lessonsRes.data);
      
      setLoading(false);
    } catch (error) {
      console.error("Error fetching data:", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  return { summary, trades, lessons, loading };
}
