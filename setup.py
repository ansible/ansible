#!/usr/bin/env python

import os
import sys
from glob import glob

sys.path.insert(0, os.path.abspath('lib'))
from ansible import __version__, __author__
from setuptools import setup,find_packages

# find library modules
from ansible.constants import DIST_MODULE_PATH
dirs=os.listdir("./library/")
data_files = []
for i in dirs:
    data_files.append((DIST_MODULE_PATH + i, glob('./library/' + i + '/*')))

print "DATA FILES=%s" % data_files

setup(name='ansible',
      version=__version__,
      description='Minimal SSH command and control',
      author=__author__,
      author_email='michael.dehaan@gmail.com',
      url='http://ansible.github.com/',
      license='GPLv3',
      install_requires=['paramiko', 'jinja2', "PyYAML"],
      package_dir = {'':'lib'},
      packages=find_packages('lib'),
      scripts=[
         'bin/ansible',
         'bin/ansible-playbook',
         'bin/ansible-pull',
         'bin/ansible-doc'
      ],
      data_files=data_files
)
