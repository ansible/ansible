#!/usr/bin/env python

import os
import sys
from glob import glob

def rel(f):
    return os.path.join(os.path.dirname(__file__), f)

sys.path.insert(0, rel('lib'))
from ansible import __version__, __author__
from distutils.core import setup

# Needed so the RPM can call setup.py and have modules land in the
# correct location. See #1277 for discussion
if getattr(sys, "real_prefix", None):
    # in a virtualenv
    DEFAULT_MODULE_PATH = os.path.join(sys.prefix, 'share/ansible/library')
else:
    DEFAULT_MODULE_PATH = '/usr/share/ansible/library'

module_path = DEFAULT_MODULE_PATH
if not os.path.exists(DEFAULT_MODULE_PATH):
    module_path = rel('library')

data_files = []
for i in os.listdir(module_path):
    data_files.append((os.path.join(DEFAULT_MODULE_PATH, i), glob('./library/' + i + '/*')))

setup(name='ansible',
      version=__version__,
      description='Radically simple IT automation',
      author=__author__,
      author_email='michael@ansibleworks.com',
      url='http://ansibleworks.com/',
      license='GPLv3',
      install_requires=['paramiko', 'jinja2', "PyYAML"],
      package_dir={ '': 'lib' },
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
