from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pathlib
import re

from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent.resolve()


def find_package_info(*file_paths):
    try:
        info_file = here.joinpath(*file_paths).read_text(encoding='utf-8')
    except Exception:
        raise RuntimeError("Unable to find package info.")

    # The version line must have the form
    # __version__ = 'ver'
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              info_file, re.M)
    author_match = re.search(r"^__author__ = ['\"]([^'\"]*)['\"]",
                             info_file, re.M)

    if version_match and author_match:
        return version_match.group(1), author_match.group(1)
    raise RuntimeError("Unable to find package info.")


long_description = (here / 'README.rst').read_text(encoding='utf-8')
install_requires = (here / 'requirements.txt').read_text(encoding='utf-8').splitlines()

__version__, __author__ = find_package_info('lib', 'ansible', 'release.py')

setup(
    name='ansible-core',
    version=__version__,
    description='Radically simple IT automation',
    long_description=long_description,
    author=__author__,
    author_email='info@ansible.com',
    url='https://ansible.com/',
    project_urls={
        'Bug Tracker': 'https://github.com/ansible/ansible/issues',
        'CI: Azure Pipelines': 'https://dev.azure.com/ansible/ansible/',
        'Code of Conduct': 'https://docs.ansible.com/ansible/latest/community/code_of_conduct.html',
        'Documentation': 'https://docs.ansible.com/ansible/',
        'Mailing lists': 'https://docs.ansible.com/ansible/latest/community/communication.html#mailing-list-information',
        'Source Code': 'https://github.com/ansible/ansible',
    },
    license='GPLv3+',
    # Ansible will also make use of a system copy of python-six and
    # python-selectors2 if installed but use a Bundled copy if it's not.
    python_requires='>=3.8',
    install_requires=install_requires,
    package_dir={'': 'lib',
                 'ansible_test': 'test/lib/ansible_test'},
    packages=find_packages('lib') + find_packages('test/lib'),
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    data_files=[],
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
