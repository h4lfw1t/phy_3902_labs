#!/usr/bin/env python3
"""
Laser Profile Analysis Module

This module provides functionality to analyze laser beam profiles using intensity measurements.
It loads data from CSV files, calculates intensity values, fits Gaussian profiles to the
derivative of intensity, and generates analysis plots.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

from utils import (
    BaseConstants,
    BaseConfig,
    FileManager,
    DataProcessor,
    PlotHelper,
    ErrorPropagation
)

# Constants
@dataclass
class ProfileConstants(BaseConstants):
    """Constants used in the laser profile analysis."""
    # Inherits common constants from BaseConstants


# Configuration
@dataclass
class ProfileConfig(BaseConfig):
    """Configuration parameters for laser profile analysis."""
    DATA_DIR: str = '../data/laser_profile/'


# Global instances
CONSTANTS = ProfileConstants()
CONFIG = ProfileConfig()


class GaussianFitter:
    """Fits Gaussian distributions to laser profile data."""

    @staticmethod
    def gaussian(x: np.ndarray, a: float, x0: float, sigma: float) -> np.ndarray:
        """
        Gaussian function for fitting.

        Args:
            x: Input x values
            a: Amplitude
            x0: Mean (center position)
            sigma: Standard deviation

        Returns:
            Gaussian function values
        """
        return a * np.exp(-(x - x0)**2 / (2 * sigma**2))

    def fit_gaussian_to_derivative(
        self,
        positions_rad: np.ndarray,
        intensities: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, Optional[float], Optional[float], Optional[float], Optional[float]]:
        """
        Fit a Gaussian to the derivative of intensity.

        Args:
            positions_rad: Position values in radians
            intensities: Intensity values

        Returns:
            Tuple containing:
            - Region of interest (ROI) positions
            - ROI intensity derivatives
            - Amplitude (or None if fit failed)
            - Mean (or None if fit failed)
            - Sigma (or None if fit failed)
            - FWHM (or None if fit failed)
        """
        # Calculate derivative
        intensity_derivative = np.gradient(intensities, positions_rad)

        # Calculate standard deviation of derivative in flat regions
        abs_deriv = np.abs(intensity_derivative)
        threshold_idx = int(len(abs_deriv) * 0.6)  # Consider lowest 60% as flat
        flat_threshold = np.sort(abs_deriv)[threshold_idx]
        flat_region = abs_deriv <= flat_threshold
        flat_stddev = np.std(intensity_derivative[flat_region])

        # Dynamic threshold based on flat region noise (3-sigma threshold)
        threshold = 3 * flat_stddev

        # Find significant regions using dynamic threshold
        significant_indices = np.where(np.abs(intensity_derivative) > threshold)[0]
        if len(significant_indices) < 3:  # Need at least 3 points for a reasonable fit
            print("Warning: Not enough significant data points found for Gaussian fit")
            return positions_rad, intensity_derivative, None, None, None, None

        # Get a continuous region around the significant area
        start_idx = max(0, significant_indices[0] - 2)
        end_idx = min(len(positions_rad) - 1, significant_indices[-1] + 2)

        positions_roi = positions_rad[start_idx:end_idx+1]
        intensity_deriv_roi = intensity_derivative[start_idx:end_idx+1]

        # Improved initial guess for Gaussian parameters
        max_abs_idx = np.argmax(np.abs(intensity_deriv_roi))
        a_guess = intensity_deriv_roi[max_abs_idx]  # Amplitude
        x0_guess = positions_roi[max_abs_idx]  # Center position

        # More robust estimate for sigma
        roi_width = positions_roi[-1] - positions_roi[0]

        # Try to find half-maximum points
        max_val = np.max(np.abs(intensity_deriv_roi))
        half_max_indices = np.where(np.abs(intensity_deriv_roi) >= max_val / 2)[0]
        if len(half_max_indices) >= 2:
            half_max_width = positions_roi[half_max_indices[-1]] - positions_roi[half_max_indices[0]]
            sigma_guess = half_max_width / 2.355  # FWHM to sigma conversion
        else:
            sigma_guess = roi_width / 4  # Default to quarter of ROI width

        # Fit the Gaussian
        try:
            popt, _ = curve_fit(
                self.gaussian,
                positions_roi,
                intensity_deriv_roi,
                p0=[a_guess, x0_guess, sigma_guess]
            )
            amplitude, mean, sigma = popt
            fwhm = 2.355 * sigma  # FWHM for Gaussian is 2.355 * sigma

            return positions_roi, intensity_deriv_roi, amplitude, mean, sigma, fwhm
        except Exception as e:
            print(f"Warning: Gaussian fit failed with error: {e}")
            return positions_roi, intensity_deriv_roi, None, None, None, None


class LaserProfileAnalyzer:
    """Main class for analyzing laser beam profiles."""

    def __init__(self):
        """Initialize analyzer with required components."""
        self.file_manager = FileManager()
        self.data_processor = DataProcessor()
        self.plot_helper = PlotHelper()
        self.gaussian_fitter = GaussianFitter()

    def calculate_intensity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate intensity and its standard deviation from LDR readings.

        Args:
            df: DataFrame with ldr_mean and ldr_stddev columns

        Returns:
            DataFrame with position, intensity, and intensity_stddev
        """
        ldr_voltage = self.data_processor.adc_to_voltage(
            df['ldr_mean'], CONSTANTS.V_SUPPLY, CONSTANTS.ANALOG_RESOLUTION
        )
        ldr_voltage_stddev = self.data_processor.adc_to_voltage(
            df['ldr_stddev'], CONSTANTS.V_SUPPLY, CONSTANTS.ANALOG_RESOLUTION
        )
        intensity = 1 / ldr_voltage
        intensity_stddev = ldr_voltage_stddev / (ldr_voltage ** 2)

        return pd.DataFrame({
            'position': df['position'],
            'intensity': intensity,
            'intensity_stddev': intensity_stddev
        })

    def analyze_profile(self, csv_path: str) -> Dict[str, Any]:
        """
        Analyze a laser beam profile from CSV data.

        Args:
            csv_path: Path to CSV file with laser profile data

        Returns:
            Dictionary with analysis results
        """
        # Extract filename for output
        filename = os.path.basename(csv_path)
        base_name = os.path.splitext(filename)[0]

        # Load and process data
        df = self.file_manager.load_csv_data(csv_path)
        intensity_df = self.calculate_intensity(df)

        # Sort by position to ensure consistency
        sorted_df = intensity_df.sort_values('position')
        positions_deg = sorted_df['position'].values
        positions_rad = self.data_processor.degrees_to_radians(positions_deg)
        intensities = sorted_df['intensity'].values
        intensities_stddev = sorted_df['intensity_stddev'].values

        # Calculate derivative of intensity
        intensity_derivative = np.gradient(intensities, positions_rad)

        # Use the new error propagation method for central differences
        dx = positions_rad[1] - positions_rad[0]  # Assuming uniform spacing
        intensity_derivative_stddev = ErrorPropagation.central_difference_error(
            intensities, intensities_stddev, dx
        )

        # Fit Gaussian to derivative
        fit_results = self.gaussian_fitter.fit_gaussian_to_derivative(positions_rad, intensities)
        positions_roi, intensity_deriv_roi, amplitude, mean, sigma, fwhm = fit_results

        # Create figure with subplots
        fig, axes = plt.subplots(2, 1, figsize=(10, 12), sharex=True)

        # Plot 1: Intensity with error bars
        axes[0].errorbar(
            positions_rad,
            intensities,
            yerr=intensities_stddev,
            fmt='o',
            ecolor='red',
            capsize=3,
            label='Intensity'
        )
        axes[0].set_ylabel('Intensity (1/V)')
        axes[0].set_title(f'Laser Profile: {base_name}')
        axes[0].grid(True)
        axes[0].legend()

        # Plot 2: Derivative with Gaussian fit and error bars
        axes[1].errorbar(
            positions_rad,
            intensity_derivative,
            yerr=intensity_derivative_stddev,
            fmt='o',
            ecolor='red',
            capsize=2,
            label='Derivative'
        )

        # Add Gaussian fit if successful
        if sigma is not None:
            # Generate x values for smooth curve
            x_fit = np.linspace(positions_rad.min(), positions_rad.max(), 1000)
            y_fit = self.gaussian_fitter.gaussian(x_fit, amplitude, mean, sigma)

            axes[1].plot(
                x_fit,
                y_fit,
                'r--',
                label=f'Gaussian Fit\nFWHM={fwhm:.3f} rad\nσ={sigma:.3f} rad'
            )

            # Mark center of Gaussian
            axes[1].axvline(
                x=mean,
                color='g',
                linestyle='--',
                label=f'Center: {mean:.3f} rad'
            )

        axes[1].set_xlabel('Position (radians)')
        axes[1].set_ylabel('Derivative of Intensity')
        axes[1].set_title('Derivative of Laser Profile (True Intensity Distribution)')
        axes[1].grid(True)
        axes[1].legend()

        # Set x-ticks to increments of pi/12 (~15 deg)
        min_rad = positions_rad.min()
        max_rad = positions_rad.max()
        xticks = np.arange(min_rad, max_rad + 0.01, np.pi/12)
        axes[1].set_xticks(xticks)
        axes[1].set_xticklabels([f"{x:.2f}" for x in xticks])

        # Save plot
        plt.tight_layout()
        out_path = os.path.join(CONFIG.OUT_DIR, f'{base_name}_analysis.png')
        self.file_manager.ensure_output_directory(os.path.dirname(out_path))
        plt.savefig(out_path)
        plt.close(fig)

        return {
            'filename': filename,
            'fwhm_gaussian': fwhm,
            'sigma_gaussian': sigma,
            'center_position': mean,
            'amplitude': amplitude,
            'intensity_derivative_stddev': intensity_derivative_stddev,
            'out_path': out_path,
            'positions_rad': positions_rad,
            'intensities': intensities,
            'intensities_stddev': intensities_stddev,
            'derivative': intensity_derivative,
            'derivative_stddev': intensity_derivative_stddev,
        }

    def create_combined_plot(self, results: List[Dict[str, Any]]) -> None:
        """
        Create a combined plot comparing multiple datasets, each in its own subplot.

        Args:
            results: List of analysis result dictionaries
        """
        # Calculate total number of datasets and required subplots
        n_datasets = len(results)

        # Create a figure with 2 rows and n_datasets columns
        fig, axes = plt.subplots(2, n_datasets, figsize=(6*n_datasets, 10), sharey='row')

        # If only one dataset, reshape axes for consistent indexing
        if n_datasets == 1:
            axes = axes.reshape(2, 1)

        # Plot each dataset in its own subplot
        for i, data in enumerate(results):
            # Top row: Intensity plot with error bars
            axes[0, i].errorbar(
                data['positions_rad'],
                data['intensities'],
                yerr=data['intensities_stddev'],
                fmt='o',
                ecolor='red',
                capsize=2,
                color='blue',
                alpha=0.7
            )

            # Set title with just the filename
            axes[0, i].set_title(f"{data['filename']}")
            axes[0, i].grid(True)

            # Bottom row: Derivative plot with error bars, Gaussian fit and beam width visualization
            axes[1, i].errorbar(
                data['positions_rad'],
                data['derivative'],
                yerr=data['derivative_stddev'],
                fmt='o',
                ecolor='red',
                capsize=2,
                color='blue',
                alpha=0.7,
                label='Derivative'
            )

            # Add Gaussian fit if we have the parameters
            if data['sigma_gaussian'] is not None and data['center_position'] is not None:
                # Generate x values for smooth curve
                x_fit = np.linspace(data['positions_rad'].min(), data['positions_rad'].max(), 1000)

                # We need to reconstruct the amplitude if it's not available
                amplitude = data['amplitude']
                if amplitude is None:
                    # Find the nearest point to the mean and use its value as reference
                    idx = np.abs(data['positions_rad'] - data['center_position']).argmin()
                    x_ref = data['positions_rad'][idx]
                    y_ref = data['derivative'][idx]
                    # Calculate what amplitude would give this value at this position
                    amplitude = y_ref / np.exp(-(x_ref - data['center_position'])**2 /
                                               (2 * data['sigma_gaussian']**2))

                y_fit = self.gaussian_fitter.gaussian(
                    x_fit,
                    amplitude,
                    data['center_position'],
                    data['sigma_gaussian']
                )

                axes[1, i].plot(
                    x_fit,
                    y_fit,
                    'r--',
                    label=f'Gaussian Fit\nFWHM={data["fwhm_gaussian"]:.3f} rad'
                )

                # Mark center of Gaussian
                axes[1, i].axvline(
                    x=data['center_position'],
                    color='g',
                    linestyle='--',
                    label=f'Center: {data["center_position"]:.3f} rad'
                )

            # Set common labels
            if i == 0:
                axes[1, i].set_ylabel('Derivative of Intensity')
            axes[1, i].set_xlabel('Position (radians)')
            axes[1, i].legend()
            axes[1, i].grid(True)

        plt.tight_layout()
        out_path = os.path.join(CONFIG.OUT_DIR, 'combined_analysis.png')
        self.file_manager.ensure_output_directory(os.path.dirname(out_path))
        plt.savefig(out_path)
        print(f"\n✓ Combined comparison plot saved to {out_path}")


