import React from 'react';
import { Trans } from '@lingui/macro';
import { CopyToClipboard, Card, Loading, Flex, TooltipIcon } from '@chives/core';
import { useGetMasterNodeMyCardQuery } from '@chives/api-react';
import {
  Box,
  TextField,
  InputAdornment,
  Grid,
  Typography,
} from '@mui/material';

export type MasterNodeMyCardProps = {
  walletId: number;
};

export default function MasterNodeMyCard(props: MasterNodeMyCardProps) {
  const { walletId } = props;
  const { data: MyCard } = useGetMasterNodeMyCardQuery({
    walletId,
  });
  const isLoading = false
  const StakingAddress = MyCard?.StakingAddress;
  const StakingAccountBalance = MyCard?.StakingAccountBalance;
  const StakingAccountStatus = MyCard?.StakingAccountStatus;
  const StakingCancelAddress = MyCard?.StakingCancelAddress;
  const StakingReceivedAddress = MyCard?.StakingReceivedAddress;


  return (
    <Flex gap={2} flexDirection="column">
      <Flex gap={1} flexGrow={1} justifyContent="space-between">
        <Typography variant="h6">
          <Trans>Staking Information</Trans>
          &nbsp;
          <TooltipIcon>
            <Trans>
              To view my masternode staking informations.
            </Trans>
          </TooltipIcon>
        </Typography>
      </Flex>

      <Card>

        <Grid item xs={12}>
          <Box display="flex">
            <Box flexGrow={1}>
              {isLoading ? (
                <Loading center />
              ) : (
                <TextField
                  label={<Trans>Staking Balance</Trans>}
                  value={StakingAccountBalance}
                  variant="filled"
                  InputProps={{
                    readOnly: true,
                    endAdornment: (
                      <InputAdornment position="end">
                        <CopyToClipboard value={StakingAccountBalance} />
                      </InputAdornment>
                    ),
                  }}
                  fullWidth
                />
              )}
            </Box>
          </Box>
        </Grid>
        <Grid item xs={12}>
          <Box display="flex">
            <Box flexGrow={1}>
              {isLoading ? (
                <Loading center />
              ) : (
                <TextField
                  label={<Trans>Staking Status</Trans>}
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
                  fullWidth
                />
              )}
            </Box>
          </Box>
        </Grid>
        <Grid item xs={12}>
          <Box display="flex">
            <Box flexGrow={1}>
              {isLoading ? (
                <Loading center />
              ) : (
                <TextField
                  label={<Trans>Received Address</Trans>}
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
                  fullWidth
                />
              )}
            </Box>
          </Box>
        </Grid>
        <Grid item xs={12}>
          <Box display="flex">
            <Box flexGrow={1}>
              {isLoading ? (
                <Loading center />
              ) : (
                <TextField
                  label={<Trans>Cancel Address</Trans>}
                  value={StakingCancelAddress}
                  variant="filled"
                  InputProps={{
                    readOnly: true,
                    endAdornment: (
                      <InputAdornment position="end">
                        <CopyToClipboard value={StakingCancelAddress} />
                      </InputAdornment>
                    ),
                  }}
                  fullWidth
                />
              )}
            </Box>
          </Box>
        </Grid>
        <Grid item xs={12}>
          <Box display="flex">
            <Box flexGrow={1}>
              {isLoading ? (
                <Loading center />
              ) : (
                <TextField
                  label={<Trans>Staking Address</Trans>}
                  value={StakingAddress}
                  variant="filled"
                  InputProps={{
                    readOnly: true,
                    endAdornment: (
                      <InputAdornment position="end">
                        <CopyToClipboard value={StakingAddress} />
                      </InputAdornment>
                    ),
                  }}
                  fullWidth
                />
              )}
            </Box>
          </Box>
        </Grid>

      </Card>
    </Flex>
  );
}
