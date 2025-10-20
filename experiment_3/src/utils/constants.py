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
    R_FIXED: float = 9955            # Fixed resistor value (ohms)
    STEPPER_STEPS_PER_REV: int = 2048  # Steps per full revolution for stepper motor
    ANALOG_RESOLUTION: int = 1023    # 10-bit ADC resolution


@dataclass
class BaseConfig:
    """Base configuration for file paths."""
    OUT_DIR: str = '../out/'
