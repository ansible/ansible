from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pathlib

from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent.resolve()


def get_version(path):
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('__version__'):
            # __version__ = "0.9"
            delim = "'" if "'" in line else '"'
            return line.split(delim)[1]
    raise RuntimeError('Unable to find version string.')


install_requires = (here / 'requirements.txt').read_text(encoding='utf-8').splitlines()
version = get_version(here / 'lib' / 'ansible' / 'release.py')

setup(
    version=version,
    install_requires=install_requires,
    package_dir={'': 'lib',
                 'ansible_test': 'test/lib/ansible_test'},
    packages=find_packages('lib') + find_packages('test/lib'),
    entry_points={
        'console_scripts': [
            'ansible=ansible.cli.adhoc:main',
            'ansible-config=ansible.cli.config:main',
            'ansible-console=ansible.cli.console:main',
            'ansible-doc=ansible.cli.doc:main',
            'ansible-galaxy=ansible.cli.galaxy:main',
            'ansible-inventory=ansible.cli.inventory:main',
            'ansible-playbook=ansible.cli.playbook:main',
            'ansible-pull=ansible.cli.pull:main',
            'ansible-vault=ansible.cli.vault:main',
            'ansible-connection=ansible.cli.scripts.ansible_connection_cli_stub:main',
            'ansible-test=ansible_test._util.target.cli.ansible_test_cli_stub:main',
        ],
    },
)
