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
  - This module allows to assign or remove subscriptions to hosts in Red Hat Satellite.
  - It operates using the Red Hat Satellite REST API, rather than make changes directly to target systems like M(redhat_subscription).
    Your hosts or hypervisors should be in the Satellite already. The module will run subscription
    related tasks (assign, remove, autoattach or replace with hypervisor subscriptions) for the
    hosts through the Satellite API.
version_added: "2.9"
author:
  - Luc Stroobant (@stroobl)
options:
  hostname:
    description:
      - The name or IP address of the Red Hat Satellite server.
    type: str
    required: yes
  url_username:
    description:
      - Satellite server user.
    type: str
    required: yes
    aliases: [username]
  url_password:
    description:
      - Satellite server password.
    type: str
    required: yes
    aliases: [password]
  org_id:
    description:
      - Satellite organization ID to work on
    type: int
    required: yes
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
    type: str
    choices: [absent, autoattach, disable_autoattach, optimize, present, vdcguests]
    default: autoattach
  content_hosts:
    description:
      - A list of content hosts to use.
      - This can also be a hostname search pattern accepted by the satellite.
    type: list
  subscription:
    description:
      - List of subscriptions to assign or remove
      - Required when action is assign or remove
      - "This field is used for the search for subscriptions, it can contain (part of) the subscription
         name, eg 'Red Hat Enterprise Linux Server Entry Level, Self-support' or another search query
         as used in the satellite, eg: 'product_id=RH00005S'"
    type: list
  unique:
    description:
     - Whether to remove all subscriptions to this host.
     - When set to C(yes) remove all other subscriptions attached to this host.
    type: bool
    default: no
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated.
      - This should only be used on personally controlled sites using self-signed certificates.
    type: bool
    default: yes
"""

EXAMPLES = """
- name: Assign subscriptions, remove all existing subscriptions (run against localhost)
  satellite_subscription:
    hostname: satellite.domain.local
    user: admin
    password: adminpass
    state: present
    content_hosts: "{{ groups.rhel_servers }}"
    subscription:
      - product_id=RH000XX
      - name=EPEL
      - name=Extra
    unique: yes
    org_id: 1
  delegate_to: localhost

- name: Assign subscriptions rhel servers, remove all existing subscriptions (run against inventory hosts/group)
  satellite_subscription:
    hostname: satellite.domain.local
    user: admin
    password: adminpass
    state: present
    content_hosts:
      - "{{ inventory_hostname }}"
    subscription:
      - "Red Hat Enterprise Linux Server Entry Level, Standard"
    unique: yes
    org_id: 1
  delegate_to: localhost

- name: remove a subscription from hosts
  satellite_subscription:
    hostname: satellite.domain.local
    user: admin
    password: adminpass
    state: absent
    content_hosts:
      - server1
      - server2
    subscription:
      - "Red Hat Enterprise Linux Server Entry Level, Self-support"
    org_id: 1

- name: run auto-attach for a host
  satellite_subscription:
    hostname: satellite.domain.local
    user: admin
    password: adminpass
    state: autoattach
    content_hosts: server1
    org_id: 1

- name: Assign VDC guest subscriptions to Satellite content hosts
  satellite_subscription:
    hostname: satellite.domain.local
    user: admin
    password: adminpass
    state: vdcguests
    content_hosts:
      - "{{ inventory_hostname }}"
    org_id: 1
    validate_certs: false
  delegate_to: localhost

- name: Optimize by replacing multiple entitlements from subscription_id 242 with the new subscription (no changes on hosts consuming a single entitlement)
  satellite_subscription:
    hostname: satellite.domain.local
    user: admin
    password: adminpass
    state: optimize
    content_hosts:
      - "subscription_id=242"
    subscription:
      - "Red Hat Enterprise Linux Server Entry Level, Self-support"
    org_id: 1
    validate_certs: false
  delegate_to: localhost
