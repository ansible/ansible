#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Daniel Korn <korndaniel1@gmail.com>
# (c) 2017, Yaacov Zamir <yzamir@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
module: manageiq_provider
short_description: Management of provider in ManageIQ.
extends_documentation_fragment: manageiq
version_added: '2.4'
author: Daniel Korn (@dkorn)
description:
  - The manageiq_provider module supports adding, updating, and deleting provider in ManageIQ.

options:
  state:
    description:
      - absent - provider should not exist, present - provider should be present, refresh - provider will be refreshed
    choices: ['absent', 'present', 'refresh']
    default: 'present'
  name:
    description: The provider's name.
    required: true
  type:
    description: The provider's type.
    required: true
    choices: ['Openshift', 'Amazon', 'oVirt', 'VMware', 'Azure', 'Director', 'OpenStack', 'GCE']
  zone:
    description: The ManageIQ zone name that will manage the provider.
    default: 'default'
  provider_region:
    description: The provider region name to connect to (e.g. AWS region for Amazon).
  host_default_vnc_port_start:
    description: The first port in the host VNC range. defaults to None.
    version_added: "2.5"
  host_default_vnc_port_end:
    description: The last port in the host VNC range. defaults to None.
    version_added: "2.5"
  subscription:
    description: Microsoft Azure subscription ID. defaults to None.
    version_added: "2.5"
  project:
    description: Google Compute Engine Project ID. defaults to None.
    version_added: "2.5"
  azure_tenant_id:
    description: Tenant ID. defaults to None.
    version_added: "2.5"
    aliases: [ keystone_v3_domain_id ]
  tenant_mapping_enabled:
    type: bool
    default: 'no'
    description: Whether to enable mapping of existing tenants. defaults to False.
    version_added: "2.5"
  api_version:
    description: The OpenStack Keystone API version. defaults to None.
    choices: ['v2', 'v3']
    version_added: "2.5"

  provider:
    description: Default endpoint connection information, required if state is true.
    suboptions:
      hostname:
        description: The provider's api hostname.
        required: true
      port:
        description: The provider's api port.
      userid:
        description: Provider's api endpoint authentication userid. defaults to None.
      password:
        description: Provider's api endpoint authentication password. defaults to None.
      auth_key:
        description: Provider's api endpoint authentication bearer token. defaults to None.
      validate_certs:
        description: Whether SSL certificates should be verified for HTTPS requests (deprecated). defaults to True.
        type: bool
        default: 'yes'
      security_protocol:
        description: How SSL certificates should be used for HTTPS requests. defaults to None.
        choices: ['ssl-with-validation','ssl-with-validation-custom-ca','ssl-without-validation','non-ssl']
      certificate_authority:
        description: The CA bundle string with custom certificates. defaults to None.

  metrics:
    description: Metrics endpoint connection information.
    suboptions:
      hostname:
        description: The provider's api hostname.
        required: true
      port:
        description: The provider's api port.
      userid:
        description: Provider's api endpoint authentication userid. defaults to None.
      password:
        description: Provider's api endpoint authentication password. defaults to None.
      auth_key:
        description: Provider's api endpoint authentication bearer token. defaults to None.
      validate_certs:
        description: Whether SSL certificates should be verified for HTTPS requests (deprecated). defaults to True.
        type: bool
        default: 'yes'
      security_protocol:
        choices: ['ssl-with-validation','ssl-with-validation-custom-ca','ssl-without-validation','non-ssl']
        description: How SSL certificates should be used for HTTPS requests. defaults to None.
      certificate_authority:
        description: The CA bundle string with custom certificates. defaults to None.
      path:
        description: Database name for oVirt metrics. Defaults to ovirt_engine_history.
        default: ovirt_engine_history

  alerts:
    description: Alerts endpoint connection information.
    suboptions:
      hostname:
        description: The provider's api hostname.
        required: true
      port:
        description: The provider's api port.
      userid:
        description: Provider's api endpoint authentication userid. defaults to None.
      password:
        description: Provider's api endpoint authentication password. defaults to None.
      auth_key:
        description: Provider's api endpoint authentication bearer token. defaults to None.
      validate_certs:
        description: Whether SSL certificates should be verified for HTTPS requests (deprecated). defaults to True.
        default: true
      security_protocol:
        choices: ['ssl-with-validation','ssl-with-validation-custom-ca','ssl-without-validation']
        description: How SSL certificates should be used for HTTPS requests. defaults to None.
      certificate_authority:
        description: The CA bundle string with custom certificates. defaults to None.

  ssh_keypair:
    description: SSH key pair used for SSH connections to all hosts in this provider.
    version_added: "2.5"
    suboptions:
      hostname:
        description: Director hostname.
        required: true
      userid:
        description: SSH username.
      auth_key:
        description: SSH private key.
