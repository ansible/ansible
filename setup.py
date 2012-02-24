#!/usr/bin/env python

from distutils.core import setup

setup(name='ansible',
      version='1.0',
      description='Minimal SSH command and control',
      author='Michael DeHaan',
      author_email='michael.dehaan@gmail.com',
      url='http://github.com/mpdehaan/ansible/',
      license='MIT',
      package_dir = { 'ansible' : 'lib/ansible' },
      packages=[
         'ansible',
      ],
      data_files=[ 
         ('/usr/share/ansible', [ 
             'library/ping',
             'library/command',
             'library/facter',
             'library/copy',
         ])
      ],
      scripts=[
         'bin/ansible',
      ]
)