"""

RETURN = """
msg:
  description: The result of the requested action
  returned: success
  type: str
  sample: Subscription assigned
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.satellite import request, host_list, put


def subscription_assign(module, sat_url, matched_subscriptions, host):

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
        url = "{0}/api/hosts/{1}/subscriptions/add_subscriptions".format(sat_url, host["id"])
        put(module, url, data)

        result.append([host["name"], "Assigned: {0}".format(sub["name"])])

    return result, error


def subscription_search(module, sat_url, org, subscription):
    """Search for subscriptions and return them"""

    matched_subscriptions = {}
    for subsearch in subscription:
        # only search for normal subscriptions to avoid returning assigned ones
        params = {"search": "type=NORMAL and ({0})".format(subsearch)}
        url = "{0}/katello/api/organizations/{1}/subscriptions".format(sat_url, org)
        matched_subscriptions[subsearch] = request(module, url, True, params)
        if matched_subscriptions[subsearch] == []:
            errors = "Sorry, no subscriptions matched. Please adjust your subscription search"
            module.fail_json(msg=errors)

    return matched_subscriptions


def subscription_remove(module, sat_url, host, sub):
    """Remove a subscription from a host"""

    url = "{0}/api/hosts/{1}/subscriptions/remove_subscriptions".format(sat_url, host["id"])
    data = {"id": host["id"], "subscriptions": [{"id": sub["id"], "quantity": sub["quantity_consumed"]}]}
    result = put(module, url, data)

    return result


def subscription_configure_autoattach(module, sat_url, host, autoheal):
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
    url = "{0}/api/hosts/{1}".format(sat_url, host["id"])
    req = put(module, url, data)

    return req


def subscription_autoattach(module, sat_url, host):
    """Run subscription autoattach for host"""

    data = {"id": host["id"]}
    url = "{0}/api/hosts/{1}/subscriptions/auto_attach".format(sat_url, host["id"])
    req = put(module, url, data)

    return req["results"]


