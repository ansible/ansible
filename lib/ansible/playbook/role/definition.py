# (c) 2014 Michael DeHaan, <michael@ansible.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pprint

from ansible import constants as C  # noqa
from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.module_utils.six import iteritems, string_types
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject, AnsibleMapping
# from ansible.playbook.attribute import Attribute
from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.become import Become
from ansible.playbook.conditional import Conditional
from ansible.playbook.taggable import Taggable
from ansible.template import Templar
from ansible.utils.path import unfrackpath

import logging
log = logging.getLogger(__name__)

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


__all__ = ['RoleDefinition']


def role_name_to_relative_content_path(role_name):
    '''Translate a namespace.reponame.rolename to relative content path.

    ie, testing.some_repo.some_role -> testing/some_repo/roles/some_role
    '''

    content_rel_role_path = None

    # TODO: decide if something like 'geerlingguy.nginx' is sufficient
    #       ie, if there will be a short names/aliases/default resolvers
    try:
        # namespace, repo, name = role_name.split('.', 2)
        name_parts = role_name.split('.', 2)
    except (ValueError, AttributeError):
        log.debug('Could not "." split role_name "%s"',
                  role_name)
        return None

    # name_parts namespace, repo, rolename or
    #  namespace.reponame (and assume there is a also a role named 'reponame'
    #  at namespace/repo/roles/reponame. ie, old style roles with one role
    # in a repo.)
    # geerlingguy.apache -> geerlingguy/apache/roles/apache
    # geerlingguy.apache.apache -> geerlingguy/apache/roles/apache
    # testing.multi.apache -> testing/multi/roles/apache
    # testing.multi ->  testing/multi/roles/multi (if it exists)
    # WARNING: if a repo name for a multicontent repo matches a role name
    #          coincedently, this introduces an ambiquity
    # mynamespace.install.add_user -> mynamespace/install/roles/add_user
    # mynamespace.install.install -> mynamespace/install/roles/install
    # mynamespace.install -> mynamespace/install/roles/install

    if len(name_parts) < 2:
        return None

    log.debug(name_parts)

    # catches 'namespace.' (trailing dot) as well as rel path cases
    # like '../some_dir.foo.bar'
    if not all(name_parts):
        return None

    log.debug('name_parts: %s', name_parts)

    namespace = name_parts.pop(0)
    repo = name_parts.pop(0)

    name = None
    try:
        name = name_parts.pop(0)
    except IndexError:
        log.debug('role name "%s" only had two name parts (namespace="%s", repo="%s") and no role name',
                  role_name, namespace, repo)

    if name:
        content_rel_role_path = os.path.join(namespace, repo, 'roles', name)
    else:
        content_rel_role_path = os.path.join(namespace, repo, 'roles', repo)

    return content_rel_role_path


def find_role_in_content_path(role_name, loader, content_search_paths):
    '''search for role in ~/.ansible/content and return first match.

    return None if no matches'''

    # try the galaxy content paths
    # TODO: this is where a 'role spec resolver' could be plugged into.
    #       The resolver would be responsible parsing/understanding the role spec
    #       (a formatted string or a dict), and figuring out the approriate galaxy
    #       namespace, repo name, and role name.
    #
    #       The next step would be finding that role on the fs.
    #       If there are conflicts or ambiquity, the resolver would apply
    #       any rules or convention or precedence to choose the correct role.
    #       For ex, if namespace isnt provided, and 2 or more namespaces have a
    #       role that matches, the resolver would choose.
    # FIXME: mv to method, deindent, return early, etc

    log.debug('content_search_paths: %s', content_search_paths)

    content_rel_role_path = role_name_to_relative_content_path(role_name)

    log.debug('content_rel_role_path: %s', content_rel_role_path)

    # didn't parse the role_name, return None
    if not content_rel_role_path:
        return None

    # TODO: the for loop isnt needed if we really really only
    #       support one content path
    for content_search_path in content_search_paths:

        fq_role_path = os.path.join(content_search_path, content_rel_role_path)
        fq_role_path = unfrackpath(fq_role_path)

        log.debug('fq_role_path: %s', fq_role_path)

        if loader.path_exists(fq_role_path):
            log.info('FOUND:     %s at content path "%s"', role_name, fq_role_path)
            return (role_name, fq_role_path)

    return None


