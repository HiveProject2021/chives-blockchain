import PlotterName from '../constants/PlotterName';
import { PlotterOptions } from '../@types/Plotter';
import { madmaxOptions, chiaposOptions } from '../constants/Plotters'; // bladebitOptions, 

export default function optionsForPlotter(plotterName: PlotterName): PlotterOptions {
  switch (plotterName) {
    // case PlotterName.BLADEBIT:
    //   return bladebitOptions;
    case PlotterName.MADMAX:
      return madmaxOptions;
    case PlotterName.CHIVESPOS: // fallthrough
    default:
      return chiaposOptions;
  }
};

