#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: manageiq_alert_profiles

short_description: Configuration of alert profiles for ManageIQ
extends_documentation_fragment: manageiq
version_added: '2.5'
author: Elad Alfassa (@elad661) <ealfassa@redhat.com>
description:
  - The manageiq_alert_profiles module supports adding, updating and deleting alert profiles in ManageIQ.

options:
  state:
    description:
      - absent - alert profile should not exist,
      - present - alert profile should exist,
    choices: ['absent', 'present']
    default: 'present'
  name:
    description:
      - The unique alert profile name in ManageIQ.
      - Required when state is "absent" or "present".
  resource_type:
    description:
      - The resource type for the alert profile in ManageIQ. Required when state is "present".
    choices: ['Vm', 'ContainerNode', 'MiqServer', 'Host', 'Storage', 'EmsCluster',
              'ExtManagementSystem', 'MiddlewareServer']
  alerts:
    description:
      - List of alert descriptions to assign to this profile.
      - Required if state is "present"
  notes:
    description:
      - Optional notes for this profile

'''

EXAMPLES = '''
- name: Add an alert profile to ManageIQ
  manageiq_alert_profiles:
    state: present
    name: Test profile
    resource_type: ContainerNode
    alerts:
      - Test Alert 01
      - Test Alert 02
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      validate_certs: False

- name: Delete an alert profile from ManageIQ
  manageiq_alert_profiles:
    state: absent
    name: Test profile
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      validate_certs: False
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.manageiq import ManageIQ, manageiq_argument_spec


class ManageIQAlertProfiles(object):
    """ Object to execute alert profile management operations in manageiq.
    """

    def __init__(self, manageiq):
        self.manageiq = manageiq

        self.module = self.manageiq.module
        self.api_url = self.manageiq.api_url
        self.client = self.manageiq.client
        self.url = '{api_url}/alert_definition_profiles'.format(api_url=self.api_url)

    def get_profiles(self):
        """ Get all alert profiles from ManageIQ
        """
        try:
            response = self.client.get(self.url + '?expand=alert_definitions,resources')
        except Exception as e:
            self.module.fail_json(msg="Failed to query alert profiles: {error}".format(error=e))
        return response.get('resources') or []

    def get_alerts(self, alert_descriptions):
        """ Get a list of alert hrefs from a list of alert descriptions
        """
        alerts = []
        for alert_description in alert_descriptions:
            alert = self.manageiq.find_collection_resource_or_fail("alert_definitions",
                                                                   description=alert_description)
            alerts.append(alert['href'])

        return alerts

    def add_profile(self, profile):
        """ Add a new alert profile to ManageIQ
        """
        # find all alerts to add to the profile
        # we do this first to fail early if one is missing.
        alerts = self.get_alerts(profile['alerts'])

        # build the profile dict to send to the server

        profile_dict = dict(name=profile['name'],
                            description=profile['name'],
                            mode=profile['resource_type'])
        if profile['notes']:
            profile_dict['set_data'] = dict(notes=profile['notes'])

        # send it to the server
        try:
            result = self.client.post(self.url, resource=profile_dict, action="create")
        except Exception as e:
            self.module.fail_json(msg="Creating profile failed {error}".format(error=e))

        # now that it has been created, we can assign the alerts
        self.assign_or_unassign(result['results'][0], alerts, "assign")

        msg = "Profile {name} created successfully"
        msg = msg.format(name=profile['name'])
        return dict(changed=True, msg=msg)

    def delete_profile(self, profile):
        """ Delete an alert profile from ManageIQ
        """
        try:
            self.client.post(profile['href'], action="delete")
        except Exception as e:
            self.module.fail_json(msg="Deleting profile failed: {error}".format(error=e))

        msg = "Successfully deleted profile {name}".format(name=profile['name'])
        return dict(changed=True, msg=msg)

    def get_alert_href(self, alert):
        """ Get an absolute href for an alert
        """
        return "{url}/alert_definitions/{id}".format(url=self.api_url, id=alert['id'])

    def assign_or_unassign(self, profile, resources, action):
        """ Assign or unassign alerts to profile, and validate the result.
        """
        alerts = [dict(href=href) for href in resources]

        subcollection_url = profile['href'] + '/alert_definitions'
        try:
            result = self.client.post(subcollection_url, resources=alerts, action=action)
            if len(result['results']) != len(alerts):
                msg = "Failed to {action} alerts to profile '{name}'," +\
                      "expected {expected} alerts to be {action}ed," +\
                      "but only {changed} were {action}ed"
                msg = msg.format(action=action,
                                 name=profile['name'],
                                 expected=len(alerts),
                                 changed=result['results'])
                self.module.fail_json(msg=msg)
        except Exception as e:
            msg = "Failed to {action} alerts to profile '{name}': {error}"
            msg = msg.format(action=action, name=profile['name'], error=e)
            self.module.fail_json(msg=msg)

        return result['results']

    def update_profile(self, old_profile, desired_profile):
        """ Update alert profile in ManageIQ
        """
        changed = False
        # we need to use client.get to query the alert definitions
        old_profile = self.client.get(old_profile['href'] + '?expand=alert_definitions')

        # figure out which alerts we need to assign / unassign
        # alerts listed by the user:
        desired_alerts = set(self.get_alerts(desired_profile['alerts']))

        # alert which currently exist in the profile
        if 'alert_definitions' in old_profile:
            # we use get_alert_href to have a direct href to the alert
            existing_alerts = set([self.get_alert_href(alert) for alert in old_profile['alert_definitions']])
        else:
            # no alerts in this profile
            existing_alerts = set()

        to_add = list(desired_alerts - existing_alerts)
        to_remove = list(existing_alerts - desired_alerts)

        # assign / unassign the alerts, if needed

        if to_remove:
            self.assign_or_unassign(old_profile, to_remove, "unassign")
            changed = True
        if to_add:
            self.assign_or_unassign(old_profile, to_add, "assign")
            changed = True

        # update other properties
        profile_dict = dict()

        if old_profile['mode'] != desired_profile['resource_type']:
            # mode needs to be updated
            profile_dict['mode'] = desired_profile['resource_type']

        # check if notes need to be updated
        old_notes = old_profile.get('set_data', {}).get('notes')

        if desired_profile['notes'] != old_notes:
            profile_dict['set_data'] = dict(notes=desired_profile['notes'])

        if profile_dict:
            # if we have any updated values
            changed = True
            try:
                result = self.client.post(old_profile['href'],
                                          resource=profile_dict,
                                          action="edit")
            except Exception as e:
                msg = "Updating profile '{name}' failed: {error}"
                msg = msg.format(name=old_profile['name'], error=e)
                self.module.fail_json(msg=msg, result=result)

        if changed:
            msg = "Profile {name} updated successfully".format(name=desired_profile['name'])
        else:
            msg = "No update needed for profile {name}".format(name=desired_profile['name'])
        return dict(changed=changed, msg=msg)


