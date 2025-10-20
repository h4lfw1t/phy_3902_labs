#!/usr/bin/env python3
"""
Physics Experiment Utilities Package

This package provides shared utilities and base classes for physics experiment analysis,
including data processing, plotting, and analysis functions.
"""

from .constants import BaseConstants, BaseConfig
from .data_processor import DataProcessor
from .error_propagation import ErrorPropagation
from .file_manager import FileManager
from .plot_helper import PlotHelper

__all__ = [
    'BaseConstants',
    'BaseConfig',
    'DataProcessor',
    'ErrorPropagation',
    'FileManager',
    'PlotHelper'
]
