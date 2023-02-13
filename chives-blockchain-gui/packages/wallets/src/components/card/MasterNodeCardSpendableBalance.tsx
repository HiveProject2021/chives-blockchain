import React, { ReactElement } from 'react';
import { Trans } from '@lingui/macro';
import { useGetMasterNodeSummaryQuery } from '@chives/api-react';
import { CardSimple } from '@chives/core';

type Props = {
  walletId: number;
  tooltip?: ReactElement<any>;
};

export default function MasterNodeCardSpendableBalance(props: Props) {
  const { walletId, tooltip } = props;

  const {
    data: MasterNodeSummary
  } = useGetMasterNodeSummaryQuery({
    walletId,
  }, {
    pollingInterval: 30000,
  });

  const error = null;
  const isLoading = false;
  const value = MasterNodeSummary?.MasterNodeStakingAmount;

  return (
    <CardSimple
      loading={isLoading}
      valueColor="secondary"
      title={<Trans>Spendable Balance</Trans>}
      tooltip={tooltip}
      value={value}
      error={error}
    />
  );
}
