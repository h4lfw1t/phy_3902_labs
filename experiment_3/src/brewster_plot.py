#!/usr/bin/env python3
"""
Brewster Angle Analysis Module

This module provides functionality to analyze Brewster angle measurements using reflected
light intensity data. It identifies perpendicular incidence angles and Brewster angles,
where the reflection of p-polarized light is minimized.
"""

import os
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any, Union

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp

from utils import (
    BaseConstants, BaseConfig, FileManager,
    DataProcessor as BaseDataProcessor,
    PlotHelper as BasePlotHelper,
    ErrorPropagation
)


@dataclass
class BrewsterConstants(BaseConstants):
    """Constants specific to Brewster angle analysis."""
    # Inherits common constants from BaseConstants


@dataclass
class BrewsterConfig(BaseConfig):
    """Configuration parameters for Brewster angle analysis."""
    DATA_DIR: str = '../data/brewster/'  # Data directory specific to Brewster experiment


# Global instances
CONSTANTS = BrewsterConstants()
CONFIG = BrewsterConfig()


class DataProcessor(BaseDataProcessor):
    """Handles data loading and processing for Brewster angle analysis."""

    @staticmethod
    def process_angle_data(data_file: str) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series,
                                                    pd.Series, pd.Series, pd.Series]:
        """
        Process raw angle data from a CSV file into angles and intensities.

        Args:
            data_file: Path to the CSV data file

        Returns:
            Tuple of (angles, ldr_voltage_feedback, ldr_resistance, intensities,
                     adc_stddev, resistance_uncertainty, intensity_uncertainty)
        """
        # Load the data using FileManager
        file_manager = FileManager()
        data = file_manager.load_csv_data(data_file)

        # Convert steps to degrees using the base class method
        angles = BaseDataProcessor.steps_to_degrees(data['step'], CONSTANTS.STEPPER_STEPS_PER_REV)

        # Convert ADC values to voltage using the base class method
        ldr_voltage_feedback = BaseDataProcessor.adc_to_voltage(
            data['adc_mean'], CONSTANTS.V_SUPPLY, CONSTANTS.ANALOG_RESOLUTION)

        # Calculate LDR resistance from voltage divider
        ldr_resistance = CONSTANTS.R_FIXED * (CONSTANTS.V_SUPPLY - ldr_voltage_feedback) / ldr_voltage_feedback

        # Convert resistance to relative light intensity (I ∝ 1/R)
        intensities = 1.0 / ldr_resistance

        # Extract adc_stddev
        adc_stddev = data['adc_stddev']

        # Convert adc_stddev to voltage uncertainty using the base class method
        voltage_stddev = BaseDataProcessor.adc_to_voltage(
            adc_stddev, CONSTANTS.V_SUPPLY, CONSTANTS.ANALOG_RESOLUTION)

        # Error propagation for resistance
        V = sp.Symbol('V')
        Rf = CONSTANTS.R_FIXED
        Vs = CONSTANTS.V_SUPPLY
        R_expr = Rf * (Vs - V) / V
        resistance_uncertainty = []
        for v, dv in zip(ldr_voltage_feedback, voltage_stddev):
            resistance_uncertainty.append(ErrorPropagation.propagate_error(R_expr, [V], {V: v}, {V: dv}))
        resistance_uncertainty = pd.Series(resistance_uncertainty)

        # Error propagation for intensity
        intensity_expr = 1 / R_expr
        intensity_uncertainty = []
        for v, dv in zip(ldr_voltage_feedback, voltage_stddev):
            intensity_uncertainty.append(ErrorPropagation.propagate_error(intensity_expr, [V], {V: v}, {V: dv}))
        intensity_uncertainty = pd.Series(intensity_uncertainty)

        return (
            pd.Series(angles),
            pd.Series(ldr_voltage_feedback),
            pd.Series(ldr_resistance),
            pd.Series(intensities),
            adc_stddev,
            resistance_uncertainty,
            intensity_uncertainty
        )


