'use client';

export default function VoiceMinimalPage() {
  console.log('VoiceMinimalPage rendering');
  
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#000000',
      color: '#ffffff',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: 'Arial, sans-serif',
      padding: '20px'
    }}>
      <h1 style={{ 
        fontSize: '3rem', 
        marginBottom: '1rem',
        background: 'linear-gradient(45deg, #3b82f6, #8b5cf6)',
        backgroundClip: 'text',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        textAlign: 'center'
      }}>
        Voice Page Debug
      </h1>
      
      <p style={{ 
        fontSize: '1.2rem', 
        marginBottom: '2rem', 
        color: '#a1a1aa',
        textAlign: 'center'
      }}>
        If you can see this page, React and Next.js are working correctly.
      </p>
      
      <div style={{
        backgroundColor: '#111111',
        border: '1px solid #333333',
        borderRadius: '12px',
        padding: '24px',
        maxWidth: '600px',
        width: '100%'
      }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Debugging Information</h2>
        <ul style={{ listStyle: 'none', padding: 0, lineHeight: '1.8' }}>
          <li>✅ React is rendering</li>
          <li>✅ 'use client' directive is working</li>
          <li>✅ CSS styles are being applied</li>
          <li>✅ Next.js app router is working</li>
        </ul>
        
        <div style={{ 
          marginTop: '20px', 
          padding: '16px', 
          backgroundColor: '#0a0a0a',
          borderRadius: '8px',
          fontSize: '0.9rem',
          color: '#e5e5e5'
        }}>
          <strong>Next steps:</strong>
          <ol style={{ marginLeft: '20px', marginTop: '8px' }}>
            <li>Check browser console for any JavaScript errors</li>
            <li>Verify that the original voice page dependencies are loading</li>
            <li>Test if WebSocket connection is the issue</li>
            <li>Check if Tailwind classes are being compiled correctly</li>
          </ol>
        </div>
      </div>
      
      <button 
        style={{
          marginTop: '2rem',
          padding: '12px 24px',
          backgroundColor: '#3b82f6',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          fontSize: '1rem',
          cursor: 'pointer',
          transition: 'background-color 0.2s'
        }}
        onClick={() => {
          alert('JavaScript is working!');
          console.log('Button clicked successfully');
        }}
        onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#2563eb'}
        onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#3b82f6'}
      >
        Test JavaScript
      </button>
    </div>
  );
}