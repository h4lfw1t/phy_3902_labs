#!/usr/bin/env python3
"""
Data Processing Module

This module provides utilities for processing experimental data from the
interferometry experiment, including ADC conversion, error propagation,
and refractive index calculations.
"""
from typing import Tuple

import numpy as np
import uncertainties.unumpy as unp


class DataProcessing:
    """Process experimental data from ADC readings to physical measurements.

    This class handles the conversion of ADC values to intensity measurements
    with automatic error propagation, as well as geometric calculations for
    fringe analysis.

    Parameters
    ----------
    r_series : float, optional
        Series resistance in the voltage divider circuit (ohms), by default 9970
    v_in : float, optional
        Input voltage to the ADC (volts), by default 5.0
    resolution : int, optional
        ADC resolution (maximum count value), by default 1023

    Attributes
    ----------
    r_series : float
        Series resistance value
    v_in : float
        Input voltage value
    resolution : int
        ADC resolution value
    """

    def __init__(
        self, r_series: float = 9970, v_in: float = 5.0, resolution: int = 1023
    ):
        self.r_series = r_series
        self.v_in = v_in
        self.resolution = resolution

    def intensity_with_error(
        self, adc_values, adc_stddev
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Convert ADC values to intensity with automatic error propagation.

        Uses the uncertainties package to automatically propagate errors through
        the complete transformation chain: ADC → Voltage → Resistance → Intensity.
        The transformation follows the voltage divider formula for an LDR circuit:

        V_LDR = ADC * V_in / resolution
        R_LDR = (R_series * V_LDR) / (V_in - V_LDR)
        Intensity = 1 / R_LDR

        Parameters
        ----------
        adc_values : array_like
            Array of ADC readings (counts)
        adc_stddev : array_like
            Standard deviation of ADC readings (uncertainty in counts)

        Returns
        -------
        intensities : ndarray
            Calculated intensity values (1/ohms)
        intensity_errors : ndarray
            Propagated uncertainties in intensity values
        """
        # Clip ADC values to prevent division by zero at saturation
        # Maximum safe ADC value leaves a small margin below v_in
        max_safe_adc = (
            self.resolution * 0.999
        )  # 99.9% of max to avoid v_ldr ≈ v_in
        adc_values_clipped = np.clip(adc_values, 0, max_safe_adc)

        # Create uncertainty-aware array from ADC values and their uncertainties
        adc_with_err = unp.uarray(adc_values_clipped, adc_stddev)

        # Convert to voltage (error automatically propagated)
        voltages = adc_with_err * self.v_in / self.resolution

        # Calculate LDR resistance (error automatically propagated)
        # R_LDR = (R_series * V_LDR) / (V_in - V_LDR)
        r_ldr = (self.r_series * voltages) / (self.v_in - voltages)

        # Calculate intensity as 1/R_LDR (error automatically propagated)
        intensity_with_err = 1.0 / r_ldr

        # Extract nominal values and standard deviations
        intensities = unp.nominal_values(intensity_with_err)
        intensity_errors = unp.std_devs(intensity_with_err)

        return intensities, intensity_errors

    @staticmethod
    def steps_to_linear_position(
        step_counts, max_steps: int, linear_scale: float
    ) -> np.ndarray:
        """Convert stepper motor steps to linear position.

        Parameters
        ----------
        step_counts : array_like
            Array of step counts from the stepper motor
        max_steps : int
            Maximum number of steps for full range
        linear_scale : float
            Linear distance corresponding to max_steps (meters)

        Returns
        -------
        positions : ndarray
            Linear positions in meters

        Examples
        --------
        >>> steps = np.array([0, 900, 1800])
        >>> positions = DataProcessing.steps_to_linear_position(steps, 1800, 0.05)
        >>> positions
        array([0.   , 0.025, 0.05 ])
        """
        return (step_counts / max_steps) * linear_scale

    @staticmethod
    def get_region_center_idx(region: Tuple[int, int]) -> int:
        """Get the center index of a fringe region.

        Helper method to calculate the midpoint index of a region tuple,
        ensuring the result is a Python integer for array indexing.

        Parameters
        ----------
        region : tuple of (int, int)
            Region boundaries as (start_index, end_index)

        Returns
        -------
        center_idx : int
            Index at the center of the region
        """
        return int((int(region[0]) + int(region[1])) // 2)

    def align_center_fringe(
        self, position: np.ndarray, center_fringe_region: Tuple[int, int]
    ) -> np.ndarray:
        """Shift position array so the center fringe is at position zero.

        Parameters
        ----------
        position : ndarray
            Array of position values (meters)
        center_fringe_region : tuple of (int, int)
            Indices defining the center fringe region (start, end)

        Returns
        -------
        aligned_position : ndarray
            Position array shifted so center fringe center is at 0
        """
        center_idx = self.get_region_center_idx(center_fringe_region)
        center_pos = position[center_idx]
        return position - center_pos

    def get_fringe_distance(
        self,
        position: np.ndarray,
        center_fringe_region: Tuple[int, int],
        outer_fringe_regions: list[Tuple[int, int]],
    ) -> list[float]:
        """Calculate distances between center fringe and outer fringes.

        Parameters
        ----------
        position : ndarray
            Array of position values (meters)
        center_fringe_region : tuple of (int, int)
            Indices defining the center fringe region (start, end)
        outer_fringe_regions : list of tuple
            List of (start, end) index tuples for outer fringes

        Returns
        -------
        distances : list of float
            Distances from center fringe to each outer fringe (meters)
        """
        center_idx = self.get_region_center_idx(center_fringe_region)
        center_pos = position[center_idx]
        distances = []
        for region in outer_fringe_regions:
            outer_idx = self.get_region_center_idx(region)
            outer_pos = position[outer_idx]
            distances.append(abs(outer_pos - center_pos))
        return distances

    @staticmethod
    def calculate_refractive_index_from_baseline(
        fringe_order: int,
        fringe_diff: float,
        grating_period: float,
        cell_width: float,
        vacuum_wavelength: float,
    ) -> float:
        """Calculate refractive index from baseline fringe shift measurements.

        Uses the theoretical relationship between fringe shift and refractive
        index in a diffraction grating interferometer with a sample cell.

        Parameters
        ----------
        fringe_order : int
            Order number of the fringe (m)
        fringe_diff : float
            Difference in fringe position between baseline and sample (meters)
        grating_period : float
            Period of the diffraction grating (meters, = 1/lines_per_meter)
        cell_width : float
            Width of the sample cell (meters)
        vacuum_wavelength : float
            Wavelength of the laser in vacuum (meters)

        Returns
        -------
        n : float
            Calculated refractive index of the sample
        """
        m = fringe_order
        delta_d_x = fringe_diff
        T = grating_period
        w = cell_width
        lambda_0 = vacuum_wavelength

        term = 1 - (m**2 * lambda_0**2) / T**2
        numerator = w**2 * term
        denominator = (w * m * lambda_0 / T - delta_d_x * np.sqrt(term)) ** 2

        n = (m * lambda_0 / T) * np.sqrt(1 + numerator / denominator)
        return n
