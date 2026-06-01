import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const FunnelChart = ({ data }) => {
  if (!data || data.length === 0) return <div>No data available</div>;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 20, right: 30, left: 40, bottom: 5 }}
      >
        <XAxis type="number" hide />
        <YAxis dataKey="stage" type="category" axisLine={false} tickLine={false} tick={{ fill: '#F3F4F6', fontSize: 12 }} width={120} />
        <Tooltip
          cursor={{ fill: 'rgba(255,255,255,0.05)' }}
          contentStyle={{ backgroundColor: '#1A1A2E', border: '1px solid #333', borderRadius: '8px' }}
        />
        <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={30}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={`rgba(168, 85, 247, ${1 - index * 0.15})`} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

export default FunnelChart;
