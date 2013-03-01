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





from ansible import utils, errors
import os

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def run(self, terms, **kwargs):
        result = None
        for term in terms:
            if isinstance(term, dict):
                files = term.get('files', [])
                paths = term.get('paths', [])
            
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
                    
                total_search = []
            

                if not pathlist:
                    total_search = filelist
                else:
                    for path in pathlist:
                        for fn in filelist:
                            f = path + '/' + fn
                            total_search.append(f)
            else:
                total_search = [term]

            result = None
            for fn in total_search:
                path = utils.path_dwim(self.basedir, fn)
                if os.path.exists(path):
                    return [path]


        if not result:
            raise errors.AnsibleError("no match found: %s, %s" % (pathlist, filelist))
