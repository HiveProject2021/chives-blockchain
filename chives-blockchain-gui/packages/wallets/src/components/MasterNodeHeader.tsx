import React, { type ReactNode } from 'react';
import { Trans } from '@lingui/macro';
import { Flex, } from '@chives/core';
import {Tab, Tabs,} from '@mui/material';
import WalletName from './WalletName';

type MasterNodeWalletProps = {
  walletId: number;
  tab: 'summary' | 'staking' | 'rewards';
  onTabChange: (tab: 'summary' | 'staking' | 'rewards') => void;
};

export default function MasterNodeHeader(props: MasterNodeWalletProps) {
  const { walletId, tab, onTabChange } = props;

  return (
    <Flex flexDirection="column" gap={2}>
      <WalletName walletId={walletId} variant="h5" />
      <Flex gap={1} alignItems="center">
        <Flex flexGrow={1} gap={1}>
          <Tabs
            value={tab}
            onChange={(_event, newValue) => onTabChange(newValue)}
            textColor="primary"
            indicatorColor="primary"
          >
            <Tab value="summary" label={<Trans>Summary</Trans>} />
            <Tab value="staking" label={<Trans>Staking</Trans>} />
            <Tab value="rewards" label={<Trans>Rewards</Trans>} />
          </Tabs>
        </Flex>
        <Flex gap={1} alignItems="center">
          {/*
          <Flex alignItems="center">
            <Typography variant="body1" color="textSecondary">
              <Trans>Status:</Trans>
            </Typography>
            &nbsp;
            <WalletStatus height={showDebugInformation} />
          </Flex>
          */}
        </Flex>
      </Flex>
    </Flex>
  );
}
