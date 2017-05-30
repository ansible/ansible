#!/usr/bin/env python2

from ansible.module_utils.basic import *
import requests

headers = {'Accept': 'application/json'}


def main():
    module = AnsibleModule(
        argument_spec={
            'username': {'required': True, 'type': 'str'},
            'password': {'required': True, 'type': 'str', 'no_log': True},
            'action': {'required': True, 'type': 'str', 'choices': ['alerts_list', 'alerts_disable', 'alerts_enable']},
            'url': {'required': True, 'type': 'str'}
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
