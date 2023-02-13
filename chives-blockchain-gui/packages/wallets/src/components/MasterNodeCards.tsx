import React, { ReactElement } from 'react';
import { Grid } from '@mui/material';
import { useGetMasterNodeSummaryQuery } from '@chives/api-react';
import { Trans } from '@lingui/macro';
import { CardSimple, Flex, TooltipIcon } from '@chives/core';
import styled from 'styled-components';
import MasterNodeReceivedGraph from './MasterNodeReceivedGraph';

export type MasterNodeCardsProps = {
  walletId: number;
  StakingAmountTip?: ReactElement<any>;
  TotalNodesTip?: ReactElement<any>;
  OnlineNodesTip?: ReactElement<any>;
  MyNodeOnlineStatusTip?: ReactElement<any>;
  RewardPoolAmount?: ReactElement<any>;
};

const StyledGraphContainer = styled.div`
  margin-left: -1rem;
  margin-right: -1rem;
  margin-top: 1rem;
  margin-bottom: -1rem;
  position: relative;
`;

export default function MasterNodeCards(props: MasterNodeCardsProps) {
  const {
    walletId,
    StakingAmountTip,
    TotalNodesTip,
    OnlineNodesTip,
    MyNodeOnlineStatusTip,
    RewardPoolAmount,
  } = props;

  const {
    data: MasterNodeSummary
  } = useGetMasterNodeSummaryQuery({
    walletId,
  }, {
    pollingInterval: 30000,
  });

  const error = null;
  const isLoading = false;
  const MasterNodeStakingAmount = MasterNodeSummary?.MasterNodeStakingAmount;
  const MasterNodeCount = MasterNodeSummary?.MasterNodeCount;
  const MasterNodeOnlineCount = MasterNodeSummary?.MasterNodeOnlineCount;
  const MyNodeOnlineStatus = MasterNodeSummary?.MyNodeOnlineStatus;
  const MasterNodeRewardPoolAmount = MasterNodeSummary?.MasterNodeRewardPoolAmount;

  return (
    <div>
      <Grid spacing={2} alignItems="stretch" container>
        <Grid xs={12} lg={4} item>
          <CardSimple
            loading={isLoading}
            title={<Trans>Staking Amount</Trans>}
            tooltip={StakingAmountTip}
            value={MasterNodeStakingAmount}
            error={error}
          >
            <Flex flexGrow={1} />
            <StyledGraphContainer>
              <MasterNodeReceivedGraph walletId={walletId} height={80} />
            </StyledGraphContainer>
          </CardSimple>
        </Grid>
        <Grid xs={12} lg={8} item>
          <Grid spacing={2} alignItems="stretch" container>
            <Grid xs={12} md={6} item>
              <CardSimple
                loading={isLoading}
                valueColor="secondary"
                title={<Trans>Total Nodes</Trans>}
                tooltip={TotalNodesTip}
                value={MasterNodeCount}
                error={error}
              />
            </Grid>
            <Grid xs={12} md={6} item>
              <CardSimple
                loading={isLoading}
                valueColor="secondary"
                title={<Trans>Online Nodes</Trans>}
                tooltip={OnlineNodesTip}
                value={MasterNodeOnlineCount}
                error={error}
              />
            </Grid>
            <Grid xs={12} md={6} item>
              <CardSimple
                loading={isLoading}
                valueColor="secondary"
                title={<Trans>My Node Status</Trans>}
                tooltip={MyNodeOnlineStatusTip}
                value={MyNodeOnlineStatus}
                error={error}
              />
            </Grid>
            <Grid xs={12} md={6} item>
              <CardSimple
                loading={isLoading}
                valueColor="secondary"
                title={<Trans>Reward Pool Amount</Trans>}
                tooltip={RewardPoolAmount}
                value={MasterNodeRewardPoolAmount}
                error={error}
              />
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </div>
  );
}

MasterNodeCards.defaultProps = {
  StakingAmountTip: undefined,
  TotalNodesTip: undefined,
  OnlineNodesTip: undefined,
  MyNodeOnlineStatusTip: undefined,
  RewardPoolAmount: undefined,
};
