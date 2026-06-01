import React from 'react';

const MetricsPanel = ({ data }) => {
  if (!data) return null;

  const peakHourObj = data.hourly_breakdown?.reduce((max, obj) => obj.footfall > max.footfall ? obj : max, {hour: 0, footfall: -1});
  const peakHour = peakHourObj?.hour !== undefined ? `${peakHourObj.hour.toString().padStart(2, '0')}:00` : "N/A";

  const metrics = [
    { label: "Total Footfall", value: data.footfall ?? 0 },
    { label: "Conversion Rate", value: `${data.conversion_rate ?? 0}%` },
    { label: "Total Revenue", value: `₹${(data.revenue ?? 0).toLocaleString()}` },
    { label: "Avg Dwell Time", value: `${((data.average_dwell_seconds ?? 0) / 60).toFixed(1)}m` },
    { label: "Peak Hour", value: peakHour }
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
