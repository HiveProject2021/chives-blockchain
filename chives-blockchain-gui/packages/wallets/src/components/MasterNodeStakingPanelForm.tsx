import React, { useState, useEffect, useRef } from 'react';
import { Trans, t } from '@lingui/macro';
import { Flex, Form, useOpenDialog, } from '@chives/core';
import {
  useGetSyncStatusQuery,
  useTakeMasterNodeStakingMutation,
} from '@chives/api-react';
import { useForm, SubmitHandler } from 'react-hook-form';
import MasterNodeStakingPanelStep1 from './MasterNodeStakingPanelStep1';
import MasterNodeStakingPanelStep2 from './MasterNodeStakingPanelStep2';
import MasterNodeStakingPanelStep3 from './MasterNodeStakingPanelStep3';
import MasterNodeStakingPanelStep4 from './MasterNodeStakingPanelStep4';
import MasterNodeStakingPanelStep5 from './MasterNodeStakingPanelStep5';

import { useGetMasterNodeMyCardQuery } from '@chives/api-react';

import useWallet from '../hooks/useWallet';
import CreateWalletSendTransactionResultDialog from './WalletSendTransactionResultDialog';

export type MasterNodeStakingPanelFormProps = {
  walletId: number;
};

type FormData = {
  stakingPeriod?: number;
  stakingAmount?: number;
};

export default function MasterNodeStakingPanelForm(props: MasterNodeStakingPanelFormProps) {
  const { walletId } = props;
  const { data: MyCard } = useGetMasterNodeMyCardQuery({
    walletId,
  }, {
    pollingInterval: 20000,
  });
  const StakingAccountStatus: boolean = MyCard?.StakingAccountStatus;
  const stakingAmount: number = MyCard?.stakingAmount;
  const stakingPeriod: number = MyCard?.stakingPeriod;

  //console.log("MyCard=========MasterNodeStakingPanelForm=================", MyCard)

  const methods = useForm<FormData>({
    defaultValues: {
      stakingPeriod: stakingPeriod,
      stakingAmount: stakingAmount,
    },
  });

  const openDialog = useOpenDialog();
  const [takeMasterNodeStaking, { isLoading: isSendTransactionLoading }] = useTakeMasterNodeStakingMutation();
  //const [takeMasterNodeRegister, { isLoading: isSendTransactionLoadingRegister }] = useTakeMasterNodeRegisterMutation();

  const { data: walletState, isLoading: isWalletSyncLoading } = useGetSyncStatusQuery({}, {
    pollingInterval: 20000,
  });

  const { wallet } = useWallet(walletId);

  if (!wallet || isWalletSyncLoading) {
    return null;
  }

  const syncing = !!walletState?.syncing;

  //const navigate = useNavigate();
  //const [loading, setLoading] = useState<boolean>(false);
  //const showError = useShowError();

  let step = 1;

  async function handleSubmit(data: FormData) {
    //const handleSubmit: SubmitHandler<FormData> = async (data) => {
    if (isSendTransactionLoading) {
      return;
    }
    if (syncing) {
      throw new Error(t`Please finish syncing before making a transaction`);
    }
    console.log("handleSubmit", data)
    console.log("walletId", walletId)
    const stakingPeriod = data.stakingPeriod;
    const stakingAmount = data.stakingAmount;

    const response = await takeMasterNodeStaking({
      walletId,
      stakingPeriod,
      stakingAmount,
    });

    const resultDialog = CreateWalletSendTransactionResultDialog({ success: response['data']['success'], message: response['data']['message'] });

    if (resultDialog) {
      await openDialog(resultDialog);
    }
    else {
      throw new Error(response.message ?? 'Something went wrong');
    }

    methods.reset();

  };

  return (
    //Not staking
    <Form methods={methods} onSubmit={handleSubmit}>
      <Flex flexDirection="column" gap={3}>
        <MasterNodeStakingPanelStep1 step={step++} myCard={MyCard} />
        <MasterNodeStakingPanelStep2 step={step++} myCard={MyCard} />
        <MasterNodeStakingPanelStep3 step={step++} myCard={MyCard} />
        <MasterNodeStakingPanelStep4 step={step++} myCard={MyCard} syncing={syncing} walletId={walletId} isSendTransactionLoading={isSendTransactionLoading} />
        {StakingAccountStatus && (
          <MasterNodeStakingPanelStep5 step={step++} myCard={MyCard} syncing={syncing} walletId={walletId} />
        )}
      </Flex>
    </Form>
  );


}
