import React from 'react';
import { Trans } from '@lingui/macro';
import { CardStep,Flex,ButtonLoading } from '@chives/core';

import {
  FormControl,
  FormControlLabel,
  Radio,
  Grid,
  Typography,
} from '@mui/material';

export type MasterNodeStakingPanelStep4Props = {
  step: number;
  myCard: any;
  isSendTransactionLoading: any;
};

export default function MasterNodeStakingPanelStep4(props: MasterNodeStakingPanelStep4Props) {
  const { step, myCard, isSendTransactionLoading } = props;
  const isLoading = false
  const StakingAccountStatus: boolean = myCard?.StakingAccountStatus;
  const StakingReceivedAddress = myCard?.StakingReceivedAddress;

  const formButton = {"submitButton":"Begin Staking","submitResult":{}};
  if(StakingAccountStatus) {
    formButton.submitButton = "Begin Register MasterNode";
  }

  return (
    <CardStep step={step} title={<Trans>Staking Operation</Trans>}>
        <Grid spacing={2} direction="column" container>
            <Grid xs={12} md={12} lg={6} item>
                <Typography color="textSecondary">
                    <Trans>
                    This step will staking your coin to a smart coin base on Lisp, and it will takes a few minutes to complete the blockchain packaging operation.
                    </Trans>
                </Typography>
                <Flex justifyContent="flex-end">
                    <ButtonLoading
                        loading={isSendTransactionLoading}
                        color="primary"
                        type="submit"
                        variant="contained"
                    >
                        <Trans>{formButton.submitButton}</Trans>
                    </ButtonLoading>
                </Flex>
            </Grid>     
        </Grid> 
    </CardStep>
  );
}
