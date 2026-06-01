import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts';

const STAGE_COLORS = ['#A855F7', '#8B5CF6', '#7C3AED', '#6D28D9', '#5B21B6'];

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const d = payload[0].payload;
    return (
      <div style={{
        backgroundColor: '#1A1A2E',
        padding: '12px 16px',
        border: '1px solid rgba(168,85,247,0.3)',
        borderRadius: '8px',
        boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
      }}>
        <p style={{ color: '#F3F4F6', margin: '0 0 4px', fontWeight: 600 }}>{d.label}</p>
        <p style={{ color: '#A855F7', margin: '0 0 2px', fontSize: '0.9rem' }}>
          Count: <strong>{d.count}</strong>
        </p>
        <p style={{ color: '#9CA3AF', margin: 0, fontSize: '0.85rem' }}>
          {d.percentage.toFixed(1)}% of visitors
        </p>
      </div>
    );
  }
  return null;
};

const FunnelChart = ({ data }) => {
  if (!data || data.length === 0) return <div style={{ color: '#9CA3AF' }}>No funnel data available</div>;

  const chartData = data.map(d => ({
    ...d,
    displayLabel: d.label || d.stage,
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 10, right: 60, left: 10, bottom: 10 }}
      >
        <XAxis type="number" hide />
        <YAxis
          dataKey="displayLabel"
          type="category"
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#D1D5DB', fontSize: 12 }}
          width={160}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
        <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={28}>
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={STAGE_COLORS[index % STAGE_COLORS.length]} />
          ))}
          <LabelList
            dataKey="count"
            position="right"
            style={{ fill: '#D1D5DB', fontSize: 13, fontWeight: 600 }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

export default FunnelChart;
