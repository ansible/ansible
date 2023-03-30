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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible import constants as C
from ansible.errors import AnsibleParserError, AnsibleUndefinedVariable, AnsibleFileNotFound, AnsibleAssertionError
from ansible.module_utils._text import to_native
from ansible.module_utils.six import string_types
from ansible.parsing.mod_args import ModuleArgsParser
from ansible.utils.display import Display

display = Display()


def load_list_of_blocks(ds, play, parent_block=None, role=None, task_include=None, use_handlers=False, variable_manager=None, loader=None):
    '''
    Given a list of mixed task/block data (parsed from YAML),
    return a list of Block() objects, where implicit blocks
    are created for each bare Task.
    '''

    # we import here to prevent a circular dependency with imports
    from ansible.playbook.block import Block

    if not isinstance(ds, (list, type(None))):
        raise AnsibleAssertionError('%s should be a list or None but is %s' % (ds, type(ds)))

    block_list = []
    if ds:
        count = iter(range(len(ds)))
        for i in count:
            block_ds = ds[i]
            # Implicit blocks are created by bare tasks listed in a play without
            # an explicit block statement. If we have two implicit blocks in a row,
            # squash them down to a single block to save processing time later.
            implicit_blocks = []
            while block_ds is not None and not Block.is_block(block_ds):
                implicit_blocks.append(block_ds)
                i += 1
                # Advance the iterator, so we don't repeat
                next(count, None)
                try:
                    block_ds = ds[i]
                except IndexError:
                    block_ds = None

            # Loop both implicit blocks and block_ds as block_ds is the next in the list
            for b in (implicit_blocks, block_ds):
                if b:
                    block_list.append(
                        Block.load(
                            b,
                            play=play,
                            parent_block=parent_block,
                            role=role,
                            task_include=task_include,
                            use_handlers=use_handlers,
                            variable_manager=variable_manager,
                            loader=loader,
                        )
                    )

    return block_list


