import React from 'react';
import styled from 'styled-components';
import { Box, BoxProps } from '@mui/material';
import { Chives } from '@chives/icons';

const StyledChives = styled(Chives)`
  max-width: 100%;
  width: auto;
  height: auto;
`;

export default function Logo(props: BoxProps) {
  return (
    <Box {...props}>
      <StyledChives />
    </Box>
  );
}