'''

EXAMPLES = '''
- name: Create a new provider in ManageIQ ('Hawkular' metrics)
  manageiq_provider:
    name: 'EngLab'
    type: 'OpenShift'
    state: 'present'
    provider:
      auth_key: 'topSecret'
      hostname: 'example.com'
      port: 8443
      validate_certs: true
      security_protocol: 'ssl-with-validation-custom-ca'
      certificate_authority: |
        -----BEGIN CERTIFICATE-----
        FAKECERTsdKgAwIBAgIBATANBgkqhkiG9w0BAQsFADAmMSQwIgYDVQQDDBtvcGVu
        c2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkwHhcNMTcwODIxMTI1NTE5WhcNMjIwODIw
        MTI1NTIwWjAmMSQwIgYDVQQDDBtvcGVuc2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkw
        ggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDUDnL2tQ2xf/zO7F7hmZ4S
        ZuwKENdI4IYuWSxye4i3hPhKg6eKPzGzmDNWkIMDOrDAj1EgVSNPtPwsOL8OWvJm
        AaTjr070D7ZGWWnrrDrWEClBx9Rx/6JAM38RT8Pu7c1hXBm0J81KufSLLYiZ/gOw
        Znks5v5RUSGcAXvLkBJeATbsbh6fKX0RgQ3fFTvqQaE/r8LxcTN1uehPX1g5AaRa
        z/SNDHaFtQlE3XcqAAukyMn4N5kdNcuwF3GlQ+tJnJv8SstPkfQcZbTMUQ7I2KpJ
        ajXnMxmBhV5fCN4rb0QUNCrk2/B+EUMBY4MnxIakqNxnN1kvgI7FBbFgrHUe6QvJ
        AgMBAAGjIzAhMA4GA1UdDwEB/wQEAwICpDAPBgNVHRMBAf8EBTADAQH/MA0GCSqG
        SIb3DQEBCwUAA4IBAQAYRV57LUsqznSLZHA77o9+0fQetIE115DYP7wea42PODJI
        QJ+JETEfoCr0+YOMAbVmznP9GH5cMTKEWHExcIpbMBU7nMZp6A3htcJgF2fgPzOA
        aTUtzkuVCSrV//mbbYVxoFOc6sR3Br0wBs5+5iz3dBSt7xmgpMzZvqsQl655i051
        gGSTIY3z5EJmBZBjwuTjal9mMoPGA4eoTPqlITJDHQ2bdCV2oDbc7zqupGrUfZFA
        qzgieEyGzdCSRwjr1/PibA3bpwHyhD9CGD0PRVVTLhw6h6L5kuN1jA20OfzWxf/o
        XUsdmRaWiF+l4s6Dcd56SuRp5SGNa2+vP9Of/FX5
        -----END CERTIFICATE-----
    metrics:
      auth_key: 'topSecret'
      role: 'hawkular'
      hostname: 'example.com'
      port: 443
      validate_certs: true
      security_protocol: 'ssl-with-validation-custom-ca'
      certificate_authority: |
        -----BEGIN CERTIFICATE-----
        FAKECERTsdKgAwIBAgIBATANBgkqhkiG9w0BAQsFADAmMSQwIgYDVQQDDBtvcGVu
        c2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkwHhcNMTcwODIxMTI1NTE5WhcNMjIwODIw
        MTI1NTIwWjAmMSQwIgYDVQQDDBtvcGVuc2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkw
        ggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDUDnL2tQ2xf/zO7F7hmZ4S
        ZuwKENdI4IYuWSxye4i3hPhKg6eKPzGzmDNWkIMDOrDAj1EgVSNPtPwsOL8OWvJm
        AaTjr070D7ZGWWnrrDrWEClBx9Rx/6JAM38RT8Pu7c1hXBm0J81KufSLLYiZ/gOw
        Znks5v5RUSGcAXvLkBJeATbsbh6fKX0RgQ3fFTvqQaE/r8LxcTN1uehPX1g5AaRa
        z/SNDHaFtQlE3XcqAAukyMn4N5kdNcuwF3GlQ+tJnJv8SstPkfQcZbTMUQ7I2KpJ
        ajXnMxmBhV5fCN4rb0QUNCrk2/B+EUMBY4MnxIakqNxnN1kvgI7FBbFgrHUe6QvJ
        AgMBAAGjIzAhMA4GA1UdDwEB/wQEAwICpDAPBgNVHRMBAf8EBTADAQH/MA0GCSqG
        SIb3DQEBCwUAA4IBAQAYRV57LUsqznSLZHA77o9+0fQetIE115DYP7wea42PODJI
        QJ+JETEfoCr0+YOMAbVmznP9GH5cMTKEWHExcIpbMBU7nMZp6A3htcJgF2fgPzOA
        aTUtzkuVCSrV//mbbYVxoFOc6sR3Br0wBs5+5iz3dBSt7xmgpMzZvqsQl655i051
        gGSTIY3z5EJmBZBjwuTjal9mMoPGA4eoTPqlITJDHQ2bdCV2oDbc7zqupGrUfZFA
        qzgieEyGzdCSRwjr1/PibA3bpwHyhD9CGD0PRVVTLhw6h6L5kuN1jA20OfzWxf/o
        XUsdmRaWiF+l4s6Dcd56SuRp5SGNa2+vP9Of/FX5
        -----END CERTIFICATE-----
    manageiq_connection:
      url: 'https://127.0.0.1:80'
      username: 'admin'
      password: 'password'
      validate_certs: true


