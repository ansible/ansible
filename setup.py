#!/usr/bin/env python

import os
import sys
from glob import glob

sys.path.insert(0, os.path.abspath('lib'))
from ansible import __version__, __author__
from distutils.core import setup

# find library modules
from ansible.constants import DEFAULT_MODULE_PATH
dirs=os.listdir("./library/")
data_files = []
for i in dirs:
    data_files.append((os.path.join(DEFAULT_MODULE_PATH, i), glob('./library/' + i + '/*')))

setup(name='ansible',
      version=__version__,
      description='Radically simple IT automation',
      author=__author__,
      author_email='michael@ansibleworks.com',
      url='http://ansibleworks.com/',
      license='GPLv3',
      install_requires=['paramiko', 'jinja2', "PyYAML"],
      package_dir={ 'ansible': 'lib/ansible' },
      packages=[
         'ansible',
         'ansible.utils',
         'ansible.inventory',
         'ansible.inventory.vars_plugins',
         'ansible.playbook',
         'ansible.runner',
         'ansible.runner.action_plugins',
         'ansible.runner.lookup_plugins',
         'ansible.runner.connection_plugins',
         'ansible.runner.filter_plugins',
         'ansible.callback_plugins',
         'ansible.module_utils'
      ],
      scripts=[
         'bin/ansible',
         'bin/ansible-playbook',
         'bin/ansible-pull',
         'bin/ansible-doc'
      ],
      data_files=data_files
)
