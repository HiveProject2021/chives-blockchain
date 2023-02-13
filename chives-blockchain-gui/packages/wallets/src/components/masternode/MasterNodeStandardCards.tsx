import React from 'react';
import { Trans } from '@lingui/macro';
import MasterNodeCards from '../MasterNodeCards';

type Props = {
  walletId: number;
};

export default function MasterNodeStandardCards(props: Props) {
  const { walletId } = props;

  return (
    <MasterNodeCards
      walletId={walletId}
      StakingAmountTip={
        <Trans>
          Refresh data every 10 minutes
        </Trans>
      }
      TotalNodesTip={
        <Trans>
          Refresh data every 10 minutes
        </Trans>
      }
      OnlineNodesTip={
        <Trans>
          Refresh data every 10 minutes
        </Trans>
      }
      MyNodeOnlineStatusTip={
        <Trans>
          Refresh data every 10 minutes
        </Trans>
      }
      RewardPoolAmount={
        <Trans>
          Refresh data every 10 minutes
        </Trans>
      }
    />
  );
}
