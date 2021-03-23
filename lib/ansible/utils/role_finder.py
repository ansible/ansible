# (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.constants import config
from ansible.parsing.dataloader import path_exists
from ansible.template import Templar
from ansible.utils.collection_loader import AnsibleCollectionRef
from ansible.utils.collection_loader._collection_finder import _get_collection_role_path
from ansible.utils.path import unfrackpath


class AnsibleRoleFinder(object):
    """
    Class used to locate the path to any available roles.

    TODO:
      - This would replace code in `ansible-doc` and `ansible-galaxy`. Maybe plugins?
      - API to filter based on file existence (e.g. meta/main.yml for a-g).
      - API to show masked roles
      - API to show only first match
    """

    def __init__(self, playbook_basedir, role_basedir=None, templar=None):
        """
        Initialize a new RoleFinder object.

        :param str playbook_basedir: Path to the playbook base directory.
        :param str role_basedir: Path to a relative role base directory.
        :param Templar templar: A Templar object used for expanding templated paths.

        The search path order for standard (i.e., non-collection-based) roles
        is identified and set here. That path order should be:
           - 'roles' subdirectory of playbook base directory
           - configured roles path (DEFAULT_ROLES_PATH)
           - relative role base directory (if any) to find dependent roles
           - playbook base directory itself
        """
        self._standard_search_paths = []
        self._standard_search_paths.append(os.path.join(playbook_basedir, u'roles'))
        self._standard_search_paths.extend(config.get_config_value('DEFAULT_ROLES_PATH'))
        if role_basedir:
            self._standard_search_paths.append(role_basedir)
        self._standard_search_paths.append(playbook_basedir)

        self._templar = self.set_templar(templar)

    # ========================================================================
    # Private API
    #
    # WARNING: Do not access any part of the private API from outside of this
    #    class. Seriously. I'm not kidding. No, really, just don't.
    # ========================================================================

    # ========================================================================
    # Public API
    # ========================================================================

    @property
    def standard_role_search_paths(self):
        return self._standard_search_paths

    def set_templar(self, templar):
        """
        Set a new Templar object to use when expanding templated paths.

        Set the value to None to remove any existing templating object and
        avoid templating operations.

        :param Templar templar: A configured templating object.
        """
        if templar and not isinstance(templar, Templar):
            raise TypeError("templar must be of type Templar")
        self._templar = templar

    def find_first(self, role_name, collection_names=None):
        """
        Find the path to the first role found with the given name.

        :param str role_name: Name of the role to find. This may be either a
            simple role name (e.g. myrole), or qualified with a collection name
            (e.g. community.general.myrole).
        :param list collection_names: A list of fully qualified collection names to search.

        :returns: Expanded path to the role, or None if not found.
        """

        # Search collection-based roles first if a collection context is given.
        path = None
        if collection_names or AnsibleCollectionRef.is_valid_fqcr(role_name):
            (simple_role_name, path, collection_name) = _get_collection_role_path(role_name, collection_names)

        if path:
            return path

        for path in self.standard_role_search_paths:
            if self._templar:
                path = self._templar.template(path)
            role_path = unfrackpath(os.path.join(path, role_name))
            if path_exists(role_path):
                return role_path

        return None

    def find_all(self):
        pass
