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

from ansible.parsing.splitter import split_args, parse_kv
from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject, AnsibleMapping
from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.conditional import Conditional
from ansible.playbook.taggable import Taggable
from ansible.errors import AnsibleParserError

class PlaybookInclude(Base):

    _name      = FieldAttribute(isa='string')
    _include   = FieldAttribute(isa='string')
    _vars      = FieldAttribute(isa='dict', default=dict())

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

        # first, we use the original parent method to correctly load the object
        # via the load_data/preprocess_data system we normally use for other
        # playbook objects
        new_obj = super(PlaybookInclude, self).load_data(ds, variable_manager, loader)

        # then we use the object to load a Playbook
        pb = Playbook(loader=loader)

        file_name = new_obj.include
        if not os.path.isabs(file_name):
            file_name = os.path.join(basedir, file_name)

        pb._load_playbook_data(file_name=file_name, variable_manager=variable_manager)

        # finally, playbook includes can specify a list of variables, which are simply
        # used to update the vars of each play in the playbook
        for entry in pb._entries:
            entry.vars.update(new_obj.vars)

        return pb

    def preprocess_data(self, ds):
        '''
        Regorganizes the data for a PlaybookInclude datastructure to line
        up with what we expect the proper attributes to be
        '''

        assert isinstance(ds, dict)

        # the new, cleaned datastructure, which will have legacy
        # items reduced to a standard structure
        new_ds = AnsibleMapping()
        if isinstance(ds, AnsibleBaseYAMLObject):
            new_ds.ansible_pos = ds.ansible_pos

        for (k,v) in ds.iteritems():
            if k == 'include':
                self._preprocess_include(ds, new_ds, k, v)
            else:
                # some basic error checking, to make sure vars are properly
                # formatted and do not conflict with k=v parameters
                # FIXME: we could merge these instead, but controlling the order
                #        in which they're encountered could be difficult
                if k == 'vars':
                    if 'vars' in new_ds:
                        raise AnsibleParserError("include parameters cannot be mixed with 'vars' entries for include statements", obj=ds)
                    elif not isinstance(v, dict):
                        raise AnsibleParserError("vars for include statements must be specified as a dictionary", obj=ds)
                new_ds[k] = v

        return super(PlaybookInclude, self).preprocess_data(new_ds)

    def _preprocess_include(self, ds, new_ds, k, v):
        '''
        Splits the include line up into filename and parameters
        '''

        # The include line must include at least one item, which is the filename
        # to include. Anything after that should be regarded as a parameter to the include
        items = split_args(v)
        if len(items) == 0:
            raise AnsibleParserError("include statements must specify the file name to include", obj=ds)
        else:
            # FIXME/TODO: validate that items[0] is a file, which also
            #             exists and is readable
            new_ds['include'] = items[0]
            if len(items) > 1:
                # rejoin the parameter portion of the arguments and
                # then use parse_kv() to get a dict of params back
                params = parse_kv(" ".join(items[1:]))
                if 'vars' in new_ds:
                    # FIXME: see fixme above regarding merging vars
                    raise AnsibleParserError("include parameters cannot be mixed with 'vars' entries for include statements", obj=ds)
                new_ds['vars'] = params

