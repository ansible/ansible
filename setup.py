#!/usr/bin/env python

import os
import sys
from glob import glob

sys.path.insert(0, os.path.abspath('lib'))
from ansible import __version__, __author__
try:
    from setuptools import setup
except ImportError:
    print "Ansible now needs setuptools in order to build. " \
          "Install it using your package manager (usually python-setuptools) or via pip (pip install setuptools)."
    sys.exit(1)

# find library modules
from ansible.constants import DEFAULT_MODULE_PATH
module_paths = DEFAULT_MODULE_PATH.split(os.pathsep)
# always install in /usr/share/ansible if specified
# otherwise use the first module path listed
if '/usr/share/ansible' in module_paths:
    install_path = '/usr/share/ansible'
else:
    install_path = module_paths[0]
dirs=os.listdir("./library/")
data_files = []
for i in dirs:
    data_files.append((os.path.join(install_path, i), glob('./library/' + i + '/*')))

setup(name='ansible',
      version=__version__,
      description='Radically simple IT automation',
      author=__author__,
      author_email='michael@ansible.com',
      url='http://ansible.com/',
      license='GPLv3',
      install_requires=['paramiko', 'jinja2', "PyYAML", 'setuptools', 'pycrypto >= 2.6'],
      package_dir={ 'ansible': 'lib/ansible' },
      packages=[
         'ansible',
         'ansible.utils',
         'ansible.utils.module_docs_fragments',
         'ansible.inventory',
         'ansible.inventory.vars_plugins',
         'ansible.playbook',
         'ansible.runner',
         'ansible.runner.action_plugins',
         'ansible.runner.lookup_plugins',
         'ansible.runner.connection_plugins',
         'ansible.runner.shell_plugins',
         'ansible.runner.filter_plugins',
         'ansible.callback_plugins',
         'ansible.module_utils'
      ],
      scripts=[
         'bin/ansible',
         'bin/ansible-playbook',
         'bin/ansible-pull',
         'bin/ansible-doc',
         'bin/ansible-galaxy',
         'bin/ansible-vault',
      ],
      data_files=data_files
)
