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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.errors import AnsibleParserError, AnsibleError
from ansible.module_utils.six import iteritems
from ansible.parsing.splitter import split_args, parse_kv
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject, AnsibleMapping
from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.conditional import Conditional
from ansible.playbook.taggable import Taggable
from ansible.template import Templar


class PlaybookInclude(Base, Conditional, Taggable):

    _name = FieldAttribute(isa='string')
    _import_playbook = FieldAttribute(isa='string')
    _vars = FieldAttribute(isa='dict', default=dict())

    @staticmethod
    def load(data, basedir, variable_manager=None, loader=None):
        return PlaybookInclude().load_data(ds=data, basedir=basedir, variable_manager=variable_manager, loader=loader)

    def load_data(self, ds, basedir, variable_manager=None, loader=None):
        '''
        Overrides the base load_data(), as we're actually going to return a new
        Playbook() object rather than a PlaybookInclude object
        '''

        # import here to avoid a dependency loop
        from ansible.playbook import Playbook
        from ansible.playbook.play import Play

        # first, we use the original parent method to correctly load the object
        # via the load_data/preprocess_data system we normally use for other
        # playbook objects
        new_obj = super(PlaybookInclude, self).load_data(ds, variable_manager, loader)

        all_vars = self.vars.copy()
        if variable_manager:
            all_vars.update(variable_manager.get_vars())

        templar = Templar(loader=loader, variables=all_vars)

        # then we use the object to load a Playbook
        pb = Playbook(loader=loader)

        file_name = templar.template(new_obj.import_playbook)
        if not os.path.isabs(file_name):
            file_name = os.path.join(basedir, file_name)

        pb._load_playbook_data(file_name=file_name, variable_manager=variable_manager)

        # finally, update each loaded playbook entry with any variables specified
        # on the included playbook and/or any tags which may have been set
        for entry in pb._entries:

            # conditional includes on a playbook need a marker to skip gathering
            if new_obj.when and isinstance(entry, Play):
                entry._included_conditional = new_obj.when[:]

            temp_vars = entry.vars.copy()
            temp_vars.update(new_obj.vars)
            param_tags = temp_vars.pop('tags', None)
            if param_tags is not None:
                entry.tags.extend(param_tags.split(','))
            entry.vars = temp_vars
            entry.tags = list(set(entry.tags).union(new_obj.tags))
            if entry._included_path is None:
                entry._included_path = os.path.dirname(file_name)

            # Check to see if we need to forward the conditionals on to the included
            # plays. If so, we can take a shortcut here and simply prepend them to
            # those attached to each block (if any)
            if new_obj.when:
                for task_block in (entry.pre_tasks + entry.roles + entry.tasks + entry.post_tasks):
                    task_block._attributes['when'] = new_obj.when[:] + task_block.when[:]

        return pb

    def preprocess_data(self, ds):
        '''
        Regorganizes the data for a PlaybookInclude datastructure to line
        up with what we expect the proper attributes to be
        '''

        assert isinstance(ds, dict), 'ds (%s) should be a dict but was a %s' % (ds, type(ds))

        # the new, cleaned datastructure, which will have legacy
        # items reduced to a standard structure
        new_ds = AnsibleMapping()
        if isinstance(ds, AnsibleBaseYAMLObject):
            new_ds.ansible_pos = ds.ansible_pos

        for (k, v) in iteritems(ds):
            if k in ('include', 'import_playbook'):
                self._preprocess_import(ds, new_ds, k, v)
            else:
                # some basic error checking, to make sure vars are properly
                # formatted and do not conflict with k=v parameters
                if k == 'vars':
                    if 'vars' in new_ds:
                        raise AnsibleParserError("import_playbook parameters cannot be mixed with 'vars' entries for import statements", obj=ds)
                    elif not isinstance(v, dict):
                        raise AnsibleParserError("vars for import_playbook statements must be specified as a dictionary", obj=ds)
                new_ds[k] = v

        return super(PlaybookInclude, self).preprocess_data(new_ds)

    def _preprocess_import(self, ds, new_ds, k, v):
        '''
        Splits the playbook import line up into filename and parameters
        '''

        if v is None:
            raise AnsibleParserError("playbook import parameter is missing", obj=ds)

        # The import_playbook line must include at least one item, which is the filename
        # to import. Anything after that should be regarded as a parameter to the import
        items = split_args(v)
        if len(items) == 0:
            raise AnsibleParserError("import_playbook statements must specify the file name to import", obj=ds)
        else:
            new_ds['import_playbook'] = items[0]
            if len(items) > 1:
                # rejoin the parameter portion of the arguments and
                # then use parse_kv() to get a dict of params back
                params = parse_kv(" ".join(items[1:]))
                if 'tags' in params:
                    new_ds['tags'] = params.pop('tags')
                if 'vars' in new_ds:
                    raise AnsibleParserError("import_playbook parameters cannot be mixed with 'vars' entries for import statements", obj=ds)
                new_ds['vars'] = params
