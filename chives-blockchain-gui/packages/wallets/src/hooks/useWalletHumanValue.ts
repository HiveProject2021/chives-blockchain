import { useMemo } from 'react';
import type { Wallet } from '@chives/api';
import { WalletType } from '@chives/api';
import BigNumber from 'bignumber.js';
import { mojoToCATLocaleString, mojoToChivesLocaleString, useLocale } from '@chives/core';

export default function useWalletHumanValue(wallet: Wallet, value?: string | number | BigNumber, unit?: string): string {
  const [locale] = useLocale();
  
  return useMemo(() => {
    if (wallet && value !== undefined) {
      const localisedValue = wallet.type === WalletType.CAT
        ? mojoToCATLocaleString(value, locale)
        : mojoToChivesLocaleString(value, locale);

      return `${localisedValue} ${unit}`;
    }

    return '';
  }, [wallet, value, unit, locale]);
}
