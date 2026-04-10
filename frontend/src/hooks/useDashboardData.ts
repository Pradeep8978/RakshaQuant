import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { SummaryData, Trade, Lesson, ChartDataPoint } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/dashboard';
// Convert http:// to ws:// and https:// to wss://
const WS_BASE = API_BASE.replace(/^http/, 'ws').replace('/api/dashboard', '/api/ws');

export function useDashboardData() {
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchInitialData = async () => {
    try {
      const [summaryRes, tradesRes, lessonsRes, chartRes] = await Promise.all([
        axios.get(`${API_BASE}/summary`).catch(() => ({ data: null })),
        axios.get(`${API_BASE}/trades`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE}/lessons`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE}/chart`).catch(() => ({ data: [] }))
      ]);

      if (summaryRes.data && !summaryRes.data.error) setSummary(summaryRes.data);
      if (tradesRes.data) setTrades(tradesRes.data);
      if (lessonsRes.data) setLessons(lessonsRes.data);
      if (chartRes.data && chartRes.data.length > 0) setChartData(chartRes.data);
      
      setLoading(false);
    } catch (error) {
      console.error("Error fetching data:", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
    
    // Setup WebSocket
    let ws: WebSocket;
    const connectWs = () => {
      ws = new WebSocket(WS_BASE);
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'summary') setSummary(payload.data);
          // In a real app we'd push trades/lessons/charts through WS too when they happen,
          // but for now we poll those slower-moving pieces.
        } catch (e) {
          console.error("WS error:", e);
        }
      };
      ws.onclose = () => {
        setTimeout(connectWs, 3000); // Reconnect
      };
    };
    
    connectWs();
    
    // Poll the slower pieces every 10s since summary is real-time via WS
    const interval = setInterval(async () => {
      const [tradesRes, lessonsRes, chartRes] = await Promise.all([
        axios.get(`${API_BASE}/trades`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE}/lessons`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE}/chart`).catch(() => ({ data: [] }))
      ]);
      if (tradesRes.data) setTrades(tradesRes.data);
      if (lessonsRes.data) setLessons(lessonsRes.data);
      if (chartRes.data && chartRes.data.length > 0) setChartData(chartRes.data);
    }, 10000);

    return () => {
      clearInterval(interval);
      if (ws) ws.close();
    };
  }, []);

  const toggleHalt = useCallback(async (halt: boolean) => {
    try {
      const res = await axios.post(`${API_BASE}/halt`, { halted: halt });
      if (res.data.success) {
        setSummary(prev => prev ? { ...prev, is_halted: res.data.is_halted } : null);
      }
    } catch (error) {
      console.error("Failed to halt", error);
    }
  }, []);

  return { summary, trades, lessons, chartData, loading, toggleHalt };
}
