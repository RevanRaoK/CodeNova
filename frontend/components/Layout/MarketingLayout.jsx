import React from 'react';
import { MarketingHeader } from './MarketingHeader';
import { Footer } from './Footer';

/**
 * Marketing layout for homepage and auth pages without sidebar
 */
export function MarketingLayout({ children }) {
     return (
          <div className="min-h-screen bg-white flex flex-col">
               <MarketingHeader />
               <main className="flex-1">
                    {children}
               </main>
               <Footer />
          </div>
     );
}