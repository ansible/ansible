# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Daniel Korn <korndaniel1@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard ManageIQ documentation fragment
    DOCUMENTATION = r'''
options:
  manageiq_connection:
    description:
      - ManageIQ connection configuration information.
    required: true
    type: dict
    suboptions:
      url:
        description:
          - ManageIQ environment url. C(MIQ_URL) env var if set. otherwise, it is required to pass it.
        type: str
        required: true
      username:
        description:
          - ManageIQ username. C(MIQ_USERNAME) env var if set. otherwise, required if no token is passed in.
        type: str
      password:
        description:
          - ManageIQ password. C(MIQ_PASSWORD) env var if set. otherwise, required if no token is passed in.
        type: str
      token:
        description:
          - ManageIQ token. C(MIQ_TOKEN) env var if set. otherwise, required if no username or password is passed in.
        type: str
      validate_certs:
        description:
          - Whether SSL certificates should be verified for HTTPS requests. defaults to True.
        type: bool
        default: yes
        aliases: [ verify_ssl ]
      ca_cert:
        description:
          - The path to a CA bundle file or directory with certificates. defaults to None.
        type: path
        aliases: [ ca_bundle_path ]

requirements:
  - 'manageiq-client U(https://github.com/ManageIQ/manageiq-api-client-python/)'
'''