- name: Update an existing provider named 'EngLab' (defaults to 'Prometheus' metrics)
  manageiq_provider:
    name: 'EngLab'
    type: 'Openshift'
    state: 'present'
    provider:
      auth_key: 'topSecret'
      hostname: 'next.example.com'
      port: 8443
      validate_certs: true
      security_protocol: 'ssl-with-validation-custom-ca'
      certificate_authority: |
        -----BEGIN CERTIFICATE-----
        FAKECERTsdKgAwIBAgIBATANBgkqhkiG9w0BAQsFADAmMSQwIgYDVQQDDBtvcGVu
        c2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkwHhcNMTcwODIxMTI1NTE5WhcNMjIwODIw
        MTI1NTIwWjAmMSQwIgYDVQQDDBtvcGVuc2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkw
        ggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDUDnL2tQ2xf/zO7F7hmZ4S
        ZuwKENdI4IYuWSxye4i3hPhKg6eKPzGzmDNWkIMDOrDAj1EgVSNPtPwsOL8OWvJm
        AaTjr070D7ZGWWnrrDrWEClBx9Rx/6JAM38RT8Pu7c1hXBm0J81KufSLLYiZ/gOw
        Znks5v5RUSGcAXvLkBJeATbsbh6fKX0RgQ3fFTvqQaE/r8LxcTN1uehPX1g5AaRa
        z/SNDHaFtQlE3XcqAAukyMn4N5kdNcuwF3GlQ+tJnJv8SstPkfQcZbTMUQ7I2KpJ
        ajXnMxmBhV5fCN4rb0QUNCrk2/B+EUMBY4MnxIakqNxnN1kvgI7FBbFgrHUe6QvJ
        AgMBAAGjIzAhMA4GA1UdDwEB/wQEAwICpDAPBgNVHRMBAf8EBTADAQH/MA0GCSqG
        SIb3DQEBCwUAA4IBAQAYRV57LUsqznSLZHA77o9+0fQetIE115DYP7wea42PODJI
        QJ+JETEfoCr0+YOMAbVmznP9GH5cMTKEWHExcIpbMBU7nMZp6A3htcJgF2fgPzOA
        aTUtzkuVCSrV//mbbYVxoFOc6sR3Br0wBs5+5iz3dBSt7xmgpMzZvqsQl655i051
        gGSTIY3z5EJmBZBjwuTjal9mMoPGA4eoTPqlITJDHQ2bdCV2oDbc7zqupGrUfZFA
        qzgieEyGzdCSRwjr1/PibA3bpwHyhD9CGD0PRVVTLhw6h6L5kuN1jA20OfzWxf/o
        XUsdmRaWiF+l4s6Dcd56SuRp5SGNa2+vP9Of/FX5
        -----END CERTIFICATE-----
    metrics:
      auth_key: 'topSecret'
      hostname: 'next.example.com'
      port: 443
      validate_certs: true
      security_protocol: 'ssl-with-validation-custom-ca'
      certificate_authority: |
        -----BEGIN CERTIFICATE-----
        FAKECERTsdKgAwIBAgIBATANBgkqhkiG9w0BAQsFADAmMSQwIgYDVQQDDBtvcGVu
        c2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkwHhcNMTcwODIxMTI1NTE5WhcNMjIwODIw
        MTI1NTIwWjAmMSQwIgYDVQQDDBtvcGVuc2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkw
        ggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDUDnL2tQ2xf/zO7F7hmZ4S
        ZuwKENdI4IYuWSxye4i3hPhKg6eKPzGzmDNWkIMDOrDAj1EgVSNPtPwsOL8OWvJm
        AaTjr070D7ZGWWnrrDrWEClBx9Rx/6JAM38RT8Pu7c1hXBm0J81KufSLLYiZ/gOw
        Znks5v5RUSGcAXvLkBJeATbsbh6fKX0RgQ3fFTvqQaE/r8LxcTN1uehPX1g5AaRa
        z/SNDHaFtQlE3XcqAAukyMn4N5kdNcuwF3GlQ+tJnJv8SstPkfQcZbTMUQ7I2KpJ
        ajXnMxmBhV5fCN4rb0QUNCrk2/B+EUMBY4MnxIakqNxnN1kvgI7FBbFgrHUe6QvJ
        AgMBAAGjIzAhMA4GA1UdDwEB/wQEAwICpDAPBgNVHRMBAf8EBTADAQH/MA0GCSqG
        SIb3DQEBCwUAA4IBAQAYRV57LUsqznSLZHA77o9+0fQetIE115DYP7wea42PODJI
        QJ+JETEfoCr0+YOMAbVmznP9GH5cMTKEWHExcIpbMBU7nMZp6A3htcJgF2fgPzOA
        aTUtzkuVCSrV//mbbYVxoFOc6sR3Br0wBs5+5iz3dBSt7xmgpMzZvqsQl655i051
        gGSTIY3z5EJmBZBjwuTjal9mMoPGA4eoTPqlITJDHQ2bdCV2oDbc7zqupGrUfZFA
        qzgieEyGzdCSRwjr1/PibA3bpwHyhD9CGD0PRVVTLhw6h6L5kuN1jA20OfzWxf/o
        XUsdmRaWiF+l4s6Dcd56SuRp5SGNa2+vP9Of/FX5
        -----END CERTIFICATE-----
    manageiq_connection:
      url: 'https://127.0.0.1'
      username: 'admin'
      password: 'password'
      validate_certs: true


