#!/usr/bin/env python3
"""
Configuration settings for intensity data processing and plotting.
"""

import os
from dataclasses import dataclass


@dataclass
class IntensityConfig:
    DATA_DIR: str = os.path.abspath(
        os.path.join("..", "data", "intensity_data")
    )
    OUT_DIR = os.path.abspath(os.path.join("..", "out", "intensity_plots"))
    MANIFEST_PATH = os.path.join(DATA_DIR, "manifest.json")
    R_SERIES: float = 9970  # Resistance in ohms
    V_IN: float = 5.0  # Input voltage
    RESOLUTION: int = 1023  # ADC resolution
    DIFFRACTION_GRATING: float = 527559  # lines per meter
    # Minimum width of fringe region in data points
    FRINGE_MIN_WIDTH: int = 10
    CENTER_FRINGE_THRESHOLD: float = (
        0.1  # Threshold for center fringe detection
    )
    OUTER_FRINGE_THRESHOLD: float = (
        0.0025  # Threshold for outer fringe detection
    )
    CUVETTE_WIDTH: float = 0.01  # Cuvette width in meters
