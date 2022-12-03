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
};

export default function MasterNodeStakingPanelStep3(props: MasterNodeStakingPanelStep3Props) {
  const { step } = props;

  return (
    <CardStep step={step} title={<Trans>Please choose staking period</Trans>}>
        <Grid spacing={2} direction="column" container>
            <Grid xs={12} md={12} lg={6} item>
                <Typography color="textSecondary">
                    <Trans>
                    Staking xcc amount, only support these three items
                    </Trans>
                </Typography>
                <FormControl variant="filled" fullWidth>
                    <RadioGroup name="StakingAmount" defaultValue={100000}>
                      <Flex gap={2} flexWrap="wrap">
                          <FormControlLabel
                          value={100000}
                          control={<Radio />}
                          label={<Trans>100,000</Trans>}
                          />
                          <FormControlLabel
                          control={<Radio />}
                          label={<Trans>300,000</Trans>}
                          value={300000}
                          />
                          <FormControlLabel
                          control={<Radio />}
                          label={<Trans>500,000</Trans>}
                          value={500000}
                          />
                      </Flex>
                    </RadioGroup>
                </FormControl>
            </Grid>     
        </Grid> 
    </CardStep>
  );
}
