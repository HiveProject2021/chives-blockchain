import React, { ReactElement } from 'react';
import { Grid } from '@mui/material';
import MasterNodeCardTotalBalance from './card/MasterNodeCardTotalBalance';
import MasterNodeCardSpendableBalance from './card/MasterNodeCardSpendableBalance';
import MasterNodeCardPendingTotalBalance from './card/MasterNodeCardPendingTotalBalance';
import MasterNodeCardPendingBalance from './card/MasterNodeCardPendingBalance';
import MasterNodeCardPendingChange from './card/MasterNodeCardPendingChange';

export type MasterNodeCardsProps = {
  walletId: number;
  totalBalanceTooltip?: ReactElement<any>;
  spendableBalanceTooltip?: ReactElement<any>;
  pendingTotalBalanceTooltip?: ReactElement<any>;
  pendingBalanceTooltip?: ReactElement<any>;
  pendingChangeTooltip?: ReactElement<any>;
};

export default function MasterNodeCards(props: MasterNodeCardsProps) {
  const {
    walletId,
    totalBalanceTooltip,
    spendableBalanceTooltip,
    pendingTotalBalanceTooltip,
    pendingBalanceTooltip,
    pendingChangeTooltip,
  } = props;

  return (
    <div>
      <Grid spacing={2} alignItems="stretch" container>
        <Grid xs={12} lg={4} item>
          <MasterNodeCardTotalBalance
            walletId={walletId}
            tooltip={totalBalanceTooltip}
          />
        </Grid>
        <Grid xs={12} lg={8} item>
          <Grid spacing={2} alignItems="stretch" container>
            <Grid xs={12} md={6} item>
              <MasterNodeCardSpendableBalance
                walletId={walletId}
                tooltip={spendableBalanceTooltip}
              />
            </Grid>
            <Grid xs={12} md={6} item>
              <MasterNodeCardPendingTotalBalance
                walletId={walletId}
                tooltip={pendingTotalBalanceTooltip}
              />
            </Grid>
            <Grid xs={12} md={6} item>
              <MasterNodeCardPendingBalance
                walletId={walletId}
                tooltip={pendingBalanceTooltip}
              />
            </Grid>
            <Grid xs={12} md={6} item>
              <MasterNodeCardPendingChange
                walletId={walletId}
                tooltip={pendingChangeTooltip}
              />
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </div>
  );
}

MasterNodeCards.defaultProps = {
  totalBalanceTooltip: undefined,
  spendableBalanceTooltip: undefined,
  pendingTotalBalanceTooltip: undefined,
  pendingBalanceTooltip: undefined,
  pendingChangeTooltip: undefined,
};
