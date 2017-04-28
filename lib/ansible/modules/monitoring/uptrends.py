#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This software may be freely redistributed under the terms of the GNU
# general public license version 2 or any later version.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: uptrends
short_description: Lists, enables or disables website monitoring on Uptrends
description:
  - The M(uptrends) module can list, enable or disable website monitoring on Uptrends
  - You have to specify username, password, action and URL of the website
options:
  username:
    description: Uptrends username
    required: true
  password:
    description: Uptrends password
    required: true
  action:
    description: Action to take
    choices: ['alerts_list', 'alerts_disable', 'alerts_enable']
    required: true
  url:
    description: URL of the service
    required: false
version_added: 2.4
author: "Julien Gormotte (@gormux)"
'''

EXAMPLES = '''
uptrends:
  username: user@example.com
  password: cmlaelkfhalfga
  action: alerts_disable
  url: www.example.com mail.example.com

uptrends:
  username: user@example.com
  password: cmlaelkfhalfga
  action: alerts_enable
  url: www.example.com mail.example.com
'''

from ansible.module_utils.basic import AnsibleModule
import requests

headers = {'Accept': 'application/json'}


def main():
    module = AnsibleModule(
        argument_spec={
            'username': {'required': True, 'type': 'str'},
            'password': {'required': True, 'type': 'str', 'no_log': True},
            'action': {'required': True, 'type': 'str', 'choices': ['alerts_list', 'alerts_disable', 'alerts_enable']},
            'url': {'required': False, 'type': 'str'}
        }, supports_check_mode=False
    )

    uptrends_url = 'https://api.uptrends.com/v3/probes/'

    args = module.params

    if args['action'] == 'alerts_list':
        r = requests.get(uptrends_url, auth=(args['username'], args['password']), headers=headers)
        urls = [re.sub(r'^(https?://)([^/]*)(.*)$', r'\2', e['URL']) for e in r.json()]

        if not args['url']:
            data = urls
        else:
            data = []
            for url in urls:
                if args['url'] in url:
                    data.append(url)

        module.exit_json(changed=False, data=data)
        module.fail_json(msg="Something fatal happened")

    if args['action'] == 'alerts_disable':
        if not args['url']:
            module.exit_json(changed=False, msg='URL is mandatory for alerts_disable')

        r = requests.get(uptrends_url, auth=(args['username'], args['password']), headers=headers)
        guids = [e['Guid'] for e in r.json() if args['url'] in e['URL']]
        changed = []
        failed = []

        for guid in guids:
            s = requests.post(uptrends_url + guid, auth=(args['username'], args['password']), headers=headers, data={u'GenerateAlert': 'False'})
            if s.status_code == 201:
                changed.append(s.json()['URL'])
            else:
                failed.append(s.json()['URL'])

        if len(failed) == 0 and len(changed) == 0:
            module.exit_json(changed=False, msg='Nothing to change')
        elif len(changed) == 0 and len(failed) > 0:
            module.fail_json(changed=False, msg='Could not change anything')
        elif len(failed) == 0 and len(changed) > 0:
            module.exit_json(changed=True, urls_disabled=changed)
        else:
            module.fail_json(changed=True, msg='Some elements could not be changed', success=changed, failures=failed)

    if args['action'] == 'alerts_enable':
        if not args['url']:
            module.exit_json(changed=False, msg='URL is mandatory for alerts_enable')

        r = requests.get(uptrends_url, auth=(args['username'], args['password']), headers=headers)
        guids = [e['Guid'] for e in r.json() if args['url'] in e['URL']]
        changed = []
        failed = []

        for guid in guids:
            s = requests.post(uptrends_url + guid, auth=(args['username'], args['password']), headers=headers, data={u'GenerateAlert': 'True'})
            if s.status_code == 201:
                changed.append(s.json()['URL'])
            else:
                failed.append(s.json()['URL'])

        if len(failed) == 0 and len(changed) == 0:
            module.exit_json(changed=False, msg='Nothing to change')
        elif len(changed) == 0 and len(failed) > 0:
            module.fail_json(changed=False, msg='Could not change anything')
        elif len(failed) == 0 and len(changed) > 0:
            module.exit_json(changed=True, urls_enabled=changed)
        else:
            module.fail_json(changed=True, msg='Some elements could not be changed', success=changed, failures=failed)

if __name__ == '__main__':
    main()
