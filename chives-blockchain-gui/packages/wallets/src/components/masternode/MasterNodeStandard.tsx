import React, { useState } from 'react';
import { Trans } from '@lingui/macro';
import { useNavigate } from 'react-router-dom';
import { WalletType } from '@chives/api';
import { Flex } from '@chives/core';
import { Box } from '@mui/material';
import MasterNodeList from '../MasterNodeList';
import MasterNodeHeader from '../MasterNodeHeader';
import MasterNodeStandardCards from './MasterNodeStandardCards';
import MasterNodeStakingPanelForm from '../MasterNodeStakingPanelForm';
import MasterNodeReceivedList from '../MasterNodeReceivedList';
import MasterNodeSyncingDataMemo from '../MasterNodeSyncingDataMemo';

type WalletMasterNodeProps = {
  walletId: number;
};

export default function WalletMasterNode(props: WalletMasterNodeProps) {
  const { walletId } = props;
  // const showDebugInformation = useShowDebugInformation();
  const navigate = useNavigate();
  const [selectedTab, setSelectedTab] = useState<
    'summary' | 'staking' | 'rewards'
  >('summary');

  return (
    <Flex flexDirection="column" gap={2.5}>
      <MasterNodeHeader
        walletId={walletId}
        tab={selectedTab}
        onTabChange={setSelectedTab}
      />

      <Box display={selectedTab === 'summary' ? 'block' : 'none'}>
        <Flex flexDirection="column" gap={4}>
          <MasterNodeStandardCards walletId={walletId} />    
          <MasterNodeList walletId={walletId} />     
          <MasterNodeSyncingDataMemo walletId={walletId} />   
        </Flex>
      </Box>
      <Box display={selectedTab === 'staking' ? 'block' : 'none'}>
        <MasterNodeStakingPanelForm walletId={walletId} />
      </Box>
      <Box display={selectedTab === 'rewards' ? 'block' : 'none'}>
        <MasterNodeReceivedList walletId={walletId} />
      </Box>

    </Flex>
  );
}
