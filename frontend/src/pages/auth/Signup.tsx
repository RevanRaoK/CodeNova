import React, { useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import {
  Box,
  Button,
  TextField,
  Typography,
  Link,
  InputAdornment,
  IconButton,
  CircularProgress,
  Alert,
  useTheme,
  Checkbox,
  FormControlLabel,
  Grid,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme as useAppTheme } from '@/theme/ThemeProvider';

const SignupPage: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { signup } = useAuth();
  const navigate = useNavigate();
  const theme = useTheme();
  const { mode } = useAppTheme();

  const validationSchema = Yup.object({
    name: Yup.string()
      .min(2, 'Name must be at least 2 characters')
      .required('Name is required'),
    email: Yup.string()
      .email('Enter a valid email')
      .required('Email is required'),
    password: Yup.string()
      .min(8, 'Password must be at least 8 characters')
      .matches(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
        'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character'
      )
      .required('Password is required'),
    confirmPassword: Yup.string()
      .oneOf([Yup.ref('password'), undefined], 'Passwords must match')
      .required('Confirm Password is required'),
    terms: Yup.boolean()
      .oneOf([true], 'You must accept the terms and conditions')
      .required('You must accept the terms and conditions'),
  });

  const formik = useFormik({
    initialValues: {
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
      terms: false,
    },
    validationSchema,
    onSubmit: async (values) => {
      setError(null);
      setLoading(true);
      try {
        await signup(values.name, values.email, values.password);
        navigate('/');
      } catch (err: any) {
        console.error('Signup error:', err);
        setError(err.response?.data?.detail || 'Failed to create account. Please try again.');
      } finally {
        setLoading(false);
      }
    },
  });

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const handleMouseDownPassword = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
  };

  return (
    <Box
      component="form"
      onSubmit={formik.handleSubmit}
      sx={{
        width: '100%',
        maxWidth: 500,
        mx: 'auto',
      }}
    >
      <Box mb={4}>
        <Typography 
          variant="h4" 
          component="h1" 
          gutterBottom
          sx={{
            fontWeight: 700,
            background: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.secondary.main} 90%)`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            display: 'inline-block',
          }}
        >
          Create your account
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Already have an account?{' '}
          <Link component={RouterLink} to="/login" color="primary">
            Sign in
          </Link>
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            id="name"
            name="name"
            label="Full Name"
            value={formik.values.name}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            error={formik.touched.name && Boolean(formik.errors.name)}
            helperText={formik.touched.name && formik.errors.name}
            margin="normal"
            variant="outlined"
            autoComplete="name"
            autoFocus
          />
        </Grid>
        
        <Grid item xs={12}>
          <TextField
            fullWidth
            id="email"
            name="email"
            label="Email address"
            type="email"
            value={formik.values.email}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            error={formik.touched.email && Boolean(formik.errors.email)}
            helperText={formik.touched.email && formik.errors.email}
            margin="normal"
            variant="outlined"
            autoComplete="email"
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            id="password"
            name="password"
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={formik.values.password}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            error={formik.touched.password && Boolean(formik.errors.password)}
            helperText={formik.touched.password && formik.errors.password}
            margin="normal"
            variant="outlined"
            autoComplete="new-password"
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    aria-label="toggle password visibility"
                    onClick={handleClickShowPassword}
                    onMouseDown={handleMouseDownPassword}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            id="confirmPassword"
            name="confirmPassword"
            label="Confirm Password"
            type={showPassword ? 'text' : 'password'}
            value={formik.values.confirmPassword}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            error={formik.touched.confirmPassword && Boolean(formik.errors.confirmPassword)}
            helperText={formik.touched.confirmPassword && formik.errors.confirmPassword}
            margin="normal"
            variant="outlined"
            autoComplete="new-password"
          />
        </Grid>
      </Grid>

      <Box mt={2} mb={3}>
        <FormControlLabel
          control={
            <Checkbox
              id="terms"
              name="terms"
              checked={formik.values.terms}
              onChange={formik.handleChange}
              color="primary"
            />
          }
          label={
            <Typography variant="body2" color={formik.touched.terms && formik.errors.terms ? 'error' : 'textSecondary'}>
              I agree to the{' '}
              <Link href="/terms" color="primary">
                Terms of Service
              </Link>{' '}
              and{' '}
              <Link href="/privacy" color="primary">
                Privacy Policy
              </Link>
            </Typography>
          }
        />
        {formik.touched.terms && formik.errors.terms && (
          <Typography variant="caption" color="error" display="block" mt={1}>
            {formik.errors.terms}
          </Typography>
        )}
      </Box>

      <Button
        type="submit"
        fullWidth
        variant="contained"
        color="primary"
        size="large"
        disabled={loading || !formik.isValid}
        sx={{
          py: 1.5,
          mb: 2,
          borderRadius: 2,
          textTransform: 'none',
          fontSize: '1rem',
          fontWeight: 600,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: `0 4px 12px ${
              mode === 'dark' 
                ? 'rgba(0, 0, 0, 0.3)' 
                : 'rgba(25, 118, 210, 0.2)'
            }`,
          },
        }}
      >
        {loading ? (
          <CircularProgress size={24} color="inherit" />
        ) : (
          'Create account'
        )}
      </Button>

      <Box mt={3} textAlign="center">
        <Typography variant="body2" color="text.secondary">
          By signing up, you agree to our{' '}
          <Link href="/terms" color="primary">
            Terms of Service
          </Link>{' '}
          and{' '}
          <Link href="/privacy" color="primary">
            Privacy Policy
          </Link>
          .
        </Typography>
      </Box>
    </Box>
  );
};

export default SignupPage;