class BrewsterAngleDetector:
    """Detects perpendicular regions and Brewster angles in reflection data."""

    @staticmethod
    def group_consecutive_indices(
        indices: np.ndarray,
        max_gap: int = 3
    ) -> List[List[int]]:
        """
        Group indices that are within max_gap of each other.

        Args:
            indices: Array of indices to group
            max_gap: Maximum allowed gap between consecutive indices

        Returns:
            List of grouped indices
        """
        if len(indices) == 0:
            return []

        groups = []
        current_group = [indices[0]]

        for i in range(1, len(indices)):
            if indices[i] - indices[i-1] <= max_gap:
                current_group.append(indices[i])
            else:
                groups.append(current_group)
                current_group = [indices[i]]

        groups.append(current_group)
        return groups

    def identify_perpendicular_angles(
        self,
        angles: pd.Series,
        intensities: pd.Series,
        window_size: int = 25
    ) -> List[Tuple[float, float, float, int, int]]:
        """
        Identify the flat regions between two steep slopes in the intensity data,
        which correspond to where the laser is perpendicular to the reflective surface.

        Args:
            angles: Series of angles in degrees (relative to arbitrary start)
            intensities: Series of corresponding intensities
            window_size: Size of the moving window for smoothing

        Returns:
            List of (start_angle, middle_angle, end_angle, start_idx, end_idx) tuples
            representing the regions where the laser is perpendicular to the surface
        """
        # Calculate and smooth the gradient
        gradient = np.gradient(intensities, angles)
        smoothed_gradient = np.convolve(gradient, np.ones(window_size)/window_size, mode='same')

        # Determine threshold for significant gradient changes (dynamic based on data)
        threshold = np.std(smoothed_gradient) * 1.5

        # Find indices where steep slopes (both positive and negative) occur
        pos_indices = np.where(smoothed_gradient > threshold)[0]
        neg_indices = np.where(smoothed_gradient < -threshold)[0]

        # Group consecutive indices and get the center of each group
        pos_groups = self.group_consecutive_indices(pos_indices)
        neg_groups = self.group_consecutive_indices(neg_indices)

        pos_centers = [int(np.mean(group)) for group in pos_groups if len(group) > 2]
        neg_centers = [int(np.mean(group)) for group in neg_groups if len(group) > 2]

        # Combine and sort all slope centers
        all_centers = sorted(pos_centers + neg_centers)

        # Find flat regions between consecutive steep slopes
        perpendicular_regions = []
        flat_region_threshold = threshold * 0.3  # Region is flat if average gradient < 30% of steep threshold
        min_region_width = 5  # Minimum width for a valid flat region

        for i in range(len(all_centers) - 1):
            start_idx = all_centers[i]
            end_idx = all_centers[i + 1]

            # Skip regions that are too narrow
            region_width = end_idx - start_idx
            if region_width < min_region_width:
                continue

            # Get angle values for this region
            middle_idx = (start_idx + end_idx) // 2
            start_angle = angles.iloc[start_idx]
            middle_angle = angles.iloc[middle_idx]
            end_angle = angles.iloc[end_idx]

            # Determine if region is flat by checking average gradient magnitude
            region_gradient_values = np.abs(smoothed_gradient[start_idx:end_idx])
            avg_gradient = np.mean(region_gradient_values)

            # Add region to results if it's flat enough
            if avg_gradient < flat_region_threshold:
                region_data = (
                    start_angle,    # Start angle
                    middle_angle,   # Middle angle
                    end_angle,      # End angle
                    start_idx,      # Start index
                    end_idx         # End index
                )
                perpendicular_regions.append(region_data)

        return perpendicular_regions

    @staticmethod
    def identify_brewster_angles(
        angles: pd.Series,
        intensities: pd.Series,
        perpendicular_regions: List[Tuple[float, float, float, int, int]],
        search_range_degrees: float = 60.0,
        smooth_window: int = 5
    ) -> List[Tuple[float, int, int]]:
        """
        Identify Brewster angles by finding the minima in reflection intensity
        on either side of the perpendicular incidence points.

        Args:
            angles: Series of angles in degrees
            intensities: Series of corresponding intensities
            perpendicular_regions: List of perpendicular region tuples
            search_range_degrees: Angular range to search around each perpendicular point
            smooth_window: Window size for smoothing the intensity data

        Returns:
            List of tuples (angle, index, region_id) representing identified Brewster angles
        """
        brewster_angles = []

        # Convert intensities to numpy array for processing
        intensities_array = intensities.to_numpy()

        # Apply light smoothing to reduce noise impact
        smoothed_intensities = np.convolve(intensities_array, np.ones(smooth_window)/smooth_window, mode='same')

        for region_id, (start_angle, middle_angle, end_angle, start_idx, end_idx) in enumerate(perpendicular_regions):
            # Define the search range around the perpendicular point
            lower_search_angle = middle_angle - search_range_degrees
            upper_search_angle = middle_angle + search_range_degrees

            # Find indices within the search range
            lower_indices = np.where((angles >= lower_search_angle) & (angles < middle_angle))[0]
            upper_indices = np.where((angles > middle_angle) & (angles <= upper_search_angle))[0]

            # Find minimum intensity in each range
            if len(lower_indices) > 0:
                # For the lower range (before perpendicular)
                lower_intensity_values = smoothed_intensities[lower_indices]
                min_idx_in_lower = np.argmin(lower_intensity_values)
                min_idx_lower = lower_indices[min_idx_in_lower]
                brewster_angle_lower = angles.iloc[min_idx_lower]
                brewster_angles.append((brewster_angle_lower, min_idx_lower, region_id))

            if len(upper_indices) > 0:
                # For the upper range (after perpendicular)
                upper_intensity_values = smoothed_intensities[upper_indices]
                min_idx_in_upper = np.argmin(upper_intensity_values)
                min_idx_upper = upper_indices[min_idx_in_upper]
                brewster_angle_upper = angles.iloc[min_idx_upper]
                brewster_angles.append((brewster_angle_upper, min_idx_upper, region_id))

        return brewster_angles


