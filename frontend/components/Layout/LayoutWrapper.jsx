import React from 'react';
import { useNavigation } from '../../contexts/NavigationContext';
import { Layout } from './Layout';
import { MarketingLayout } from './MarketingLayout';
import { AdminLayout } from './AdminLayout';

/**
 * Layout wrapper that conditionally renders different layouts based on navigation context
 */
export function LayoutWrapper({ children }) {
     const { layoutType } = useNavigation();

     switch (layoutType) {
          case 'marketing':
               return <MarketingLayout>{children}</MarketingLayout>;
          case 'admin':
               return <AdminLayout>{children}</AdminLayout>;
          case 'app':
          default:
               return <Layout>{children}</Layout>;
     }
}