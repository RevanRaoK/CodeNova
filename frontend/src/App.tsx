import { RouterProvider } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { router } from './router';

function App() {
  return (
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}

export default App;