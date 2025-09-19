import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { clsx } from 'clsx';
import { Container } from './Container';
import { Button } from '../ui/Button';
import { Icon } from '../ui/Icon';
import { useTheme } from '../../contexts/ThemeContext';

interface HeaderProps {
  className?: string;
  isAuthenticated?: boolean;
  user?: {
    name: string;
    email: string;
    avatar?: string;
  };
  onLogin?: () => void;
  onLogout?: () => void;
  onProfileClick?: () => void;
}

export const Header = ({
  className,
  isAuthenticated = false,
  user,
  onLogin,
  onLogout,
  onProfileClick,
}) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  return (
    <header className={clsx(
      'bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-40',
      className
    )}>
      <Container>
        <div className="flex items-center justify-between h-16">
          {/* Logo and Brand */}
          <div className="flex items-center space-x-4">
            <Link to="/" className="flex items-center space-x-2">
              <Icon 
                name="code-bracket" 
                size="lg" 
                className="text-blue-600 dark:text-blue-400" 
              />
              <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                CodeReview AI
              </h1>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            {isAuthenticated && (
              <>
                <NavLink 
                  to="/review" 
                  className={({ isActive }) => clsx(
                    'transition-colors',
                    isActive 
                      ? 'text-blue-600 dark:text-blue-400 font-medium' 
                      : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'
                  )}
                >
                  Review Code
                </NavLink>
                <NavLink 
                  to="/history" 
                  className={({ isActive }) => clsx(
                    'transition-colors',
                    isActive 
                      ? 'text-blue-600 dark:text-blue-400 font-medium' 
                      : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'
                  )}
                >
                  History
                </NavLink>
                <NavLink 
                  to="/patterns" 
                  className={({ isActive }) => clsx(
                    'transition-colors',
                    isActive 
                      ? 'text-blue-600 dark:text-blue-400 font-medium' 
                      : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'
                  )}
                >
                  Patterns
                </NavLink>
              </>
            )}
          </nav>

          {/* Right side actions */}
          <div className="flex items-center space-x-3">
            {/* Theme toggle */}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            >
              <Icon 
                name={theme === 'light' ? 'moon' : 'sun'} 
                size="sm" 
              />
            </Button>

            {/* Authentication actions */}
            {isAuthenticated ? (
              <div className="flex items-center space-x-3">
                {/* User menu */}
                <div className="relative">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onProfileClick}
                    className="flex items-center space-x-2"
                  >
                    {user?.avatar ? (
                      <img 
                        src={user.avatar} 
                        alt={user.name}
                        className="h-6 w-6 rounded-full"
                      />
                    ) : (
                      <Icon name="user" size="sm" />
                    )}
                    <span className="hidden sm:inline text-sm">
                      {user?.name || 'Profile'}
                    </span>
                  </Button>
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onLogout}
                  leftIcon="arrow-right-on-rectangle"
                  className="hidden sm:inline-flex"
                >
                  Logout
                </Button>
              </div>
            ) : (
              <Button
                variant="primary"
                size="sm"
                onClick={onLogin}
              >
                Sign In
              </Button>
            )}

            {/* Mobile menu button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleMobileMenu}
              className="md:hidden"
              aria-label="Toggle mobile menu"
            >
              <Icon 
                name={isMobileMenuOpen ? 'x-mark' : 'bars-3'} 
                size="sm" 
              />
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-slate-200 dark:border-slate-800 py-4 animate-in slide-in-from-top-2 duration-200">
            <nav className="flex flex-col space-y-3">
              {isAuthenticated ? (
                <>
                  <NavLink 
                    to="/review" 
                    className={({ isActive }) => clsx(
                      'transition-colors px-2 py-1 rounded',
                      isActive 
                        ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 font-medium' 
                        : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 hover:bg-slate-50 dark:hover:bg-slate-800'
                    )}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    Review Code
                  </NavLink>
                  <NavLink 
                    to="/history" 
                    className={({ isActive }) => clsx(
                      'transition-colors px-2 py-1 rounded',
                      isActive 
                        ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 font-medium' 
                        : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 hover:bg-slate-50 dark:hover:bg-slate-800'
                    )}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    History
                  </NavLink>
                  <NavLink 
                    to="/patterns" 
                    className={({ isActive }) => clsx(
                      'transition-colors px-2 py-1 rounded',
                      isActive 
                        ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 font-medium' 
                        : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 hover:bg-slate-50 dark:hover:bg-slate-800'
                    )}
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    Patterns
                  </NavLink>
                  <div className="border-t border-slate-200 dark:border-slate-800 pt-3 mt-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={onLogout}
                      leftIcon="arrow-right-on-rectangle"
                      className="w-full justify-start"
                    >
                      Logout
                    </Button>
                  </div>
                </>
              ) : (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={onLogin}
                  className="mx-2"
                >
                  Sign In
                </Button>
              )}
            </nav>
          </div>
        )}
      </Container>
    </header>
  );
};