- name: Delete a provider in ManageIQ
  manageiq_provider:
    name: 'EngLab'
    type: 'Openshift'
    state: 'absent'
    manageiq_connection:
      url: 'https://127.0.0.1'
      username: 'admin'
      password: 'password'
      validate_certs: true


- name: Create a new Amazon provider in ManageIQ using token authentication
  manageiq_provider:
    name: 'EngAmazon'
    type: 'Amazon'
    state: 'present'
    provider:
      hostname: 'amazon.example.com'
      userid: 'hello'
      password: 'world'
    manageiq_connection:
      url: 'https://127.0.0.1'
      token: 'VeryLongToken'
      validate_certs: true


- name: Create a new oVirt provider in ManageIQ
  manageiq_provider:
    name: 'RHEV'
    type: 'oVirt'
    state: 'present'
    provider:
      hostname: 'rhev01.example.com'
      userid: 'admin@internal'
      password: 'password'
      validate_certs: true
      certificate_authority: |
        -----BEGIN CERTIFICATE-----
        FAKECERTsdKgAwIBAgIBATANBgkqhkiG9w0BAQsFADAmMSQwIgYDVQQDDBtvcGVu
        c2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkwHhcNMTcwODIxMTI1NTE5WhcNMjIwODIw
        MTI1NTIwWjAmMSQwIgYDVQQDDBtvcGVuc2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkw
        ggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDUDnL2tQ2xf/zO7F7hmZ4S
        ZuwKENdI4IYuWSxye4i3hPhKg6eKPzGzmDNWkIMDOrDAj1EgVSNPtPwsOL8OWvJm
        AaTjr070D7ZGWWnrrDrWEClBx9Rx/6JAM38RT8Pu7c1hXBm0J81KufSLLYiZ/gOw
        Znks5v5RUSGcAXvLkBJeATbsbh6fKX0RgQ3fFTvqQaE/r8LxcTN1uehPX1g5AaRa
        z/SNDHaFtQlE3XcqAAukyMn4N5kdNcuwF3GlQ+tJnJv8SstPkfQcZbTMUQ7I2KpJ
        ajXnMxmBhV5fCN4rb0QUNCrk2/B+EUMBY4MnxIakqNxnN1kvgI7FBbFgrHUe6QvJ
        AgMBAAGjIzAhMA4GA1UdDwEB/wQEAwICpDAPBgNVHRMBAf8EBTADAQH/MA0GCSqG
        SIb3DQEBCwUAA4IBAQAYRV57LUsqznSLZHA77o9+0fQetIE115DYP7wea42PODJI
        QJ+JETEfoCr0+YOMAbVmznP9GH5cMTKEWHExcIpbMBU7nMZp6A3htcJgF2fgPzOA
        aTUtzkuVCSrV//mbbYVxoFOc6sR3Br0wBs5+5iz3dBSt7xmgpMzZvqsQl655i051
        gGSTIY3z5EJmBZBjwuTjal9mMoPGA4eoTPqlITJDHQ2bdCV2oDbc7zqupGrUfZFA
        qzgieEyGzdCSRwjr1/PibA3bpwHyhD9CGD0PRVVTLhw6h6L5kuN1jA20OfzWxf/o
        XUsdmRaWiF+l4s6Dcd56SuRp5SGNa2+vP9Of/FX5
        -----END CERTIFICATE-----
    metrics:
      hostname: 'metrics.example.com'
      path: 'ovirt_engine_history'
      userid: 'user_id_metrics'
      password: 'password_metrics'
      validate_certs: true
      certificate_authority: |
        -----BEGIN CERTIFICATE-----
        FAKECERTsdKgAwIBAgIBATANBgkqhkiG9w0BAQsFADAmMSQwIgYDVQQDDBtvcGVu
        c2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkwHhcNMTcwODIxMTI1NTE5WhcNMjIwODIw
        MTI1NTIwWjAmMSQwIgYDVQQDDBtvcGVuc2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkw
        ggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDUDnL2tQ2xf/zO7F7hmZ4S
        ZuwKENdI4IYuWSxye4i3hPhKg6eKPzGzmDNWkIMDOrDAj1EgVSNPtPwsOL8OWvJm
        AaTjr070D7ZGWWnrrDrWEClBx9Rx/6JAM38RT8Pu7c1hXBm0J81KufSLLYiZ/gOw
        Znks5v5RUSGcAXvLkBJeATbsbh6fKX0RgQ3fFTvqQaE/r8LxcTN1uehPX1g5AaRa
        z/SNDHaFtQlE3XcqAAukyMn4N5kdNcuwF3GlQ+tJnJv8SstPkfQcZbTMUQ7I2KpJ
        ajXnMxmBhV5fCN4rb0QUNCrk2/B+EUMBY4MnxIakqNxnN1kvgI7FBbFgrHUe6QvJ
        AgMBAAGjIzAhMA4GA1UdDwEB/wQEAwICpDAPBgNVHRMBAf8EBTADAQH/MA0GCSqG
        SIb3DQEBCwUAA4IBAQAYRV57LUsqznSLZHA77o9+0fQetIE115DYP7wea42PODJI
        QJ+JETEfoCr0+YOMAbVmznP9GH5cMTKEWHExcIpbMBU7nMZp6A3htcJgF2fgPzOA
        aTUtzkuVCSrV//mbbYVxoFOc6sR3Br0wBs5+5iz3dBSt7xmgpMzZvqsQl655i051
        gGSTIY3z5EJmBZBjwuTjal9mMoPGA4eoTPqlITJDHQ2bdCV2oDbc7zqupGrUfZFA
        qzgieEyGzdCSRwjr1/PibA3bpwHyhD9CGD0PRVVTLhw6h6L5kuN1jA20OfzWxf/o
        XUsdmRaWiF+l4s6Dcd56SuRp5SGNa2+vP9Of/FX5
        -----END CERTIFICATE-----
    manageiq_connection:
      url: 'https://127.0.0.1'
      username: 'admin'
      password: 'password'
      validate_certs: true

