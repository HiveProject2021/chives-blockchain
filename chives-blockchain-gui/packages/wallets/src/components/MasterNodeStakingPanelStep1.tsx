import React from 'react';
import { Trans } from '@lingui/macro';
import { CardStep,CopyToClipboard, Loading} from '@chives/core';

import { useGetMasterNodeMyCardQuery } from '@chives/api-react';
import {
  Box,
  TextField,
  InputAdornment,
  Grid,
} from '@mui/material';

export type MasterNodeStakingPanelStep1Props = {
  step: number;
  myCard: any;
};

export default function MasterNodeStakingPanelStep1(props: MasterNodeStakingPanelStep1Props) {
  const { step, myCard } = props;
  const isLoading = false
  const WalletBalance = myCard?.WalletBalance;
  const WalletMaxSent = myCard?.WalletMaxSent;
  const StakingAccountStatus = myCard?.StakingAccountStatus;
  const StakingCancelAddress = myCard?.StakingCancelAddress;
  const StakingAccountBalance = myCard?.StakingAccountBalance;


  return (
    <CardStep step={step} title={<Trans>Staking Information</Trans>}>
        <Grid spacing={2} direction="row" container>
            <Grid item xs={6}>
              <Box display="flex">
                  <Box flexGrow={1}>
                  {isLoading ? (
                      <Loading center />
                  ) : (
                      <TextField
                      label={<Trans>Wallet Balance</Trans>}
                      value={WalletBalance}
                      variant="filled"
                      InputProps={{
                          readOnly: true,
                          endAdornment: (
                          <InputAdornment position="end">
                              <CopyToClipboard value={WalletBalance} />
                          </InputAdornment>
                          ),
                      }}
                      fullWidth
                      />
                  )}
                  </Box>
              </Box>
            </Grid>   
            <Grid item xs={6}>
              <Box display="flex">
                  <Box flexGrow={1}>
                  {isLoading ? (
                      <Loading center />
                  ) : (
                      <TextField
                      label={<Trans>Wallet Max Sent</Trans>}
                      value={WalletMaxSent}
                      variant="filled"
                      InputProps={{
                          readOnly: true,
                          endAdornment: (
                          <InputAdornment position="end">
                              <CopyToClipboard value={WalletMaxSent} />
                          </InputAdornment>
                          ),
                      }}
                      fullWidth
                      />
                  )}
                  </Box>
              </Box>
            </Grid>  
        </Grid> 
    </CardStep>

  );
}
