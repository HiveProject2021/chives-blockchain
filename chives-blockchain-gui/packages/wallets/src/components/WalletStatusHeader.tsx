import React from 'react';
import { Trans } from '@lingui/macro';
import { Flex, Loading, StateColor, StateIndicatorDot } from '@chives/core';
import { useGetWalletConnectionsQuery } from '@chives/api-react';
import { Box, ButtonGroup, Button } from '@mui/material';
import WalletStatus from './WalletStatus';
import { useTheme } from '@mui/styles';

export default function WalletStatusHeader() {
  const theme = useTheme();
  const { data: connections, isLoading } = useGetWalletConnectionsQuery({}, {
    pollingInterval: 10000,
  });

  const color = isLoading
    ? theme.palette.text.secondary
    : !connections?.length
    ? StateColor.WARNING
    : StateColor.SUCCESS;

  return (
    <ButtonGroup variant="outlined" color="secondary" size="small">
      <Button>
        <WalletStatus
          color={theme.palette.text.primary}
          indicator
          reversed
          justChildren
        />
      </Button>
      <Button>
        <Flex gap={1} alignItems="center">
          <StateIndicatorDot color={color} />
          <Box>
            {isLoading ? (
              <Loading size={32} />
            ) : !connections?.length ? (
              <Trans>Not Connected</Trans>
            ) : (
              <Trans>Connected ({connections?.length})</Trans>
            )}
          </Box>
        </Flex>
      </Button>
    </ButtonGroup>
  );
}
