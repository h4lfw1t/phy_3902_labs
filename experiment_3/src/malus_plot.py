#!/usr/bin/env python3
"""
Malus' Law Visualization Module

This module provides functionality to visualize data from Malus' Law experiments,
which demonstrates the relationship between the intensity of polarized light and the angle
between two polarizing filters.
"""

import os
from dataclasses import dataclass
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from utils import (
    BaseConstants,
    BaseConfig,
    FileManager,
    DataProcessor as BaseDataProcessor,
    PlotHelper as BasePlotHelper,
)


@dataclass
class MalusConstants(BaseConstants):
    """Constants specific to Malus' Law analysis."""
    # Inherits common constants from BaseConstants


@dataclass
class MalusConfig(BaseConfig):
    """Configuration parameters for Malus' Law analysis."""
    DATA_DIR: str = '../data/malus/'  # Data directory specific to Malus experiment


# Global instances
CONSTANTS = MalusConstants()
CONFIG = MalusConfig()


class MalusDataProcessor(BaseDataProcessor):
    """Handles data processing for Malus' Law analysis."""

    @staticmethod
    def process_angle_data(data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Process raw data to extract angles and intensity values.

        Args:
            data: DataFrame containing raw experiment data

        Returns:
            Tuple of (angles, ldr_voltage_feedback, ldr_voltage_stddev)
        """
        # Extract angle and intensity data
        angles = BaseDataProcessor.steps_to_degrees(data['step'], CONSTANTS.STEPPER_STEPS_PER_REV)
        ldr_voltage_feedback = BaseDataProcessor.adc_to_voltage(
            data['adc_mean'], CONSTANTS.V_SUPPLY, CONSTANTS.ANALOG_RESOLUTION)
        ldr_voltage_stddev = BaseDataProcessor.adc_to_voltage(
            data['adc_stddev'], CONSTANTS.V_SUPPLY, CONSTANTS.ANALOG_RESOLUTION)

        # Find index of first maximum
        first_max_idx = np.argmax(ldr_voltage_feedback)

        # Roll arrays so first maximum is at index 0
        angles = np.roll(angles, -first_max_idx)
        ldr_voltage_feedback = np.roll(ldr_voltage_feedback, -first_max_idx)
        ldr_voltage_stddev = np.roll(ldr_voltage_stddev, -first_max_idx)

        # Shift angles so that first maximum is at 0 and wrap around
        angles = angles - angles[0]
        angles = np.mod(angles, 360)

        return angles, ldr_voltage_feedback, ldr_voltage_stddev


class MalusPlotHelper(BasePlotHelper):
    """Helper methods for plotting Malus' Law data."""

    @staticmethod
    def create_malus_plot(
        angles: np.ndarray,
        voltages: np.ndarray,
        voltage_stddev: np.ndarray,
        title: str = "Malus' Law: Angle vs LDR Voltage"
    ) -> plt.Figure:
        """
        Create visualization plot for Malus' Law data.

        Args:
            angles: Array of angle values in degrees
            voltages: Array of voltage values
            voltage_stddev: Array of voltage standard deviations
            title: Plot title

        Returns:
            The matplotlib Figure object
        """
        fig, ax = BasePlotHelper.setup_basic_figure()

        # Plot measured data with error bars
        ax.errorbar(
            angles,
            voltages,
            yerr=voltage_stddev,
            label='Measured Voltage',
            marker='o',
            linestyle='None',
            markersize=3,
            color='blue',
            ecolor='lightgray',
            elinewidth=1,
            capsize=2
        )

        ax.set_title(title)
        ax.set_xlabel('Angle (degrees)')
        ax.set_ylabel('LDR Voltage (V)')
        ax.set_xlim(0, 360)
        ax.set_xticks(np.arange(0, 361, 30))

        # Set y-axis limits with a small buffer
        y_min = max(0, voltages.min() - 0.1)  # Ensure non-negative
        y_max = voltages.max() + 0.1
        ax.set_ylim(y_min, y_max)

        ax.grid(True)
        ax.legend()

        plt.tight_layout()
        return fig


class MalusLawAnalyzer:
    """Main class for visualizing Malus' Law experiments."""

    def __init__(self):
        """Initialize the analyzer with required components."""
        self.file_manager = FileManager()
        self.data_processor = MalusDataProcessor()
        self.plot_helper = MalusPlotHelper()

    def plot_malus_law_data(self, data_file: str) -> Dict[str, Any]:
        """
        Plot data from a single Malus' Law data file.

        Args:
            data_file: Path to the CSV data file

        Returns:
            Dictionary with plot results
        """
        # Get filename for output naming
        base_filename = os.path.splitext(os.path.basename(data_file))[0]

        # Load and process data
        data = self.file_manager.load_csv_data(data_file)
        angles, voltages, voltage_stddev = self.data_processor.process_angle_data(data)

        # Create plot
        fig = self.plot_helper.create_malus_plot(
            angles,
            voltages,
            voltage_stddev,
            title=f"Malus' Law: {base_filename}"
        )

        # Ensure output directory exists and save plot
        out_dir = self.file_manager.ensure_output_directory(CONFIG.OUT_DIR)
        out_filename = f"malus_plot_{base_filename}.png"
        out_path = self.plot_helper.save_figure(fig, out_filename, out_dir)

        plt.show()
        plt.close(fig)

        # Return plot results
        return {
            'filename': os.path.basename(data_file),
            'output_path': out_path,
            'max_voltage': voltages.max(),
            'min_voltage': voltages.min(),
            'voltage_range': voltages.max() - voltages.min()
        }


def main() -> None:
    """
    Main function to process and plot all Malus' Law data files.
    """
    # Initialize analyzer
    analyzer = MalusLawAnalyzer()

    # Get absolute path to data directory
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), CONFIG.DATA_DIR))

    # Process each CSV file in the data directory
    for file in os.listdir(data_dir):
        if file.endswith(".csv"):
            print(f"\nProcessing file: {file}")
            data_file = os.path.join(data_dir, file)
            result = analyzer.plot_malus_law_data(data_file)

            # Report basic statistics
            print(f"  ✓ Voltage range: {result['min_voltage']:.3f}V - {result['max_voltage']:.3f}V")
            print(f"  ✓ Peak-to-peak amplitude: {result['voltage_range']:.3f}V")
            print(f"  ✓ Plot saved to {result['output_path']}")



if __name__ == "__main__":
    main()