#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Luc Stroobant (luc.stroobant@wdc.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {"metadata_version": "1.1", "status": ["preview"], "supported_by": "community"}


DOCUMENTATION = """
---
module: satellite_subscription
short_description: Manage host subscriptions (licenses) on Red Hat Satellite
description:
  - This module allows to assign or remove subscriptions to hosts in the satellite
  - It works on the Satellite side, so not from the client side like redhat_subscription.
    Your hosts or hypervisors should be in the Satellite already. The module will run subscription
    related tasks (assign, remove, autoattach or replace with hypervisor subscriptions) for the
    hosts through the Satellite API.
version_added: "2.8"
requirements:
  - requests
author:
  - Luc Stroobant (@stroobl)
options:
  satellite_hostname:
    description:
      - Red Hat Satelite server (6.x) hostname
    required: true
  username:
    description:
      - Satellite server username
    required: true
  password:
    description:
      - Satellite server password
    required: true
  organization:
    description:
      - Satellite organization ID to work on
    required: true
  state:
    description:
      - "present: assign a subscription of subscription_type to host"
      - "absent: remove subscription of subscription_type from host"
      - "autoattach: run subscription autoattach for host (autoattach will be enabled if necessary)"
      - "disable_autoattach: disable subscription autoattach for host"
      - "vdcguests: remove all Red Hat subscriptions from a hypervisor's guests and run autoattach
         to replace them with virtual guest subscriptions. Run this against a virt-who hypervisor to
         remove all other subscriptions assigned to the guests. Useful if you configured a VDC
         subscription on a hypervisor that didn't have it before."
      - "optimize: use to replace subscriptions on physical servers with a higher multiplier with subscriptions with a lower multiplier."
    choices: [present, absent, autoattach, disable_autoattach, vdcguests, optimize]
    default: autoattach
  content_host:
    description:
      - List of content hosts to work with
      - Can also be a hostname search pattern accepted by the satellite.
  subscription:
    description:
      - List of subscriptions to assign or remove
      - Required when action is assign or remove
      - "This field is used for the search for subscriptions, it can contain (part of) the subscription
         name, eg 'Red Hat Enterprise Linux Server Entry Level, Self-support' or another search query
         as used in the satellite, eg: 'product_id=RH00005S'"
  unique:
    description:
     - Set to true to remove all other subscriptions attached to the host
    type: bool
    default: False
  verify_ssl:
    description:
      - Check ssl certificates?
    type: bool
    default: True
"""

EXAMPLES = """
- name: Assign subscriptions, remove all existing subscriptions (run against localhost)
  satellite_subscription:
    satellite_hostname: "{{ satellite_fqdn }}"
    username: "{{ satellite_admin_user }}"
    password: "{{ satellite_admin_pass }}"
    state: present
    content_host: "{{ groups.rhel_servers }}"
    subscription:
      - product_id=RH000XX
      - name=EPEL
      - name=Extra
    unique: true
    organization: 1
  delegate_to: localhost

- name: Assign subscriptions rhel servers, remove all existing subscriptions (run against inventory hosts/group)
  satellite_subscription:
    satellite_hostname: "{{ satellite_fqdn }}"
    username: "{{ satellite_admin_user }}"
    password: "{{ satellite_admin_pass }}"
    state: present
    content_host:
      - "{{ inventory_hostname }}"
    subscription: "{{ redhat_subscriptions }}"
    unique: true
    organization: 1
  delegate_to: localhost

- name: remove a subscription from hosts
  satellite_subscription:
    satellite_hostname: "{{ satellite_fqdn }}"
    username: "{{ satellite_admin_user }}"
    password: "{{ satellite_admin_pass }}"
    state: absent
    content_host:
      - server1
      - server2
    subscription:
      - "Red Hat Enterprise Linux Server Entry Level, Self-support"
    organization: 1

- name: run auto-attach for a host
  satellite_subscription:
    satellite_hostname: "{{ satellite_fqdn }}"
    username: "{{ satellite_admin_user }}"
    password: "{{ satellite_admin_pass }}"
    state: autoattach
    content_host: server1
    organization: 1

- name: assign VDC guest subscriptions to Satellite content hosts
  satellite_subscription:
    satellite_hostname: "{{ satellite_fqdn }}"
    username: "{{ satellite_admin_user }}"
    password: "{{ satellite_admin_pass }}"
    state: vdcguests
    content_host:
      - "{{ inventory_hostname }}"
    organization: "{{ satellite_organization_id }}"
    verify_ssl: "{{ satellite_verify_ssl }}"
  delegate_to: localhost

- name: Optimize by replacing multiple entitlements from subscription_id 242 with the new subscription (no changes on hosts consuming a single entitlement)
  satellite_subscription:
    satellite_hostname: "{{ satellite_fqdn }}"
    username: "{{ satellite_admin_user }}"
    password: "{{ satellite_admin_pass }}"
    state: optimize
    content_host:
      - "subscription_id=242"
    subscription:
      - "Red Hat Enterprise Linux Server Entry Level, Self-support"
    organization: "{{ satellite_organization_id }}"
    verify_ssl: "{{ satellite_verify_ssl }}"
  delegate_to: localhost
"""

