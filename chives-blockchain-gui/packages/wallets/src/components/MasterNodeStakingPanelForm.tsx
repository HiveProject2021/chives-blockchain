import React, { useState, useEffect, useRef } from 'react';
import { Trans } from '@lingui/macro';
import { CardStep, CopyToClipboard, Loading, Back, useShowError, ButtonLoading, Flex, Form} from '@chives/core';
import { useNavigate, useLocation } from 'react-router';
import { useForm, SubmitHandler } from 'react-hook-form';
import MasterNodeStakingPanelStep1 from './MasterNodeStakingPanelStep1';
import MasterNodeStakingPanelStep2 from './MasterNodeStakingPanelStep2';
import MasterNodeStakingPanelStep3 from './MasterNodeStakingPanelStep3';

import { useGetMasterNodeMyCardQuery } from '@chives/api-react';

type FormData = {
  StakingPeriod?: number;
  StakingAmount?: number;
};

export type MasterNodeStakingPanelFormProps = {
  walletId: number;
};

export default function MasterNodeStakingPanelForm(props: MasterNodeStakingPanelFormProps) {
  const { walletId } = props;
  const { data: MyCard } = useGetMasterNodeMyCardQuery({
    walletId,
  });
  
  const navigate = useNavigate();
  const [loading, setLoading] = useState<boolean>(false);
  const showError = useShowError();

  const methods = useForm<FormData>({
    defaultValues: { StakingPeriod:0, StakingAmount:100000 },
  });

  let step = 1;

  const isLoading = false
  const StakingAddress = MyCard?.StakingAddress;
  const StakingAccountBalance = MyCard?.StakingAccountBalance;
  const StakingAccountStatus = MyCard?.StakingAccountStatus;
  const StakingCancelAddress = MyCard?.StakingCancelAddress;
  const StakingReceivedAddress = MyCard?.StakingReceivedAddress;

  const handleSubmit: SubmitHandler<FormData> = async (data) => {
    try {
      setLoading(true);
      console.log("handleSubmit");
      console.log(data);
      //const { p2SingletonPuzzleHash, delay, createNFT, ...rest } = data;
      
      //await startPlotting(plotAddConfig).unwrap();

      //navigate('/dashboard/plot');
    } catch (error) {
      await showError(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form methods={methods} onSubmit={handleSubmit}>
      <Flex flexDirection="column" gap={3}>
        <MasterNodeStakingPanelStep1 step={step++} myCard={MyCard}/>
        <MasterNodeStakingPanelStep2 step={step++}/>
        <MasterNodeStakingPanelStep3 step={step++}/>
        <Flex justifyContent="flex-end">
          <ButtonLoading
            loading={loading}
            color="primary"
            type="submit"
            variant="contained"
          >
            <Trans>Begin Staking</Trans>
          </ButtonLoading>
        </Flex>
      </Flex>
    </Form>
  );

}
