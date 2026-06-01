import React from 'react';
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';

const COLORS = ['#6B21A8', '#8B5CF6', '#A855F7', '#C084FC', '#D8B4FE'];

const CustomizedContent = (props) => {
  const { root, depth, x, y, width, height, index, payload, colors, rank, name } = props;

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill: depth < 2 ? colors[Math.floor((index / root.children.length) * 6)] : 'none',
          stroke: '#1A1A2E',
          strokeWidth: 2 / (depth + 1e-10),
          strokeOpacity: 1 / (depth + 1e-10),
        }}
      />
      {
        depth === 1 ? (
          <text x={x + width / 2} y={y + height / 2 + 7} textAnchor="middle" fill="#fff" fontSize={14}>
            {name}
          </text>
        ) : null
      }
      {
        depth === 1 ? (
          <text x={x + 4} y={y + 18} fill="#fff" fontSize={16} fillOpacity={0.9}>
            {index + 1}
          </text>
        ) : null
      }
    </g>
  );
};

const HeatmapView = ({ data }) => {
  if (!data || data.length === 0) return <div>No data available</div>;

  // Format data for Treemap
  const treemapData = data.map(zone => ({
    name: zone.name,
    size: zone.visit_count,
    avgDwell: zone.avg_dwell_sec
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{ backgroundColor: '#1A1A2E', padding: '10px', border: '1px solid #333', borderRadius: '8px' }}>
          <p style={{ color: '#F3F4F6', margin: '0 0 5px 0', fontWeight: 'bold' }}>{data.name}</p>
          <p style={{ color: '#A855F7', margin: 0 }}>Visits: {data.size}</p>
          <p style={{ color: '#0D9488', margin: 0 }}>Avg Dwell: {data.avgDwell}s</p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <Treemap
        data={treemapData}
        dataKey="size"
        aspectRatio={4 / 3}
        stroke="#fff"
        fill="#8884d8"
        content={<CustomizedContent colors={COLORS} />}
      >
        <Tooltip content={<CustomTooltip />} />
      </Treemap>
    </ResponsiveContainer>
  );
};

export default HeatmapView;
