#!/usr/bin/env python

import os
import sys

sys.path.insert(0, os.path.abspath('lib'))
from ansible import __version__, __author__
try:
    from setuptools import setup, find_packages
except ImportError:
    print("Ansible now needs setuptools in order to build. Install it using"
            " your package manager (usually python-setuptools) or via pip (pip"
            " install setuptools).")
    sys.exit(1)

setup(name='ansible',
      version=__version__,
      description='Radically simple IT automation',
      author=__author__,
      author_email='support@ansible.com',
      url='http://ansible.com/',
      license='GPLv3',
      # Ansible will also make use of a system copy of python-six if installed but use a
      # Bundled copy if it's not.
      install_requires=['paramiko', 'jinja2', "PyYAML", 'setuptools', 'pycrypto >= 2.6'],
      package_dir={ '': 'lib' },
      packages=find_packages('lib'),
      package_data={
         '': ['module_utils/*.ps1', 'modules/core/windows/*.ps1', 'modules/extras/windows/*.ps1', 'galaxy/data/*'],
      },
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Information Technology',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Natural Language :: English',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: System :: Installation/Setup',
          'Topic :: System :: Systems Administration',
          'Topic :: Utilities',
      ],
      entry_points={
            'console_scripts': [
                  'ansible = ansible.cli.adhoc:entry_point',
                  'ansible-playbook = ansible.cli.playbook:entry_point',
                  'ansible-pull = ansible.cli.pull:entry_point',
                  'ansible-doc = ansible.cli.doc:entry_point',
                  'ansible-galaxy = ansible.cli.galaxy:entry_point',
                  'ansible-vault = ansible.cli.vault:entry_point'
            ]
      },
      data_files=[],
)