class PlotHelper(BasePlotHelper):
    """Helper methods for plotting and visualization of Brewster angle data."""

    @staticmethod
    def setup_subplot(
        pos: int,
        x_data: pd.Series,
        y_data: pd.Series,
        title: str,
        ylabel: str,
        color: str = 'blue',
        yerr: Optional[pd.Series] = None,
        label: Optional[str] = None
    ) -> plt.Axes:
        """
        Helper function to setup consistent subplot formatting.

        Args:
            pos: Position index for the subplot
            x_data: X-axis data
            y_data: Y-axis data
            title: Plot title
            ylabel: Y-axis label
            color: Color for the data points
            yerr: Error values for y-data
            label: Label for the data series

        Returns:
            The configured matplotlib Axes object
        """
        ax = plt.subplot(2, 2, pos)
        if yerr is not None:
            ax.errorbar(x_data, y_data, yerr=yerr, fmt='o', markersize=3, color=color,
                       ecolor='gray', alpha=0.7, capsize=2, label=label)
        else:
            ax.scatter(x_data, y_data, marker='o', s=3, color=color, label=label)
        if label:
            ax.legend()
        ax.set_title(title)
        ax.set_xlabel('Incident Angle (degrees)')
        ax.set_ylabel(ylabel)
        ax.set_xlim(0, 360)
        ax.set_xticks(np.arange(0, 361, 30))
        ax.grid(True)
        return ax

    @staticmethod
    def relabel_x_axis(ax: plt.Axes, offset: float) -> None:
        """
        Relabel the x-axis with incident angles while keeping data in place.

        Args:
            ax: Matplotlib axis to relabel
            offset: Angle offset for 0° reference point
        """
        # Current ticks (evenly spaced from 0 to 360)
        original_ticks = np.arange(0, 361, 30)

        # Create new tick labels that are shifted by the offset
        # First, convert to the range -180 to 180
        new_labels = [(tick - offset) % 360 for tick in original_ticks]
        new_labels = [label - 360 if label > 180 else label for label in new_labels]

        # Find the minimum value
        min_label = min(new_labels)

        # Adjust labels to start from min_label and be strictly increasing
        adjusted_labels = []
        prev_label = min_label - 1  # Start below the minimum

        for label in new_labels:
            # If this label would decrease, add 360 to it
            while label <= prev_label:
                label += 360
            adjusted_labels.append(label)
            prev_label = label

        # Set the new tick labels without moving data points
        ax.set_xticks(original_ticks)
        ax.set_xticklabels([f"{int(label)}" for label in adjusted_labels])

        # Update xlabel to indicate the reference
        ax.set_xlabel('Incident Angle (degrees)')

    @staticmethod
    def get_incident_angle_label(region_index: int) -> str:
        """
        Get a label for a perpendicular region.

        Args:
            region_index: The index of the region

        Returns:
            A string label (0° for first, 180° for second, etc.)
        """
        return f"{region_index * 180}°"

    @classmethod
    def highlight_regions(
        cls,
        ax: plt.Axes,
        regions: List[Tuple],
        offset: float = 0.0,
        alpha: float = 0.3,
        show_region: bool = False
    ) -> None:
        """
        Highlight perpendicular regions on a plot.

        Args:
            ax: Matplotlib axis to draw on
            regions: List of perpendicular region tuples
            offset: Angle offset for 0° reference point
            alpha: Transparency for region highlighting
            show_region: Whether to show the span of the region
        """
        # Define distinct colors for each perpendicular angle line
        colors = ['green', 'blue', 'purple', 'orange', 'cyan', 'magenta']

        # For each region, highlight and label with the appropriate angle
        for i, (start_angle, middle_angle, end_angle, _, _) in enumerate(regions):
            # Calculate the label text (0° for first, 180° for second, etc.)
            label_text = cls.get_incident_angle_label(i)

            # Get color for this line (cycle through colors if more regions than colors)
            color = colors[i % len(colors)]

            # Highlight the middle angle - this is our best guess for the perpendicular angle
            line = ax.axvline(x=middle_angle, color=color, linestyle='--', label=label_text)

            # Add text label near the line at the top of the plot
            y_pos = ax.get_ylim()[1] * 0.95  # Position at 95% of the y-axis height
            ax.text(middle_angle, y_pos, label_text,
                    color=color, fontweight='bold', ha='center', va='top',
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=2))

            # Show the region bounds if requested
            if show_region:
                # Use a lighter version of the same color for the region
                region_color = color
                ax.axvspan(start_angle, end_angle, color=region_color, alpha=alpha)

        # Add a legend only if regions were found
        if regions:
            handles, labels = ax.get_legend_handles_labels()
            # Filter to only include the perpendicular angle lines we just added
            perpendicular_handles = [h for h, l in zip(handles, labels) if '°' in l]
            perpendicular_labels = [l for l in labels if '°' in l]
            if perpendicular_handles:
                ax.legend(perpendicular_handles, perpendicular_labels, loc='best')

    @staticmethod
    def highlight_brewster_angles(
        ax: plt.Axes,
        brewster_angles: List[Tuple],
        angle_offset: float = 0.0
    ) -> None:
        """
        Highlights Brewster angles on the plot with vertical lines.

        Args:
            ax: Matplotlib axis to draw on
            brewster_angles: List of tuples (angle, index, region_id)
            angle_offset: Angle offset for 0° reference point
        """
        if not brewster_angles:
            return

        # Colors for Brewster angle lines - use a different color scheme than perpendicular lines
        brewster_colors = ['darkred', 'darkgreen', 'darkblue', 'darkorange', 'darkmagenta', 'darkcyan']

        # Group brewster angles by their associated perpendicular region
        brewster_by_region = {}
        for ba_angle, _, region_id in brewster_angles:
            if region_id not in brewster_by_region:
                brewster_by_region[region_id] = []
            brewster_by_region[region_id].append(ba_angle)

        # Draw each Brewster angle with its label
        for region_id, angles_list in brewster_by_region.items():
            # Use a color based on the region ID
            color = brewster_colors[region_id % len(brewster_colors)]

            # For each angle in this region group
            for i, angle in enumerate(angles_list):
                # Get the incident angle for labeling
                incident_angle = angle - angle_offset

                # Create a label that shows the incident angle
                label = f"θB = {incident_angle:.1f}°"

                # Add a vertical line for this Brewster angle
                line = ax.axvline(x=angle, color=color, linestyle=':', linewidth=1.5,
                                 label=f"θB ({region_id})" if i==0 else "")

                # Calculate text position - alternate between top and bottom for visibility
                if i % 2 == 0:
                    y_frac = 0.65  # 65% up the axis
                    va = 'top'
                else:
                    y_frac = 0.50  # 50% up the axis
                    va = 'bottom'

                # Add text label at the appropriate position using axis transform
                ax.text(angle, y_frac, label,
                        color=color, fontweight='bold', ha='center', va=va,
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=2),
                        transform=ax.get_xaxis_transform(),
                        )

        # Update legend with Brewster angle entries
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels, loc='best')


