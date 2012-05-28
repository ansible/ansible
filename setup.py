#!/usr/bin/env python

# NOTE: setup.py does NOT install the contents of the library dir
# for you, you should go through "make install" or "make RPMs" 
# for that, or manually copy modules over.

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
      install_requires=['paramiko', 'jinja2', "PyYAML"],
      package_dir={ 'ansible': 'lib/ansible' },
      packages=[
         'ansible',
         'ansible.inventory',
         'ansible.playbook',
         'ansible.runner',
      ],
      scripts=[
         'bin/ansible',
         'bin/ansible-playbook'
      ]
)
