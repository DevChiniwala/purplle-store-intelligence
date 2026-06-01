import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', backgroundColor: '#3b0726', color: '#f87171', borderRadius: '8px', border: '1px solid #ef4444' }}>
          <h3 style={{ margin: '0 0 10px 0' }}>Something went wrong</h3>
          <p style={{ margin: 0, fontSize: '0.9em', opacity: 0.8 }}>{this.state.error?.toString()}</p>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
