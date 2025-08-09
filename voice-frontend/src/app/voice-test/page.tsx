'use client';

export default function VoiceTestPage() {
  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#000', 
      color: '#fff', 
      padding: '20px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '1rem' }}>Voice Test Page</h1>
      <p>If you can see this, React is working correctly.</p>
      <div style={{ 
        backgroundColor: '#333', 
        padding: '20px', 
        borderRadius: '8px', 
        marginTop: '20px' 
      }}>
        <p>This is a simplified version to test basic functionality.</p>
        <button 
          style={{ 
            backgroundColor: '#007bff', 
            color: 'white', 
            border: 'none', 
            padding: '10px 20px', 
            borderRadius: '4px',
            cursor: 'pointer'
          }}
          onClick={() => alert('Button clicked!')}
        >
          Test Button
        </button>
      </div>
    </div>
  );
}