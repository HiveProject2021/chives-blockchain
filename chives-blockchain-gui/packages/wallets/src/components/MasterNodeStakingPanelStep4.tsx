import React from 'react';
import { Trans, t } from '@lingui/macro';
import { CardStep,Flex,ButtonLoading,useOpenDialog } from '@chives/core';
import {useTakeMasterNodeRegisterMutation, } from '@chives/api-react';

import {
  FormControl,
  FormControlLabel,
  Radio,
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
  const isLoading = false
  const StakingAccountStatus: boolean = myCard?.StakingAccountStatus;
  const StakingReceivedAddress = myCard?.StakingReceivedAddress;

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
              {!StakingAccountStatus && (
                <Typography color="textSecondary">
                    <Trans>
                    This step will staking your coin to a smart coin base on Lisp, and it will takes a few minutes to complete the blockchain packaging operation.
                    </Trans>
                </Typography>
              )}
              {!StakingAccountStatus && (
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
              )}

              {StakingAccountStatus && (
                <Typography color="textSecondary">
                    <Trans>
                    This step will register your masternode to blockchain.
                    </Trans>
                </Typography>
              )}
              {StakingAccountStatus && (
                <Flex justifyContent="flex-end">
                    <ButtonLoading
                        loading={isSendTransactionLoadingRegister}
                        color="primary"
                        type="button"
                        variant="contained"
                        onClick={handleSubmit}
                    >
                        <Trans>Begin Register MasterNode</Trans>
                    </ButtonLoading>
                </Flex>
              )}
                
            </Grid>     
        </Grid> 
    </CardStep>
  );
}