- name: Create a new VMware provider in ManageIQ
  manageiq_provider:
    name: 'EngVMware'
    type: 'VMware'
    state: 'present'
    provider:
      hostname: 'vcenter.example.com'
      host_default_vnc_port_start: 5800
      host_default_vnc_port_end: 5801
      userid: 'root'
      password: 'password'
    manageiq_connection:
      url: 'https://127.0.0.1'
      token: 'VeryLongToken'
      validate_certs: true

- name: Create a new Azure provider in ManageIQ
  manageiq_provider:
    name: 'EngAzure'
    type: 'Azure'
    provider_region: 'northeurope'
    subscription: 'e272bd74-f661-484f-b223-88dd128a4049'
    azure_tenant_id: 'e272bd74-f661-484f-b223-88dd128a4048'
    state: 'present'
    provider:
      hostname: 'azure.example.com'
      userid: 'e272bd74-f661-484f-b223-88dd128a4049'
      password: 'password'
    manageiq_connection:
      url: 'https://cf-6af0.rhpds.opentlc.com'
      username: 'admin'
      password: 'password'
      validate_certs: false

- name: Create a new OpenStack Director provider in ManageIQ with rsa keypair
  manageiq_provider:
    name: 'EngDirector'
    type: 'Director'
    api_version: 'v3'
    state: 'present'
    provider:
      hostname: 'director.example.com'
      userid: 'admin'
      password: 'password'
      security_protocol: 'ssl-with-validation'
      validate_certs: 'true'
      certificate_authority: |
        -----BEGIN CERTIFICATE-----
        FAKECERTsdKgAwIBAgIBATANBgkqhkiG9w0BAQsFADAmMSQwIgYDVQQDDBtvcGVu
        c2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkwHhcNMTcwODIxMTI1NTE5WhcNMjIwODIw
        MTI1NTIwWjAmMSQwIgYDVQQDDBtvcGVuc2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkw
        ggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDUDnL2tQ2xf/zO7F7hmZ4S
        ZuwKENdI4IYuWSxye4i3hPhKg6eKPzGzmDNWkIMDOrDAj1EgVSNPtPwsOL8OWvJm
        AaTjr070D7ZGWWnrrDrWEClBx9Rx/6JAM38RT8Pu7c1hXBm0J81KufSLLYiZ/gOw
        Znks5v5RUSGcAXvLkBJeATbsbh6fKX0RgQ3fFTvqQaE/r8LxcTN1uehPX1g5AaRa
        z/SNDHaFtQlE3XcqAAukyMn4N5kdNcuwF3GlQ+tJnJv8SstPkfQcZbTMUQ7I2KpJ
        ajXnMxmBhV5fCN4rb0QUNCrk2/B+EUMBY4MnxIakqNxnN1kvgI7FBbFgrHUe6QvJ
        AgMBAAGjIzAhMA4GA1UdDwEB/wQEAwICpDAPBgNVHRMBAf8EBTADAQH/MA0GCSqG
        SIb3DQEBCwUAA4IBAQAYRV57LUsqznSLZHA77o9+0fQetIE115DYP7wea42PODJI
        QJ+JETEfoCr0+YOMAbVmznP9GH5cMTKEWHExcIpbMBU7nMZp6A3htcJgF2fgPzOA
        aTUtzkuVCSrV//mbbYVxoFOc6sR3Br0wBs5+5iz3dBSt7xmgpMzZvqsQl655i051
        gGSTIY3z5EJmBZBjwuTjal9mMoPGA4eoTPqlITJDHQ2bdCV2oDbc7zqupGrUfZFA
        qzgieEyGzdCSRwjr1/PibA3bpwHyhD9CGD0PRVVTLhw6h6L5kuN1jA20OfzWxf/o
        XUsdmRaWiF+l4s6Dcd56SuRp5SGNa2+vP9Of/FX5
        -----END CERTIFICATE-----
    ssh_keypair:
      hostname: director.example.com
      userid: heat-admin
      auth_key: 'SecretSSHPrivateKey'

