# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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
import stat
import errno

from ansible import errors
from ansible import utils
import ansible.constants as C

def _load_vars(basepath, results, vault_password=None):
    """
    Load variables from any potential yaml filename combinations of basepath,
    returning result.
    """

    paths_to_check = [ "".join([basepath, ext]) 
                       for ext in C.YAML_FILENAME_EXTENSIONS ]

    found_paths = []

    for path in paths_to_check:
        found, results = _load_vars_from_path(path, results, vault_password=vault_password)
        if found:
            found_paths.append(path)


    # disallow the potentially confusing situation that there are multiple
    # variable files for the same name. For example if both group_vars/all.yml
    # and group_vars/all.yaml
    if len(found_paths) > 1:
        raise errors.AnsibleError("Multiple variable files found. "
            "There should only be one. %s" % ( found_paths, ))

    return results

def _load_vars_from_path(path, results, vault_password=None):
    """
    Robustly access the file at path and load variables, carefully reporting
    errors in a friendly/informative way.

    Return the tuple (found, new_results, )
    """

    try:
        # in the case of a symbolic link, we want the stat of the link itself,
        # not its target
        pathstat = os.lstat(path)
    except os.error, err:
        # most common case is that nothing exists at that path.
        if err.errno == errno.ENOENT:
            return False, results
        # otherwise this is a condition we should report to the user
        raise errors.AnsibleError(
            "%s is not accessible: %s." 
            " Please check its permissions." % ( path, err.strerror))

    # symbolic link
    if stat.S_ISLNK(pathstat.st_mode):
        try:
            target = os.path.realpath(path)
        except os.error, err2:
            raise errors.AnsibleError("The symbolic link at %s "
                "is not readable: %s.  Please check its permissions."
                % (path, err2.strerror, ))
        # follow symbolic link chains by recursing, so we repeat the same
        # permissions checks above and provide useful errors.
        return _load_vars_from_path(target, results)

    # directory
    if stat.S_ISDIR(pathstat.st_mode):

        # support organizing variables across multiple files in a directory
        return True, _load_vars_from_folder(path, results, vault_password=vault_password)

    # regular file
    elif stat.S_ISREG(pathstat.st_mode):
        data = utils.parse_yaml_from_file(path, vault_password=vault_password)
        if type(data) != dict:
            raise errors.AnsibleError(
                "%s must be stored as a dictionary/hash" % path)

        # combine vars overrides by default but can be configured to do a
        # hash merge in settings
        results = utils.combine_vars(results, data)
        return True, results

    # something else? could be a fifo, socket, device, etc.
    else:
        raise errors.AnsibleError("Expected a variable file or directory "
            "but found a non-file object at path %s" % (path, ))

def _load_vars_from_folder(folder_path, results, vault_password=None):
    """
    Load all variables within a folder recursively.
    """

    # this function and _load_vars_from_path are mutually recursive

    try:
        names = os.listdir(folder_path)
    except os.error, err:
        raise errors.AnsibleError(
            "This folder cannot be listed: %s: %s." 
             % ( folder_path, err.strerror))
        
    # evaluate files in a stable order rather than whatever order the
    # filesystem lists them.
    names.sort() 

    # do not parse hidden files or dirs, e.g. .svn/
    paths = [os.path.join(folder_path, name) for name in names if not name.startswith('.')]
    for path in paths:
        _found, results = _load_vars_from_path(path, results, vault_password=vault_password)
    return results

            
class VarsModule(object):

    """
    Loads variables from group_vars/<groupname> and host_vars/<hostname> in directories parallel
    to the inventory base directory or in the same directory as the playbook.  Variables in the playbook
    dir will win over the inventory dir if files are in both.
    """

    def __init__(self, inventory):

        """ constructor """

        self.inventory = inventory

    def run(self, host, vault_password=None):

        """ main body of the plugin, does actual loading """

        inventory = self.inventory
        basedir = inventory.playbook_basedir()
        if basedir is not None: 
            basedir = os.path.abspath(basedir)
        self.pb_basedir = basedir

        # sort groups by depth so deepest groups can override the less deep ones
        groupz = sorted(inventory.groups_for_host(host.name), key=lambda g: g.depth)
        groups = [ g.name for g in groupz ]
        inventory_basedir = inventory.basedir()

        results = {}
        scan_pass = 0

        # look in both the inventory base directory and the playbook base directory
        for basedir in [ inventory_basedir, self.pb_basedir ]:


            # this can happen from particular API usages, particularly if not run
            # from /usr/bin/ansible-playbook
            if basedir is None:
                continue

            scan_pass = scan_pass + 1

            # it's not an eror if the directory does not exist, keep moving
            if not os.path.exists(basedir):
                continue

            # save work of second scan if the directories are the same
            if inventory_basedir == self.pb_basedir and scan_pass != 1:
                continue

            # load vars in dir/group_vars/name_of_group
            for group in groups:
                base_path = os.path.join(basedir, "group_vars/%s" % group)
                results = _load_vars(base_path, results, vault_password=vault_password)

            # same for hostvars in dir/host_vars/name_of_host
            base_path = os.path.join(basedir, "host_vars/%s" % host.name)
            results = _load_vars(base_path, results, vault_password=vault_password)

        # all done, results is a dictionary of variables for this particular host.
        return results

