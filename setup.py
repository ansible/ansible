from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pathlib

from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent.resolve()

install_requires = (here / 'requirements.txt').read_text(encoding='utf-8').splitlines()

setup(
    install_requires=install_requires,
    package_dir={'': 'lib',
                 'ansible_test': 'test/lib/ansible_test'},
    packages=find_packages('lib') + find_packages('test/lib'),
)