class BrewsterAnalyzer:
    """Main class for analyzing and reporting Brewster angle experiments."""

    def __init__(self):
        """Initialize the Brewster angle analyzer with required components."""
        self.detector = BrewsterAngleDetector()
        self.data_processor = DataProcessor()
        self.plot_helper = PlotHelper()

    def create_brewster_plots(
        self,
        angles: pd.Series,
        ldr_voltage_feedback: pd.Series,
        ldr_resistance: pd.Series,
        intensities: pd.Series,
        perpendicular_regions: List[Tuple],
        brewster_angles: List[Tuple],
        adc_stddev: pd.Series,
        resistance_uncertainty: pd.Series,
        intensity_uncertainty: pd.Series,
    ) -> str:
        """
        Create visualization plots for Brewster angle analysis, with error bars.

        Args:
            angles: Series of angle measurements
            ldr_voltage_feedback: Series of voltage measurements
            ldr_resistance: Series of calculated resistance values
            intensities: Series of calculated intensity values
            perpendicular_regions: List of perpendicular region tuples
            brewster_angles: List of Brewster angle tuples
            adc_stddev: Series of ADC standard deviations
            resistance_uncertainty: Series of resistance uncertainties
            intensity_uncertainty: Series of intensity uncertainties

        Returns:
            Path to the saved plot file
        """
        # Create a figure using the base PlotHelper's method
        fig, _ = BasePlotHelper.setup_basic_figure(figsize=(12, 8))

        # Determine the angle offset based on perpendicular regions
        angle_offset = 0
        if perpendicular_regions:
            angle_offset = perpendicular_regions[0][1]  # Middle angle of first region

        # Convert ADC stddev to voltage uncertainty using DataProcessor utility
        voltage_uncertainty = BaseDataProcessor.adc_to_voltage(
            adc_stddev, CONSTANTS.V_SUPPLY, CONSTANTS.ANALOG_RESOLUTION)

        # Plot 1: Raw voltage (with error bars)
        voltage_ax = self.plot_helper.setup_subplot(
            1, angles,
            ldr_voltage_feedback,
            'LDR Voltage vs Angle',
            'Voltage (V)',
            'blue', yerr=voltage_uncertainty,
            label='LDR Voltage'
        )
        self.plot_helper.relabel_x_axis(voltage_ax, angle_offset)

        # Plot 2: Calculated resistance (with error bars)
        resistance_ax = self.plot_helper.setup_subplot(
            2,
            angles, ldr_resistance,
            'LDR Resistance vs Angle',
            'Resistance (Ω)',
            'green', yerr=resistance_uncertainty,
            label='LDR Resistance'
        )
        self.plot_helper.relabel_x_axis(resistance_ax, angle_offset)

        # Plot 3: Light intensity with perpendicular regions (with error bars)
        intensity_ax = self.plot_helper.setup_subplot(
            3,
            angles,
            intensities,
            'Light Intensity vs Angle (Brewster Angle Measurement)',
            'Relative Light Intensity',
            'red',
            yerr=intensity_uncertainty,
            label='Intensity'
        )
        self.plot_helper.relabel_x_axis(intensity_ax, angle_offset)

        # Calculate gradient for visualization
        gradient = np.gradient(intensities, angles)
        smoothed_gradient = np.convolve(gradient, np.ones(25)/25, mode='same')

        # Plot 4: Gradient visualization
        gradient_ax = plt.subplot(2, 2, 4)
        gradient_ax.plot(angles, smoothed_gradient, color='blue', linewidth=1)
        gradient_ax.set_title('Gradient of Intensity vs Angle')
        gradient_ax.set_ylabel('Intensity Gradient')
        gradient_ax.set_xlim(0, 360)
        gradient_ax.set_xticks(np.arange(0, 361, 30))
        gradient_ax.grid(True)
        gradient_ax.axhline(y=0, color='gray', linestyle='--')
        self.plot_helper.relabel_x_axis(gradient_ax, angle_offset)

        # Highlight regions and Brewster angles on intensity and gradient plots
        self.plot_helper.highlight_regions(intensity_ax, perpendicular_regions, offset=angle_offset)
        self.plot_helper.highlight_brewster_angles(intensity_ax, brewster_angles, angle_offset)
        self.plot_helper.highlight_regions(gradient_ax, perpendicular_regions, offset=angle_offset)
        self.plot_helper.highlight_brewster_angles(gradient_ax, brewster_angles, angle_offset)

        plt.tight_layout()

        # Use FileManager to ensure output directory exists
        file_manager = FileManager()
        out_dir = file_manager.ensure_output_directory(CONFIG.OUT_DIR)

        # Save figure using the base PlotHelper method
        out_filename = 'brewster_plot.png'
        out_path = BasePlotHelper.save_figure(fig, out_filename, out_dir)

        plt.show()
        plt.close(fig)

        return out_path

    def analyze_brewster_data(self, data_file: str) -> Tuple[pd.Series, pd.Series, List[Tuple], List[Tuple]]:
        """
        Process and analyze Brewster angle data from a CSV file.

        Args:
            data_file: Path to the CSV data file

        Returns:
            Tuple of (angles, intensities, perpendicular_regions, brewster_angles)
        """
        # Load and process the data - using the full path provided from main()
        (angles, ldr_voltage_feedback, ldr_resistance, intensities, adc_stddev,
         resistance_uncertainty, intensity_uncertainty) = self.data_processor.process_angle_data(data_file)

        # Identify perpendicular angles (where laser is perpendicular to surface)
        perpendicular_regions = self.detector.identify_perpendicular_angles(angles, intensities)

        # Identify Brewster angles based on intensity minima around perpendicular points
        brewster_angles = self.detector.identify_brewster_angles(angles, intensities, perpendicular_regions)

        # Create the plots
        self.create_brewster_plots(
            angles, ldr_voltage_feedback, ldr_resistance, intensities,
            perpendicular_regions, brewster_angles, adc_stddev,
            resistance_uncertainty, intensity_uncertainty
        )

        return angles, intensities, perpendicular_regions, brewster_angles

    @staticmethod
    def report_perpendicular_regions(
        perpendicular_regions: List[Tuple],
        angles: pd.Series,
        intensities: pd.Series
    ) -> None:
        """
        Print detailed analysis of the identified perpendicular regions.

        Args:
            perpendicular_regions: List of identified perpendicular regions
            angles: Series of angle measurements
            intensities: Series of intensity measurements
        """
        # Calculate the angle offset based on the first perpendicular region
        angle_offset = perpendicular_regions[0][1] if perpendicular_regions else 0

        for i, (start_angle, middle_angle, end_angle, start_idx, end_idx) in enumerate(perpendicular_regions):
            # Calculate the width of the region in degrees
            region_width = end_angle - start_angle

            # Calculate the flatness metric (lower is flatter)
            region_gradient = np.gradient(intensities.iloc[start_idx:end_idx], angles.iloc[start_idx:end_idx])
            flatness = np.mean(np.abs(region_gradient))

            # Calculate incident angles
            middle_incident = middle_angle - angle_offset
            start_incident = start_angle - angle_offset
            end_incident = end_angle - angle_offset

            print(f"  Region {i+1}:")
            print(f"    Raw angle center: {middle_angle:.1f}°")
            print(f"    Incident angle center: {middle_incident:.1f}°")
            print(f"    Raw spans: {start_angle:.1f}° to {end_angle:.1f}° (width: {region_width:.1f}°)")
            print(f"    Incident spans: {start_incident:.1f}° to {end_incident:.1f}°")
            print(f"    Flatness metric: {flatness:.5f}")

            # Map to theoretical angles - assumes the first region is 0° and second is 180°
            if len(perpendicular_regions) >= 2:
                if i == 0:
                    print("    Maps to theoretical incident angle: 0° (laser perpendicular to surface)")
                elif i == 1:
                    print("    Maps to theoretical incident angle: 180° (laser perpendicular to surface)")

        # Calculate the relative angle between regions if we found both
        if len(perpendicular_regions) >= 2:
            angle_diff = perpendicular_regions[1][1] - perpendicular_regions[0][1]
            print(f"\n  Angle difference between perpendicular regions (raw): {angle_diff:.1f}°")
            print("  Expected difference: 180° (theoretical)")

            # Check if our angle difference is close to expected
            if abs(angle_diff - 180) < 30:
                print("  ✓ Angle difference is close to expected value (180°)")
            else:
                print("  ⚠ Angle difference deviates significantly from expected value (180°)")
                print("    This may indicate issues with the measurement or detection algorithm.")

    @staticmethod
    def report_brewster_angles(
        brewster_angles: List[Tuple],
        perpendicular_regions: List[Tuple],
        intensities: pd.Series,
        angle_offset: float
    ) -> None:
        """
        Print detailed analysis of the identified Brewster angles.

        Args:
            brewster_angles: List of brewster angle tuples (angle, index, region_id)
            perpendicular_regions: List of perpendicular region tuples
            intensities: Series of intensity measurements
            angle_offset: Angle offset for 0° reference
        """
        print("\nIdentified Brewster angles (reflection minima):")

        # Group the Brewster angles by their associated perpendicular region
        brewster_by_region = {}
        for angle, idx, region_id in brewster_angles:
            region_id = int(region_id)  # Ensure region_id is an integer
            if region_id not in brewster_by_region:
                brewster_by_region[region_id] = []
            brewster_by_region[region_id].append((angle, idx))

        for region_id, angles_list in brewster_by_region.items():
            perp_angle = perpendicular_regions[region_id][1]  # Middle angle of this region
            print(f"  Region {region_id} (centered at {perp_angle:.1f}°):")

            for i, (angle, idx) in enumerate(angles_list):
                incident_angle = angle - angle_offset
                intensity_value = intensities.iloc[idx]
                angle_diff = angle - perp_angle
                position = "before" if angle_diff < 0 else "after"

                print(f"    Brewster angle {i+1}: {angle:.1f}° raw, {incident_angle:.1f}° incident")
                print(f"    Position: {position} perpendicular point (offset {abs(angle_diff):.1f}°)")
                print(f"    Intensity value: {intensity_value:.8f}")

                # Theoretical Brewster angle is ~56° for glass with n=1.5
                if incident_angle > 90:
                    incident_angle -= 180  # Normalize to -90° to +90°
                print(f"    Experimental Brewster angle (incident): {incident_angle:.1f}°")
                if 50 <= abs(incident_angle) <= 60:
                    print(f"    ✓ Close to theoretical Brewster angle (~56.3° for glass with n=1.5)")
                else:
                    print(f"    ⚠ Deviates from expected Brewster angle range (45°-65°)")
                print("")


