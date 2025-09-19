import React from 'react';
import { clsx } from 'clsx';
import { Icon, type IconName } from '../ui/Icon';

interface SidebarItem {
  id: string;
  label: string;
  icon: IconName;
  href?: string;
  onClick?: () => void;
  active?: boolean;
  badge?: string | number;
  disabled?: boolean;
}

interface SidebarSection {
  title?: string;
  items: SidebarItem[];
}

interface SidebarProps {
  sections: SidebarSection[];
  className?: string;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sections,
  className,
  isCollapsed = false,
  onToggleCollapse,
}) => {
  const handleItemClick = (item: SidebarItem) => {
    if (item.disabled) return;
    
    if (item.onClick) {
      item.onClick();
    } else if (item.href) {
      window.location.href = item.href;
    }
  };

  return (
    <aside className={clsx(
      'bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 transition-all duration-300',
      isCollapsed ? 'w-16' : 'w-64',
      className
    )}>
      <div className="flex flex-col h-full">
        {/* Collapse toggle */}
        {onToggleCollapse && (
          <div className="p-4 border-b border-slate-200 dark:border-slate-800">
            <button
              onClick={onToggleCollapse}
              className="w-full flex items-center justify-center p-2 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              <Icon 
                name={isCollapsed ? 'chevron-right' : 'chevron-left'} 
                size="sm" 
                className="text-slate-500 dark:text-slate-400"
              />
            </button>
          </div>
        )}

        {/* Navigation sections */}
        <nav className="flex-1 p-4 space-y-6 overflow-y-auto">
          {sections.map((section, sectionIndex) => (
            <div key={sectionIndex}>
              {section.title && !isCollapsed && (
                <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">
                  {section.title}
                </h3>
              )}
              
              <ul className="space-y-1">
                {section.items.map((item) => (
                  <li key={item.id}>
                    <button
                      onClick={() => handleItemClick(item)}
                      disabled={item.disabled}
                      className={clsx(
                        'w-full flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors',
                        'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
                        item.active
                          ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
                          : 'text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800',
                        item.disabled && 'opacity-50 cursor-not-allowed',
                        isCollapsed ? 'justify-center' : 'justify-start'
                      )}
                      title={isCollapsed ? item.label : undefined}
                    >
                      <Icon 
                        name={item.icon} 
                        size="sm" 
                        className={clsx(
                          item.active 
                            ? 'text-blue-600 dark:text-blue-400' 
                            : 'text-slate-500 dark:text-slate-400',
                          !isCollapsed && 'mr-3'
                        )}
                      />
                      
                      {!isCollapsed && (
                        <>
                          <span className="flex-1 text-left">{item.label}</span>
                          {item.badge && (
                            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-200">
                              {item.badge}
                            </span>
                          )}
                        </>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
      </div>
    </aside>
  );
};

// Predefined sidebar configurations
export const defaultSidebarSections: SidebarSection[] = [
  {
    items: [
      {
        id: 'dashboard',
        label: 'Dashboard',
        icon: 'home',
        href: '/dashboard',
        active: true,
      },
      {
        id: 'review',
        label: 'Review Code',
        icon: 'code-bracket',
        href: '/review',
      },
      {
        id: 'history',
        label: 'History',
        icon: 'clock',
        href: '/history',
        badge: '12',
      },
      {
        id: 'patterns',
        label: 'Patterns',
        icon: 'chart-bar',
        href: '/patterns',
      },
    ],
  },
  {
    title: 'Account',
    items: [
      {
        id: 'profile',
        label: 'Profile',
        icon: 'user',
        href: '/profile',
      },
      {
        id: 'settings',
        label: 'Settings',
        icon: 'cog-6-tooth',
        href: '/settings',
      },
    ],
  },
];