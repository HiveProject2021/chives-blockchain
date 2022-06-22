import React from 'react';
import { Trans } from '@lingui/macro';
import { FormatLargeNumber, CardSimple } from '@chives/core';
import { useGetTotalHarvestersSummaryQuery } from '@chives/api-react';

export default function PlotCardPlotsDuplicate() {
  const { duplicates, initializedHarvesters, isLoading } = useGetTotalHarvestersSummaryQuery();

  return (
    <CardSimple
      title={<Trans>Duplicate Plots</Trans>}
      value={<FormatLargeNumber value={duplicates} />}
      loading={isLoading || !initializedHarvesters}
    />
  );
}
