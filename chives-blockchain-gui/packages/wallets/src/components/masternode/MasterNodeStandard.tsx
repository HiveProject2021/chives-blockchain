import React, { useState } from 'react';
import { Trans } from '@lingui/macro';
import { useNavigate } from 'react-router-dom';
import { WalletType } from '@chives/api';
import { Flex } from '@chives/core';
import { Offers as OffersIcon } from '@chives/icons';
import { Box, Typography, ListItemIcon, MenuItem } from '@mui/material';
import MasterNodeList from '../MasterNodeList';
import MasterNodeStandardCards from './MasterNodeStandardCards';
import WalletReceiveAddress from '../WalletReceiveAddress';
import WalletSend from '../WalletSend';
import WalletHeader from '../WalletHeader';

type WalletMasterNodeProps = {
  walletId: number;
};

export default function WalletMasterNode(props: WalletMasterNodeProps) {
  const { walletId } = props;
  // const showDebugInformation = useShowDebugInformation();
  const navigate = useNavigate();
  const [selectedTab, setSelectedTab] = useState<
    'summary' | 'send' | 'receive'
  >('summary');

  function handleCreateOffer() {
    navigate('/dashboard/offers/create', {
      state: {
        walletId,
        walletType: WalletType.STANDARD_WALLET,
        referrerPath: location.hash.split('#').slice(-1)[0],
      },
    });
  }

  return (
    <Flex flexDirection="column" gap={2.5}>
      <WalletHeader
        walletId={walletId}
        tab={selectedTab}
        onTabChange={setSelectedTab}
        actions={({ onClose }) => (
          <>
            <MenuItem
              onClick={() => {
                onClose();
                handleCreateOffer();
              }}
            >
              <ListItemIcon>
                <OffersIcon />
              </ListItemIcon>
              <Typography variant="inherit" noWrap>
                <Trans>Create Offer</Trans>
              </Typography>
            </MenuItem>
          </>
        )}
      />

      <Box display={selectedTab === 'summary' ? 'block' : 'none'}>
        <Flex flexDirection="column" gap={4}>
          <MasterNodeStandardCards walletId={walletId} />
          <MasterNodeList walletId={walletId} />
        </Flex>
      </Box>
      <Box display={selectedTab === 'send' ? 'block' : 'none'}>
        <WalletSend walletId={walletId} />
      </Box>
      <Box display={selectedTab === 'receive' ? 'block' : 'none'}>
        <WalletReceiveAddress walletId={walletId} />
      </Box>

      {/*
      {showDebugInformation && (
        <WalletConnections walletId={walletId} />
      )}
      */}
    </Flex>
  );
}
