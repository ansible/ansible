#!/usr/bin/python
# (c) Quentin Stafford-Fraser 2015
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Create Webfaction website using Ansible and the Webfaction API

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: webfaction_site
short_description: Add or remove a website on a Webfaction host
description:
    - Add or remove a website on a Webfaction host.  Further documentation at http://github.com/quentinsf/ansible-webfaction.
author: Quentin Stafford-Fraser (@quentinsf)
version_added: "2.0"
notes:
    - Sadly, you I(do) need to know your webfaction hostname for the C(host) parameter.  But at least, unlike the API, you don't need to know the IP
      address. You can use a DNS name.
    - If a site of the same name exists in the account but on a different host, the operation will exit.
    - >
      You can run playbooks that use this on a local machine, or on a Webfaction host, or elsewhere, since the scripts use the remote webfaction API.
      The location is not important. However, running them on multiple hosts I(simultaneously) is best avoided. If you don't specify I(localhost) as
      your host, you may want to add C(serial: 1) to the plays.
    - See `the webfaction API <http://docs.webfaction.com/xmlrpc-api/>`_ for more info.

options:

    name:
        description:
            - The name of the website
        required: true

    state:
        description:
            - Whether the website should exist
        required: false
        choices: ['present', 'absent']
        default: "present"

    host:
        description:
            - The webfaction host on which the site should be created.
        required: true

    https:
        description:
            - Whether or not to use HTTPS
        required: false
        choices:
            - true
            - false
        default: 'false'

    site_apps:
        description:
            - A mapping of URLs to apps
        required: false

    subdomains:
        description:
            - A list of subdomains associated with this site.
        required: false
        default: null

    login_name:
        description:
            - The webfaction account to use
        required: true

    login_password:
        description:
            - The webfaction password to use
        required: true
'''

EXAMPLES = '''
  - name: create website
    webfaction_site:
      name: testsite1
      state: present
      host: myhost.webfaction.com
      subdomains:
        - 'testsite1.my_domain.org'
      site_apps:
        - ['testapp1', '/']
      https: no
      login_name: "{{webfaction_user}}"
      login_password: "{{webfaction_passwd}}"
'''

import socket
import xmlrpclib

from ansible.module_utils.basic import AnsibleModule


webfaction = xmlrpclib.ServerProxy('https://api.webfaction.com/')


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            # You can specify an IP address or hostname.
            host=dict(required=True),
            https=dict(required=False, type='bool', default=False),
            subdomains=dict(required=False, type='list', default=[]),
            site_apps=dict(required=False, type='list', default=[]),
            login_name=dict(required=True),
            login_password=dict(required=True, no_log=True),
        ),
        supports_check_mode=True
    )
    site_name = module.params['name']
    site_state = module.params['state']
    site_host = module.params['host']
    site_ip = socket.gethostbyname(site_host)

    session_id, account = webfaction.login(
        module.params['login_name'],
        module.params['login_password']
    )

    site_list = webfaction.list_websites(session_id)
    site_map = dict([(i['name'], i) for i in site_list])
    existing_site = site_map.get(site_name)

    result = {}

    # Here's where the real stuff happens

    if site_state == 'present':

        # Does a site with this name already exist?
        if existing_site:

            # If yes, but it's on a different IP address, then fail.
            # If we wanted to allow relocation, we could add a 'relocate=true' option
            # which would get the existing IP address, delete the site there, and create it
            # at the new address.  A bit dangerous, perhaps, so for now we'll require manual
            # deletion if it's on another host.

            if existing_site['ip'] != site_ip:
                module.fail_json(msg="Website already exists with a different IP address. Please fix by hand.")

            # If it's on this host and the key parameters are the same, nothing needs to be done.

            if (existing_site['https'] == module.boolean(module.params['https'])) and \
               (set(existing_site['subdomains']) == set(module.params['subdomains'])) and \
               (dict(existing_site['website_apps']) == dict(module.params['site_apps'])):
                module.exit_json(
                    changed=False
                )

        positional_args = [
            session_id, site_name, site_ip,
            module.boolean(module.params['https']),
            module.params['subdomains'],
        ]
        for a in module.params['site_apps']:
            positional_args.append((a[0], a[1]))

        if not module.check_mode:
            # If this isn't a dry run, create or modify the site
            result.update(
                webfaction.create_website(
                    *positional_args
                ) if not existing_site else webfaction.update_website(
                    *positional_args
                )
            )

    elif site_state == 'absent':

        # If the site's already not there, nothing changed.
        if not existing_site:
            module.exit_json(
                changed=False,
            )

        if not module.check_mode:
            # If this isn't a dry run, delete the site
            result.update(
                webfaction.delete_website(session_id, site_name, site_ip)
            )

    else:
        module.fail_json(msg="Unknown state specified: {}".format(site_state))

    module.exit_json(
        changed=True,
        result=result
    )


if __name__ == '__main__':
    main()
