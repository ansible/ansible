# (c) 2013, seth vidal <skvidal@fedoraproject.org> red hat, inc
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# take a list of files and (optionally) a list of paths
# return the first existing file found in the paths
# [file1, file2, file3], [path1, path2, path3]
# search order is:
# path1/file1
# path1/file2
# path1/file3
# path2/file1
# path2/file2
# path2/file3
# path3/file1
# path3/file2
# path3/file3

# first file found with os.path.exists() is returned
# no file matches raises ansibleerror
# EXAMPLES
# - name: copy first existing file found to /some/file
#   action: copy src=$item dest=/some/file
#   with_first_found:
#    - files: foo ${inventory_hostname} bar
#      paths: /tmp/production /tmp/staging

# that will look for files in this order:
# /tmp/production/foo
#                 ${inventory_hostname}
#                 bar
# /tmp/staging/foo
#              ${inventory_hostname}
#              bar

# - name: copy first existing file found to /some/file
#   action: copy src=$item dest=/some/file
#   with_first_found:
#    - files: /some/place/foo ${inventory_hostname} /some/place/else

#  that will look for files in this order:
#  /some/place/foo
#  $relative_path/${inventory_hostname}
#  /some/place/else

# example - including tasks:
# tasks:
# - include: $item
#   with_first_found:
#    - files: generic
#      paths: tasks/staging tasks/production
# this will include the tasks in the file generic where it is found first (staging or production)

# example simple file lists
# tasks:
# - name: first found file
#   action: copy src=$item dest=/etc/file.cfg
#   with_first_found:
#   - files: foo.${inventory_hostname} foo


# example skipping if no matched files
# First_found also offers the ability to control whether or not failing
# to find a file returns an error or not
#
# - name: first found file - or skip
#   action: copy src=$item dest=/etc/file.cfg
#   with_first_found:
#   - files: foo.${inventory_hostname}
#     skip: true

# example a role with default configuration and configuration per host
# you can set multiple terms with their own files and paths to look through.
# consider a role that sets some configuration per host falling back on a default config.
#
# - name: some configuration template
#   template: src={{ item }} dest=/etc/file.cfg mode=0444 owner=root group=root
#   with_first_found:
#    - files:
#       - ${inventory_hostname}/etc/file.cfg
#      paths:
#       - ../../../templates.overwrites
#       - ../../../templates
#    - files:
#       - etc/file.cfg
#      paths:
#       - templates

# the above will return an empty list if the files cannot be found at all
# if skip is unspecificed or if it is set to false then it will return a list
# error which can be caught bye ignore_errors: true for that action.

# finally - if you want you can use it, in place to replace first_available_file:
# you simply cannot use the - files, path or skip options. simply replace
# first_available_file with with_first_found and leave the file listing in place
#
#
# - name: with_first_found like first_available_file
#   action: copy src=$item dest=/tmp/faftest
#   with_first_found:
#    - ../files/foo
#    - ../files/bar
#    - ../files/baz
#   ignore_errors: true

import os

from jinja2.exceptions import UndefinedError

from ansible.errors import AnsibleFileNotFound, AnsibleLookupError, AnsibleUndefinedVariable
from ansible.module_utils.six import string_types
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        anydict = False
        skip = False

        for term in terms:
            if isinstance(term, dict):
                anydict = True

        total_search = []
        if anydict:
            for term in terms:
                if isinstance(term, dict):
                    files = term.get('files', [])
                    paths = term.get('paths', [])
                    skip = boolean(term.get('skip', False), strict=False)

                    filelist = files
                    if isinstance(files, string_types):
                        files = files.replace(',', ' ')
                        files = files.replace(';', ' ')
                        filelist = files.split(' ')

                    pathlist = paths
                    if paths:
                        if isinstance(paths, string_types):
                            paths = paths.replace(',', ' ')
                            paths = paths.replace(':', ' ')
                            paths = paths.replace(';', ' ')
                            pathlist = paths.split(' ')

                    if not pathlist:
                        total_search = filelist
                    else:
                        for path in pathlist:
                            for fn in filelist:
                                f = os.path.join(path, fn)
                                total_search.append(f)
                else:
                    total_search.append(term)
        else:
            total_search = self._flatten(terms)

        for fn in total_search:
            try:
                fn = self._templar.template(fn)
            except (AnsibleUndefinedVariable, UndefinedError):
                continue

            # get subdir if set by task executor, default to files otherwise
            subdir = getattr(self, '_subdir', 'files')
            path = None
            path = self.find_file_in_search_path(variables, subdir, fn, ignore_missing=True)
            if path is not None:
                return [path]
        else:
            if skip:
                return []
            else:
                raise AnsibleLookupError("No file was found when using with_first_found. Use the 'skip: true' option to allow this task to be skipped if no "
                                         "files are found")
