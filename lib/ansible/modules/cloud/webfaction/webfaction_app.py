#!/usr/bin/python
#
# (c) Quentin Stafford-Fraser 2015, with contributions gratefully acknowledged from:
#     * Andy Baker
#     * Federico Tarantini
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Create a Webfaction application using Ansible and the Webfaction API
#
# Valid application types can be found by looking here:
# http://docs.webfaction.com/xmlrpc-api/apps.html#application-types

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: webfaction_app
short_description: Add or remove applications on a Webfaction host
description:
    - Add or remove applications on a Webfaction host.  Further documentation at http://github.com/quentinsf/ansible-webfaction.
author: Quentin Stafford-Fraser (@quentinsf)
version_added: "2.0"
notes:
    - >
      You can run playbooks that use this on a local machine, or on a Webfaction host, or elsewhere, since the scripts use the remote webfaction API.
      The location is not important. However, running them on multiple hosts I(simultaneously) is best avoided. If you don't specify I(localhost) as
      your host, you may want to add C(serial: 1) to the plays.
    - See `the webfaction API <http://docs.webfaction.com/xmlrpc-api/>`_ for more info.

options:
    name:
        description:
            - The name of the application
        required: true

    state:
        description:
            - Whether the application should exist
        required: false
        choices: ['present', 'absent']
        default: "present"

    type:
        description:
            - The type of application to create. See the Webfaction docs at http://docs.webfaction.com/xmlrpc-api/apps.html for a list.
        required: true

    autostart:
        description:
            - Whether the app should restart with an autostart.cgi script
        required: false
        default: "no"

    extra_info:
        description:
            - Any extra parameters required by the app
        required: false
        default: null

    port_open:
        description:
            - IF the port should be opened
        required: false
        default: false

    login_name:
        description:
            - The webfaction account to use
        required: true

    login_password:
        description:
            - The webfaction password to use
        required: true

    machine:
        description:
            - The machine name to use (optional for accounts with only one machine)
        required: false

'''

EXAMPLES = '''
  - name: Create a test app
    webfaction_app:
      name="my_wsgi_app1"
      state=present
      type=mod_wsgi35-python27
      login_name={{webfaction_user}}
      login_password={{webfaction_passwd}}
      machine={{webfaction_machine}}
'''

import xmlrpclib

from ansible.module_utils.basic import AnsibleModule


webfaction = xmlrpclib.ServerProxy('https://api.webfaction.com/')


def main():

    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            state = dict(required=False, choices=['present', 'absent'], default='present'),
            type = dict(required=True),
            autostart = dict(required=False, type='bool', default=False),
            extra_info = dict(required=False, default=""),
            port_open = dict(required=False, type='bool', default=False),
            login_name = dict(required=True),
            login_password = dict(required=True, no_log=True),
            machine = dict(required=False, default=False),
        ),
        supports_check_mode=True
    )
    app_name  = module.params['name']
    app_type = module.params['type']
    app_state = module.params['state']

    if module.params['machine']:
        session_id, account = webfaction.login(
            module.params['login_name'],
            module.params['login_password'],
            module.params['machine']
        )
    else:
        session_id, account = webfaction.login(
            module.params['login_name'],
            module.params['login_password']
        )

    app_list = webfaction.list_apps(session_id)
    app_map = dict([(i['name'], i) for i in app_list])
    existing_app = app_map.get(app_name)

    result = {}

    # Here's where the real stuff happens

    if app_state == 'present':

        # Does an app with this name already exist?
        if existing_app:
            if existing_app['type'] != app_type:
                module.fail_json(msg="App already exists with different type. Please fix by hand.")

            # If it exists with the right type, we don't change it
            # Should check other parameters.
            module.exit_json(
                changed = False,
            )

        if not module.check_mode:
            # If this isn't a dry run, create the app
            result.update(
                webfaction.create_app(
                    session_id, app_name, app_type,
                    module.boolean(module.params['autostart']),
                    module.params['extra_info'],
                    module.boolean(module.params['port_open'])
                )
            )

    elif app_state == 'absent':

        # If the app's already not there, nothing changed.
        if not existing_app:
            module.exit_json(
                changed = False,
            )

        if not module.check_mode:
            # If this isn't a dry run, delete the app
            result.update(
                webfaction.delete_app(session_id, app_name)
            )

    else:
        module.fail_json(msg="Unknown state specified: {}".format(app_state))


    module.exit_json(
        changed = True,
        result = result
    )


if __name__ == '__main__':
    main()
