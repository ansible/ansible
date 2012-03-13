#!/usr/bin/env python

import glob
import os
import sys

sys.path.insert(0, os.path.abspath('lib'))
from ansible import __version__, __author__
from distutils.core import setup

setup(name='ansible',
      version=__version__,
      description='Minimal SSH command and control',
      author=__author__,
      author_email='michael.dehaan@gmail.com',
      url='http://ansible.github.com/',
      license='GPLv3',
      package_dir = { 'ansible' : 'lib/ansible' },
      packages=[
         'ansible',
      ],
      scripts=[
         'bin/ansible',
         'bin/ansible-playbook'
      ]
)
