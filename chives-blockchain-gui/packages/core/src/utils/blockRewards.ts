import Big from 'big.js';

const MOJO_PER_CHIVES = Big(100000000);
const BLOCKS_PER_YEAR = 1681920;

export function calculatePoolReward(height: number): Big {
  if (height > 170000)  {
    if (height === 0) {
      return MOJO_PER_CHIVES.times(0);
    }
    if (height < 3 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(2*100*0.45).times(7 / 8);
    }
    if (height < 6 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(1*100*0.45).times(7 / 8);
    }
    if (height < 9 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(0.5*100*0.45).times(7 / 8);
    }
    if (height < 12 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(0.25*100*0.45).times(7 / 8);
    }
    return MOJO_PER_CHIVES.times(0.125*100*0.45).times(7 / 8);
  }
  else {
    if (height === 0) {
      return MOJO_PER_CHIVES.times(0);
    }
    if (height < 3 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(2*100*0.9).times(7 / 8);
    }
    if (height < 6 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(1*100*0.9).times(7 / 8);
    }
    if (height < 9 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(0.5*100*0.9).times(7 / 8);
    }
    if (height < 12 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(0.25*100*0.9).times(7 / 8);
    }
    return MOJO_PER_CHIVES.times(0.125*100*0.9).times(7 / 8);
  }
}

export function calculateBaseFarmerReward(height: number): Big {
  if (height > 170000)  {
    if (height === 0) {
      return MOJO_PER_CHIVES.times(0);
    }
    if (height < 3 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(2*100*0.45).times(1 / 8);
    }
    if (height < 6 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(1*100*0.45).times(1 / 8);
    }
    if (height < 9 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(0.5*100*0.45).times(1 / 8);
    }
    if (height < 12 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(0.25*100*0.45).times(1 / 8);
    }
    return MOJO_PER_CHIVES.times(0.125*100*0.45).times(1 / 8);
  }
  else {
    if (height === 0) {
      return MOJO_PER_CHIVES.times(0);
    }
    if (height < 3 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(2*100*0.9).times(1 / 8);
    }
    if (height < 6 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(1*100*0.9).times(1 / 8);
    }
    if (height < 9 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(0.5*100*0.9).times(1 / 8);
    }
    if (height < 12 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(0.25*100*0.9).times(1 / 8);
    }
    return MOJO_PER_CHIVES.times(0.125*100*0.9).times(1 / 8);
  }
}


export function calculateBaseCommunityReward(height: number): Big {
  if (height > 170000)  {
    if (height === 0) {
      return MOJO_PER_CHIVES.times(0);
    }
    if (height < 3 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(2*100).times(0.55);
    }
    if (height < 6 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(1*100).times(0.55);
    }
    if (height < 9 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(0.5*100).times(0.55);
    }
    if (height < 12 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(0.25*100).times(0.55);
    }
    return MOJO_PER_CHIVES.times(0.125*100).times(0.55);
  }
  else {
    if (height === 0) {
      return MOJO_PER_CHIVES.times(0);
    }
    if (height < 3 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(2*100).times(0.1);
    }
    if (height < 6 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(1*100).times(0.1);
    }
    if (height < 9 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(0.5*100).times(0.1);
    }
    if (height < 12 * BLOCKS_PER_YEAR) {
      return MOJO_PER_CHIVES.times(0.25*100).times(0.1);
    }
    return MOJO_PER_CHIVES.times(0.125*100).times(0.1);
  }
}