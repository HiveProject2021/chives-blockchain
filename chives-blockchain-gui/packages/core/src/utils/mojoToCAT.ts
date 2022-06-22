import BigNumber from 'bignumber.js';
import Unit from '../constants/Unit';
import chivesFormatter from './chivesFormatter';

export default function mojoToCAT(mojo: string | number | BigNumber): BigNumber {
  return chivesFormatter(mojo, Unit.MOJO)
    .to(Unit.CAT)
    .toBigNumber();
}