- name: Create a new OpenStack provider in ManageIQ with amqp metrics
  manageiq_provider:
    name: 'EngOpenStack'
    type: 'OpenStack'
    api_version: 'v3'
    state: 'present'
    provider_region: 'europe'
    tenant_mapping_enabled: 'False'
    keystone_v3_domain_id: 'mydomain'
    provider:
      hostname: 'openstack.example.com'
      userid: 'admin'
      password: 'password'
      security_protocol: 'ssl-with-validation'
      validate_certs: 'true'
      certificate_authority: |
        -----BEGIN CERTIFICATE-----
        FAKECERTsdKgAwIBAgIBATANBgkqhkiG9w0BAQsFADAmMSQwIgYDVQQDDBtvcGVu
        c2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkwHhcNMTcwODIxMTI1NTE5WhcNMjIwODIw
        MTI1NTIwWjAmMSQwIgYDVQQDDBtvcGVuc2hpZnQtc2lnbmVyQDE1MDMzMjAxMTkw
        ggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDUDnL2tQ2xf/zO7F7hmZ4S
        ZuwKENdI4IYuWSxye4i3hPhKg6eKPzGzmDNWkIMDOrDAj1EgVSNPtPwsOL8OWvJm
        AaTjr070D7ZGWWnrrDrWEClBx9Rx/6JAM38RT8Pu7c1hXBm0J81KufSLLYiZ/gOw
        Znks5v5RUSGcAXvLkBJeATbsbh6fKX0RgQ3fFTvqQaE/r8LxcTN1uehPX1g5AaRa
        z/SNDHaFtQlE3XcqAAukyMn4N5kdNcuwF3GlQ+tJnJv8SstPkfQcZbTMUQ7I2KpJ
        ajXnMxmBhV5fCN4rb0QUNCrk2/B+EUMBY4MnxIakqNxnN1kvgI7FBbFgrHUe6QvJ
        AgMBAAGjIzAhMA4GA1UdDwEB/wQEAwICpDAPBgNVHRMBAf8EBTADAQH/MA0GCSqG
        SIb3DQEBCwUAA4IBAQAYRV57LUsqznSLZHA77o9+0fQetIE115DYP7wea42PODJI
        QJ+JETEfoCr0+YOMAbVmznP9GH5cMTKEWHExcIpbMBU7nMZp6A3htcJgF2fgPzOA
        aTUtzkuVCSrV//mbbYVxoFOc6sR3Br0wBs5+5iz3dBSt7xmgpMzZvqsQl655i051
        gGSTIY3z5EJmBZBjwuTjal9mMoPGA4eoTPqlITJDHQ2bdCV2oDbc7zqupGrUfZFA
        qzgieEyGzdCSRwjr1/PibA3bpwHyhD9CGD0PRVVTLhw6h6L5kuN1jA20OfzWxf/o
        XUsdmRaWiF+l4s6Dcd56SuRp5SGNa2+vP9Of/FX5
        -----END CERTIFICATE-----
    metrics:
      role: amqp
      hostname: 'amqp.example.com'
      security_protocol: 'non-ssl'
      port: 5666
      userid: admin
      password: password


- name: Create a new GCE provider in ManageIQ
  manageiq_provider:
    name: 'EngGoogle'
    type: 'GCE'
    provider_region: 'europe-west1'
    project: 'project1'
    state: 'present'
    provider:
      hostname: 'gce.example.com'
      auth_key: 'google_json_key'
      validate_certs: 'false'
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.manageiq import ManageIQ, manageiq_argument_spec


def supported_providers():
    return dict(
        Openshift=dict(
            class_name='ManageIQ::Providers::Openshift::ContainerManager',
            authtype='bearer',
            default_role='default',
            metrics_role='prometheus',
            alerts_role='prometheus_alerts',
        ),
        Amazon=dict(
            class_name='ManageIQ::Providers::Amazon::CloudManager',
        ),
        oVirt=dict(
            class_name='ManageIQ::Providers::Redhat::InfraManager',
            default_role='default',
            metrics_role='metrics',
        ),
        VMware=dict(
            class_name='ManageIQ::Providers::Vmware::InfraManager',
        ),
        Azure=dict(
            class_name='ManageIQ::Providers::Azure::CloudManager',
        ),
        Director=dict(
            class_name='ManageIQ::Providers::Openstack::InfraManager',
            ssh_keypair_role="ssh_keypair"
        ),
        OpenStack=dict(
            class_name='ManageIQ::Providers::Openstack::CloudManager',
        ),
        GCE=dict(
            class_name='ManageIQ::Providers::Google::CloudManager',
        ),
    )


def endpoint_list_spec():
    return dict(
        provider=dict(type='dict', options=endpoint_argument_spec()),
        metrics=dict(type='dict', options=endpoint_argument_spec()),
        alerts=dict(type='dict', options=endpoint_argument_spec()),
        ssh_keypair=dict(type='dict', options=endpoint_argument_spec()),
    )


def endpoint_argument_spec():
    return dict(
        role=dict(),
        hostname=dict(required=True),
        port=dict(type='int'),
        validate_certs=dict(default=True, type='bool', aliases=['verify_ssl']),
        certificate_authority=dict(),
        security_protocol=dict(
            choices=[
                'ssl-with-validation',
                'ssl-with-validation-custom-ca',
                'ssl-without-validation',
                'non-ssl',
            ],
        ),
        userid=dict(),
        password=dict(no_log=True),
        auth_key=dict(no_log=True),
        subscription=dict(no_log=True),
        project=dict(),
        uid_ems=dict(),
        path=dict(),
    )


