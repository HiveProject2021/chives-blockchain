const chives = require('../../util/chives');

describe('chives', () => {
  it('converts number mojo to chives', () => {
    const result = chives.mojo_to_chives(1000000);

    expect(result).toBe(0.000001);
  });
  it('converts string mojo to chives', () => {
    const result = chives.mojo_to_chives('1000000');

    expect(result).toBe(0.000001);
  });
  it('converts number mojo to chives string', () => {
    const result = chives.mojo_to_chives_string(1000000);

    expect(result).toBe('0.000001');
  });
  it('converts string mojo to chives string', () => {
    const result = chives.mojo_to_chives_string('1000000');

    expect(result).toBe('0.000001');
  });
  it('converts number chives to mojo', () => {
    const result = chives.chives_to_mojo(0.000001);

    expect(result).toBe(1000000);
  });
  it('converts string chives to mojo', () => {
    const result = chives.chives_to_mojo('0.000001');

    expect(result).toBe(1000000);
  });
  it('converts number mojo to colouredcoin', () => {
    const result = chives.mojo_to_colouredcoin(1000000);

    expect(result).toBe(1000);
  });
  it('converts string mojo to colouredcoin', () => {
    const result = chives.mojo_to_colouredcoin('1000000');

    expect(result).toBe(1000);
  });
  it('converts number mojo to colouredcoin string', () => {
    const result = chives.mojo_to_colouredcoin_string(1000000);

    expect(result).toBe('1,000');
  });
  it('converts string mojo to colouredcoin string', () => {
    const result = chives.mojo_to_colouredcoin_string('1000000');

    expect(result).toBe('1,000');
  });
  it('converts number colouredcoin to mojo', () => {
    const result = chives.colouredcoin_to_mojo(1000);

    expect(result).toBe(1000000);
  });
  it('converts string colouredcoin to mojo', () => {
    const result = chives.colouredcoin_to_mojo('1000');

    expect(result).toBe(1000000);
  });
});
