#!/usr/bin/env python3
"""
Plot Helper Module

This module provides common plotting functionality for physics experiments.
"""

import os
from typing import Tuple

import matplotlib.pyplot as plt


class PlotHelper:
    """Base class with common plotting functionality."""

    @staticmethod
    def setup_basic_figure(figsize: Tuple[float, float] = (10, 6)) -> Tuple[plt.Figure, plt.Axes]:
        """
        Create a basic figure with a single subplot.

        Args:
            figsize: Figure size (width, height) in inches

        Returns:
            Tuple of (figure, axes)
        """
        fig, ax = plt.subplots(figsize=figsize)
        return fig, ax

    @staticmethod
    def save_figure(fig: plt.Figure, filename: str, directory: str = '../out/') -> str:
        """
        Save figure to file and ensure directory exists.

        Args:
            fig: Figure to save
            filename: Filename for the figure
            directory: Directory to save in

        Returns:
            Path to saved file
        """
        # Ensure directory exists
        os.makedirs(os.path.abspath(directory), exist_ok=True)

        # Create full path
        file_path = os.path.join(directory, filename)

        # Save figure
        fig.savefig(file_path)

        return file_path
