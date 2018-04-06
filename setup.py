##! /usr/bin/env python

import json
import os
import os.path
import re
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


# shim for setuptools<30.3:
try:
    from setuptools.config import read_configuration
except ImportError:
    try:
        from configparser import ConfigParser, NoSectionError
    except ImportError:
        from ConfigParser import ConfigParser, NoSectionError
        ConfigParser.read_file = ConfigParser.readfp

    def read_configuration(filepath):
        """Read metadata and options from setup.cfg located at filepath."""
        cfg = ConfigParser()
        with open(filepath) as f:
            cfg.read_file(f)

        def maybe_read_files(d):
            d = d.strip()
            if not d.startswith('file:'):
                return d

            descs = []
            for fname in map(str.strip, d[5:].split(',')):
                with open(fname) as f:
                    descs.append(f.read())

            return ''.join(descs)

        cfg_val_to_list = lambda _: list(filter(bool, map(str.strip, _.strip().splitlines())))
        cfg_val_to_dict = lambda _: dict(map(lambda l: list(map(str.strip, l.split('=', 1))), filter(bool, map(str.strip, _.strip().splitlines()))))
        cfg_val_to_primitive = lambda _: json.loads(_.strip().lower())

        md = dict(cfg.items('metadata'))
        for list_key in 'classifiers', 'keywords':
            try:
                md[list_key] = cfg_val_to_list(md[list_key])
            except KeyError:
                pass
        try:
            md['long_description'] = maybe_read_files(md['long_description'])
        except KeyError:
            pass

        opt = dict(cfg.items('options'))
        try:
            opt['zip_safe'] = cfg_val_to_primitive(opt['zip_safe'])
        except KeyError:
            pass
        for list_key in 'scripts', 'install_requires', 'setup_requires':
            try:
                opt[list_key] = cfg_val_to_list(opt[list_key])
            except KeyError:
                pass
        try:
            opt['package_dir'] = cfg_val_to_dict(opt['package_dir'])
        except KeyError:
            pass

        opt_package_data = dict(cfg.items('options.package_data'))
        try:
            if not opt_package_data.get('', '').strip():
                opt_package_data[''] = opt_package_data['*']
                del opt_package_data['*']
        except KeyError:
            pass

        try:
            opt_extras_require = dict(cfg.items('options.extras_require'))
            opt['extras_require'] = {}
            for k, v in opt_extras_require.items():
                opt['extras_require'][k] = cfg_val_to_list(v)
        except NoSectionError:
            pass

        opt['package_data'] = {}
        for k, v in opt_package_data.items():
            opt['package_data'][k] = cfg_val_to_list(v)

        cur_pkgs = opt.get('packages', '').strip()
        if '\n' in cur_pkgs:
            opt['packages'] = cfg_val_to_list(opt['packages'])
        elif cur_pkgs.startswith('find:'):
            opt_packages_find = dict(cfg.items('options.packages.find'))
            opt['packages'] = find_packages(**opt_packages_find)

        return {'metadata': md, 'options': opt}


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
    except (IOError, OSError) as e:
        # IOError on py2, OSError on py3.  Both have errno
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

# specify any extra requirements for installation
extra_requirements = dict()
extra_requirements_dir = 'packaging/requirements'
for extra_requirements_filename in os.listdir(extra_requirements_dir):
    filename_match = re.search(r'^requirements-(\w*).txt$', extra_requirements_filename)
    if filename_match:
        with open(os.path.join(extra_requirements_dir, extra_requirements_filename)) as extra_requirements_file:
            extra_requirements[filename_match.group(1)] = extra_requirements_file.read().splitlines()


setup_params = dict(
    # Use the distutils SDist so that symlinks are not expanded
    # Use a custom Build for the same reason
    cmdclass={
        'build_py': BuildPyCommand,
        'build_scripts': BuildScriptsCommand,
        'install_lib': InstallLibCommand,
        'install_scripts': InstallScriptsCommand,
        'sdist': SDistCommand,
    },
    version=__version__,
    author=__author__,
    # Ansible will also make use of a system copy of python-six and
    # python-selectors2 if installed but use a Bundled copy if it's not.
    install_requires=install_requirements,
    extras_require=extra_requirements,
)

declarative_setup_params = read_configuration('setup.cfg')
setup_params = dict(setup_params, **declarative_setup_params['metadata'])
setup_params = dict(setup_params, **declarative_setup_params['options'])


__name__ == '__main__' and setuptools.setup(**setup_params)