def main():

    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(type='str', required=True),
            url_username=dict(type='str', required=True, aliases=['username']),
            url_password=dict(type='str', required=True, no_log=True, aliases=['password']),
            org_id=dict(type='int', required=True),
            state=dict(
                type='str', default="autoattach",
                choices=['absent', 'autoattach', 'disable_autoattach', 'optimize', 'present', 'vdcguests'],
            ),
            content_hosts=dict(type='list', required=True),
            subscription=dict(type='list'),
            unique=dict(type='bool', default=False),
            validate_certs=dict(type='bool', default=True),
        ),
        supports_check_mode=False,
    )

    # Force basic auth for satellite api calls
    module.params["force_basic_auth"] = True

    hostname = module.params["hostname"]
    state = module.params["state"]
    org = module.params["org_id"]
    content_hosts = module.params["content_hosts"]
    subscription = module.params["subscription"]
    unique = module.params["unique"]

    changed = False
    result = []

    sat_url = "https://{0}".format(hostname)

    # get the list of hosts to work on
    hosts = []
    for content_host in content_hosts:
        hl = host_list(module, sat_url, org, content_host)
        hosts.extend(hl)

    if state == "autoattach":
        for host in hosts:
            # run auto attach if enabled
            if host["subscription_facet_attributes"]["autoheal"]:
                subs = subscription_autoattach(module, sat_url, host)
                result.append("Triggered auto-attach run, attached subscriptions:")
                for sub in subs:
                    result.append(sub["product_name"])
                changed = True
            # or enable and run auto attach if disabled
            else:
                subscription_configure_autoattach(module, sat_url, host, True)
                subs = subscription_autoattach(module, sat_url, host)
                result.append("Enabled and triggered auto-attach run, attached subscriptions:")
                for sub in subs:
                    result.append(sub["product_name"])
                changed = True

    if state == "disable_autoattach":
        for host in hosts:
            if host["subscription_facet_attributes"]["autoheal"]:
                subscription_configure_autoattach(module, sat_url, host, False)
                result.append("Auto-attach disabled")
                changed = True
            else:
                result.append("Auto-attach already disabled")

    elif state == "present":

        # loop over hosts to assign
        for host in hosts:

            if unique:
                # get existing subscriptions on host
                url = "{0}/api/hosts/{1}/subscriptions".format(sat_url, host["id"])
                hostsubs = request(module, url)
                # and remove them
                for sub in hostsubs["results"]:
                    subscription_remove(module, sat_url, host, sub)
                    result.append([host["name"], "Removed: {0}".format(sub["name"])])

            # search for our subscriptions
            matched_subscriptions = subscription_search(module, sat_url, org, subscription)

            # assign the free subscription(s) to host
            res, error = subscription_assign(module, sat_url, matched_subscriptions, host)
            result.append(res)
            if error:
                module.fail_json(msg=result)
            changed = True

    elif state == "absent":
        # loop over hosts to remove
        for host in hosts:
            # get existing subscriptions on host
            url = "{0}/api/hosts/{1}/subscriptions".format(sat_url, host["id"])
            hostsubs = request(module, url)
            for sub in hostsubs["results"]:
                for subsearch in subscription:
                    if "=" in subsearch:
                        # this is a search with a key, get the key and value
                        (key, value) = subsearch.split("=")
                        if value in sub[key]:
                            subscription_remove(module, sat_url, host, sub)
                            result.append([host["name"], "Removed: {0}".format(sub["name"])])
                            changed = True
                    else:
                        # only match on name if no key is given
                        if subsearch in sub["name"]:
                            subscription_remove(module, sat_url, host, sub)
                            result.append([host["name"], "Removed: {0}".format(sub["name"])])
                            changed = True

    elif state == "vdcguests":
        # loop over hypervisors
        for host in hosts:
            # request detailed info for host
            url = "{0}/api/hosts/{1}".format(sat_url, host["id"])
            host_info = request(module, url)
            # loop over guests on hypervisor
            for guest in host_info["subscription_facet_attributes"]["virtual_guests"]:
                # get existing guest subscriptions
                url = "{0}/api/hosts/{1}/subscriptions".format(sat_url, guest["id"])
                guest_subs = request(module, url)
                # remove existing Red Hat subscriptions, except the ones from the hypervisor
                for sub in guest_subs["results"]:
                    if "hypervisor" not in sub and sub["account_number"]:
                        subscription_remove(module, sat_url, guest, sub)
                        result.append([guest["name"], "removed: {0}".format(sub["name"])])
                # run autoattach
                subscription_autoattach(module, sat_url, guest)

    elif state == "optimize":
        # loop over hosts
        for host in hosts:
            # skip virtual machines - TODO only tested with VMware ("VMware Virtual Platform")
            if host["model_name"] and "Virtual" in host["model_name"]:
                continue
            else:
                # get existing subscriptions on host
                url = "{0}/api/hosts/{1}/subscriptions".format(sat_url, host["id"])
                hostsubs = request(module, url)
                for sub in hostsubs["results"]:
                    # remove subscription if it's using an entitlment per socket
                    if (
                        sub["account_number"]
                        and sub["sockets"] != "1"
                        and sub["quantity_consumed"] == int(sub["sockets"])
                    ):
                        # search for our subscriptions
                        matched_subscriptions = subscription_search(
                            module, sat_url, org, subscription
                        )
                        # assign the free subscription(s) to host
                        res, error = subscription_assign(
                            module, sat_url, matched_subscriptions, host
                        )
                        result.append(res)
                        if not error:
                            changed = True
                        else:
                            module.fail_json(msg=result)
                        # remove the original subscription
                        subscription_remove(module, sat_url, host, sub)
                        result.append([host["name"], "Removed: {0} {1}".format(sub["quantity_consumed"], sub["name"])])
                        changed = True
                        # skip to next host
                        break

    module.exit_json(changed=changed, msg=result)


if __name__ == "__main__":
    main()
