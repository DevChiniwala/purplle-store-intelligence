import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import MetricsPanel from './components/MetricsPanel';
import FunnelChart from './components/FunnelChart';
import FootfallTimeline from './components/FootfallTimeline';
import HeatmapView from './components/HeatmapView';
import AnomalyFeed from './components/AnomalyFeed';
import EventLog from './components/EventLog';
import ErrorBoundary from './components/ErrorBoundary';
import './index.css';

function App() {
  const [metrics, setMetrics] = useState(null);
  const [funnel, setFunnel] = useState(null);
  const [anomalies, setAnomalies] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [events, setEvents] = useState(null);
  const [loading, setLoading] = useState(true);
  const storeId = "ST1008";

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [metricsRes, funnelRes, anomaliesRes, heatmapRes, eventsRes] = await Promise.all([
          fetch(`http://localhost:8000/api/v1/stores/${storeId}/metrics`),
          fetch(`http://localhost:8000/api/v1/stores/${storeId}/funnel`),
          fetch(`http://localhost:8000/api/v1/stores/${storeId}/anomalies`),
          fetch(`http://localhost:8000/api/v1/stores/${storeId}/heatmap`),
          fetch(`http://localhost:8000/api/v1/events?page=1&page_size=20`)
        ]);

        if (metricsRes.ok) setMetrics(await metricsRes.json());
        if (funnelRes.ok) setFunnel(await funnelRes.json());
        if (anomaliesRes.ok) setAnomalies(await anomaliesRes.json());
        if (heatmapRes.ok) setHeatmap(await heatmapRes.json());
        if (eventsRes.ok) setEvents(await eventsRes.json());
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', color: '#fff' }}>Loading Intelligence Data...</div>;
  }

  return (
    <div className="App">
      <Header storeName={metrics?.store_name || "Purplle Store"} />
      
      <main className="dashboard-grid">
        <div className="metrics-panel">
          <ErrorBoundary>
            <MetricsPanel data={metrics} />
          </ErrorBoundary>
        </div>

        <div className="panel funnel-panel">
          <h2>Conversion Funnel</h2>
          <div className="chart-container">
            <ErrorBoundary>
              <FunnelChart data={funnel?.stages || []} />
            </ErrorBoundary>
          </div>
        </div>

        <div className="panel timeline-panel">
          <h2>Footfall Timeline</h2>
          <div className="chart-container">
            <ErrorBoundary>
              <FootfallTimeline data={metrics?.hourly_breakdown || []} />
            </ErrorBoundary>
          </div>
        </div>

        <div className="panel heatmap-panel">
          <h2>Zone Heatmap</h2>
          <div className="chart-container">
            <ErrorBoundary>
              <HeatmapView data={heatmap?.zones || []} />
            </ErrorBoundary>
          </div>
        </div>

        <div className="panel anomalies-panel">
          <h2>Anomalies</h2>
          <ErrorBoundary>
            <AnomalyFeed data={anomalies?.anomalies || []} />
          </ErrorBoundary>
        </div>

        <div className="panel events-panel">
          <h2>Real-time Events</h2>
          <ErrorBoundary>
            <EventLog data={events?.events || []} />
          </ErrorBoundary>
        </div>
      </main>
    </div>
  );
}

export default App;
