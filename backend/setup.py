"""
Setup file for CodeNova backend to enable proper imports in tests.
"""

from setuptools import setup, find_packages

setup(
    name="codenova-backend",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.9",
)
