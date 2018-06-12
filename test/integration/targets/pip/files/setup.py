#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="ansible_test_pip_chdir",
    version="0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'ansible_test_pip_chdir = ansible_test_pip_chdir:main'
        ]
    }
)
