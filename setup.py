
from __future__ import print_function

import json
import os
import os.path
import re
import sys
import warnings

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
          " install setuptools).", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, os.path.abspath('lib'))
from ansible.release import __version__, __author__


SYMLINK_CACHE = 'SYMLINK_CACHE.json'


def _find_symlinks(topdir, extension=''):
    """Find symlinks that should be maintained

    Maintained symlinks exist in the bin dir or are modules which have
    aliases.  Our heuristic is that they are a link in a certain path which
    point to a file in the same directory.

    .. warn::

        We want the symlinks in :file:`bin/` that link into :file:`lib/ansible/*` (currently,
        :command:`ansible`, :command:`ansible-test`, and :command:`ansible-connection`) to become
        real files on install.  Updates to the heuristic here *must not* add them to the symlink
        cache.
    """
    symlinks = defaultdict(list)
    for base_path, dirs, files in os.walk(topdir):
        for filename in files:
            filepath = os.path.join(base_path, filename)
            if os.path.islink(filepath) and filename.endswith(extension):
                target = os.readlink(filepath)
                if target.startswith('/'):
                    # We do not support absolute symlinks at all
                    continue

                if os.path.dirname(target) == '':
                    link = filepath[len(topdir):]
                    if link.startswith('/'):
                        link = link[1:]
                    symlinks[os.path.basename(target)].append(link)
                else:
                    # Count how many directory levels from the topdir we are
                    levels_deep = os.path.dirname(filepath).count('/')

                    # Count the number of directory levels higher we walk up the tree in target
                    target_depth = 0
                    for path_component in target.split('/'):
                        if path_component == '..':
                            target_depth += 1
                            # If we walk past the topdir, then don't store
                            if target_depth >= levels_deep:
                                break
                        else:
                            target_depth -= 1
                    else:
                        # If we managed to stay within the tree, store the symlink
                        link = filepath[len(topdir):]
                        if link.startswith('/'):
                            link = link[1:]
                        symlinks[target].append(link)

    return symlinks


def _cache_symlinks(symlink_data):
    with open(SYMLINK_CACHE, 'w') as f:
        json.dump(symlink_data, f)


def _maintain_symlinks(symlink_type, base_path):
    """Switch a real file into a symlink"""
    try:
        # Try the cache first because going from git checkout to sdist is the
        # only time we know that we're going to cache correctly
        with open(SYMLINK_CACHE, 'r') as f:
            symlink_data = json.load(f)
    except (IOError, OSError) as e:
        # IOError on py2, OSError on py3.  Both have errno
        if e.errno == 2:
            # SYMLINKS_CACHE doesn't exist.  Fallback to trying to create the
            # cache now.  Will work if we're running directly from a git
            # checkout or from an sdist created earlier.
            library_symlinks = _find_symlinks('lib', '.py')
            library_symlinks.update(_find_symlinks('test/lib'))

            symlink_data = {'script': _find_symlinks('bin'),
                            'library': library_symlinks,
                            }

            # Sanity check that something we know should be a symlink was
            # found.  We'll take that to mean that the current directory
            # structure properly reflects symlinks in the git repo
            if 'ansible-playbook' in symlink_data['script']['ansible']:
                _cache_symlinks(symlink_data)
            else:
                raise RuntimeError(
                    "Pregenerated symlink list was not present and expected "
                    "symlinks in ./bin were missing or broken. "
                    "Perhaps this isn't a git checkout?"
                )
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
        library_symlinks = _find_symlinks('lib', '.py')
        library_symlinks.update(_find_symlinks('test/lib'))

        symlinks = {'script': _find_symlinks('bin'),
                    'library': library_symlinks,
                    }
        _cache_symlinks(symlinks)

        SDist.run(self)

        # Print warnings at the end because no one will see warnings before all the normal status
        # output
        if os.environ.get('_ANSIBLE_SDIST_FROM_MAKEFILE', False) != '1':
            warnings.warn('When setup.py sdist is run from outside of the Makefile,'
                          ' the generated tarball may be incomplete.  Use `make snapshot`'
                          ' to create a tarball from an arbitrary checkout or use'
                          ' `cd packaging/release && make release version=[..]` for official builds.',
                          RuntimeWarning)


