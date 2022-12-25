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
  const StakingAccountStatus: boolean = myCard?.StakingAccountStatus;
  const WalletMaxSent: number = myCard?.WalletMaxSent;
  const stakingPeriod: number = myCard?.stakingPeriod;
  

  return (
    <CardStep step={step} title={<Trans>Please choose staking period</Trans>}>
        <Grid spacing={2} direction="column" container>
            <Grid xs={12} md={12} lg={6} item>
                <Typography color="textSecondary">
                    <Trans>
                    Staking xcc will storage in a smart coin, only staking period finished, xcc will can be withdrawal.
                    </Trans>
                </Typography>
                
                  {StakingAccountStatus && (
                    <FormControl variant="filled" fullWidth>
                      <RadioGroup name="stakingPeriod" defaultValue={stakingPeriod}>
                        <Flex gap={2} flexWrap="wrap">
                            <FormControlLabel
                            value={stakingPeriod}
                            control={<Radio />}
                            label={<Trans>{stakingPeriod} Year</Trans>}
                            disabled={true}
                            />
                        </Flex>
                      </RadioGroup>
                    </FormControl>
                  )}
                  {!StakingAccountStatus && (
                    <FormControl variant="filled" fullWidth>
                      <RadioGroup name="stakingPeriod" defaultValue={0}>
                        <Flex gap={2} flexWrap="wrap">
                            <FormControlLabel
                            value={0}
                            control={<Radio />}
                            label={<Trans>5 minutes(For test/No reward)</Trans>}
                            disabled={WalletMaxSent<100000 || myCard==undefined}
                            />
                            <FormControlLabel
                            control={<Radio />}
                            label={<Trans>One year</Trans>}
                            value={1}
                            disabled={WalletMaxSent<100000 || myCard==undefined}
                            />
                            <FormControlLabel
                            control={<Radio />}
                            label={<Trans>Two year</Trans>}
                            value={2}
                            disabled={WalletMaxSent<100000 || myCard==undefined}
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