def main() -> None:
    """
    Main function to process and analyze all Brewster angle data files.
    """
    # Initialize the analyzer and file manager
    analyzer = BrewsterAnalyzer()
    file_manager = FileManager()

    # Get the absolute data directory path using FileManager
    data_dir = file_manager.get_data_directory(__file__, CONFIG.DATA_DIR)

    # Process each CSV file in the data directory
    for file in os.listdir(data_dir):
        if not file.endswith('.csv'):  # Only process CSV files
            continue

        print(f"\nAnalyzing data from {file}")

        # Create full file path
        file_path = os.path.join(data_dir, file)

        # Check if this is p-polarized data (only these can show Brewster angle)
        is_p_polarized = "p_polarized" in file

        # Process data and generate plots
        if is_p_polarized:
            # For p-polarized data, identify both perpendicular regions and Brewster angles
            angles, intensities, perpendicular_regions, brewster_angles = analyzer.analyze_brewster_data(file_path)
        else:
            # For other data (like s-polarized), don't look for Brewster angles
            # To maintain compatibility, we'll still use the same function but ignore the Brewster angles
            angles, intensities, perpendicular_regions, brewster_angles = analyzer.analyze_brewster_data(file_path)
            # Clear any accidentally identified Brewster angles for non-p-polarized data
            brewster_angles = []

        # Find minimum intensity point
        min_idx = np.argmin(intensities)
        brewster_angle_raw = angles.iloc[min_idx]

        # Calculate the angle offset to get the incident angle
        angle_offset = 0
        if perpendicular_regions:
            angle_offset = perpendicular_regions[0][1]  # Middle angle of first perpendicular region

        # Calculate the minimum intensity angle in the incident angle reference frame
        brewster_incident_angle = brewster_angle_raw - angle_offset

        # For any data file, report the global minimum intensity
        print(f"Global minimum intensity (raw angle): {brewster_angle_raw:.1f}°")
        print(f"Global minimum intensity (incident angle): {brewster_incident_angle:.1f}°")

        # Report regions where the laser is likely perpendicular to the reflective surface
        print("Identified flat regions (where laser is perpendicular to surface):")

        if not perpendicular_regions:
            print("  No suitable perpendicular regions found. Try adjusting the detection parameters.")
        else:
            analyzer.report_perpendicular_regions(perpendicular_regions, angles, intensities)

        # Only report on Brewster angles for p-polarized data
        if is_p_polarized and brewster_angles:
            analyzer.report_brewster_angles(brewster_angles, perpendicular_regions, intensities, angle_offset)
        elif is_p_polarized and not brewster_angles:
            print("\nNo Brewster angles identified in this p-polarized data.")
            print("Try adjusting the search parameters or check data quality.")


if __name__ == "__main__":
    main()
