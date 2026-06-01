import React from 'react';
import { AlertTriangle, Info, Zap } from 'lucide-react';

const getIcon = (severity) => {
  switch (severity) {
    case 'high': return <AlertTriangle size={16} color="#EF4444" />;
    case 'medium': return <Zap size={16} color="#F59E0B" />;
    case 'low': return <Info size={16} color="#3B82F6" />;
    default: return <Info size={16} color="#9CA3AF" />;
  }
};

const AnomalyFeed = ({ data }) => {
  if (!data || data.length === 0) return <div>No anomalies detected recently.</div>;

  return (
    <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
      {data.map((anomaly, idx) => (
        <div key={idx} className={`anomaly-card ${anomaly.severity}`}>
          <div className="anomaly-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {getIcon(anomaly.severity)}
              <span className="anomaly-type">{anomaly.type.replace('_', ' ')}</span>
            </div>
            <span className="anomaly-time">{new Date(anomaly.timestamp).toLocaleTimeString()}</span>
          </div>
          <div className="anomaly-desc">{anomaly.description}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            Zone: {anomaly.zone}
          </div>
        </div>
      ))}
    </div>
  );
};

export default AnomalyFeed;
