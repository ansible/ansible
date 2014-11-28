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
#  - name: copy first existing file found to /some/file
#    action: copy src=$item dest=/some/file
#    with_first_found: 
#     - files: foo ${inventory_hostname} bar
#       paths: /tmp/production /tmp/staging

# that will look for files in this order:
# /tmp/production/foo
#                 ${inventory_hostname}
#                 bar
# /tmp/staging/foo
#              ${inventory_hostname}
#              bar
                  
#  - name: copy first existing file found to /some/file
#    action: copy src=$item dest=/some/file
#    with_first_found: 
#     - files: /some/place/foo ${inventory_hostname} /some/place/else

#  that will look for files in this order:
#  /some/place/foo
#  $relative_path/${inventory_hostname}
#  /some/place/else

# example - including tasks:
#  tasks:
#  - include: $item
#    with_first_found:
#     - files: generic
#       paths: tasks/staging tasks/production
# this will include the tasks in the file generic where it is found first (staging or production)

# example simple file lists
#tasks:
#- name: first found file
#  action: copy src=$item dest=/etc/file.cfg
#  with_first_found:
#  - files: foo.${inventory_hostname} foo


# example skipping if no matched files
# First_found also offers the ability to control whether or not failing
# to find a file returns an error or not
#
#- name: first found file - or skip
#  action: copy src=$item dest=/etc/file.cfg
#  with_first_found:
#  - files: foo.${inventory_hostname}
#    skip: true

# example a role with default configuration and configuration per host
# you can set multiple terms with their own files and paths to look through.
# consider a role that sets some configuration per host falling back on a default config.
#
#- name: some configuration template
#  template: src={{ item }} dest=/etc/file.cfg mode=0444 owner=root group=root
#  with_first_found:
#   - files:
#      - ${inventory_hostname}/etc/file.cfg
#     paths:
#      - ../../../templates.overwrites
#      - ../../../templates
#   - files:
#      - etc/file.cfg
#     paths:
#      - templates

# the above will return an empty list if the files cannot be found at all
# if skip is unspecificed or if it is set to false then it will return a list 
# error which can be caught bye ignore_errors: true for that action.

# finally - if you want you can use it, in place to replace first_available_file:
# you simply cannot use the - files, path or skip options. simply replace
# first_available_file with with_first_found and leave the file listing in place
#
#
#  - name: with_first_found like first_available_file
#    action: copy src=$item dest=/tmp/faftest
#    with_first_found:
#     - ../files/foo
#     - ../files/bar
#     - ../files/baz
#    ignore_errors: true


from ansible import utils, errors
import os

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def run(self, terms, inject=None, **kwargs):

        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)

        result = None
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
                    skip  = utils.boolean(term.get('skip', False))

                    filelist = files
                    if isinstance(files, basestring):
                        files = files.replace(',', ' ')
                        files = files.replace(';', ' ')
                        filelist = files.split(' ')

                    pathlist = paths
                    if paths:
                        if isinstance(paths, basestring):
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
            total_search = terms

        for fn in total_search:
            if inject and '_original_file' in inject:
                # check the templates and vars directories too,
                # if they exist
                for roledir in ('templates', 'vars'):
                    path = utils.path_dwim(os.path.join(self.basedir, '..', roledir), fn)
                    if os.path.exists(path):
                        return [path]
            # if none of the above were found, just check the
            # current filename against the basedir (this will already
            # have ../files from runner, if it's a role task
            path = utils.path_dwim(self.basedir, fn)
            if os.path.exists(path):
                return [path]
        else:
            if skip:
                return []
            else:
                return [None]

