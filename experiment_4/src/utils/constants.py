#!/usr/bin/env python3
"""
Constants Module

This module provides constants used across multiple physics experiments.
"""

from dataclasses import dataclass


@dataclass
class BaseConstants:
    """Base constants used across multiple experiments."""
    V_SUPPLY: float = 5.0            # Supply voltage (V)
    R_FIXED: float = 100000.0            # Fixed resistor value (ohms)
    ANALOG_RESOLUTION: int = 1023    # 10-bit ADC resolution


@dataclass
class BaseConfig:
    """Base configuration for file paths."""
    OUT_DIR: str = '../out/'
