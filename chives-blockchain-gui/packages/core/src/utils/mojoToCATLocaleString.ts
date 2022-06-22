import BigNumber from 'bignumber.js';
import Unit from '../constants/Unit';
import chivesFormatter from './chivesFormatter';

export default function mojoToCATLocaleString(mojo: string | number | BigNumber, locale?: string) {
  return chivesFormatter(mojo, Unit.MOJO)
    .to(Unit.CAT)
    .toLocaleString(locale);
}
