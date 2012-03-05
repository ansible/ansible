#!/usr/bin/env python

from distutils.core import setup

setup(name='ansible',
      version='1.0',
      description='Minimal SSH command and control',
      author='Michael DeHaan',
      author_email='michael.dehaan@gmail.com',
      url='http://github.com/mpdehaan/ansible/',
      license='GPLv3',
      package_dir = { 'ansible' : 'lib/ansible' },
      packages=[
         'ansible',
      ],
      data_files=[ 
         ('/usr/share/ansible', [ 
             'library/ping',
             'library/command',
             'library/facter',
             'library/ohai',
             'library/copy',
             'library/setup',
             'library/service',
             'library/template',
             'library/git',
         ]),
         ('/usr/share/man/man1', [
                'docs/man/man1/ansible.1'
         ]),
         ('/usr/share/man/man5', [
                'docs/man/man5/ansible-modules.5',
                'docs/man/man5/ansible-playbook.5'
         ])
      ],
      scripts=[
         'bin/ansible',
         'bin/ansible-playbook'
      ]
)