def read_file(file_name):
    """Read file and return its contents."""
    with open(file_name, 'r') as f:
        return f.read()


def read_requirements(file_name):
    """Read requirements file as a list."""
    reqs = read_file(file_name).splitlines()
    if not reqs:
        raise RuntimeError(
            "Unable to read requirements from the %s file"
            "That indicates this copy of the source code is incomplete."
            % file_name
        )
    return reqs


PYCRYPTO_DIST = 'pycrypto'


def get_crypto_req():
    """Detect custom crypto from ANSIBLE_CRYPTO_BACKEND env var.

    pycrypto or cryptography. We choose a default but allow the user to
    override it. This translates into pip install of the sdist deciding what
    package to install and also the runtime dependencies that pkg_resources
    knows about.
    """
    crypto_backend = os.environ.get('ANSIBLE_CRYPTO_BACKEND', '').strip()

    if crypto_backend == PYCRYPTO_DIST:
        # Attempt to set version requirements
        return '%s >= 2.6' % PYCRYPTO_DIST

    return crypto_backend or None


def substitute_crypto_to_req(req):
    """Replace crypto requirements if customized."""
    crypto_backend = get_crypto_req()

    if crypto_backend is None:
        return req

    def is_not_crypto(r):
        CRYPTO_LIBS = PYCRYPTO_DIST, 'cryptography'
        return not any(r.lower().startswith(c) for c in CRYPTO_LIBS)

    return [r for r in req if is_not_crypto(r)] + [crypto_backend]


def read_extras():
    """Specify any extra requirements for installation."""
    extras = dict()
    extra_requirements_dir = 'packaging/requirements'
    for extra_requirements_filename in os.listdir(extra_requirements_dir):
        filename_match = re.search(r'^requirements-(\w*).txt$', extra_requirements_filename)
        if not filename_match:
            continue
        extra_req_file_path = os.path.join(extra_requirements_dir, extra_requirements_filename)
        try:
            extras[filename_match.group(1)] = read_file(extra_req_file_path).splitlines()
        except RuntimeError:
            pass
    return extras


def get_dynamic_setup_params():
    """Add dynamically calculated setup params to static ones."""
    return {
        # Retrieve the long description from the README
        'long_description': read_file('README.rst'),
        'install_requires': substitute_crypto_to_req(
            read_requirements('requirements.txt'),
        ),
        'extras_require': read_extras(),
    }


static_setup_params = dict(
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
    project_urls={
        'Bug Tracker': 'https://github.com/ansible/ansible/issues',
        'CI: Shippable': 'https://app.shippable.com/github/ansible/ansible',
        'Code of Conduct': 'https://docs.ansible.com/ansible/latest/community/code_of_conduct.html',
        'Documentation': 'https://docs.ansible.com/ansible/',
        'Mailing lists': 'https://docs.ansible.com/ansible/latest/community/communication.html#mailing-list-information',
        'Source Code': 'https://github.com/ansible/ansible',
    },
    license='GPLv3+',
    # Ansible will also make use of a system copy of python-six and
    # python-selectors2 if installed but use a Bundled copy if it's not.
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*',
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
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
        'bin/ansible-config',
        'bin/ansible-inventory',
        'bin/ansible-test',
    ],
    data_files=[],
    # Installing as zip files would break due to references to __file__
    zip_safe=False
)


def main():
    """Invoke installation process using setuptools."""
    setup_params = dict(static_setup_params, **get_dynamic_setup_params())
    ignore_warning_regex = (
        r"Unknown distribution option: '(project_urls|python_requires)'"
    )
    warnings.filterwarnings(
        'ignore',
        message=ignore_warning_regex,
        category=UserWarning,
        module='distutils.dist',
    )
    setup(**setup_params)
    warnings.resetwarnings()


if __name__ == '__main__':
    main()