def main():
    argument_spec = dict(
        name=dict(type='str'),
        resource_type=dict(type='str', choices=['Vm',
                                                'ContainerNode',
                                                'MiqServer',
                                                'Host',
                                                'Storage',
                                                'EmsCluster',
                                                'ExtManagementSystem',
                                                'MiddlewareServer']),
        alerts=dict(type='list'),
        notes=dict(type='str'),
        state=dict(default='present', choices=['present', 'absent']),
    )
    # add the manageiq connection arguments to the arguments
    argument_spec.update(manageiq_argument_spec())

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=[('state', 'present', ['name', 'resource_type']),
                                        ('state', 'absent', ['name'])])

    state = module.params['state']
    name = module.params['name']

    manageiq = ManageIQ(module)
    manageiq_alert_profiles = ManageIQAlertProfiles(manageiq)

    existing_profile = manageiq.find_collection_resource_by("alert_definition_profiles",
                                                            name=name)

    # we need to add or update the alert profile
    if state == "present":
        if not existing_profile:
            # a profile with this name doesn't exist yet, let's create it
            res_args = manageiq_alert_profiles.add_profile(module.params)
        else:
            # a profile with this name exists, we might need to update it
            res_args = manageiq_alert_profiles.update_profile(existing_profile, module.params)

    # this alert profile should not exist
    if state == "absent":
        # if we have an alert profile with this name, delete it
        if existing_profile:
            res_args = manageiq_alert_profiles.delete_profile(existing_profile)
        else:
            # This alert profile does not exist in ManageIQ, and that's okay
            msg = "Alert profile '{name}' does not exist in ManageIQ"
            msg = msg.format(name=name)
            res_args = dict(changed=False, msg=msg)

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
