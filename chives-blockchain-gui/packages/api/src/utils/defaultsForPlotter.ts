import PlotterName from '../constants/PlotterName';
import { PlotterDefaults } from '../@types/Plotter';
import { madmaxDefaults, chiaposDefaults } from '../constants/Plotters'; // bladebitDefaults,

export default function defaultsForPlotter(plotterName: PlotterName): PlotterDefaults {
  switch (plotterName) {
    // case PlotterName.BLADEBIT:
    //   return bladebitDefaults;
    case PlotterName.MADMAX:
      return madmaxDefaults;
    case PlotterName.CHIVESPOS: // fallthrough
    default:
      return chiaposDefaults;
  }
}
