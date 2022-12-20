import React from 'react';
import { Trans, t } from '@lingui/macro';
import { CardStep,Flex,ButtonLoading,useOpenDialog } from '@chives/core';
import {useTakeMasterNodeRegisterMutation, } from '@chives/api-react';

import {
  Grid,
  Typography,
} from '@mui/material';

import CreateWalletSendTransactionResultDialog from './WalletSendTransactionResultDialog';

export type MasterNodeStakingPanelStep4Props = {
  step: number;
  myCard: any;
  syncing: boolean;
  walletId: number;
  isSendTransactionLoading: boolean;
};

export default function MasterNodeStakingPanelStep4(props: MasterNodeStakingPanelStep4Props) {
  const { step, myCard, syncing, walletId, isSendTransactionLoading } = props;
  const StakingAccountStatus: boolean = myCard?.StakingAccountStatus;
  const StakingAccountBalance: number = myCard?.StakingAccountBalance;
  const WalletMaxSent: number = myCard?.WalletMaxSent;
  const StakingRegisterMasterNode: number = myCard?.StakingRegisterMasterNode;

  const openDialog = useOpenDialog();
  const [takeMasterNodeRegister, { isLoading: isSendTransactionLoadingRegister }] = useTakeMasterNodeRegisterMutation();

  async function handleSubmit() {
    //const handleSubmit: SubmitHandler<FormData> = async (data) => {
    if (isSendTransactionLoadingRegister) {
      return;
    }
    if (syncing) {
      throw new Error(t`Please finish syncing before making a transaction`);
    }
    console.log("walletId", walletId)
    const response = await takeMasterNodeRegister({
      walletId,
    });

    console.log("takeMasterNodeRegister ------------------")
    console.log(response)

    const resultDialog = CreateWalletSendTransactionResultDialog({success: response['data']['success'], message: response['data']['message']});

    if (resultDialog) {
      await openDialog(resultDialog);
    }
    else {
      throw new Error(response.message ?? 'Something went wrong');
    }

  };

  return (
    <CardStep step={step} title={<Trans>Staking Operation</Trans>}>
        <Grid spacing={2} direction="column" container>
            <Grid xs={12} md={12} lg={6} item>
              {!StakingAccountStatus && WalletMaxSent<100000 && (
                <Typography color="textSecondary">
                    <Trans>
                    Staking a masternode requires at least 100000 xcc in your wallet.
                    </Trans>
                </Typography>
              )}
              {!StakingAccountStatus && WalletMaxSent>=100000 && (
                <Typography color="textSecondary">
                    <Trans>
                    This step will stake your coins into a Lisp-based smartcoin and will take a few minutes to package into the blockchain.
                    </Trans>
                </Typography>
              )}
              {!StakingAccountStatus && WalletMaxSent>=100000 && (
                <Flex justifyContent="flex-end">
                    <ButtonLoading
                        loading={isSendTransactionLoading}
                        color="primary"
                        type="submit"
                        variant="contained"
                    >
                        <Trans>Start Staking</Trans>
                    </ButtonLoading>
                </Flex>
              )}

              {StakingAccountStatus && StakingRegisterMasterNode && (
                <Typography color="textSecondary">
                    <Trans>
                    Your masternode is running, you need keep Chives fullnode and wallet is running and then will receive the reward every day.
                    </Trans>
                </Typography>
              )}
              {StakingAccountStatus && !StakingRegisterMasterNode && (
                <Typography color="textSecondary">
                    <Trans>
                    This step will register your masternode to the blockchain.
                    </Trans>
                </Typography>
              )}
              {StakingAccountStatus && !StakingRegisterMasterNode && (
                <Flex justifyContent="flex-end">
                    <ButtonLoading
                        loading={isSendTransactionLoadingRegister}
                        color="primary"
                        type="button"
                        variant="contained"
                        onClick={handleSubmit}
                    >
                        <Trans>Start Register MasterNode</Trans>
                    </ButtonLoading>
                </Flex>
              )}
                
            </Grid>     
        </Grid> 
    </CardStep>
  );
}
