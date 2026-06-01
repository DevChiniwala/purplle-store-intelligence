import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const FootfallTimeline = ({ data }) => {
  if (!data || data.length === 0) return <div>No data available</div>;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart
        data={data}
        margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
        <XAxis dataKey="hour" stroke="#9CA3AF" tick={{ fill: '#9CA3AF', fontSize: 12 }} />
        <YAxis stroke="#9CA3AF" tick={{ fill: '#9CA3AF', fontSize: 12 }} />
        <Tooltip
          contentStyle={{ backgroundColor: '#1A1A2E', border: '1px solid #333', borderRadius: '8px' }}
          itemStyle={{ color: '#F3F4F6' }}
        />
        <Legend />
        <Line type="monotone" dataKey="footfall" stroke="#A855F7" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} name="Footfall" />
        <Line type="monotone" dataKey="revenue" stroke="#0D9488" strokeWidth={3} dot={{ r: 4 }} name="Revenue" />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default FootfallTimeline;
