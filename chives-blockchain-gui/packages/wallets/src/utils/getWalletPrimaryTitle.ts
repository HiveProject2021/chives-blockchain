import { WalletType } from '@chives/api';
import type { Wallet } from '@chives/api';

export default function getWalletPrimaryTitle(wallet: Wallet): string {
  switch (wallet.type) {
    case WalletType.STANDARD_WALLET:
      return 'Chives';
    default:
      return wallet.name;
  }
}
