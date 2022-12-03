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
};

export default function MasterNodeStakingPanelStep2(props: MasterNodeStakingPanelStep2Props) {
  const { step } = props;

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
                    <RadioGroup name="StakingPeriod" defaultValue={0}>
                      <Flex gap={2} flexWrap="wrap">
                          <FormControlLabel
                          value={0}
                          control={<Radio />}
                          label={<Trans>5 minutes(For test)</Trans>}
                          />
                          <FormControlLabel
                          control={<Radio />}
                          label={<Trans>One year</Trans>}
                          value={1}
                          />
                          <FormControlLabel
                          control={<Radio />}
                          label={<Trans>Two year</Trans>}
                          value={2}
                          />
                      </Flex>
                    </RadioGroup>
                </FormControl>
            </Grid>     
        </Grid> 
    </CardStep>
  );
}
