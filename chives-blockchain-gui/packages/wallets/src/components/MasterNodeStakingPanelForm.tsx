import React, { useState, useEffect, useRef } from 'react';
import { Trans } from '@lingui/macro';
import { CardStep, CopyToClipboard, Loading, Back, useShowError, ButtonLoading, Flex, Form, 
  useOpenDialog,
  chivesToMojo,
  getTransactionResult,} from '@chives/core';
import {
  useGetSyncStatusQuery,
  useTakeMasterNodeStakingMutation,
  useFarmBlockMutation,
} from '@chives/api-react';
import { useNavigate, useLocation } from 'react-router';
import { useForm, SubmitHandler } from 'react-hook-form';
import MasterNodeStakingPanelStep1 from './MasterNodeStakingPanelStep1';
import MasterNodeStakingPanelStep2 from './MasterNodeStakingPanelStep2';
import MasterNodeStakingPanelStep3 from './MasterNodeStakingPanelStep3';

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
  });

  const openDialog = useOpenDialog();
  const [takeMasterNodeStaking, { isLoading: isSendTransactionLoading }] = useTakeMasterNodeStakingMutation();
  const methods = useForm<FormData>({
    defaultValues: {
      stakingPeriod: 1,
      stakingAmount: 300000,
    },
  });

  const { data: walletState, isLoading: isWalletSyncLoading } = useGetSyncStatusQuery({}, {
    pollingInterval: 10000,
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

    const stakingPeriod = data.stakingPeriod;
    const stakingAmount = data.stakingAmount;

    const response = await takeMasterNodeStaking({
      walletId,
      stakingPeriod,
      stakingAmount,
    });
    console.log("------------------")
    console.log(response)

    const result = getTransactionResult(response.transaction);
    const resultDialog = CreateWalletSendTransactionResultDialog({success: result.success, message: result.message});

    if (resultDialog) {
      await openDialog(resultDialog);
    }
    else {
      throw new Error(result.message ?? 'Something went wrong');
    }

    methods.reset();
    
  };

  return (
    <Form methods={methods} onSubmit={handleSubmit}>
      <Flex flexDirection="column" gap={3}>
        <MasterNodeStakingPanelStep1 step={step++} myCard={MyCard}/>
        <MasterNodeStakingPanelStep2 step={step++}/>
        <MasterNodeStakingPanelStep3 step={step++}/>
        <Flex justifyContent="flex-end">
          <ButtonLoading
            loading={isSendTransactionLoading}
            color="primary"
            type="submit"
            variant="contained"
          >
            <Trans>Begin Staking</Trans>
          </ButtonLoading>
        </Flex>
      </Flex>
    </Form>
  );

}
