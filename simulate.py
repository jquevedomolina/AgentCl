#!/usr/bin/env python3
"""Chlorine Dosing Simulator — generates trending water quality data and runs the dosing agent in a loop."""

from src.simulator.runner import run_simulator

if __name__ == "__main__":
    print("💧 Starting Chlorine Dosing Simulator...")
    print("   Press Ctrl+C to stop.\n")
    run_simulator()
