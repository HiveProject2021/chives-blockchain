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
          Staking Amount
        </Trans>
      }
      TotalNodesTip={
        <Trans>
          Total Nodes
        </Trans>
      }
      OnlineNodesTip={
        <Trans>
          Online Nodes
        </Trans>
      }
      HaveSendAmountTip={
        <Trans>
          Have Send Amount
        </Trans>
      }
      RewardPoolAmount={
        <Trans>
          Reward Pool Amount
        </Trans>
      }
    />
  );
}
