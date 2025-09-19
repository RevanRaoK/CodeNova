function App() {
  return (
    <div style={{ padding: '20px', backgroundColor: '#f0f0f0', minHeight: '100vh' }}>
      <h1 style={{ color: '#333', fontSize: '32px', marginBottom: '16px' }}>
        Simple Test
      </h1>
      <p style={{ color: '#666', fontSize: '18px' }}>
        This is a basic test without any custom components or Tailwind classes.
      </p>
      <div style={{ 
        backgroundColor: 'white', 
        padding: '20px', 
        borderRadius: '8px', 
        marginTop: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h2 style={{ color: '#333', marginBottom: '10px' }}>Status</h2>
        <p style={{ color: '#666' }}>
          If you can see this, React is working correctly.
        </p>
      </div>
    </div>
  );
}

export default App;