import React from 'react';
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';

const COLORS = ['#6B21A8', '#8B5CF6', '#A855F7', '#C084FC', '#D8B4FE', '#7C3AED'];

const CustomizedContent = (props) => {
  const { x, y, width, height, index, name, root } = props;
  if (width < 30 || height < 30) return null;

  const total = root?.children?.length || 1;
  const fill = COLORS[index % COLORS.length];

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill,
          stroke: '#0F0F23',
          strokeWidth: 3,
          rx: 6,
          ry: 6,
          opacity: 0.85,
        }}
      />
      {width > 60 && height > 40 && (
        <>
          <text
            x={x + width / 2}
            y={y + height / 2 - 6}
            textAnchor="middle"
            fill="#fff"
            fontSize={13}
            fontWeight={600}
          >
            {name}
          </text>
          <text
            x={x + width / 2}
            y={y + height / 2 + 14}
            textAnchor="middle"
            fill="rgba(255,255,255,0.7)"
            fontSize={11}
          >
            {props.size} visits
          </text>
        </>
      )}
    </g>
  );
};

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
        <p style={{ color: '#F3F4F6', margin: '0 0 4px', fontWeight: 600 }}>{d.name}</p>
        <p style={{ color: '#A855F7', margin: '2px 0' }}>Visits: {d.size}</p>
        <p style={{ color: '#0D9488', margin: 0 }}>Avg Dwell: {d.avgDwell}s</p>
      </div>
    );
  }
  return null;
};

const HeatmapView = ({ data }) => {
  if (!data || data.length === 0) return <div style={{ color: '#9CA3AF' }}>No zone data available</div>;

  const treemapData = data.map(zone => ({
    name: zone.name,
    size: zone.visit_count,
    avgDwell: zone.avg_dwell_sec,
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <Treemap
        data={treemapData}
        dataKey="size"
        stroke="#0F0F23"
        fill="#8884d8"
        content={<CustomizedContent />}
      >
        <Tooltip content={<CustomTooltip />} />
      </Treemap>
    </ResponsiveContainer>
  );
};

export default HeatmapView;
