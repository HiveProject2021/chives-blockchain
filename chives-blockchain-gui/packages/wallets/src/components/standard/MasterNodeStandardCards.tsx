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
      totalBalanceTooltip={
        <Trans>
          This is the total amount of chives in the blockchain at the current peak
          block that is controlled by your private keys. It includes frozen
          farming rewards, but not pending incoming and outgoing transactions.
        </Trans>
      }
      spendableBalanceTooltip={
        <Trans>
          This is the amount of Chives that you can currently use to make
          transactions. It does not include pending farming rewards, pending
          incoming transactions, and Chives that you have just spent but is not
          yet in the blockchain.
        </Trans>
      }
      pendingTotalBalanceTooltip={
        <Trans>
          This is the total balance + pending balance: it is what your balance
          will be after all pending transactions are confirmed.
        </Trans>
      }
      pendingBalanceTooltip={
        <Trans>
          This is the sum of the incoming and outgoing pending transactions (not
          yet included into the blockchain). This does not include farming
          rewards.
        </Trans>
      }
      pendingChangeTooltip={
        <Trans>
          This is the pending change, which are change coins which you have sent
          to yourself, but have not been confirmed yet.
        </Trans>
      }
    />
  );
}
