import BigNumber from 'bignumber.js';
import Unit from '../constants/Unit';
import chivesFormatter from './chivesFormatter';

export default function mojoToChivesLocaleString(mojo: string | number | BigNumber, locale?: string) {
  return chivesFormatter(mojo, Unit.MOJO)
    .to(Unit.CHIVES)
    .toLocaleString(locale);
}
