import React from 'react';
import { Users, TrendingUp, IndianRupee, Clock, BarChart3, ShoppingCart } from 'lucide-react';

const formatRevenue = (val) => {
  const n = Number(val) || 0;
  if (n >= 100000) return `₹${(n / 100000).toFixed(1)}L`;
  if (n >= 1000) return `₹${(n / 1000).toFixed(1)}K`;
  return `₹${n.toFixed(0)}`;
};

const formatDwell = (seconds) => {
  const s = Number(seconds) || 0;
  const m = Math.floor(s / 60);
  const sec = Math.round(s % 60);
  return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
};

const MetricsPanel = ({ data }) => {
  if (!data) return null;

  const hourly = data.hourly_breakdown || [];
  const peakHourObj = hourly.reduce(
    (max, obj) => (obj.footfall > max.footfall ? obj : max),
    { hour: 0, footfall: -1 }
  );
  const peakHour =
    peakHourObj.footfall > 0
      ? `${peakHourObj.hour.toString().padStart(2, '0')}:00`
      : 'N/A';

  const metrics = [
    {
      label: 'Total Footfall',
      value: data.footfall ?? 0,
      icon: <Users size={22} />,
      color: '#A855F7',
    },
    {
      label: 'Conversion Rate',
      value: `${(data.conversion_rate ?? 0).toFixed(1)}%`,
      icon: <TrendingUp size={22} />,
      color: '#10B981',
    },
    {
      label: 'Total Revenue',
      value: formatRevenue(data.revenue),
      icon: <IndianRupee size={22} />,
      color: '#F59E0B',
    },
    {
      label: 'Avg Dwell Time',
      value: formatDwell(data.average_dwell_seconds),
      icon: <Clock size={22} />,
      color: '#3B82F6',
    },
    {
      label: 'Transactions',
      value: data.transactions ?? 0,
      icon: <ShoppingCart size={22} />,
      color: '#0D9488',
    },
    {
      label: 'Peak Hour',
      value: peakHour,
      icon: <BarChart3 size={22} />,
      color: '#EC4899',
    },
  ];

  return (
    <>
      {metrics.map((m, idx) => (
        <div key={idx} className="metric-card">
          <div className="metric-icon" style={{ color: m.color }}>
            {m.icon}
          </div>
          <div className="metric-value">{m.value}</div>
          <div className="metric-label">{m.label}</div>
        </div>
      ))}
    </>
  );
};

export default MetricsPanel;
