import React from 'react';
import { Trans } from '@lingui/macro';
import { FormatLargeNumber, CardSimple } from '@chives/core';
import { useGetTotalHarvestersSummaryQuery } from '@chives/api-react';

export default function PlotCardTotalPlots() {
  const { plots, initializedHarvesters, isLoading } = useGetTotalHarvestersSummaryQuery();

  return (
    <CardSimple
      title={<Trans>Total Plots</Trans>}
      value={<FormatLargeNumber value={plots} />}
      loading={isLoading || !initializedHarvesters}
    />
  );
}
