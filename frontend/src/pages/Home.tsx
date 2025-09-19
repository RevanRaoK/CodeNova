import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '@mui/material/styles';
import {
  Box,
  Button,
  Container,
  Grid,
  Typography,
  Card,
  CardContent,
  CardMedia,
  useMediaQuery,
  alpha,
} from '@mui/material';
import {
  Code as CodeIcon,
  AutoFixHigh as AutoFixHighIcon,
  Security as SecurityIcon,
  GitHub as GitHubIcon,
  ArrowForward as ArrowForwardIcon,
  CodeOff as CodeOffIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { useAuth } from '@/contexts/AuthContext';

const features = [
  {
    icon: <CodeIcon fontSize="large" color="primary" />,
    title: 'AI-Powered Code Review',
    description: 'Get instant, intelligent code reviews from our advanced AI that learns from your codebase.',
  },
  {
    icon: <AutoFixHighIcon fontSize="large" color="primary" />,
    title: 'Automated Refactoring',
    description: 'Automatically refactor your code to follow best practices and improve maintainability.',
  },
  {
    icon: <SecurityIcon fontSize="large" color="primary" />,
    title: 'Security Analysis',
    description: 'Identify security vulnerabilities and potential issues before they make it to production.',
  },
  {
    icon: <CodeOffIcon fontSize="large" color="primary" />,
    title: 'Code Quality',
    description: 'Maintain high code quality with automated style checks and code quality metrics.',
  },
  {
    icon: <GitHubIcon fontSize="large" color="primary" />,
    title: 'GitHub Integration',
    description: 'Seamlessly integrate with your GitHub repositories for continuous code review.',
  },
  {
    icon: <SpeedIcon fontSize="large" color="primary" />,
    title: 'Performance Insights',
    description: 'Get performance optimization suggestions to make your code run faster and more efficiently.',
  },
];

const HomePage: React.FC = () => {
  const theme = useTheme();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isSmallScreen = useMediaQuery(theme.breakpoints.down('sm'));

  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate('/code-review');
    } else {
      navigate('/signup');
    }
  };

  return (
    <Box sx={{ width: '100%', overflow: 'hidden' }}>
      {/* Hero Section */}
      <Box
        sx={{
          pt: { xs: 8, md: 12 },
          pb: { xs: 8, md: 16 },
          position: 'relative',
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(
            theme.palette.secondary.main,
            0.1
          )} 100%)`,
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: `radial-gradient(circle at 20% 30%, ${alpha(theme.palette.primary.main, 0.1)} 0%, transparent 40%), 
                         radial-gradient(circle at 80% 70%, ${alpha(theme.palette.secondary.main, 0.1)} 0%, transparent 40%)`,
            zIndex: 0,
          },
        }}
      >
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography
                variant={isSmallScreen ? 'h3' : 'h2'}
                component="h1"
                gutterBottom
                sx={{
                  fontWeight: 800,
                  lineHeight: 1.2,
                  mb: 3,
                  background: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.secondary.main} 90%)`,
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                AI-Powered Code Reviews in Seconds
              </Typography>
              <Typography
                variant={isSmallScreen ? 'h6' : 'h5'}
                color="text.secondary"
                paragraph
                sx={{
                  mb: 4,
                  maxWidth: '90%',
                  fontWeight: 400,
                }}
              >
                Improve code quality, catch bugs early, and learn best practices with intelligent AI code reviews.
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 4 }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleGetStarted}
                  endIcon={<ArrowForwardIcon />}
                  sx={{
                    px: 4,
                    py: 1.5,
                    borderRadius: 2,
                    textTransform: 'none',
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.3)}`,
                    '&:hover': {
                      boxShadow: `0 6px 24px ${alpha(theme.palette.primary.main, 0.4)}`,
                    },
                  }}
                >
                  {isAuthenticated ? 'Go to Code Review' : 'Get Started for Free'}
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => window.open('https://github.com/your-repo', '_blank')}
                  startIcon={<GitHubIcon />}
                  sx={{
                    px: 4,
                    py: 1.5,
                    borderRadius: 2,
                    textTransform: 'none',
                    fontSize: '1.1rem',
                    fontWeight: 500,
                  }}
                >
                  View on GitHub
                </Button>
              </Box>
            </Grid>
            {!isMobile && (
              <Grid item xs={12} md={6}>
                <Box
                  sx={{
                    position: 'relative',
                    borderRadius: 4,
                    overflow: 'hidden',
                    boxShadow: theme.shadows[10],
                    border: `1px solid ${theme.palette.divider}`,
                    backgroundColor: theme.palette.background.paper,
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: 40,
                      background: theme.palette.mode === 'dark' ? '#2d2d2d' : '#f5f5f5',
                      borderBottom: `1px solid ${theme.palette.divider}`,
                      display: 'flex',
                      alignItems: 'center',
                      padding: '0 16px',
                    },
                    '&::after': {
                      content: '""',
                      position: 'absolute',
                      top: 12,
                      left: 16,
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: '#ff5f56',
                      boxShadow: '20px 0 0 #ffbd2e, 40px 0 0 #27c93f',
                    },
                  }}
                >
                  <Box
                    component="img"
                    src="/images/code-review-demo.png"
                    alt="CodeNova Code Review"
                    sx={{
                      width: '100%',
                      height: 'auto',
                      display: 'block',
                      mt: 5,
                    }}
                    onError={(e) => {
                      // Fallback to a code block if image fails to load
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      target.insertAdjacentHTML(
                        'afterend',
                        `<pre style="margin: 0; padding: 20px; font-family: 'Roboto Mono', monospace; font-size: 14px; line-height: 1.5; color: ${theme.palette.text.primary};">