RETURN = """
stdout:
  description: The result of the requested action
  returned: success
  type: str
  sample: Subscription assigned
stderr:
  description: Errors when trying to execute action
  returned: success
  type: str
  sample: Authentication failed
"""

from ansible.module_utils import six
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.satellite import requests_available, request, host_list, put


def subscription_assign(sat_url, user, password, matched_subscriptions, host, module, verify):

    result = []
    error = False
    # check for available subsciptions in our list(s)
    for subsearch in matched_subscriptions:
        available_subscription = None
        for sub in matched_subscriptions[subsearch]:
            if sub["available"] != 0:
                # subscription found: stop searching
                available_subscription = dict(sub)
                break
        if not available_subscription:
            result.append(
                "Errors: Sorry, no more subscriptions available of this type. Please adjust your subscription search."
            )
            error = True
            break

        # format json data for request
        data = {"id": host["id"], "subscriptions": [{"id": available_subscription["id"], "quantity": 1}]}

        # attach the available subscription to this host
        apicall = "{0}/api/hosts/{1}/subscriptions/add_subscriptions".format(sat_url, host["id"])
        put(apicall, user, password, data, verify)

        result.append([host["name"], "Assigned: {0}".format(sub["name"])])

    return result, error


def subscription_search(sat_url, user, password, org, subscription, module, verify):
    """Search for subscriptions and return them"""

    matched_subscriptions = {}
    for subsearch in subscription:
        # only search for normal subscriptions to avoid returning assigned ones
        params = {"search": "type=NORMAL and ({0})".format(subsearch)}
        apicall = "{0}/katello/api/organizations/{1}/subscriptions".format(sat_url, org)
        matched_subscriptions[subsearch] = request(apicall, user, password, verify, True, params)
        if matched_subscriptions[subsearch] == []:
            errors = "Sorry, no subscriptions matched. Please adjust your subscription search"
            module.fail_json(msg=errors)

    return matched_subscriptions


def subscription_remove(sat_url, user, password, host, sub, verify):
    """Remove a subscription from a host"""

    apicall = "{0}/api/hosts/{1}/subscriptions/remove_subscriptions".format(sat_url, host["id"])
    data = {"id": host["id"], "subscriptions": [{"id": sub["id"], "quantity": sub["quantity_consumed"]}]}
    result = put(apicall, user, password, data, verify)

    return result


def subscription_configure_autoattach(sat_url, user, password, host, autoheal, verify):
    """Configure autoattach for a host (autoheal = bool)"""
    data = {
        "id": host["id"],
        "subscription_facet_attributes": {
            "autoheal": autoheal,
            "id": host["subscription_facet_attributes"]["id"],
            "release_version": "",
            "service_level": "",
        },
    }
    apicall = "{0}/api/hosts/{1}".format(sat_url, host["id"])
    req = put(apicall, user, password, data, verify)

    return req


def subscription_autoattach(sat_url, user, password, host, verify):
    """Run subscription autoattach for host"""

    data = {"id": host["id"]}
    apicall = "{0}/api/hosts/{1}/subscriptions/auto_attach".format(sat_url, host["id"])
    req = put(apicall, user, password, data, verify)

    return req["results"]


