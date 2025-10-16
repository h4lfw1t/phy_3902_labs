#!/usr/bin/env python3
"""
File Manager Module

This module provides utilities for file operations across experiments.
"""

import os
import pandas as pd


class FileManager:
    """Handles file operations across experiments."""

    @staticmethod
    def ensure_output_directory(directory_path: str) -> str:
        """
        Ensure the output directory exists.

        Args:
            directory_path: Relative or absolute path to directory

        Returns:
            Absolute path to the created directory
        """
        dir_path = os.path.abspath(directory_path)
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    @staticmethod
    def get_data_directory(base_dir: str, experiment_subdir: str) -> str:
        """
        Construct absolute path to data directory.

        Args:
            base_dir: Base directory (usually __file__)
            experiment_subdir: Experiment subdirectory

        Returns:
            Absolute path to data directory
        """
        return os.path.abspath(os.path.join(os.path.dirname(base_dir), experiment_subdir))

    @staticmethod
    def load_csv_data(file_path: str) -> pd.DataFrame:
        """
        Load CSV data from file.

        Args:
            file_path: Path to CSV file

        Returns:
            DataFrame containing loaded data
        """
        return pd.read_csv(file_path)
