#!/usr/bin/python
# -*- coding: utf-8 -*-
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

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}

DOCUMENTATION = '''
---
module: datadog_dashboard
short_description: Manage Datadog dashboards
description:
    - "Manage Datadog screenboards and timeboards"
    - "Options like described on http://docs.datadoghq.com/api/"
version_added: "2.7"
author: "Fabian Krämer (@fakraemer)"
notes:
    - "Exports the remote dashboard as datadog_dashboard fact if run in check mode, see examples."
    - "Widgets are currently not validated on the client-side, have a look at http://docs.datadoghq.com/api/screenboards/#timeseries-widget or export."
    - "Overwrites remote state, since the script can not know if either local or remote config changed."
    - "Datadog trims titles longer than 80 characters, this is not prevented on the client-side."
requirements:
    - datadog
    - deepdiff
options:
    api_key:
        description:
            - Your Datadog API key
        required: true
    app_key:
        description:
            - Your Datadog app key
        required: true
    id:
        description:
            - "Your Datadog timeboard or screenboard id, extract from the URI: /dash/<id> or /screen/<id>"
        required: false
        default: null
    title:
        description:
            - The title of your timeboard. Note that this is not required for check mode (export)
        required: false
        default: null
    board_title:
        description:
            - The title of your screenboard. Note that this is not required for check mode (export)
        required: false
        default: null
    description:
        description:
            - The description of your dashboard. Note that this is only required for timeboards, as well as not required for check mode (export)
        required: false
        default: null
    graphs:
        description:
            - The graphs of your dashboard. Note that this indicates that you're using timeboards. Again, this is not required for check mode (export)
        required: false
        default: null
    widgets:
        description:
            - The widgets of your dashboard. Note that this indicates that you're using screenboards. Again, this is not required for check mode (export)
        required: false
        default: null
    template_variables:
        description:
            - The template variables of your dashboard. Again, this is not required for check mode (export)
        required: false
        default: null
    width:
        description:
            - The width of your screenboard
        required: false
        default: null
    height:
        description:
            - The height of your screenboard
        required: false
        default: null
'''

