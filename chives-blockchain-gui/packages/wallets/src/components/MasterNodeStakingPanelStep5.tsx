import React from 'react';
import { Trans, t } from '@lingui/macro';
import { CardStep,Flex,ButtonLoading, Form, useOpenDialog, } from '@chives/core';
import { useTakeMasterNodeCancelMutation, } from '@chives/api-react';
import {
  Grid,
  Typography,
} from '@mui/material';
import CreateWalletSendTransactionResultDialog from './WalletSendTransactionResultDialog';

export type MasterNodeStakingPanelStep5Props = {
  step: number;
  myCard: any;
  syncing: boolean;
  walletId: number;
};

export default function MasterNodeStakingPanelStep5(props: MasterNodeStakingPanelStep5Props) {
  const { step, myCard, syncing, walletId } = props;
  const openDialog = useOpenDialog();
  const [takeMasterNodeCancel, { isLoading: isSendTransactionLoading }] = useTakeMasterNodeCancelMutation();

  async function handleSubmit() {
    //const handleSubmit: SubmitHandler<FormData> = async (data) => {
    if (isSendTransactionLoading) {
      return;
    }
    if (syncing) {
      throw new Error(t`Please finish syncing before making a transaction`);
    }
    console.log("walletId", walletId)
    const response = await takeMasterNodeCancel({
      walletId,
    });

    console.log("takeMasterNodeCancel ------------------")
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
    <CardStep step={step} title={<Trans>Cancel Staking</Trans>}>
        <Grid spacing={2} direction="column" container>
            <Grid xs={12} md={12} lg={6} item>
                <Typography color="textSecondary">
                    <Trans>
                    Your coin have staking in a smart coin base on Lisp, you can cancel it when the staking period is finished.
                    </Trans>
                </Typography>
                <Flex justifyContent="flex-end">
                    <ButtonLoading
                        loading={isSendTransactionLoading}
                        color="primary"
                        type="button"
                        variant="outlined"
                        onClick={handleSubmit}
                    >
                        <Trans>Cancel Staking</Trans>
                    </ButtonLoading>
                </Flex>
            </Grid>     
        </Grid> 
    </CardStep>
  );
}
