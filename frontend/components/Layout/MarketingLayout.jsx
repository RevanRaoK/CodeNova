import React from 'react';
import { MarketingHeader } from './MarketingHeader';
import { Footer } from './Footer';

/**
 * Marketing layout for homepage and auth pages without sidebar
 */
export function MarketingLayout({ children }) {
  return (
    <div className="min-h-screen bg-white flex flex-col transition-colors duration-200">
      <MarketingHeader />
      <main className="flex-1 text-gray-900">{children}</main>
      <Footer />
    </div>
  );
}
