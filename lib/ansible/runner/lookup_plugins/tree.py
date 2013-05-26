# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os
import fnmatch
from ansible import utils

class LookupModule(object):
    """Return a list of files recursively matching a glob.

    Relative paths in will yield relative paths out, to facilitate recreating
    a local directory tree in a different location on a remote host.
    """
    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def getfiles(self, paths, filterglob='*', followlinks=True):
        """Yield names of all files under `paths` recursively that match
        shell glob `filterglob`.

        :param list(str) paths: The roots at which to start.  Beware dupes.
        :param bool followlinks: If True, recurse into dir links.  Beware infinite loops.
        :param str filterglob: Shell wildcard pattern against which files (not dirs!) are tested.
        :raises ValueError: if any path in `paths` is invalid.
        """
        for path in paths:
            if os.path.isdir(path):
                for (dirname, _, files) in os.walk(path, followlinks=followlinks):
                    for filename in files:
                        if fnmatch.fnmatch(filename, filterglob):
                            yield os.path.join(dirname, filename)
            elif os.path.exists(path):
                if fnmatch.fnmatch(path, filterglob):
                    yield path
            else:
                raise ValueError("'%s' is not a valid path." % (path))

    def run(self, terms, inject=None, **kwargs):
        # We want to keep relative paths relative (to the playbook dir) and absolute paths absolute.
        # But, relative paths need to be relative to CWD for os.walk to find them.
        # So, we prepend the basedir to relative paths, call os.walk, then strip it back off.
        dirs = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)
        paths = []
        for dir_ in dirs:
            if os.path.isabs(dir_):
                paths.append(dir_)
            elif os.path.expanduser(dir_) != dir_:
                paths.append(os.path.expanduser(dir_))
            else:
                paths.append(os.path.join(self.basedir, dir_))

        def relativize(path):
            if os.path.isabs(path):
                return path
            else:
                return os.path.relpath(path, self.basedir)

        files = map(relativize, self.getfiles(paths, kwargs.get('filter', '*'), kwargs.get('followlinks', True)))
        return files
