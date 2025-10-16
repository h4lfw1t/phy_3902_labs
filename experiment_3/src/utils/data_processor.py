#!/usr/bin/env python3
"""
Data Processor Module

This module provides data processing operations for physics experiments.
"""

from typing import Union

import numpy as np
import pandas as pd


class DataProcessor:
    """Base class for data processing operations."""

    @staticmethod
    def degrees_to_radians(degrees: Union[np.ndarray, pd.Series]) -> np.ndarray:
        """
        Convert degrees to radians.

        Args:
            degrees: Array of values in degrees

        Returns:
            Array of values in radians
        """
        return np.deg2rad(degrees)

    @staticmethod
    def steps_to_degrees(steps: Union[np.ndarray, pd.Series], steps_per_rev: int) -> np.ndarray:
        """
        Convert stepper motor steps to degrees.

        Args:
            steps: Array of step values
            steps_per_rev: Steps per full revolution

        Returns:
            Array of angle values in degrees
        """
        return 360 * np.array(steps) / steps_per_rev

    @staticmethod
    def adc_to_voltage(adc_values: Union[np.ndarray, pd.Series], v_supply: float, resolution: int) -> np.ndarray:
        """
        Convert ADC values to voltage.

        Args:
            adc_values: Array of ADC readings
            v_supply: Supply voltage
            resolution: ADC resolution (e.g., 1023 for 10-bit)

        Returns:
            Array of voltage values
        """
        return np.array(adc_values) * v_supply / resolution