def delete_nulls(h):
    """ Remove null entries from a hash

    Returns:
        a hash without nulls
    """
    if isinstance(h, list):
        return map(delete_nulls, h)
    if isinstance(h, dict):
        return dict((k, delete_nulls(v)) for k, v in h.items() if v is not None)

    return h


class ManageIQProvider(object):
    """
        Object to execute provider management operations in manageiq.
    """

    def __init__(self, manageiq):
        self.manageiq = manageiq

        self.module = self.manageiq.module
        self.api_url = self.manageiq.api_url
        self.client = self.manageiq.client

    def class_name_to_type(self, class_name):
        """ Convert class_name to type

        Returns:
            the type
        """
        out = [k for k, v in supported_providers().items() if v['class_name'] == class_name]
        if len(out) == 1:
            return out[0]

        return None

    def zone_id(self, name):
        """ Search for zone id by zone name.

        Returns:
            the zone id, or send a module Fail signal if zone not found.
        """
        zone = self.manageiq.find_collection_resource_by('zones', name=name)
        if not zone:  # zone doesn't exist
            self.module.fail_json(
                msg="zone %s does not exist in manageiq" % (name))

        return zone['id']

    def provider(self, name):
        """ Search for provider object by name.

        Returns:
            the provider, or None if provider not found.
        """
        return self.manageiq.find_collection_resource_by('providers', name=name)

    def build_connection_configurations(self, provider_type, endpoints):
        """ Build "connection_configurations" objects from
        requested endpoints provided by user

        Returns:
            the user requested provider endpoints list
        """
        connection_configurations = []
        endpoint_keys = endpoint_list_spec().keys()
        provider_defaults = supported_providers().get(provider_type, {})

        # get endpoint defaults
        endpoint = endpoints.get('provider')
        default_auth_key = endpoint.get('auth_key')

        # build a connection_configuration object for each endpoint
        for endpoint_key in endpoint_keys:
            endpoint = endpoints.get(endpoint_key)
            if endpoint:
                # get role and authtype
                role = endpoint.get('role') or provider_defaults.get(endpoint_key + '_role', 'default')
                if role == 'default':
                    authtype = provider_defaults.get('authtype') or role
                else:
                    authtype = role

                # set a connection_configuration
                connection_configurations.append({
                    'endpoint': {
                        'role': role,
                        'hostname': endpoint.get('hostname'),
                        'port': endpoint.get('port'),
                        'verify_ssl': [0, 1][endpoint.get('validate_certs', True)],
                        'security_protocol': endpoint.get('security_protocol'),
                        'certificate_authority': endpoint.get('certificate_authority'),
                        'path': endpoint.get('path'),
                    },
                    'authentication': {
                        'authtype': authtype,
                        'userid': endpoint.get('userid'),
                        'password': endpoint.get('password'),
                        'auth_key': endpoint.get('auth_key') or default_auth_key,
                    }
                })

        return connection_configurations

    def delete_provider(self, provider):
        """ Deletes a provider from manageiq.

        Returns:
            a short message describing the operation executed.
        """
        try:
            url = '%s/providers/%s' % (self.api_url, provider['id'])
            result = self.client.post(url, action='delete')
        except Exception as e:
            self.module.fail_json(msg="failed to delete provider %s: %s" % (provider['name'], str(e)))

        return dict(changed=True, msg=result['message'])

    def edit_provider(self, provider, name, provider_type, endpoints, zone_id, provider_region,
                      host_default_vnc_port_start, host_default_vnc_port_end,
                      subscription, project, uid_ems, tenant_mapping_enabled, api_version):
        """ Edit a provider from manageiq.

        Returns:
            a short message describing the operation executed.
        """
        url = '%s/providers/%s' % (self.api_url, provider['id'])

        resource = dict(
            name=name,
            zone={'id': zone_id},
            provider_region=provider_region,
            connection_configurations=endpoints,
            host_default_vnc_port_start=host_default_vnc_port_start,
            host_default_vnc_port_end=host_default_vnc_port_end,
            subscription=subscription,
            project=project,
            uid_ems=uid_ems,
            tenant_mapping_enabled=tenant_mapping_enabled,
            api_version=api_version,
        )

        # NOTE: we do not check for diff's between requested and current
        #       provider, we always submit endpoints with password or auth_keys,
        #       since we can not compare with current password or auth_key,
        #       every edit request is sent to ManageIQ API without comparing
        #       it to current state.

        # clean nulls, we do not send nulls to the api
        resource = delete_nulls(resource)

        # try to update provider
        try:
            result = self.client.post(url, action='edit', resource=resource)
        except Exception as e:
            self.module.fail_json(msg="failed to update provider %s: %s" % (provider['name'], str(e)))

        return dict(
            changed=True,
            msg="successfully updated the provider %s: %s" % (provider['name'], result))

    def create_provider(self, name, provider_type, endpoints, zone_id, provider_region,
                        host_default_vnc_port_start, host_default_vnc_port_end,
                        subscription, project, uid_ems, tenant_mapping_enabled, api_version):
        """ Creates the provider in manageiq.

        Returns:
            a short message describing the operation executed.
        """
        resource = dict(
            name=name,
            zone={'id': zone_id},
            provider_region=provider_region,
            host_default_vnc_port_start=host_default_vnc_port_start,
            host_default_vnc_port_end=host_default_vnc_port_end,
            subscription=subscription,
            project=project,
            uid_ems=uid_ems,
            tenant_mapping_enabled=tenant_mapping_enabled,
            api_version=api_version,
            connection_configurations=endpoints,
        )

        # clean nulls, we do not send nulls to the api
        resource = delete_nulls(resource)

        # try to create a new provider
        try:
            url = '%s/providers' % (self.api_url)
            result = self.client.post(url, type=supported_providers()[provider_type]['class_name'], **resource)
        except Exception as e:
            self.module.fail_json(msg="failed to create provider %s: %s" % (name, str(e)))

        return dict(
            changed=True,
            msg="successfully created the provider %s: %s" % (name, result['results']))

    def refresh(self, provider, name):
        """ Trigger provider refresh.

        Returns:
            a short message describing the operation executed.
        """
        try:
            url = '%s/providers/%s' % (self.api_url, provider['id'])
            result = self.client.post(url, action='refresh')
        except Exception as e:
            self.module.fail_json(msg="failed to refresh provider %s: %s" % (name, str(e)))

        return dict(
            changed=True,
            msg="refreshing provider %s" % name)


