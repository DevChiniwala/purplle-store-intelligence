import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        backgroundColor: '#1A1A2E',
        padding: '12px 16px',
        border: '1px solid rgba(168,85,247,0.3)',
        borderRadius: '8px',
        boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
      }}>
        <p style={{ color: '#9CA3AF', margin: '0 0 6px', fontSize: '0.85rem' }}>
          {String(label).padStart(2, '0')}:00 – {String(label).padStart(2, '0')}:59
        </p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color, margin: '2px 0', fontSize: '0.9rem' }}>
            {p.name}: <strong>{p.name === 'Revenue' ? `₹${Number(p.value).toLocaleString()}` : p.value}</strong>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const FootfallTimeline = ({ data }) => {
  if (!data || data.length === 0) return <div style={{ color: '#9CA3AF' }}>No timeline data</div>;

  // Only show footfall as an area chart (revenue is on a wildly different scale)
  const chartData = data.map(d => ({
    hour: `${String(d.hour).padStart(2, '0')}:00`,
    rawHour: d.hour,
    footfall: d.footfall || 0,
    transactions: d.transactions || 0,
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart
        data={chartData}
        margin={{ top: 10, right: 20, left: 0, bottom: 10 }}
      >
        <defs>
          <linearGradient id="colorFootfall" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#A855F7" stopOpacity={0.4} />
            <stop offset="95%" stopColor="#A855F7" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="colorTxns" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#0D9488" stopOpacity={0.4} />
            <stop offset="95%" stopColor="#0D9488" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
        <XAxis
          dataKey="hour"
          stroke="#6B7280"
          tick={{ fill: '#9CA3AF', fontSize: 11 }}
          tickLine={false}
          interval={2}
        />
        <YAxis stroke="#6B7280" tick={{ fill: '#9CA3AF', fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="footfall"
          stroke="#A855F7"
          strokeWidth={2.5}
          fill="url(#colorFootfall)"
          name="Footfall"
          dot={{ r: 3, fill: '#A855F7' }}
          activeDot={{ r: 6, stroke: '#A855F7', strokeWidth: 2, fill: '#1A1A2E' }}
        />
        <Area
          type="monotone"
          dataKey="transactions"
          stroke="#0D9488"
          strokeWidth={2}
          fill="url(#colorTxns)"
          name="Transactions"
          dot={{ r: 2, fill: '#0D9488' }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default FootfallTimeline;
