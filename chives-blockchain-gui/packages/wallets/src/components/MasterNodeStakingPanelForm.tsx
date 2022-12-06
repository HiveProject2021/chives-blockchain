import React, { useState, useEffect, useRef } from 'react';
import { Trans, t } from '@lingui/macro';
import { CardStep, CopyToClipboard, Loading, Back, useShowError, ButtonLoading, Flex, Form, 
  useOpenDialog,
  getTransactionResult,} from '@chives/core';
import {
  useGetSyncStatusQuery,
  useTakeMasterNodeStakingMutation,
  useTakeMasterNodeRegisterMutation,
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
  const StakingAccountStatus: boolean = MyCard?.StakingAccountStatus;
  const stakingAmount: number = MyCard?.stakingAmount;
  const stakingPeriod: number = MyCard?.stakingPeriod;
  
  const methods = useForm<FormData>({
    defaultValues: {
      stakingPeriod: stakingPeriod,
      stakingAmount: stakingAmount,
    },
  });

  const openDialog = useOpenDialog();
  const [takeMasterNodeStaking, { isLoading: isSendTransactionLoading }] = useTakeMasterNodeStakingMutation();
  const [takeMasterNodeRegister, { isLoading: isSendTransactionLoadingRegister }] = useTakeMasterNodeRegisterMutation();

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

  
  async function handleSubmitStaking(data: FormData) {
    //const handleSubmitStaking: SubmitHandler<FormData> = async (data) => {
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

    const resultDialog = CreateWalletSendTransactionResultDialog({success: response.success, message: response.message});

    if (resultDialog) {
      await openDialog(resultDialog);
    }
    else {
      throw new Error(response.message ?? 'Something went wrong');
    }

    methods.reset();
    
  };

  async function handleSubmitRegister(data: FormData) {
    //const handleSubmitRegister: SubmitHandler<FormData> = async (data) => {
    if (isSendTransactionLoadingRegister) {
      return;
    }
    if (syncing) {
      throw new Error(t`Please finish syncing before making a transaction`);
    }

    const stakingPeriod = data.stakingPeriod;
    const stakingAmount = data.stakingAmount;

    const response = await takeMasterNodeRegister({
      walletId,
    });
    console.log("------------------")
    console.log(response)

    const resultDialog = CreateWalletSendTransactionResultDialog({success: response.success, message: response.message});

    if (resultDialog) {
      await openDialog(resultDialog);
    }
    else {
      throw new Error(response.message ?? 'Something went wrong');
    }

    methods.reset();
    
  };

  if(!StakingAccountStatus) {
    return (
      //Not staking
      <Form methods={methods} onSubmit={handleSubmitStaking}>
        <Flex flexDirection="column" gap={3}>
          <MasterNodeStakingPanelStep1 step={step++} myCard={MyCard}/>
          <MasterNodeStakingPanelStep2 step={step++} myCard={MyCard}/>
          <MasterNodeStakingPanelStep3 step={step++} myCard={MyCard}/>
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
  else {
    //have staking and begin to register masternode
    return (
      <Form methods={methods} onSubmit={handleSubmitRegister}>
        <Flex flexDirection="column" gap={3}>
          <MasterNodeStakingPanelStep1 step={step++} myCard={MyCard}/>
          <MasterNodeStakingPanelStep2 step={step++} myCard={MyCard}/>
          <MasterNodeStakingPanelStep3 step={step++} myCard={MyCard}/>
          <Flex justifyContent="flex-end">
            <ButtonLoading
              loading={isSendTransactionLoading}
              color="primary"
              type="submit"
              variant="contained"
            >
              <Trans>Begin Register MasterNode</Trans>
            </ButtonLoading>
          </Flex>
        </Flex>
      </Form>
    );
  }
  

}
