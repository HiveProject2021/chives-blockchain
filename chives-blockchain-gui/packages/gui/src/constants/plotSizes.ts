type PlotSize = {
  label: string;
  value: number;
  workspace: string;
  defaultRam: number;
};

export const defaultPlotSize: PlotSize = {
  label: '11.5GiB',
  value: 29,
  workspace: '29.87GiB',
  defaultRam: 847,
};

const plotSizes: PlotSize[] = [
  { label: '600MiB', value: 25, workspace: '1.8GiB', defaultRam: 512 },
  defaultPlotSize,
  { label: '23.8GiB', value: 30, workspace: '59.75GiB', defaultRam: 1024 },
  { label: '49.1GiB', value: 31, workspace: '119.5GiB', defaultRam: 1695 },
];

export const plotSizeOptions = plotSizes.map((item) => ({
  value: item.value,
  label: `${item.label} (k=${item.value}, temporary space: ${item.workspace})`,
}));

export default plotSizes;