def main():

    module = AnsibleModule(
        argument_spec=dict(
            satellite_hostname=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            organization=dict(required=True, type=int),
            state=dict(
                default="autoattach",
                choices=["present", "absent", "autoattach", "disable_autoattach", "vdcguests", "optimize"],
            ),
            content_host=dict(type=list, required=True),
            subscription=dict(type=list),
            unique=dict(type='bool', default=False),
            verify_ssl=dict(type='bool', default=True),
        ),
        supports_check_mode=False,
    )

    if not requests_available:
        module.fail_json(msg="Library 'requests' is required.")

    sat = module.params["satellite_hostname"]
    state = module.params["state"]
    user = module.params["username"]
    password = module.params["password"]
    org = module.params["organization"]
    content_host = module.params["content_host"]
    subscription = module.params["subscription"]
    unique = module.params["unique"]
    verify = module.params["verify_ssl"]

    errors = None
    changed = False
    result = []

    sat_url = "https://{0}".format(sat)

    # get the list of hosts to work on
    hosts = []
    for ch in content_host:
        hl = host_list(sat_url, user, password, org, verify, ch)
        hosts.extend(hl)

    if state == "autoattach":
        for host in hosts:
            # run auto attach if enabled
            if host["subscription_facet_attributes"]["autoheal"]:
                subs = subscription_autoattach(sat_url, user, password, host, verify)
                result.append("Triggered auto-attach run, attached subscriptions:")
                for sub in subs:
                    result.append(sub["product_name"])
                changed = True
            # or enable and run auto attach if disabled
            else:
                subscription_configure_autoattach(sat_url, user, password, host, True, verify)
                subs = subscription_autoattach(sat_url, user, password, host, verify)
                result.append("Enabled and triggered auto-attach run, attached subscriptions:")
                for sub in subs:
                    result.append(sub["product_name"])
                changed = True

    if state == "disable_autoattach":
        for host in hosts:
            if host["subscription_facet_attributes"]["autoheal"]:
                subscription_configure_autoattach(sat_url, user, password, host, False, verify)
                result.append("Auto-attach disabled")
                changed = True
            else:
                result.append("Auto-attach already disabled")

    elif state == "present":

        # loop over hosts to assign
        for host in hosts:

            if unique:
                # get existing subscriptions on host
                apicall = "{0}/api/hosts/{1}/subscriptions".format(sat_url, host["id"])
                hostsubs = request(apicall, user, password, verify)
                # and remove them
                for sub in hostsubs["results"]:
                    subscription_remove(sat_url, user, password, host, sub, verify)
                    result.append([host["name"], "Removed: {0}".format(sub["name"])])

            # search for our subscriptions
            matched_subscriptions = subscription_search(sat_url, user, password, org, subscription, module, verify)

            # assign the free subscription(s) to host
            res, error = subscription_assign(sat_url, user, password, matched_subscriptions, host, module, verify)
            result.append(res)
            if not error:
                changed = True
            else:
                module.fail_json(msg=result)

    elif state == "absent":
        # loop over hosts to remove
        for host in hosts:
            # get existing subscriptions on host
            apicall = "{0}/api/hosts/{1}/subscriptions".format(sat_url, host["id"])
            hostsubs = request(apicall, user, password, verify)
            for sub in hostsubs["results"]:
                for subsearch in subscription:
                    if "=" in subsearch:
                        # this is a search with a key, get the key and value
                        (key, value) = subsearch.split("=")
                        if value in sub[key]:
                            subscription_remove(sat_url, user, password, host, sub, verify)
                            result.append([host["name"], "Removed: {0}".format(sub["name"])])
                            changed = True
                    else:
                        # only match on name if no key is given
                        if subsearch in sub["name"]:
                            subscription_remove(sat_url, user, password, host, sub, verify)
                            result.append([host["name"], "Removed: {0}".format(sub["name"])])
                            changed = True

    elif state == "vdcguests":
        # loop over hypervisors
        for host in hosts:
            # request detailed info for host
            apicall = "{0}/api/hosts/{1}".format(sat_url, host["id"])
            host_info = request(apicall, user, password, verify, False)
            # loop over guests on hypervisor
            for guest in host_info["subscription_facet_attributes"]["virtual_guests"]:
                # get existing guest subscriptions
                apicall = "{0}/api/hosts/{1}/subscriptions".format(sat_url, guest["id"])
                guest_subs = request(apicall, user, password, verify)
                # remove existing Red Hat subscriptions, except the ones from the hypervisor
                for sub in guest_subs["results"]:
                    if "hypervisor" not in sub and sub["account_number"]:
                        subscription_remove(sat_url, user, password, guest, sub, verify)
                        result.append([guest["name"], "removed: {0}".format(sub["name"])])
                # run autoattach
                subscription_autoattach(sat_url, user, password, guest, verify)

    elif state == "optimize":
        # loop over hosts
        for host in hosts:
            # skip virtual machines - TODO only tested with VMware ("VMware Virtual Platform")
            if host["model_name"] and "Virtual" in host["model_name"]:
                continue
            else:
                # get existing subscriptions on host
                apicall = "{0}/api/hosts/{1}/subscriptions".format(sat_url, host["id"])
                hostsubs = request(apicall, user, password, verify)
                for sub in hostsubs["results"]:
                    # remove subscription if it's using an entitlment per socket
                    if (
                        sub["account_number"]
                        and sub["sockets"] != "1"
                        and sub["quantity_consumed"] == int(sub["sockets"])
                    ):
                        # search for our subscriptions
                        matched_subscriptions = subscription_search(
                            sat_url, user, password, org, subscription, module, verify
                        )
                        # assign the free subscription(s) to host
                        res, error = subscription_assign(
                            sat_url, user, password, matched_subscriptions, host, module, verify
                        )
                        result.append(res)
                        if not error:
                            changed = True
                        else:
                            module.fail_json(msg=result)
                        # remove the original subscription
                        subscription_remove(sat_url, user, password, host, sub, verify)
                        result.append([host["name"], "Removed: {0} {1}".format(sub["quantity_consumed"], sub["name"])])
                        changed = True
                        # skip to next host
                        break

    module.exit_json(changed=changed, data=result, stderr=errors)


if __name__ == "__main__":
    main()
