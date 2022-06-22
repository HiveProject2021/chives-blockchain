import React, { useMemo } from 'react';
import { Trans } from '@lingui/macro';
import { useCurrencyCode, mojoToChivesLocaleString, CardSimple, useLocale } from '@chives/core';
import { useGetFarmedAmountQuery } from '@chives/api-react';

export default function FarmCardTotalChivesFarmed() {
  const currencyCode = useCurrencyCode();
  const [locale] = useLocale();
  const { data, isLoading, error } = useGetFarmedAmountQuery();

  const farmedAmount = data?.farmedAmount;

  const totalChivesFarmed = useMemo(() => {
    if (farmedAmount !== undefined) {
      return (
        <>
          {mojoToChivesLocaleString(farmedAmount, locale)}
          &nbsp;
          {currencyCode}
        </>
      );
    }
  }, [farmedAmount, locale, currencyCode]);

  return (
    <CardSimple
      title={<Trans>Total Chives Farmed</Trans>}
      value={totalChivesFarmed}
      loading={isLoading}
      error={error}
    />
  );
}
