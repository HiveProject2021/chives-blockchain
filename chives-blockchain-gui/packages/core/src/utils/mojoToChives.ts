import BigNumber from 'bignumber.js';
import Unit from '../constants/Unit';
import chivesFormatter from './chivesFormatter';

export default function mojoToChives(mojo: string | number | BigNumber): BigNumber {
  return chivesFormatter(mojo, Unit.MOJO)
    .to(Unit.CHIVES)
    .toBigNumber();
}