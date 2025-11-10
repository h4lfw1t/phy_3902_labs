#!/usr/bin/env python3

import numpy as np
import sympy as sp
from error_propagation import ErrorPropagation

class DataProcessing:
    def __init__(self, r_series=9970, v_in=5.0, resolution=1023):
        self.r_series = r_series
        self.v_in = v_in
        self.resolution = resolution

    def adc_to_voltage(self, adc_values):
        """Convert ADC values to voltages."""
        return adc_values * self.v_in / self.resolution

    def voltage_to_intensity(self, voltages):
        """Convert voltages to intensity using LDR circuit."""
        r_ldr = (self.r_series * voltages) / (self.v_in - voltages)
        intensity = 1.0 / r_ldr
        return intensity

    def intensity_with_error(self, adc_values, adc_stddev):
        """Return intensity and propagated error from ADC values and stddev."""
        adc = sp.Symbol('adc')
        v_ldr = adc * self.v_in / self.resolution
        r_ldr = (self.r_series * v_ldr) / (self.v_in - v_ldr)
        intensity_expr = 1 / r_ldr

        voltages = self.adc_to_voltage(adc_values)
        r_ldr_vals = (self.r_series * voltages) / (self.v_in - voltages)
        intensities = 1.0 / r_ldr_vals

        intensity_errors = []
        for val, std in zip(adc_values, adc_stddev):
            values = {adc: val}
            uncertainties = {adc: std}
            err = ErrorPropagation.propagate_error(intensity_expr, [adc], values, uncertainties)
            intensity_errors.append(err)
        return intensities, intensity_errors

    def steps_to_linear_position(self, step_counts, max_steps, linear_scale):
        """Convert step counts to linear position using a scale factor."""
        return (step_counts / max_steps) * linear_scale

    def align_center_fringe(self, position, center_fringe_region):
        """Shift position data so center fringe is at position 0."""
        center_idx = (center_fringe_region[0] + center_fringe_region[1]) // 2
        center_pos = position[center_idx]
        return position - center_pos

    def get_fringe_distance(self, position, center_fringe_region, outer_fringe_regions):
        """Calculate distance between center and outer fringes."""
        center_idx = (center_fringe_region[0] + center_fringe_region[1]) // 2
        center_pos = position[center_idx]
        distances = []
        for start, end in outer_fringe_regions:
            outer_idx = (start + end) // 2
            outer_pos = position[outer_idx]
            distances.append(abs(outer_pos - center_pos))
        return distances

    def calculate_angle(self, fringe_distance, wavelength, setup_length):
        """Calculate angle based on fringe distance and experimental setup."""
        # Example: theta = arctan(fringe_distance / setup_length)
        return np.arctan(fringe_distance / setup_length)
