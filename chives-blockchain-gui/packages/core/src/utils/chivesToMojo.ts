import BigNumber from 'bignumber.js';
import Unit from '../constants/Unit';
import chivesFormatter from './chivesFormatter';

export default function chivesToMojo(chives: string | number | BigNumber): BigNumber {
  return chivesFormatter(chives, Unit.CHIVES)
    .to(Unit.MOJO)
    .toBigNumber();
}