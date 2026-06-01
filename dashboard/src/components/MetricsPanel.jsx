import React from 'react';

const MetricsPanel = ({ data }) => {
  if (!data) return null;

  const metrics = [
    { label: "Total Footfall", value: data.total_footfall },
    { label: "Conversion Rate", value: `${data.store_conversion_rate}%` },
    { label: "Total Revenue", value: `₹${data.total_revenue.toLocaleString()}` },
    { label: "Avg Dwell Time", value: `${data.average_dwell_time_minutes}m` },
    { label: "Peak Hour", value: data.peak_hour }
  ];

  return (
    <>
      {metrics.map((m, idx) => (
        <div key={idx} className="metric-card">
          <div className="metric-value">{m.value}</div>
          <div className="metric-label">{m.label}</div>
        </div>
      ))}
    </>
  );
};

export default MetricsPanel;
