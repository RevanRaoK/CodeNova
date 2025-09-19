import { useState } from 'react';
import { Button } from './components/ui/Button';

function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold text-slate-900 mb-4">
          Simple Component Test
        </h1>
        <p className="text-lg text-slate-600 mb-8">
          Testing basic components without theme provider.
        </p>
        
        <div className="bg-white p-6 rounded-lg shadow border border-slate-200">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Counter: {count}</h2>
          <div className="space-x-3">
            <Button variant="primary" onClick={() => setCount(count + 1)}>
              Increment
            </Button>
            <Button variant="secondary" onClick={() => setCount(count - 1)}>
              Decrement
            </Button>
            <Button variant="outline" onClick={() => setCount(0)}>
              Reset
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;