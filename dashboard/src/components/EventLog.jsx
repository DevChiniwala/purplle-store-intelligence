import React from 'react';

const EventLog = ({ data }) => {
  if (!data || data.length === 0) return <div>No events available.</div>;

  const getEventColor = (type) => {
    if (type.includes('ENTRY') || type.includes('ENTER')) return '#10B981';
    if (type.includes('EXIT')) return '#EF4444';
    if (type.includes('BILLING')) return '#F59E0B';
    return '#3B82F6';
  };

  return (
    <div className="event-log-container">
      {data.map((event, idx) => (
        <div key={idx} className="event-row">
          <div className="event-time">
            {new Date(event.timestamp).toLocaleTimeString()}
          </div>
          <div className="event-type" style={{ color: getEventColor(event.event_type) }}>
            {event.event_type}
          </div>
          <div className="event-details">
            Visitor: {event.visitor_id || 'Unknown'} | Zone: {event.zone_id || 'N/A'} | Cam: {event.camera_id}
          </div>
        </div>
      ))}
    </div>
  );
};

export default EventLog;
