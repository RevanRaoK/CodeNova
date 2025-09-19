import { GlobalStyles as MuiGlobalStyles, useTheme } from '@mui/material';

export const GlobalStyles = () => {
  const theme = useTheme();
  
  return (
    <MuiGlobalStyles
      styles={{
        '*, *::before, *::after': {
          boxSizing: 'border-box',
          margin: 0,
          padding: 0,
        },
        html: {
          height: '100%',
          width: '100%',
          WebkitFontSmoothing: 'antialiased',
          MozOsxFontSmoothing: 'grayscale',
        },
        body: {
          margin: 0,
          padding: 0,
          minHeight: '100vh',
          width: '100%',
          backgroundColor: theme.palette.background.default,
          color: theme.palette.text.primary,
          lineHeight: 1.5,
          '&.no-scroll': {
            overflow: 'hidden',
          },
        },
        '#root': {
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
          width: '100%',
        },
        a: {
          color: theme.palette.primary.main,
          textDecoration: 'none',
          '&:hover': {
            textDecoration: 'underline',
          },
        },
        'h1, h2, h3, h4, h5, h6': {
          margin: 0,
          fontWeight: 600,
          lineHeight: 1.2,
        },
        p: {
          margin: 0,
        },
        button: {
          cursor: 'pointer',
          '&:disabled': {
            cursor: 'not-allowed',
          },
        },
        'img, svg': {
          maxWidth: '100%',
          height: 'auto',
        },
        'ul, ol': {
          listStyle: 'none',
          margin: 0,
          padding: 0,
        },
      }}
    />
  );
};

export default GlobalStyles;
