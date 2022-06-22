import React from 'react';
import { SvgIcon, SvgIconProps } from '@mui/material';
import ChivesIcon from './images/chives.svg';

export default function Keys(props: SvgIconProps) {
  return <SvgIcon component={ChivesIcon} viewBox="0 0 150 58" {...props} />;
}