EXAMPLES = '''
# Export a dashboard to file, extract the id from the URI: /dash/<id> or /screen/<id>.
# Run the playbook with -C (check mode), otherwise the module will assume you want to create a dashboard (and will fail due to lack of configuration).
# You can amend your config with the what has been written to the copy file.
- datadog_dashboard:
    api_key: "{{ datadog_api_key }}"
    app_key: "{{ datadog_app_key }}"
    id: 104320
- copy: content="{{ datadog_dashboard | to_nice_yaml }}" dest=/path/to/file
  always_run: yes

# Create a screenboard, extract the id from the response and add it to the config in order to update on future runs.
- datadog_dashboard:
    api_key: "9775a026f1ca7d1c6c5af9d94d9595a4"
    app_key: "87ce4a24b5553d2e482ea8a8500e71b8ad4554ff"
    board_title: hello world
    height: 80
    widgets:
    -   auto_refresh: false
        bgcolor: yellow
        board_id: 67387
        font_size: '100'
        height: 19
        html: hello world
        refresh_every: 30000
        text_align: center
        tick: true
        tick_edge: left
        tick_pos: 50%
        title: true
        title_align: left
        title_size: 16
        title_text: ''
        type: note
        width: 57
        x: 31
        y: 14
    width: 100%
- copy: content="{{ datadog_dashboard | to_nice_yaml }}" dest=/path/to/file

# Update a screenboard.
- datadog_dashboard:
    api_key: "9775a026f1ca7d1c6c5af9d94d9595a4"
    app_key: "87ce4a24b5553d2e482ea8a8500e71b8ad4554ff"
    id: 67387
    board_title: hello world
    height: 80
    widgets:
    -   auto_refresh: false
        bgcolor: yellow
        board_id: 67387
        font_size: '100'
        height: 19
        html: hello world
        refresh_every: 30000
        text_align: center
        tick: true
        tick_edge: left
        tick_pos: 50%
        title: true
        title_align: left
        title_size: 16
        title_text: ''
        type: note
        width: 57
        x: 31
        y: 14
    width: 100%

# Update a timeboard.
- datadog_dashboard:
    api_key: "9775a026f1ca7d1c6c5af9d94d9595a4"
    app_key: "87ce4a24b5553d2e482ea8a8500e71b8ad4554ff"
    id: 105734
    description: shows the system load
    graphs:
    -   definition:
            requests:
            -   conditional_formats: []
                q: avg:system.load.1{*}
                type: line
            viz: timeseries
        title: Avg of system.load.1 over *
    title: system load
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from copy import deepcopy
from functools import partial

IMPORT_ERROR = None

try:
    from datadog import initialize, api
except ImportError:
    IMPORT_ERROR = '"datadog" lib required for this module'

try:
    from deepdiff import DeepDiff
except ImportError:
    IMPORT_ERROR = '"deepdiff" lib required for this module'

__metaclass__ = type


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(required=True),
            app_key=dict(required=True),
            id=dict(),
            title=dict(),
            board_title=dict(),
            description=dict(),
            graphs=dict(type='list'),
            widgets=dict(type='list'),
            template_variables=dict(type='list'),
            height=dict(),
            width=dict()
        ),
        supports_check_mode=True
    )

    if IMPORT_ERROR is not None:
        module.fail_json(msg=IMPORT_ERROR)

    options = {
        'api_key': module.params['api_key'],
        'app_key': module.params['app_key']
    }

    initialize(**options)

    did = module.params.get('id', None)

    # don't need additional params for check, just retrieve the remote state
    if did is not None:
        current, patch = _diff_dashboard(module)
        print("diff %s" % patch)
        if len(patch) == 0:
            module.exit_json(changed=False, msg="dashboard {0} did not change".format(did))
        elif module.check_mode:
            module.exit_json(changed=True, msg="dashboard {0} changed".format(did), ansible_facts={'datadog_dashboard': current})

    # check timeboard and screenshot specific params
    _run_dashboard_func(module, partial(_check_timeboard_params, module), partial(_check_screenboard_params, module))

    # only run if we're not in check mode, if an id was set the dashboard will have been already compared to the remote state
    if not module.check_mode:
        if did is None:
            did = _create_dashboard(module)
            module.exit_json(changed=True, msg="dashboard {0} created".format(did))
        else:
            _update_dashboard(module)
            module.exit_json(changed=True, msg="dashboard {0} updated".format(did))


def _check_timeboard_params(module, graphs):
    _return_dict_value_or_fail(module, module.params, 'title')
    _return_dict_value_or_fail(module, module.params, 'description')
    for idx, graph in enumerate(graphs):
        def check(key):
            _return_dict_value_or_fail(module, graph, key, 'graphs[{0}] is missing required arguments: {1}'.format(idx, key))
        check('title')
        check('definition')


def _check_screenboard_params(module, widgets):
    _return_dict_value_or_fail(module, module.params, 'board_title')
    for idx, widget in enumerate(widgets):
        def check(key):
            _return_dict_value_or_fail(module, widget, key, 'widgets[{0}] is missing required arguments: {1}'.format(idx, key))
        check('type')
        check('x')
        check('y')
        check('width')
        check('height')


def _exists_and_is_not_none(dic, key):
    return key in dic and dic[key] is not None


def _return_dict_value_or_fail(module, dic, key, msg=None):
    if _exists_and_is_not_none(dic, key):
        return dic[key]
    if msg is None:
        return module.fail_json(msg='missing required arguments: ' + key)
    else:
        return module.fail_json(msg=msg)


def _deepcopy_if_present(source, target, key):
    if _exists_and_is_not_none(source, key):
        target[key] = deepcopy(source[key])


def _managed_view(dashboard):
    view = {}
    copy = partial(_deepcopy_if_present, dashboard, view)
    # both
    copy('description')
    copy('template_variables')
    # timeboard
    copy('title')
    copy('graphs')
    # screenboard
    copy('board_title')
    copy('widgets')
    copy('width')
    copy('height')
    return view


def _run_dashboard_func(module, timeboard_func, screenboard_func, none_func=None):
    graphs = _exists_and_is_not_none(module.params, 'graphs')
    widgets = _exists_and_is_not_none(module.params, 'widgets')
    if graphs and widgets:
        module.fail_json(msg='exclusive arguments: either provide graphs or widgets, not both')
    elif graphs:
        return timeboard_func(module.params['graphs'])
    elif widgets:
        return screenboard_func(module.params['widgets'])
    if none_func is None:
        return module.fail_json(msg='missing required arguments: either provide graphs or widgets, run with check mode (-C) to retrieve the remote state')
    else:
        return none_func()


def _explode_timeboard_response(response):
    if 'dash' in response:
        return response['dash']
    return response


def _get_dashboard_response(module, timeboard_api_call, screenboard_api_call, none_func=None):
    response = _run_dashboard_func(module, lambda _: _explode_timeboard_response(timeboard_api_call()), lambda _: screenboard_api_call(),
                                   None if none_func is None else lambda: _explode_timeboard_response(none_func()))
    if 'errors' in response:
        module.fail_json(msg=str(response['errors']))
    return response


def _diff_dashboard(module):
    did = module.params['id']

    # special case to support migrations, try to hit both APIs in order to identify the type
    def either():
        response = api.Timeboard.get(did)
        errors = []
        if 'errors' in response:
            errors = response['errors']
            response = api.Screenboard.get(did)
        if 'errors' in response:
            errors += response['errors']
            return {'errors': errors}
        return response

    current = _managed_view(_get_dashboard_response(module, lambda: api.Timeboard.get(did), lambda: api.Screenboard.get(did), either))
    desired = _managed_view(module.params)
    diff = DeepDiff(current, desired)
    return current, diff


def _create_dashboard(module):
    desired = _managed_view(module.params)
    return _get_dashboard_response(module, lambda: api.Timeboard.create(**desired), lambda: api.Screenboard.create(**desired))['id']


def _update_dashboard(module):
    did = module.params['id']
    desired = _managed_view(module.params)
    _get_dashboard_response(module, lambda: api.Timeboard.update(did, **desired), lambda: api.Screenboard.update(did, **desired))

if __name__ == '__main__':
    main()
