import { Outlet, useNavigate } from 'react-router-dom';
import { Header } from './Header';
import { Footer } from './Footer';

interface AppLayoutProps {
  isAuthenticated?: boolean;
  user?: {
    name: string;
    email: string;
    avatar?: string;
  };
  onLogout?: () => void;
}

export const AppLayout = ({
  isAuthenticated = false,
  user,
  onLogout
}) => {
  const navigate = useNavigate();

  const handleLogin = () => {
    navigate('/login');
  };

  const handleProfileClick = () => {
    navigate('/profile');
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        isAuthenticated={isAuthenticated}
        user={user}
        onLogin={handleLogin}
        onLogout={onLogout}
        onProfileClick={handleProfileClick}
      />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};