def load_list_of_tasks(ds, play, block=None, role=None, task_include=None, use_handlers=False, variable_manager=None, loader=None):
    '''
    Given a list of task datastructures (parsed from YAML),
    return a list of Task() or TaskInclude() objects.
    '''

    # we import here to prevent a circular dependency with imports
    from ansible.playbook.block import Block
    from ansible.playbook.handler import Handler
    from ansible.playbook.task import Task
    from ansible.playbook.task_include import TaskInclude
    from ansible.playbook.role_include import IncludeRole
    from ansible.playbook.handler_task_include import HandlerTaskInclude
    from ansible.template import Templar
    from ansible.utils.plugin_docs import get_versioned_doclink

    if not isinstance(ds, list):
        raise AnsibleAssertionError('The ds (%s) should be a list but was a %s' % (ds, type(ds)))

    task_list = []
    for task_ds in ds:
        if not isinstance(task_ds, dict):
            raise AnsibleAssertionError('The ds (%s) should be a dict but was a %s' % (ds, type(ds)))

        if 'block' in task_ds:
            if use_handlers:
                raise AnsibleParserError("Using a block as a handler is not supported.", obj=task_ds)
            t = Block.load(
                task_ds,
                play=play,
                parent_block=block,
                role=role,
                task_include=task_include,
                use_handlers=use_handlers,
                variable_manager=variable_manager,
                loader=loader,
            )
            task_list.append(t)
        else:
            args_parser = ModuleArgsParser(task_ds)
            try:
                (action, args, delegate_to) = args_parser.parse(skip_action_validation=True)
            except AnsibleParserError as e:
                # if the raises exception was created with obj=ds args, then it includes the detail
                # so we dont need to add it so we can just re raise.
                if e.obj:
                    raise
                # But if it wasn't, we can add the yaml object now to get more detail
                raise AnsibleParserError(to_native(e), obj=task_ds, orig_exc=e)

            if action in C._ACTION_ALL_INCLUDE_IMPORT_TASKS:

                if use_handlers:
                    include_class = HandlerTaskInclude
                else:
                    include_class = TaskInclude

                t = include_class.load(
                    task_ds,
                    block=block,
                    role=role,
                    task_include=None,
                    variable_manager=variable_manager,
                    loader=loader
                )

                all_vars = variable_manager.get_vars(play=play, task=t)
                templar = Templar(loader=loader, variables=all_vars)

                # check to see if this include is dynamic or static:
                # 1. the user has set the 'static' option to false or true
                # 2. one of the appropriate config options was set
                if action in C._ACTION_INCLUDE_TASKS:
                    is_static = False
                elif action in C._ACTION_IMPORT_TASKS:
                    is_static = True
                else:
                    include_link = get_versioned_doclink('user_guide/playbooks_reuse_includes.html')
                    display.deprecated('"include" is deprecated, use include_tasks/import_tasks instead. See %s for details' % include_link, "2.16")
                    is_static = not templar.is_template(t.args['_raw_params']) and t.all_parents_static() and not t.loop

                if is_static:
                    if t.loop is not None:
                        if action in C._ACTION_IMPORT_TASKS:
                            raise AnsibleParserError("You cannot use loops on 'import_tasks' statements. You should use 'include_tasks' instead.", obj=task_ds)
                        else:
                            raise AnsibleParserError("You cannot use 'static' on an include with a loop", obj=task_ds)

                    # we set a flag to indicate this include was static
                    t.statically_loaded = True

                    # handle relative includes by walking up the list of parent include
                    # tasks and checking the relative result to see if it exists
                    parent_include = block
                    cumulative_path = None

                    found = False
                    subdir = 'tasks'
                    if use_handlers:
                        subdir = 'handlers'
                    while parent_include is not None:
                        if not isinstance(parent_include, TaskInclude):
                            parent_include = parent_include._parent
                            continue
                        try:
                            parent_include_dir = os.path.dirname(templar.template(parent_include.args.get('_raw_params')))
                        except AnsibleUndefinedVariable as e:
                            if not parent_include.statically_loaded:
                                raise AnsibleParserError(
                                    "Error when evaluating variable in dynamic parent include path: %s. "
                                    "When using static imports, the parent dynamic include cannot utilize host facts "
                                    "or variables from inventory" % parent_include.args.get('_raw_params'),
                                    obj=task_ds,
                                    suppress_extended_error=True,
                                    orig_exc=e
                                )
                            raise
                        if cumulative_path is None:
                            cumulative_path = parent_include_dir
                        elif not os.path.isabs(cumulative_path):
                            cumulative_path = os.path.join(parent_include_dir, cumulative_path)
                        include_target = templar.template(t.args['_raw_params'])
                        if t._role:
                            new_basedir = os.path.join(t._role._role_path, subdir, cumulative_path)
                            include_file = loader.path_dwim_relative(new_basedir, subdir, include_target)
                        else:
                            include_file = loader.path_dwim_relative(loader.get_basedir(), cumulative_path, include_target)

                        if os.path.exists(include_file):
                            found = True
                            break
                        else:
                            parent_include = parent_include._parent

                    if not found:
                        try:
                            include_target = templar.template(t.args['_raw_params'])
                        except AnsibleUndefinedVariable as e:
                            raise AnsibleParserError(
                                "Error when evaluating variable in import path: %s.\n\n"
                                "When using static imports, ensure that any variables used in their names are defined in vars/vars_files\n"
                                "or extra-vars passed in from the command line. Static imports cannot use variables from facts or inventory\n"
                                "sources like group or host vars." % t.args['_raw_params'],
                                obj=task_ds,
                                suppress_extended_error=True,
                                orig_exc=e)
                        if t._role:
                            include_file = loader.path_dwim_relative(t._role._role_path, subdir, include_target)
                        else:
                            include_file = loader.path_dwim(include_target)

                    data = loader.load_from_file(include_file)
                    if not data:
                        display.warning('file %s is empty and had no tasks to include' % include_file)
                        continue
                    elif not isinstance(data, list):
                        raise AnsibleParserError("included task files must contain a list of tasks", obj=data)

                    # since we can't send callbacks here, we display a message directly in
                    # the same fashion used by the on_include callback. We also do it here,
                    # because the recursive nature of helper methods means we may be loading
                    # nested includes, and we want the include order printed correctly
                    display.vv("statically imported: %s" % include_file)

                    ti_copy = t.copy(exclude_parent=True)
                    ti_copy._parent = block
                    included_blocks = load_list_of_blocks(
                        data,
                        play=play,
                        parent_block=None,
                        task_include=ti_copy,
                        role=role,
                        use_handlers=use_handlers,
                        loader=loader,
                        variable_manager=variable_manager,
                    )

                    tags = ti_copy.tags[:]

                    # now we extend the tags on each of the included blocks
                    for b in included_blocks:
                        b.tags = list(set(b.tags).union(tags))
                    # END FIXME

                    # FIXME: handlers shouldn't need this special handling, but do
                    #        right now because they don't iterate blocks correctly
                    if use_handlers:
                        for b in included_blocks:
                            task_list.extend(b.block)
                    else:
                        task_list.extend(included_blocks)
                else:
                    t.is_static = False
                    task_list.append(t)

            elif action in C._ACTION_ALL_PROPER_INCLUDE_IMPORT_ROLES:
                if use_handlers:
                    raise AnsibleParserError(f"Using '{action}' as a handler is not supported.", obj=task_ds)

                ir = IncludeRole.load(
                    task_ds,
                    block=block,
                    role=role,
                    task_include=None,
                    variable_manager=variable_manager,
                    loader=loader,
                )

                #   1. the user has set the 'static' option to false or true
                #   2. one of the appropriate config options was set
                is_static = False
                if action in C._ACTION_IMPORT_ROLE:
                    is_static = True

                if is_static:
                    if ir.loop is not None:
                        if action in C._ACTION_IMPORT_ROLE:
                            raise AnsibleParserError("You cannot use loops on 'import_role' statements. You should use 'include_role' instead.", obj=task_ds)
                        else:
                            raise AnsibleParserError("You cannot use 'static' on an include_role with a loop", obj=task_ds)

                    # we set a flag to indicate this include was static
                    ir.statically_loaded = True

                    # template the role name now, if needed
                    all_vars = variable_manager.get_vars(play=play, task=ir)
                    templar = Templar(loader=loader, variables=all_vars)
                    ir.post_validate(templar=templar)
                    ir._role_name = templar.template(ir._role_name)

                    # uses compiled list from object
                    blocks, _ = ir.get_block_list(variable_manager=variable_manager, loader=loader)
                    task_list.extend(blocks)
                else:
                    # passes task object itself for latter generation of list
                    task_list.append(ir)
            else:
                if use_handlers:
                    t = Handler.load(task_ds, block=block, role=role, task_include=task_include, variable_manager=variable_manager, loader=loader)
                else:
                    t = Task.load(task_ds, block=block, role=role, task_include=task_include, variable_manager=variable_manager, loader=loader)

                task_list.append(t)

    return task_list


def load_list_of_roles(ds, play, current_role_path=None, variable_manager=None, loader=None, collection_search_list=None):
    """
    Loads and returns a list of RoleInclude objects from the ds list of role definitions
    :param ds: list of roles to load
    :param play: calling Play object
    :param current_role_path: path of the owning role, if any
    :param variable_manager: varmgr to use for templating
    :param loader: loader to use for DS parsing/services
    :param collection_search_list: list of collections to search for unqualified role names
    :return:
    """
    # we import here to prevent a circular dependency with imports
    from ansible.playbook.role.include import RoleInclude

    if not isinstance(ds, list):
        raise AnsibleAssertionError('ds (%s) should be a list but was a %s' % (ds, type(ds)))

    roles = []
    for role_def in ds:
        i = RoleInclude.load(role_def, play=play, current_role_path=current_role_path, variable_manager=variable_manager,
                             loader=loader, collection_list=collection_search_list)
        roles.append(i)

    return roles
