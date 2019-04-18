#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 CallFire Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


################################################################################
# Documentation
################################################################################

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gcdns_zone
short_description: Creates or removes zones in Google Cloud DNS
description:
    - Creates or removes managed zones in Google Cloud DNS.
version_added: "2.2"
author: "William Albert (@walbert947)"
requirements:
    - "apache-libcloud >= 0.19.0"
deprecated:
    removed_in: "2.12"
    why: Updated modules released with increased functionality
    alternative: Use M(gcp_dns_managed_zone) instead.
options:
    state:
        description:
            - Whether the given zone should or should not be present.
        choices: ["present", "absent"]
        default: "present"
    zone:
        description:
            - The DNS domain name of the zone.
            - This is NOT the Google Cloud DNS zone ID (e.g., example-com). If
              you attempt to specify a zone ID, this module will attempt to
              create a TLD and will fail.
        required: true
        aliases: ['name']
    description:
        description:
            - An arbitrary text string to use for the zone description.
        default: ""
    service_account_email:
        description:
            - The e-mail address for a service account with access to Google
              Cloud DNS.
    pem_file:
        description:
            - The path to the PEM file associated with the service account
              email.
            - This option is deprecated and may be removed in a future release.
              Use I(credentials_file) instead.
    credentials_file:
        description:
            - The path to the JSON file associated with the service account
              email.
    project_id:
        description:
            - The Google Cloud Platform project ID to use.
notes:
    - See also M(gcdns_record).
    - Zones that are newly created must still be set up with a domain registrar
      before they can be used.
'''

EXAMPLES = '''
# Basic zone creation example.
- name: Create a basic zone with the minimum number of parameters.
  gcdns_zone: zone=example.com

# Zone removal example.
- name: Remove a zone.
  gcdns_zone: zone=example.com state=absent

# Zone creation with description
- name: Creating a zone with a description
  gcdns_zone: zone=example.com description="This is an awesome zone"
'''

RETURN = '''
description:
    description: The zone's description
    returned: success
    type: str
    sample: This is an awesome zone
state:
    description: Whether the zone is present or absent
    returned: success
    type: str
    sample: present
zone:
    description: The zone's DNS name
    returned: success
    type: str
    sample: example.com.
