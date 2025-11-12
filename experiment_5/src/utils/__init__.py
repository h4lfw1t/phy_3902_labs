#!/usr/bin/env python3
"""
Physics Experiment Utilities Package

This package provides shared utilities and base classes for physics experiment analysis,
including data processing, plotting, and analysis functions.
"""

from .data_processing import DataProcessing
from .error_propagation import ErrorPropagation
from .fringe_analysis import FringeAnalysis

__all__ = [
    'DataProcessing',
    'ErrorPropagation',
    'FringeAnalysis',
]
