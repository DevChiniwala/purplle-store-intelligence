import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck } from 'lucide-react';

const Header = ({ storeName }) => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="dashboard-header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <Activity size={28} color="#A855F7" />
        <h1>{storeName} | Store Intelligence</h1>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          {time.toLocaleDateString()} {time.toLocaleTimeString()}
        </div>
        <div className="health-status">
          <div className="health-indicator"></div>
          <ShieldCheck size={16} />
          <span>System Healthy</span>
        </div>
      </div>
    </header>
  );
};

export default Header;
