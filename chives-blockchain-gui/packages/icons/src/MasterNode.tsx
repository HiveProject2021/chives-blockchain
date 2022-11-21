import React from 'react';
import { SvgIcon, SvgIconProps } from '@mui/material';
import MasterNodeIcon from './images/MasterNode.svg';

export default function Tokens(props: SvgIconProps) {
  return <SvgIcon component={MasterNodeIcon} viewBox="0 0 37 28" {...props} />;
}
