# (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.constants import config
from ansible.template import Templar
from ansible.utils.collection_loader import AnsibleCollectionRef
from ansible.utils.collection_loader._collection_finder import _get_collection_role_path
from ansible.utils.path import unfrackpath


class AnsibleRoleFinder(object):
    """
    Class used to locate the path to any available roles.

    Example usage:

        finder = AnsibleRoleFinder(data_loader)

        # Find 'myrole' standard role
        result = finder.find_first('myrole')

        # Find 'myrole' in ansible.example collection
        result = finder.find_first('ansible.example.myrole')

        # Find 'myrole' in any of the listed collections or as standard role.
        result = finder.find_first('myrole', ['ansible.example', 'community.general'])

    TODO:
      - This would replace code in `ansible-doc` and `ansible-galaxy`. Maybe plugins?
      - API to filter based on file existence (e.g. meta/main.yml for a-g).
      - API to show masked roles
      - API to show only first match
    """

    def __init__(self, data_loader, role_basedir=None, templar=None):
        """
        Initialize a new RoleFinder object.

        :param DataLoader data_loader: A DataLoader object to use for identifying
            base directory and path existence.
        :param str role_basedir: Path to a relative role base directory.
        :param Templar templar: A Templar object used for expanding templated paths.

        The search path order for standard (i.e., non-collection-based) roles
        is identified and set here. That path order should be:
           - 'roles' subdirectory of playbook base directory
           - configured roles path (DEFAULT_ROLES_PATH)
           - relative role base directory (if any) to find dependent roles
           - playbook base directory itself
        """
        self.__loader = data_loader
        self.__templar = templar
        self.__standard_search_paths = []
        self.__standard_search_paths.append(os.path.join(self.__loader.get_basedir(), u'roles'))
        self.__standard_search_paths.extend(config.get_config_value('DEFAULT_ROLES_PATH'))
        if role_basedir:
            self.__standard_search_paths.append(role_basedir)
        self.__standard_search_paths.append(self.__loader.get_basedir())

    # ========================================================================
    # Public API
    # ========================================================================

    @property
    def standard_role_search_paths(self):
        return self.__standard_search_paths

    @property
    def templar(self):
        return self.__templar

    @templar.setter
    def templar(self, value):
        """
        Set a new Templar object to use when expanding templated paths.

        Set the value to None to remove any existing templating object and
        avoid templating operations.

        :param Templar value: A configured templating object.
        """
        if value and not isinstance(value, Templar):
            raise TypeError("templar must be of type Templar")
        self.__templar = value

    def find_first(self, role_name, collection_names=None):
        """
        Find the path to the first role found with the given name.

        :param str role_name: Name of the role to find. This may be either a
            simple role name (e.g. myrole), or qualified with a collection name
            (e.g. community.general.myrole).

        :param list collection_names: A list of fully qualified collection names to search.

        :returns: A Result object, or None if not found.
        """
        if self.__templar:
            role_name = self.__templar.template(role_name)

        # Search collection-based roles first if a collection context is given.
        role_tuple = None
        if collection_names or AnsibleCollectionRef.is_valid_fqcr(role_name):
            role_tuple = _get_collection_role_path(role_name, collection_names)

        if role_tuple:
            (simple_role_name, role_path, collection_name) = role_tuple
            return self.Result(simple_role_name, role_path, collection_name)

        for path in self.standard_role_search_paths:
            if self.__templar:
                path = self.__templar.template(path)
            role_path = unfrackpath(os.path.join(path, role_name))
            if self.__loader.path_exists(role_path):
                return self.Result(role_name, role_path)

        # if not found elsewhere try to extract path from name
        role_path = unfrackpath(role_name)
        if self.__loader.path_exists(role_path):
            role_name = os.path.basename(role_name)
            return self.Result(role_name, role_path)

        return None

    def find_all(self, role_names=None, collection_names=None, include_masked=False):
        """
        Find all roles.

        :param list role_names: List of role names to use as a filter. These values
            should be the simple role name and NOT qualified with a collection name.

        :param list collection_names: List of collection names to use as a filter.
            This filter will take precedence over the role name filter.

        :param bool include_masked: Whether or not to include roles of the same name
            that would otherwise be masked by the first-found algorithm. This has no
            effect if a value for collection_names is supplied.

        :returns: A list of Result objects.
        """
        results = []
        return results

    def filter_by_file(self, results, relative_file_names):
        """
        Filter a list of results by existence of one or more supplied files.

        :param list results: A list of Result objects to filter.

        :param list relative_file_names: A list of file names used to filter
            the results. E.g. ['meta/main.yml', 'meta/main.yaml']

        :returns: A filtered list of Result objects.
        """
        filtered_results = []
        return filtered_results

    # ========================================================================
    # Private API
    # ========================================================================

    class Result(object):
        """
        Class used as the result of all AnsibleRoleFinder API calls.

        This is a nested class because it is useless outside the context of an
        AnsibleRoleFinder object and makes the association between the classes
        clear.
        """

        def __init__(self, role_name, role_path, collection_name=None, masked=False):
            if AnsibleCollectionRef.is_valid_fqcr(role_name):
                raise Exception("Role name should not contain FQCN")

            # Remove any path information that may have been given with the role name.
            self.role_name = os.path.basename(role_name)

            self.role_path = role_path
            self.collection_name = collection_name
            self.masked = masked

        def __repr__(self):
            return "%s, masked: %s" % (self.role_path, self.masked)
