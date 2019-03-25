#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_router
short_description: Manages routers on Apache CloudStack based clouds.
description:
    - Start, restart, stop and destroy routers.
    - I(state=present) is not able to create routers, use M(cs_network) instead.
version_added: '2.2'
author: René Moser (@resmo)
options:
  name:
    description:
      - Name of the router.
    type: str
    required: true
  service_offering:
    description:
      - Name or id of the service offering of the router.
    type: str
  domain:
    description:
      - Domain the router is related to.
    type: str
  account:
    description:
      - Account the router is related to.
    type: str
  project:
    description:
      - Name of the project the router is related to.
    type: str
  zone:
    description:
      - Name of the zone the router is deployed in.
      - If not set, all zones are used.
    type: str
    version_added: '2.4'
  state:
    description:
      - State of the router.
    type: str
    default: present
    choices: [ present, absent, started, stopped, restarted ]
  poll_async:
    description:
      - Poll async jobs until job has finished.
    default: yes
    type: bool
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure the router has the desired service offering, no matter if
# the router is running or not.
- name: Present router
  cs_router:
    name: r-40-VM
    service_offering: System Offering for Software Router
  delegate_to: localhost

- name: Ensure started
  cs_router:
    name: r-40-VM
    state: started
  delegate_to: localhost

# Ensure started with desired service offering.
# If the service offerings changes, router will be rebooted.
- name: Ensure started with desired service offering
  cs_router:
    name: r-40-VM
    service_offering: System Offering for Software Router
    state: started
  delegate_to: localhost

- name: Ensure stopped
  cs_router:
    name: r-40-VM
    state: stopped
  delegate_to: localhost

- name: Remove a router
  cs_router:
    name: r-40-VM
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the router.
  returned: success
  type: str
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: Name of the router.
  returned: success
  type: str
  sample: r-40-VM
created:
  description: Date of the router was created.
  returned: success
  type: str
  sample: 2014-12-01T14:57:57+0100
template_version:
  description: Version of the system VM template.
  returned: success
  type: str
  sample: 4.5.1
requires_upgrade:
  description: Whether the router needs to be upgraded to the new template.
  returned: success
  type: bool
  sample: false
redundant_state:
  description: Redundant state of the router.
  returned: success
  type: str
  sample: UNKNOWN
role:
  description: Role of the router.
  returned: success
  type: str
  sample: VIRTUAL_ROUTER
zone:
  description: Name of zone the router is in.
  returned: success
  type: str
  sample: ch-gva-2
service_offering:
  description: Name of the service offering the router has.
  returned: success
  type: str
  sample: System Offering For Software Router
state:
  description: State of the router.
  returned: success
  type: str
  sample: Active
domain:
  description: Domain the router is related to.
  returned: success
  type: str
  sample: ROOT
account:
  description: Account the router is related to.
  returned: success
  type: str
  sample: admin
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackRouter(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackRouter, self).__init__(module)
        self.returns = {
            'serviceofferingname': 'service_offering',
            'version': 'template_version',
            'requiresupgrade': 'requires_upgrade',
            'redundantstate': 'redundant_state',
            'role': 'role'
        }
        self.router = None

    def get_service_offering_id(self):
        service_offering = self.module.params.get('service_offering')
        if not service_offering:
            return None

        args = {
            'issystem': True
        }

        service_offerings = self.query_api('listServiceOfferings', **args)
        if service_offerings:
            for s in service_offerings['serviceoffering']:
                if service_offering in [s['name'], s['id']]:
                    return s['id']
        self.module.fail_json(msg="Service offering '%s' not found" % service_offering)

    def get_router(self):
        if not self.router:
            router = self.module.params.get('name')

            args = {
                'projectid': self.get_project(key='id'),
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'listall': True,
                'fetch_list': True,
            }

            if self.module.params.get('zone'):
                args['zoneid'] = self.get_zone(key='id')

            routers = self.query_api('listRouters', **args)
            if routers:
                for r in routers:
                    if router.lower() in [r['name'].lower(), r['id']]:
                        self.router = r
                        break
        return self.router

    def start_router(self):
        router = self.get_router()
        if not router:
            self.module.fail_json(msg="Router not found")

        if router['state'].lower() != "running":
            self.result['changed'] = True

            args = {
                'id': router['id'],
            }

            if not self.module.check_mode:
                res = self.query_api('startRouter', **args)

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    router = self.poll_job(res, 'router')
        return router

    def stop_router(self):
        router = self.get_router()
        if not router:
            self.module.fail_json(msg="Router not found")

        if router['state'].lower() != "stopped":
            self.result['changed'] = True

            args = {
                'id': router['id'],
            }

            if not self.module.check_mode:
                res = self.query_api('stopRouter', **args)

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    router = self.poll_job(res, 'router')
        return router

    def reboot_router(self):
        router = self.get_router()
        if not router:
            self.module.fail_json(msg="Router not found")

        self.result['changed'] = True

        args = {
            'id': router['id'],
        }

        if not self.module.check_mode:
            res = self.query_api('rebootRouter', **args)

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                router = self.poll_job(res, 'router')
        return router

    def absent_router(self):
        router = self.get_router()
        if router:
            self.result['changed'] = True

            args = {
                'id': router['id'],
            }

            if not self.module.check_mode:
                res = self.query_api('destroyRouter', **args)

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    self.poll_job(res, 'router')
            return router

    def present_router(self):
        router = self.get_router()
        if not router:
            self.module.fail_json(msg="Router can not be created using the API, see cs_network.")

        args = {
            'id': router['id'],
            'serviceofferingid': self.get_service_offering_id(),
        }

        state = self.module.params.get('state')

        if self.has_changed(args, router):
            self.result['changed'] = True

            if not self.module.check_mode:
                current_state = router['state'].lower()

                self.stop_router()
                router = self.query_api('changeServiceForRouter', **args)

                if state in ['restarted', 'started']:
                    router = self.start_router()

                # if state=present we get to the state before the service
                # offering change.
                elif state == "present" and current_state == "running":
                    router = self.start_router()

        elif state == "started":
            router = self.start_router()

        elif state == "stopped":
            router = self.stop_router()

        elif state == "restarted":
            router = self.reboot_router()

        return router


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        service_offering=dict(),
        state=dict(choices=['present', 'started', 'stopped', 'restarted', 'absent'], default="present"),
        domain=dict(),
        account=dict(),
        project=dict(),
        zone=dict(),
        poll_async=dict(type='bool', default=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_router = AnsibleCloudStackRouter(module)

    state = module.params.get('state')
    if state in ['absent']:
        router = acs_router.absent_router()
    else:
        router = acs_router.present_router()

    result = acs_router.get_result(router)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
