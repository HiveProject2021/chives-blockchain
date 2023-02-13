import React from 'react';
import { Trans } from '@lingui/macro';
import { CardStep} from '@chives/core';
import { useGetMasterNodeSyncingDataQuery } from '@chives/api-react';


export type MasterNodeSyncingDataMemoProps = {
    walletId: number;
  };
  

export default function MasterNodeSyncingDataMemo(props: MasterNodeSyncingDataMemoProps) {
    const { walletId } = props;
    useGetMasterNodeSyncingDataQuery({
        walletId,
        }, {
        pollingInterval: 600000,
        });
    return (
        <CardStep step={1} title={<Trans>Refresh data every 10 minutes</Trans>}>
        </CardStep>
    );
}
