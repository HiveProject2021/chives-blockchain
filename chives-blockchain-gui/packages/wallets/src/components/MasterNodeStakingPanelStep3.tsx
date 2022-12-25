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

export type MasterNodeStakingPanelStep3Props = {
  step: number;
  myCard: any;
};

export default function MasterNodeStakingPanelStep3(props: MasterNodeStakingPanelStep3Props) {
  const { step, myCard } = props;
  const StakingAccountStatus: boolean = myCard?.StakingAccountStatus;
  const WalletMaxSent: number = myCard?.WalletMaxSent;
  const stakingAmount: number = myCard?.stakingAmount;

  return (
    <CardStep step={step} title={<Trans>Please choose staking period</Trans>}>
        <Grid spacing={2} direction="column" container>
            <Grid xs={12} md={12} lg={6} item>
                <Typography color="textSecondary">
                    <Trans>
                    Staking xcc amount, only support these four items
                    </Trans>
                </Typography>
                {StakingAccountStatus && (
                  <FormControl variant="filled" fullWidth>
                    <RadioGroup name="stakingAmount" defaultValue={stakingAmount}>
                      <Flex gap={2} flexWrap="wrap">
                          <FormControlLabel
                          value={stakingAmount}
                          control={<Radio />}
                          label={stakingAmount}
                          disabled={StakingAccountStatus}
                          />
                      </Flex>
                    </RadioGroup>
                  </FormControl>
                )}
                {!StakingAccountStatus && (
                  <FormControl variant="filled" fullWidth>
                    <RadioGroup name="stakingAmount" defaultValue={100000}>
                      <Flex gap={2} flexWrap="wrap">
                          <FormControlLabel
                          value={100000}
                          control={<Radio />}
                          label={<Trans>100,000</Trans>}
                          disabled={WalletMaxSent<100000 || myCard==undefined}
                          />
                          <FormControlLabel
                          control={<Radio />}
                          label={<Trans>300,000</Trans>}
                          value={300000}
                          disabled={WalletMaxSent<300000 || myCard==undefined}
                          />
                          <FormControlLabel
                          control={<Radio />}
                          label={<Trans>500,000</Trans>}
                          value={500000}
                          disabled={WalletMaxSent<500000 || myCard==undefined}
                          />
                          <FormControlLabel
                          control={<Radio />}
                          label={<Trans>1,000,000</Trans>}
                          value={1000000}
                          disabled={StakingAccountStatus || WalletMaxSent<1000000 || myCard==undefined}
                          />
                      </Flex>
                    </RadioGroup>
                  </FormControl>
                )}
                
            </Grid>     
        </Grid> 
    </CardStep>
  );
}
