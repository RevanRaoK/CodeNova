import React from 'react';
import { Box, Typography } from '@mui/material';

export const PatternLibraryPage: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Pattern Library
      </Typography>
      <Typography variant="body1">
        This is the Pattern Library page. You can add your UI components and patterns here.
      </Typography>
    </Box>
  );
};

export default PatternLibraryPage;
