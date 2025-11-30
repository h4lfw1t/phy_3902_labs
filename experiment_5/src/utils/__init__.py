#!/usr/bin/env python3
"""
Physics Experiment Utilities Package

This package provides shared utilities and base classes for physics experiment
analysis, specifically designed for interferometry experiments using
diffraction gratings.

Modules
-------
data_processing
    Data conversion and processing utilities including ADC to intensity
    conversion with automatic error propagation, position calculations,
    and refractive index calculations from baseline measurements.

fringe_analysis
    Fringe detection, numbering, and analysis utilities for interference
    patterns. Includes methods for baseline comparison and refractive
    index determination.

Classes
-------
DataProcessing
    Main class for processing experimental data from ADC readings to
    physical measurements with automatic error propagation.

FringeAnalysis
    Main class for analyzing interference fringe patterns, detecting
    fringes, assigning order numbers, and calculating refractive indices.

IntensityConfig
    Configuration settings for intensity data processing and plotting,
    including data directories, experimental constants, and thresholds.

Examples
--------
Basic usage for processing intensity data:

>>> from utils import DataProcessing, FringeAnalysis, IntensityConfig
>>> constants = IntensityConfig()
>>> data_proc = DataProcessing(r_series=9970, v_in=5.0, resolution=1023)
>>> analyzer = FringeAnalysis(fringe_min_width=10)
>>> # Load your data and analyze
>>> analyzer.analyze(data, manifest_entry, data_proc, constants)

Notes
-----
This package requires the following dependencies:
- numpy: numerical computations
- scipy: signal processing (connected component labeling)
- uncertainties: automatic error propagation
- pandas: data loading and manipulation
"""

from .data_processing import DataProcessing
from .fringe_analysis import FringeAnalysis
from .intensity_config import IntensityConfig

__all__ = [
    "DataProcessing",
    "FringeAnalysis",
    "IntensityConfig",
]
