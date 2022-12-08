import React from 'react';
import { Trans } from '@lingui/macro';
import { CardStep,RadioGroup,Flex } from '@chives/core';

import {
  FormControl,
  FormControlLabel,
  Radio,
  Grid,
  Typography,
} from '@mui/material';

export type MasterNodeStakingPanelStep2Props = {
  step: number;
  myCard: any;
};

export default function MasterNodeStakingPanelStep2(props: MasterNodeStakingPanelStep2Props) {
  const { step, myCard } = props;
  const isLoading = false
  const StakingAccountStatus: boolean = myCard?.StakingAccountStatus;
  const StakingReceivedAddress = myCard?.StakingReceivedAddress;

  return (
    <CardStep step={step} title={<Trans>Please choose staking period</Trans>}>
        <Grid spacing={2} direction="column" container>
            <Grid xs={12} md={12} lg={6} item>
                <Typography color="textSecondary">
                    <Trans>
                    Staking xcc will storage in a smart coin, only staking period finished, xcc will can be withdrawal.
                    </Trans>
                </Typography>
                <FormControl variant="filled" fullWidth>
                    <RadioGroup name="stakingPeriod">
                      <Flex gap={2} flexWrap="wrap">
                          <FormControlLabel
                          value={0}
                          control={<Radio />}
                          label={<Trans>5 minutes(For test)</Trans>}
                          disabled={StakingAccountStatus}
                          />
                          <FormControlLabel
                          control={<Radio />}
                          label={<Trans>One year</Trans>}
                          value={1}
                          disabled={StakingAccountStatus}
                          />
                          <FormControlLabel
                          control={<Radio />}
                          label={<Trans>Two year</Trans>}
                          value={2}
                          disabled={StakingAccountStatus}
                          />
                      </Flex>
                    </RadioGroup>
                </FormControl>
            </Grid>     
        </Grid> 
    </CardStep>
  );
}
