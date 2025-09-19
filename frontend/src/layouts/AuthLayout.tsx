import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box, Container, useTheme, useMediaQuery, styled } from '@mui/material';
import { motion } from 'framer-motion';

const AuthContainer = styled(Box)(({ theme }) => ({
  minHeight: '100vh',
  display: 'flex',
  flexDirection: 'row',
  backgroundColor: theme.palette.background.default,
}));

const LeftPanel = styled(Box)(({ theme }) => ({
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  padding: theme.spacing(8),
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
  position: 'relative',
  overflow: 'hidden',
  [theme.breakpoints.down('md')]: {
    display: 'none',
  },
}));

const RightPanel = styled(Box)(({ theme }) => ({
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  padding: theme.spacing(4),
  [theme.breakpoints.down('md')]: {
    flex: '1 1 100%',
    padding: theme.spacing(2),
  },
}));

const AuthCard = styled(Box)(({ theme }) => ({
  width: '100%',
  maxWidth: 480,
  backgroundColor: theme.palette.background.paper,
  borderRadius: theme.shape.borderRadius * 2,
  boxShadow: theme.shadows[10],
  padding: theme.spacing(4, 3),
  [theme.breakpoints.down('sm')]: {
    padding: theme.spacing(3, 2),
    boxShadow: 'none',
    backgroundColor: 'transparent',
  },
}));

const Logo = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  marginBottom: theme.spacing(4),
  '& svg': {
    width: 40,
    height: 40,
    marginRight: theme.spacing(1.5),
  },
  '& h1': {
    fontSize: '1.5rem',
    fontWeight: 700,
    margin: 0,
    lineHeight: 1.2,
    background: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.secondary.main} 90%)`,
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  [theme.breakpoints.down('sm')]: {
    justifyContent: 'center',
    '& h1': {
      fontSize: '1.75rem',
    },
  },
}));

const Illustration = styled('div')(({ theme }) => ({
  width: '100%',
  maxWidth: 500,
  margin: '0 auto',
  '& img': {
    width: '100%',
    height: 'auto',
    display: 'block',
  },
}));

const AuthLayout: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <AuthContainer>
      <LeftPanel>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          style={{
            zIndex: 1,
            textAlign: 'center',
            width: '100%',
            maxWidth: 500,
          }}
        >
          <Box mb={4}>
            <h1 style={{ 
              fontSize: '2.5rem', 
              fontWeight: 700, 
              marginBottom: theme.spacing(2),
              color: theme.palette.primary.contrastText,
            }}>
              Welcome to CodeNova
            </h1>
            <p style={{
              fontSize: '1.1rem',
              opacity: 0.9,
              lineHeight: 1.6,
              margin: 0,
            }}>
              The AI-powered code review platform that helps you write better code, faster.
            </p>
          </Box>
          
          <Illustration>
            <img 
              src="/images/auth-illustration.svg" 
              alt="Code review illustration" 
              onError={(e) => {
                // Fallback to a placeholder if the image fails to load
                const target = e.target as HTMLImageElement;
                target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiB2aWV3Qm94PSIwIDAgNDAwIDMwMCIgZmlsbD0ibm9uZSI+CiAgPHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSIzMDAiIGZpbGw9IiMxOTc2RDIiLz4KICA8cGF0aCBkPSJNMTUwIDEwMEgyNTBWMTUwSDE1MFYxMDBaIiBmaWxsPSJ3aGl0ZSIgZmlsbC1vcGFjaXR5PSIwLjEiLz4KICA8cGF0aCBkPSJNMTUwIDUwSDI1MFYxMDBIMTUwVjUwWiIgZmlsbD0id2hpdGUiIGZpbGwtb3BhY2l0eT0iMC4xNSIvPgogIDxwYXRoIGQ9Ik0xMDAgMTUwSDE1MFYyMDBIMTAwVjE1MFoiIGZpbGw9IndoaXRlIiBmaWxsLW9wYWNpdHk9IjAuMiIvPgogIDxwYXRoIGQ9Ik0yMDAgMTUwSDI1MFYyMDBIMjAwVjE1MFoiIGZpbGw9IndoaXRlIiBmaWxsLW9wYWNpdHk9IjAuMiIvPgogIDxwYXRoIGQ9Ik0xMDAgMjAwSDE1MFYyNTBIMTAwVjIwMFoiIGZpbGw9IndoaXRlIiBmaWxsLW9wYWNpdHk9IjAuMSIvPgogIDxwYXRoIGQ9Ik0yMDAgMjAwSDI1MFYyNTBIMjAwVjIwMFoiIGZpbGw9IndoaXRlIiBmaWxsLW9wYWNpdHk9IjAuMSIvPgogIDxwYXRoIGQ9Ik0xNTAgMjAwSDIwMFYyNTBIMTUwVjIwMFoiIGZpbGw9IndoaXRlIiBmaWxsLW9wYWNpdHk9IjAuMDUiLz4KPC9zdmc+'
              }}
            />
          </Illustration>
          
          <Box mt={6} sx={{ opacity: 0.8, fontSize: '0.9rem' }}>
            <p> {new Date().getFullYear()} CodeNova. All rights reserved.</p>
          </Box>
        </motion.div>
        
        {/* Decorative elements */}
        <Box 
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            overflow: 'hidden',
            zIndex: 0,
            '&::before, &::after': {
              content: '""',
              position: 'absolute',
              borderRadius: '50%',
              background: 'rgba(255, 255, 255, 0.1)',
            },
            '&::before': {
              width: 300,
              height: 300,
              top: -100,
              right: -100,
            },
            '&::after': {
              width: 200,
              height: 200,
              bottom: -50,
              left: -50,
            },
          }}
        />
      </LeftPanel>
      
      <RightPanel>
        <AuthCard>
          <Box sx={{ textAlign: isMobile ? 'center' : 'left', mb: 4 }}>
            <Logo>
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="url(#paint0_linear)"/>
                <path d="M2 17L12 22L22 17" stroke="url(#paint1_linear)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="url(#paint2_linear)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <defs>
                  <linearGradient id="paint0_linear" x1="2" y1="7" x2="22" y2="7" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#1976D2"/>
                    <stop offset="1" stopColor="#64B5F6"/>
                  </linearGradient>
                  <linearGradient id="paint1_linear" x1="2" y1="19.5" x2="22" y2="19.5" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#1976D2"/>
                    <stop offset="1" stopColor="#64B5F6"/>
                  </linearGradient>
                  <linearGradient id="paint2_linear" x1="2" y1="14.5" x2="22" y2="14.5" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#1976D2"/>
                    <stop offset="1" stopColor="#64B5F6"/>
                  </linearGradient>
                </defs>
              </svg>
              <h1>CodeNova</h1>
            </Logo>
            
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.5 }}
            >
              <Outlet />
            </motion.div>
          </Box>
        </AuthCard>
        
        {isMobile && (
          <Box mt={4} textAlign="center" sx={{ opacity: 0.7, fontSize: '0.875rem' }}>
            <p> {new Date().getFullYear()} CodeNova. All rights reserved.</p>
          </Box>
        )}
      </RightPanel>
    </AuthContainer>
  );
};

export default AuthLayout;