// Example code review
function calculateTotal(items) {
  // AI Suggestion: Consider using reduce for summing array values
  return items.reduce((sum, item) => sum + item.price, 0);
}

// Security issue detected
const password = 'secret123'; // ⚠️ Warning: Hardcoded credentials detected

// Performance suggestion
const filtered = largeArray.filter(x => x > 10); // 💡 Consider using .some() or .every() if you only need to check a condition
</pre>`
                      );
                    }}
                  />
                </Box>
              </Grid>
            )}
          </Grid>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Box textAlign="center" mb={8}>
          <Typography
            variant="h4"
            component="h2"
            sx={{
              fontWeight: 700,
              mb: 2,
              background: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.secondary.main} 90%)`,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              display: 'inline-block',
            }}
          >
            Why Choose CodeNova?
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 700, mx: 'auto' }}>
            Powerful features to improve your development workflow and code quality
          </Typography>
        </Box>

        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'transform 0.3s, box-shadow 0.3s',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: theme.shadows[8],
                  },
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 3,
                  overflow: 'hidden',
                }}
              >
                <CardContent sx={{ p: 4, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                  <Box
                    sx={{
                      width: 60,
                      height: 60,
                      borderRadius: '50%',
                      backgroundColor: alpha(theme.palette.primary.main, 0.1),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mb: 3,
                    }}
                  >
                    {feature.icon}
                  </Box>
                  <Typography variant="h6" component="h3" gutterBottom sx={{ fontWeight: 600, mb: 1 }}>
                    {feature.title}
                  </Typography>
                  <Typography color="text.secondary" sx={{ flexGrow: 1 }}>
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* CTA Section */}
      <Box
        sx={{
          py: 8,
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(
            theme.palette.secondary.main,
            0.1
          )} 100%)`,
          mt: 8,
        }}
      >
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          <Typography variant="h4" component="h2" gutterBottom sx={{ fontWeight: 700, mb: 2 }}>
            Ready to improve your code quality?
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}>
            Join thousands of developers who trust CodeNova for their code reviews and quality assurance.
          </Typography>
          <Button
            variant="contained"
            size="large"
            onClick={handleGetStarted}
            endIcon={<ArrowForwardIcon />}
            sx={{
              px: 6,
              py: 1.5,
              borderRadius: 2,
              textTransform: 'none',
              fontSize: '1.1rem',
              fontWeight: 600,
              boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.3)}`,
              '&:hover': {
                boxShadow: `0 6px 24px ${alpha(theme.palette.primary.main, 0.4)}`,
              },
            }}
          >
            {isAuthenticated ? 'Go to Dashboard' : 'Get Started for Free'}
          </Button>
        </Container>
      </Box>
    </Box>
  );
};

export default HomePage;
