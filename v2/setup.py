#!/usr/bin/env python

import sys

from ansible import __version__
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
      author='Michael DeHaan',
      author_email='michael@ansible.com',
      url='http://ansible.com/',
      license='GPLv3',
      install_requires=['paramiko', 'jinja2', "PyYAML", 'setuptools', 'pycrypto >= 2.6', 'six >= 1.4.0'],
      # package_dir={ '': 'lib' },
      # packages=find_packages('lib'),
      package_data={
         '': ['module_utils/*.ps1', 'modules/core/windows/*.ps1', 'modules/extras/windows/*.ps1'],
      },
      scripts=[
         'bin/ansible',
         'bin/ansible-playbook',
         # 'bin/ansible-pull',
         # 'bin/ansible-doc',
         # 'bin/ansible-galaxy',
         # 'bin/ansible-vault',
      ],
      data_files=[],
)