class RoleDefinition(Base, Become, Conditional, Taggable):

    _role = FieldAttribute(isa='string')

    def __init__(self, play=None, role_basedir=None, variable_manager=None, loader=None):

        super(RoleDefinition, self).__init__()

        self._play = play
        self._variable_manager = variable_manager
        self._loader = loader

        self._role_path = None
        self._role_basedir = role_basedir
        self._role_params = dict()

    # def __repr__(self):
    #     return 'ROLEDEF: ' + self._attributes.get('role', '<no name set>')

    @staticmethod
    def load(data, variable_manager=None, loader=None):
        raise AnsibleError("not implemented")

    def preprocess_data(self, ds):
        # role names that are simply numbers can be parsed by PyYAML
        # as integers even when quoted, so turn it into a string type
        if isinstance(ds, int):
            ds = "%s" % ds

        if not isinstance(ds, dict) and not isinstance(ds, string_types) and not isinstance(ds, AnsibleBaseYAMLObject):
            raise AnsibleAssertionError()

        if isinstance(ds, dict):
            ds = super(RoleDefinition, self).preprocess_data(ds)

        # save the original ds for use later
        self._ds = ds

        # we create a new data structure here, using the same
        # object used internally by the YAML parsing code so we
        # can preserve file:line:column information if it exists
        new_ds = AnsibleMapping()
        if isinstance(ds, AnsibleBaseYAMLObject):
            new_ds.ansible_pos = ds.ansible_pos

        # first we pull the role name out of the data structure,
        # and then use that to determine the role path (which may
        # result in a new role name, if it was a file path)
        role_name = self._load_role_name(ds)
        (role_name, role_path) = self._load_role_path(role_name)

        # next, we split the role params out from the valid role
        # attributes and update the new datastructure with that
        # result and the role name
        if isinstance(ds, dict):
            (new_role_def, role_params) = self._split_role_params(ds)
            new_ds.update(new_role_def)
            self._role_params = role_params

        # set the role name in the new ds
        new_ds['role'] = role_name

        # we store the role path internally
        self._role_path = role_path

        # and return the cleaned-up data structure
        return new_ds

    def _load_role_name(self, ds):
        '''
        Returns the role name (either the role: or name: field) from
        the role definition, or (when the role definition is a simple
        string), just that string
        '''

        if isinstance(ds, string_types):
            log.debug('role_name: %s (role ds was a string)', ds)
            return ds

        role_name = ds.get('role', ds.get('name'))
        if not role_name or not isinstance(role_name, string_types):
            raise AnsibleError('role definitions must contain a role name', obj=ds)

        # if we have the required datastructures, and if the role_name
        # contains a variable, try and template it now
        if self._variable_manager:
            all_vars = self._variable_manager.get_vars(play=self._play)
            templar = Templar(loader=self._loader, variables=all_vars)
            if templar._contains_vars(role_name):
                role_name = templar.template(role_name)

        log.info('using role_name: %s', role_name)
        log.info('role_name: %s ds:\n%s', role_name, pprint.pformat(ds))
        return role_name

    def _load_role_path(self, role_name):
        '''
        the 'role', as specified in the ds (or as a bare string), can either
        be a simple name or a full path. If it is a full path, we use the
        basename as the role name, otherwise we take the name as-given and
        append it to the default role path
        '''

        log.info('Look for:  %s', role_name)
        # log.debug('installed_role_spec: %s', installed_role_spec)

        # we always start the search for roles in the base directory of the playbook
        role_search_paths = [
            os.path.join(self._loader.get_basedir(), u'roles'),
        ]

        # also search in the configured roles path
        if C.DEFAULT_ROLES_PATH:
            role_search_paths.extend(C.DEFAULT_ROLES_PATH)

        # next, append the roles basedir, if it was set, so we can
        # search relative to that directory for dependent roles
        if self._role_basedir:
            role_search_paths.append(self._role_basedir)

        # finally as a last resort we look in the current basedir as set
        # in the loader (which should be the playbook dir itself) but without
        # the roles/ dir appended
        role_search_paths.append(self._loader.get_basedir())
        log.debug('role_search_paths: %s', role_search_paths)

        # create a templar class to template the dependency names, in
        # case they contain variables
        if self._variable_manager is not None:
            all_vars = self._variable_manager.get_vars(play=self._play)
        else:
            all_vars = dict()

        templar = Templar(loader=self._loader, variables=all_vars)
        role_name = templar.template(role_name)

        # Look for roles in the content search path (~/.ansible/content) based on dotted role
        # names.
        content_results = find_role_in_content_path(role_name, self._loader,
                                                    content_search_paths=C.DEFAULT_CONTENT_PATH)
        log.debug('content_results: %s', content_results)

        if content_results:
            log.debug('returning %s (found a role in content path for role_name=%s)',
                      repr(content_results), role_name)

            return content_results

        # now iterate through the possible paths and return the first one we find
        for path in role_search_paths:
            path = templar.template(path)

            # fq_role_name = resolve_role_name(role_name)
            role_path = unfrackpath(os.path.join(path, role_name))

            log.debug('search for role=%s in path: %s (role_path=%s)', role_name, path, role_path)
            if self._loader.path_exists(role_path):
                log.info('FOUND:     %s at role path: "%s"', role_name, role_path)

                return (role_name, role_path)

        # if not found elsewhere try to extract path from name
        role_path = unfrackpath(role_name)

        log.debug('trying role_name=%s as a path: %s ', role_name, role_path)

        if self._loader.path_exists(role_path):
            log.debug('FOUND:     %s (via relative path) at path: "%s"', role_name, role_path)

            role_name = os.path.basename(role_name)
            return (role_name, role_path)

        log.info('Failed to find the role "%s" in content paths %s', role_name, C.DEFAULT_CONTENT_PATH)
        log.info('Failed to find the role "%s" in any of the roles paths: %s',
                 role_name, ":".join(role_search_paths))

        raise AnsibleError("the role '%s' was not found in %s" % (role_name, ":".join(role_search_paths)), obj=self._ds)

    def _split_role_params(self, ds):
        '''
        Splits any random role params off from the role spec and store
        them in a dictionary of params for parsing later
        '''

        role_def = dict()
        role_params = dict()
        base_attribute_names = frozenset(self._valid_attrs.keys())
        for (key, value) in iteritems(ds):
            # use the list of FieldAttribute values to determine what is and is not
            # an extra parameter for this role (or sub-class of this role)
            # FIXME: hard-coded list of exception key names here corresponds to the
            #        connection fields in the Base class. There may need to be some
            #        other mechanism where we exclude certain kinds of field attributes,
            #        or make this list more automatic in some way so we don't have to
            #        remember to update it manually.
            if key not in base_attribute_names:
                # this key does not match a field attribute, so it must be a role param
                role_params[key] = value
            else:
                # this is a field attribute, so copy it over directly
                role_def[key] = value

        return (role_def, role_params)

    def get_role_params(self):
        return self._role_params.copy()

    def get_role_path(self):
        return self._role_path