def main():
    zone_id = None
    endpoints = []
    argument_spec = dict(
        state=dict(choices=['absent', 'present', 'refresh'], default='present'),
        name=dict(required=True),
        zone=dict(default='default'),
        provider_region=dict(),
        host_default_vnc_port_start=dict(),
        host_default_vnc_port_end=dict(),
        subscription=dict(),
        project=dict(),
        azure_tenant_id=dict(aliases=['keystone_v3_domain_id']),
        tenant_mapping_enabled=dict(default=False, type='bool'),
        api_version=dict(choices=['v2', 'v3']),
        type=dict(choices=supported_providers().keys()),
    )
    # add the manageiq connection arguments to the arguments
    argument_spec.update(manageiq_argument_spec())
    # add the endpoint arguments to the arguments
    argument_spec.update(endpoint_list_spec())

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ('state', 'present', ['provider']),
            ('state', 'refresh', ['name'])],
        required_together=[
            ['host_default_vnc_port_start', 'host_default_vnc_port_end']
        ],
    )

    name = module.params['name']
    zone_name = module.params['zone']
    provider_type = module.params['type']
    raw_endpoints = module.params
    provider_region = module.params['provider_region']
    host_default_vnc_port_start = module.params['host_default_vnc_port_start']
    host_default_vnc_port_end = module.params['host_default_vnc_port_end']
    subscription = module.params['subscription']
    uid_ems = module.params['azure_tenant_id']
    project = module.params['project']
    tenant_mapping_enabled = module.params['tenant_mapping_enabled']
    api_version = module.params['api_version']
    state = module.params['state']

    manageiq = ManageIQ(module)
    manageiq_provider = ManageIQProvider(manageiq)

    provider = manageiq_provider.provider(name)

    # provider should not exist
    if state == "absent":
        # if we have a provider, delete it
        if provider:
            res_args = manageiq_provider.delete_provider(provider)
        # if we do not have a provider, nothing to do
        else:
            res_args = dict(
                changed=False,
                msg="provider %s: does not exist in manageiq" % (name))

    # provider should exist
    if state == "present":
        # get data user did not explicitly give
        if zone_name:
            zone_id = manageiq_provider.zone_id(zone_name)

        # if we do not have a provider_type, use the current provider_type
        if provider and not provider_type:
            provider_type = manageiq_provider.class_name_to_type(provider['type'])

        # check supported_providers types
        if not provider_type:
            manageiq_provider.module.fail_json(
                msg="missing required argument: provider_type")

        # check supported_providers types
        if provider_type not in supported_providers().keys():
            manageiq_provider.module.fail_json(
                msg="provider_type %s is not supported" % (provider_type))

        # build "connection_configurations" objects from user requested endpoints
        # "provider" is a required endpoint, if we have it, we have endpoints
        if raw_endpoints.get("provider"):
            endpoints = manageiq_provider.build_connection_configurations(provider_type, raw_endpoints)

        # if we have a provider, edit it
        if provider:
            res_args = manageiq_provider.edit_provider(provider, name, provider_type, endpoints, zone_id, provider_region,
                                                       host_default_vnc_port_start, host_default_vnc_port_end,
                                                       subscription, project, uid_ems, tenant_mapping_enabled, api_version)
        # if we do not have a provider, create it
        else:
            res_args = manageiq_provider.create_provider(name, provider_type, endpoints, zone_id, provider_region,
                                                         host_default_vnc_port_start, host_default_vnc_port_end,
                                                         subscription, project, uid_ems, tenant_mapping_enabled, api_version)

    # refresh provider (trigger sync)
    if state == "refresh":
        if provider:
            res_args = manageiq_provider.refresh(provider, name)
        else:
            res_args = dict(
                changed=False,
                msg="provider %s: does not exist in manageiq" % (name))

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
