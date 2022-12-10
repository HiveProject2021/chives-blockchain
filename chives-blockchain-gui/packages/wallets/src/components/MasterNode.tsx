import { Alert } from '@mui/material';
import { useParams } from 'react-router-dom';
import { Trans } from '@lingui/macro';
import { Suspender } from '@chives/core';
import { WalletType } from '@chives/api';
import React from 'react';
import MasterNodeStandard from './masternode/MasterNodeStandard';
import useWallet from '../hooks/useWallet';

export default function MasterNode() {
  const { walletId } = useParams();
  const { wallet, loading } = useWallet(walletId);
  if (loading) {
    return (
      <Suspender />
    );
  }

  if (!wallet) {
    return (
      <Alert severity="warning">
        <Trans>Wallet {walletId} not found</Trans>
      </Alert>
    );
  }

  if (wallet.type === WalletType.STANDARD_WALLET) {
    return (
      <MasterNodeStandard walletId={Number(walletId)} />
    );
  }

  return (
    <Alert severity="warning">
      <Trans>Wallet with type {wallet.type} not supported</Trans>
    </Alert>
  );
}
