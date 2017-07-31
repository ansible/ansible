
import json
import os
import os.path
import sys
from collections import defaultdict
from distutils.command.build_scripts import build_scripts as BuildScripts
from distutils.command.sdist import sdist as SDist

try:
    from setuptools import setup, find_packages
    from setuptools.command.build_py import build_py as BuildPy
    from setuptools.command.install_lib import install_lib as InstallLib
    from setuptools.command.install_scripts import install_scripts as InstallScripts
except ImportError:
    print("Ansible now needs setuptools in order to build. Install it using"
          " your package manager (usually python-setuptools) or via pip (pip"
          " install setuptools).")
    sys.exit(1)

sys.path.insert(0, os.path.abspath('lib'))
from ansible.release import __version__, __author__


SYMLINK_CACHE = 'SYMLINK_CACHE.json'


def _find_symlinks(topdir, extension=''):
    """Find symlinks that should be maintained

    Maintained symlinks exist in the bin dir or are modules which have
    aliases.  Our heuristic is that they are a link in a certain path which
    point to a file in the same directory.
    """
    symlinks = defaultdict(list)
    for base_path, dirs, files in os.walk(topdir):
        for filename in files:
            filepath = os.path.join(base_path, filename)
            if os.path.islink(filepath) and filename.endswith(extension):
                target = os.readlink(filepath)
                if os.path.dirname(target) == '':
                    link = filepath[len(topdir):]
                    if link.startswith('/'):
                        link = link[1:]
                    symlinks[os.path.basename(target)].append(link)
    return symlinks


def _cache_symlinks(symlink_data):
    with open(SYMLINK_CACHE, 'w') as f:
        f.write(json.dumps(symlink_data))


def _maintain_symlinks(symlink_type, base_path):
    """Switch a real file into a symlink"""
    try:
        # Try the cache first because going from git checkout to sdist is the
        # only time we know that we're going to cache correctly
        with open(SYMLINK_CACHE, 'r') as f:
            symlink_data = json.loads(f.read())
    except IOError as e:
        if e.errno == 2:
            # SYMLINKS_CACHE doesn't exist.  Fallback to trying to create the
            # cache now.  Will work if we're running directly from a git
            # checkout or from an sdist created earlier.
            symlink_data = {'script': _find_symlinks('bin'),
                            'library': _find_symlinks('lib', '.py'),
                            }

            # Sanity check that something we know should be a symlink was
            # found.  We'll take that to mean that the current directory
            # structure properly reflects symlinks in the git repo
            if 'ansible-playbook' in symlink_data['script']['ansible']:
                _cache_symlinks(symlink_data)
            else:
                raise
        else:
            raise
    symlinks = symlink_data[symlink_type]

    for source in symlinks:
        for dest in symlinks[source]:
            dest_path = os.path.join(base_path, dest)
            if not os.path.islink(dest_path):
                try:
                    os.unlink(dest_path)
                except OSError as e:
                    if e.errno == 2:
                        # File does not exist which is all we wanted
                        pass
                os.symlink(source, dest_path)


class BuildPyCommand(BuildPy):
    def run(self):
        BuildPy.run(self)
        _maintain_symlinks('library', self.build_lib)


class BuildScriptsCommand(BuildScripts):
    def run(self):
        BuildScripts.run(self)
        _maintain_symlinks('script', self.build_dir)


class InstallLibCommand(InstallLib):
    def run(self):
        InstallLib.run(self)
        _maintain_symlinks('library', self.install_dir)


class InstallScriptsCommand(InstallScripts):
    def run(self):
        InstallScripts.run(self)
        _maintain_symlinks('script', self.install_dir)


class SDistCommand(SDist):
    def run(self):
        # have to generate the cache of symlinks for release as sdist is the
        # only command that has access to symlinks from the git repo
        symlinks = {'script': _find_symlinks('bin'),
                    'library': _find_symlinks('lib', '.py'),
                    }
        _cache_symlinks(symlinks)

        SDist.run(self)


with open('requirements.txt') as requirements_file:
    install_requirements = requirements_file.read().splitlines()
    if not install_requirements:
        print("Unable to read requirements from the requirements.txt file"
              "That indicates this copy of the source code is incomplete.")
        sys.exit(2)

# pycrypto or cryptography.   We choose a default but allow the user to
# override it.  This translates into pip install of the sdist deciding what
# package to install and also the runtime dependencies that pkg_resources
# knows about
crypto_backend = os.environ.get('ANSIBLE_CRYPTO_BACKEND', None)
if crypto_backend:
    if crypto_backend.strip() == 'pycrypto':
        # Attempt to set version requirements
        crypto_backend = 'pycrypto >= 2.6'

    install_requirements = [r for r in install_requirements if not (r.lower().startswith('pycrypto') or r.lower().startswith('cryptography'))]
    install_requirements.append(crypto_backend)


setup(
    # Use the distutils SDist so that symlinks are not expanded
    # Use a custom Build for the same reason
    cmdclass={
        'build_py': BuildPyCommand,
        'build_scripts': BuildScriptsCommand,
        'install_lib': InstallLibCommand,
        'install_scripts': InstallScriptsCommand,
        'sdist': SDistCommand,
    },
    name='ansible',
    version=__version__,
    description='Radically simple IT automation',
    author=__author__,
    author_email='info@ansible.com',
    url='https://ansible.com/',
    license='GPLv3+',
    # Ansible will also make use of a system copy of python-six and
    # python-selectors2 if installed but use a Bundled copy if it's not.
    install_requires=install_requirements,
    package_dir={'': 'lib'},
    packages=find_packages('lib'),
    package_data={
        '': [
            'module_utils/powershell/*.psm1',
            'module_utils/powershell/*/*.psm1',
            'modules/windows/*.ps1',
            'modules/windows/*/*.ps1',
            'galaxy/data/*/*.*',
            'galaxy/data/*/*/.*',
            'galaxy/data/*/*/*.*',
            'galaxy/data/*/tests/inventory',
            'config/data/*.yaml',
            'config/data/*.yml',
        ],
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
    scripts=[
        'bin/ansible',
        'bin/ansible-playbook',
        'bin/ansible-pull',
        'bin/ansible-doc',
        'bin/ansible-galaxy',
        'bin/ansible-console',
        'bin/ansible-connection',
        'bin/ansible-vault',
    ],
    data_files=[],
)
