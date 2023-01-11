import React from 'react';
import { Trans } from '@lingui/macro';
import { CardStep, CopyToClipboard, Loading } from '@chives/core';

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
  const StakingAccountStatus: boolean = myCard?.StakingAccountStatus;
  const StakingReceivedAddress = myCard?.StakingReceivedAddress;

  return (
    <CardStep step={step} title={<Trans>Staking Information</Trans>}>
      <Grid spacing={2} direction="row" container>
        {!StakingAccountStatus && (
          <>
            <Grid item xs={6}>
              <Box display="flex">
                <Box flexGrow={1}>
                  {isLoading ? (
                    <Loading center />
                  ) : (
                    <TextField
                      disabled
                      name="WalletBalance"
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
                      fullWidth />
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
                      disabled
                      name="WalletMaxSent"
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
                      fullWidth />
                  )}
                </Box>
              </Box>
            </Grid>
          </>
        )}

        {StakingAccountStatus && (
          <>
            <Grid item xs={6}>
              <Box display="flex">
                <Box flexGrow={1}>
                  {isLoading ? (
                    <Loading center />
                  ) : (
                    <TextField
                      disabled
                      name="StakingAccountStatus"
                      label={<Trans>Staking Account Status</Trans>}
                      value={StakingAccountStatus}
                      variant="filled"
                      InputProps={{
                        readOnly: true,
                        endAdornment: (
                          <InputAdornment position="end">
                            <CopyToClipboard value={StakingAccountStatus} />
                          </InputAdornment>
                        ),
                      }}
                      fullWidth />
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
                      disabled
                      name="StakingReceivedAddress"
                      label={<Trans>Staking Received Address</Trans>}
                      value={StakingReceivedAddress}
                      variant="filled"
                      InputProps={{
                        readOnly: true,
                        endAdornment: (
                          <InputAdornment position="end">
                            <CopyToClipboard value={StakingReceivedAddress} />
                          </InputAdornment>
                        ),
                      }}
                      fullWidth />
                  )}
                </Box>
              </Box>
            </Grid>
          </>
        )}

      </Grid>
    </CardStep>

  );
}