def main() -> None:
    """Main entry point for the laser profile analysis program."""
    # Create file manager and ensure output directory exists
    file_manager = FileManager()
    out_dir_abs = os.path.abspath(os.path.join(os.path.dirname(__file__), CONFIG.OUT_DIR))
    file_manager.ensure_output_directory(out_dir_abs)

    # List all CSV files in DATA_DIR
    data_dir_abs = os.path.abspath(os.path.join(os.path.dirname(__file__), CONFIG.DATA_DIR))
    csv_files = [fname for fname in os.listdir(data_dir_abs) if fname.lower().endswith('.csv')]

    analyzer = LaserProfileAnalyzer()
    results = []

    for fname in csv_files:
        csv_path = os.path.join(data_dir_abs, fname)
        print(f"Processing {fname}...")
        result = analyzer.analyze_profile(csv_path)
        results.append(result)
        print(f"  ✓ Saved to {result['out_path']}")

        if result['fwhm_gaussian'] is not None:
            print(f"  ✓ Beam width (Gaussian FWHM): {result['fwhm_gaussian']:.3f} rad")
        else:
            print("  ✗ Could not determine beam width using Gaussian fit")

    # Compare results if we have two datasets
    if len(results) == 2:
        print("\nComparison of two datasets:")

        # Compare Gaussian measurements ensuring ratio is always less than 1
        if results[0]['fwhm_gaussian'] is not None and results[1]['fwhm_gaussian'] is not None:
            # Determine which value is larger to ensure ratio is < 1
            if results[0]['fwhm_gaussian'] > results[1]['fwhm_gaussian']:
                # First value is larger, so put it in denominator
                gaussian_ratio = results[1]['fwhm_gaussian'] / results[0]['fwhm_gaussian']
                ratio_description = f"{results[1]['filename']} / {results[0]['filename']}"
            else:
                # Second value is larger or equal, put it in denominator
                gaussian_ratio = results[0]['fwhm_gaussian'] / results[1]['fwhm_gaussian']
                ratio_description = f"{results[0]['filename']} / {results[1]['filename']}"

            print(f"Gaussian FWHM ratio ({ratio_description}): {gaussian_ratio:.3f}")
        else:
            print("Could not calculate Gaussian FWHM ratio: One or both datasets have invalid measurements")

        # Create combined plot
        analyzer.create_combined_plot(results)


if __name__ == "__main__":
    main()