'''


################################################################################
# Imports
################################################################################

from distutils.version import LooseVersion

try:
    from libcloud import __version__ as LIBCLOUD_VERSION
    from libcloud.common.google import InvalidRequestError
    from libcloud.common.google import ResourceExistsError
    from libcloud.common.google import ResourceNotFoundError
    from libcloud.dns.types import Provider
    # The libcloud Google Cloud DNS provider.
    PROVIDER = Provider.GOOGLE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False
    PROVIDER = None

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gcdns import gcdns_connect


################################################################################
# Constants
################################################################################

# Apache libcloud 0.19.0 was the first to contain the non-beta Google Cloud DNS
# v1 API. Earlier versions contained the beta v1 API, which has since been
# deprecated and decommissioned.
MINIMUM_LIBCLOUD_VERSION = '0.19.0'

# The URL used to verify ownership of a zone in Google Cloud DNS.
ZONE_VERIFICATION_URL = 'https://www.google.com/webmasters/verification/'

################################################################################
# Functions
################################################################################


def create_zone(module, gcdns, zone):
    """Creates a new Google Cloud DNS zone."""

    description = module.params['description']
    extra = dict(description=description)
    zone_name = module.params['zone']

    # Google Cloud DNS wants the trailing dot on the domain name.
    if zone_name[-1] != '.':
        zone_name = zone_name + '.'

    # If we got a zone back, then the domain exists.
    if zone is not None:
        return False

    # The zone doesn't exist yet.
    try:
        if not module.check_mode:
            gcdns.create_zone(domain=zone_name, extra=extra)
        return True

    except ResourceExistsError:
        # The zone already exists. We checked for this already, so either
        # Google is lying, or someone was a ninja and created the zone
        # within milliseconds of us checking for its existence. In any case,
        # the zone has already been created, so we have nothing more to do.
        return False

    except InvalidRequestError as error:
        if error.code == 'invalid':
            # The zone name or a parameter might be completely invalid. This is
            # typically caused by an illegal DNS name (e.g. foo..com).
            module.fail_json(
                msg="zone name is not a valid DNS name: %s" % zone_name,
                changed=False
            )

        elif error.code == 'managedZoneDnsNameNotAvailable':
            # Google Cloud DNS will refuse to create zones with certain domain
            # names, such as TLDs, ccTLDs, or special domain names such as
            # example.com.
            module.fail_json(
                msg="zone name is reserved or already in use: %s" % zone_name,
                changed=False
            )

        elif error.code == 'verifyManagedZoneDnsNameOwnership':
            # This domain name needs to be verified before Google will create
            # it. This occurs when a user attempts to create a zone which shares
            # a domain name with a zone hosted elsewhere in Google Cloud DNS.
            module.fail_json(
                msg="ownership of zone %s needs to be verified at %s" % (zone_name, ZONE_VERIFICATION_URL),
                changed=False
            )

        else:
            # The error is something else that we don't know how to handle,
            # so we'll just re-raise the exception.
            raise


def remove_zone(module, gcdns, zone):
    """Removes an existing Google Cloud DNS zone."""

    # If there's no zone, then we're obviously done.
    if zone is None:
        return False

    # An empty zone will have two resource records:
    #   1. An NS record with a list of authoritative name servers
    #   2. An SOA record
    # If any additional resource records are present, Google Cloud DNS will
    # refuse to remove the zone.
    if len(zone.list_records()) > 2:
        module.fail_json(
            msg="zone is not empty and cannot be removed: %s" % zone.domain,
            changed=False
        )

    try:
        if not module.check_mode:
            gcdns.delete_zone(zone)
        return True

    except ResourceNotFoundError:
        # When we performed our check, the zone existed. It may have been
        # deleted by something else. It's gone, so whatever.
        return False

    except InvalidRequestError as error:
        if error.code == 'containerNotEmpty':
            # When we performed our check, the zone existed and was empty. In
            # the milliseconds between the check and the removal command,
            # records were added to the zone.
            module.fail_json(
                msg="zone is not empty and cannot be removed: %s" % zone.domain,
                changed=False
            )

        else:
            # The error is something else that we don't know how to handle,
            # so we'll just re-raise the exception.
            raise


def _get_zone(gcdns, zone_name):
    """Gets the zone object for a given domain name."""

    # To create a zone, we need to supply a zone name. However, to delete a
    # zone, we need to supply a zone ID. Zone ID's are often based on zone
    # names, but that's not guaranteed, so we'll iterate through the list of
    # zones to see if we can find a matching name.
    available_zones = gcdns.iterate_zones()
    found_zone = None

    for zone in available_zones:
        if zone.domain == zone_name:
            found_zone = zone
            break

    return found_zone


def _sanity_check(module):
    """Run module sanity checks."""

    zone_name = module.params['zone']

    # Apache libcloud needs to be installed and at least the minimum version.
    if not HAS_LIBCLOUD:
        module.fail_json(
            msg='This module requires Apache libcloud %s or greater' % MINIMUM_LIBCLOUD_VERSION,
            changed=False
        )
    elif LooseVersion(LIBCLOUD_VERSION) < MINIMUM_LIBCLOUD_VERSION:
        module.fail_json(
            msg='This module requires Apache libcloud %s or greater' % MINIMUM_LIBCLOUD_VERSION,
            changed=False
        )

    # Google Cloud DNS does not support the creation of TLDs.
    if '.' not in zone_name or len([label for label in zone_name.split('.') if label]) == 1:
        module.fail_json(
            msg='cannot create top-level domain: %s' % zone_name,
            changed=False
        )

################################################################################
# Main
################################################################################


def main():
    """Main function"""

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            zone=dict(required=True, aliases=['name'], type='str'),
            description=dict(default='', type='str'),
            service_account_email=dict(type='str'),
            pem_file=dict(type='path'),
            credentials_file=dict(type='path'),
            project_id=dict(type='str')
        ),
        supports_check_mode=True
    )

    _sanity_check(module)

    zone_name = module.params['zone']
    state = module.params['state']

    # Google Cloud DNS wants the trailing dot on the domain name.
    if zone_name[-1] != '.':
        zone_name = zone_name + '.'

    json_output = dict(
        state=state,
        zone=zone_name,
        description=module.params['description']
    )

    # Build a connection object that was can use to connect with Google
    # Cloud DNS.
    gcdns = gcdns_connect(module, provider=PROVIDER)

    # We need to check if the zone we're attempting to create already exists.
    zone = _get_zone(gcdns, zone_name)

    diff = dict()

    # Build the 'before' diff
    if zone is None:
        diff['before'] = ''
        diff['before_header'] = '<absent>'
    else:
        diff['before'] = dict(
            zone=zone.domain,
            description=zone.extra['description']
        )
        diff['before_header'] = zone_name

    # Create or remove the zone.
    if state == 'present':
        diff['after'] = dict(
            zone=zone_name,
            description=module.params['description']
        )
        diff['after_header'] = zone_name

        changed = create_zone(module, gcdns, zone)

    elif state == 'absent':
        diff['after'] = ''
        diff['after_header'] = '<absent>'

        changed = remove_zone(module, gcdns, zone)

    module.exit_json(changed=changed, diff=diff, **json_output)


if __name__ == '__main__':
    main()
