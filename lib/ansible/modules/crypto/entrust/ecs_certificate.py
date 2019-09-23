#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c), Entrust Datacard Corporation, 2019
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ecs_certificate
author:
    - Chris Trufan (@ctrufan)
version_added: '2.9'
short_description: Request SSL/TLS certificates with the Entrust Certificate Services (ECS) API
description:
    - Create, reissue, and renew certificates with the Entrust Certificate Services (ECS) API.
    - Requires credentials for the L(Entrust Certificate Services,https://www.entrustdatacard.com/products/categories/ssl-certificates) (ECS) API.
    - In order to request a certificate, the domain and organization used in the certificate signing request must be already
      validated in the ECS system. It is I(not) the responsibility of this module to perform those steps.
notes:
    - C(path) must be specified as the output location of the certificate.
requirements:
    - cryptography >= 1.6
options:
    backup:
        description:
            - Path to store a backup of the initial certificate, if I(path) pointed to an existing file certificate.
        type: bool
        default: false
    force:
        description:
            - If force is used, a certificate is requested regardless of whether I(path) points to an existing valid certificate.
            - If C(request_type=renew), a forced renew will fail if the certificate being renewed has been issued within the past 30 days, regardless of the
              value of I(remaining_days) or the return value of I(cert_days) - the ECS API does not support the "renew" operation for certificates that are not
              at least 30 days old.
        type: bool
        default: false
    path:
        description:
            - Path to put the certificate file as a PEM encoded cert.
            - If the certificate at this location is not an Entrust issued certificate, a new certificate will always be requested regardless of validity.
            - If there is already an Entrust certificate at this location, whether it is replaced is dependent upon the I(remaining_days) calculation.
            - If an existing certificate is being replaced (see I(remaining_days), I(force), I(tracking_id)), the operation taken to replace it is dependent
              on I(request_type)
        type: path
        required: true
    full_chain_path:
        description:
            - Path to put the full certificate chain of the certificate, intermediates, and roots.
        type: path
    csr:
        description:
            - Base-64 encoded Certificate Signing Request (CSR). I(csr) is accepted with or without PEM formatting around the Base-64 string.
            - If no I(csr) is provided when C(request_type=reissue) or C(request_type=renew), the certificate will be generated with the same public key as
              the certificate being renewed or reissued.
            - If I(subject_alt_name) is specified, it will override the subject alternate names in the CSR.
            - If I(eku) is specified, it will override the extended key usage in the CSR.
            - If I(ou) is specified, it will override the organizational units "ou=" present in the subject distinguished name of the CSR, if any.
            - The organization "O=" field from the CSR will not be used. It will be replaced in the issued certificate by I(org) if present, and if not present,
              the organization tied to I(client_id).
        type: str
    tracking_id:
        description:
            - Tracking ID of certificate to reissue or renew.
            - I(tracking_id) is invalid if C(request_type=new) or C(request_type=validate_only).
            - If there is a certificate present in I(path) and it is an ECS certificate, I(tracking_id) will be ignored.
            - If there is not a certificate present in I(path) or there is but it is from another provider, the certificate represented by I(tracking_id) will
              be renewed or reissued and saved to I(path).
            - If there is not a certificate present in I(path) and the I(force) and I(remaining_days) parameters do not indicate a new certificate is needed,
              the certificate referenced by I(tracking_id) certificate will be saved to I(path).
            - This can be used when a known certificate is not currently present on a server, but you want to renew or reissue it to be managed by an ansible
              playbook. For example, if you specify C(request_type=renew), I(tracking_id) of an issued certificate, and I(path) to a file that does not exist,
              the first run of a task will download the certificate specified by I(tracking_id) (assuming it is still valid), and future runs of the task will
              (if applicable - see I(force) and I(remaining_days)) renew the certificate now present in I(path).
        type: int
    remaining_days:
        description:
            - The number of days the certificate must have left being valid. If C(cert_days < remaining_days) then a new certificate will be
              obtained using I(request_type).
            - If C(request_type=renew), a renew will fail if the certificate being renewed has been issued within the past 30 days, so do not set a
              I(remaining_days) value that is within 30 days of the full lifetime of the certificate being acted upon. (e.g. if you are requesting Certificates
              with a 90 day lifetime, do not set remaining_days to a value C(60) or higher).
            - The I(force) option may be used to ensure that a new certificate is always obtained.
        type: int
        default: 30
    request_type:
        description:
            - Operation performed if I(tracking_id) references a valid certificate to reissue, or there is already a certificate present in I(path) but either
              I(force) is specified or C(cert_days < remaining_days).
            - Specifying C(request_type=validate_only) means the request will be validated against the ECS API, but no certificate will be issued.
            - Specifying C(request_type=new) means a certificate request will always be submitted and a new certificate issued.
            - Specifying C(request_type=renew) means that an existing certificate (specified by I(tracking_id) if present, otherwise I(path)) will be renewed.
              If there is no certificate to renew, a new certificate is requested.
            - Specifying C(request_type=reissue) means that an existing certificate (specified by I(tracking_id) if present, otherwise I(path)) will be
              reissued.
              If there is no certificate to reissue, a new certificate is requested.
            - If a certificate was issued within the past 30 days, the 'renew' operation is not a valid operation and will fail.
            - Note that C(reissue) is an operation that will result in the revocation of the certificate that is reissued, be cautious with it's use.
            - I(check_mode) is only supported if C(request_type=new)
            - For example, setting C(request_type=renew) and C(remaining_days=30) and pointing to the same certificate on multiple playbook runs means that on
              the first run new certificate will be requested. It will then be left along on future runs until it is within 30 days of expiry, then the
              ECS "renew" operation will be performed.
        type: str
        choices: [ 'new', 'renew', 'reissue', 'validate_only']
        default: new
    cert_type:
        description:
            - The type of certificate product to request.
            - If a certificate is being reissued or renewed, this parameter is ignored, and the C(cert_type) of the initial certificate is used.
        type: str
        choices: [ 'STANDARD_SSL', 'ADVANTAGE_SSL', 'UC_SSL', 'EV_SSL', 'WILDCARD_SSL', 'PRIVATE_SSL', 'PD_SSL', 'CODE_SIGNING', 'EV_CODE_SIGNING',
                   'CDS_INDIVIDUAL', 'CDS_GROUP', 'CDS_ENT_LITE', 'CDS_ENT_PRO', 'SMIME_ENT' ]
    subject_alt_name:
        description:
            - The subject alternative name identifiers, as an array of values (applies to I(cert_type) with a value of C(STANDARD_SSL), C(ADVANTAGE_SSL),
              C(UC_SSL), C(EV_SSL), C(WILDCARD_SSL), C(PRIVATE_SSL), and C(PD_SSL)).
            - If you are requesting a new SSL certificate, and you pass a I(subject_alt_name) parameter, any SAN names in the CSR are ignored.
              If no subjectAltName parameter is passed, the SAN names in the CSR are used.
            - See I(request_type) to understand more about SANs during reissues and renewals.
            - In the case of certificates of type C(STANDARD_SSL) certificates, if the CN of the certificate is <domain>.<tld> only the www.<domain>.<tld> value
              is accepted. If the CN of the certificate is www.<domain>.<tld> only the <domain>.<tld> value is accepted.
        type: list
        elements: str
    eku:
        description:
            - If specified, overrides the key usage in the I(csr).
        type: str
        choices: [ SERVER_AUTH, CLIENT_AUTH, SERVER_AND_CLIENT_AUTH ]
    ct_log:
        description:
            - In compliance with browser requirements, this certificate may be posted to the Certificate Transparency (CT) logs. This is a best practice
              technique that helps domain owners monitor certificates issued to their domains. Note that not all certificates are eligible for CT logging.
            - If I(ct_log) is not specified, the certificate uses the account default.
            - If I(ct_log) is specified and the account settings allow it, I(ct_log) overrides the account default.
            - If I(ct_log) is set to C(false), but the account settings are set to "always log", the certificate generation will fail.
        type: bool
    client_id:
        description:
            - The client ID to submit the Certificate Signing Request under.
            - If no client ID is specified, the certificate will be submitted under the primary client with ID of 1.
            - When using a client other than the primary client, the I(org) parameter cannot be specified.
            - The issued certificate will have an organization value in the subject distinguished name represented by the client.
        type: int
        default: 1
    org:
        description:
            - Organization "O=" to include in the certificate.
            - If I(org) is not specified, the organization from the client represented by I(client_id) is used.
            - Unless the I(cert_type) is C(PD_SSL), this field may not be specified if the value of I(client_id) is not the primary client of "1". For all
              non-primary clients, certificates may only be issued with the organization of that client.
        type: str
    ou:
        description:
            - Organizational unit "OU=" to include in the certificate.
            - I(ou) behavior is dependent on whether organizational units are enabled for your account. If organizational unit support is disabled for your
              account, organizational units from the I(csr) and the I(ou) parameter are ignored.
            - If both I(csr) and I(ou) are specified, the value in I(ou) will override the OU fields present in the subject distinguished name in the I(csr)
            - If neither I(csr) nor I(ou) are specified for a renew or reissue operation, the OU fields in the initial certificate are reused.
            - An invalid OU from I(csr) is ignored, but any invalid organizational units in I(ou) will result in an error indicating "Unapproved OU". The I(ou)
              parameter can be used to force failure if an unapproved organizational unit is provided.
            - A maximum of one OU may be specified for current products. Multiple OUs are reserved for future products.
        type: list
        elements: str
    end_user_key_storage_agreement:
        description:
            - The end user of the Code Signing certificate must generate and store the private key for this request on cryptographically secure
              hardware to be compliant with the Entrust CSP and Subscription agreement. If requesting a certificate of type C(CODE_SIGNING) or
              C(EV_CODE_SIGNING), you must set I(end_user_key_storage_agreement) to true if and only if you acknowledge that you will inform the user of this
              requirement.
            - Applicable only to I(cert_type) of values C(CODE_SIGNING) and C(EV_CODE_SIGNING).
        type: bool
    tracking_info:
        description: Free form tracking information to attach to the record for the certificate.
        type: str
    requester_name:
        description: Requester name to associate with certificate tracking information.
        type: str
        required: true
    requester_email:
        description: Requester email to associate with certificate tracking information and receive delivery and expiry notices for the certificate.
        type: str
        required: true
    requester_phone:
        description: Requester phone number to associate with certificate tracking information.
        type: str
        required: true
    additional_emails:
        description: A list of additional email addresses to receive the delivery notice and expiry notification for the certificate.
        type: list
        elements: str
    custom_fields:
        description:
            - Mapping of custom fields to associate with the certificate request and certificate.
            - Only supported if custom fields are enabled for your account.
            - Each custom field specified must be a custom field you have defined for your account.
        type: dict
        suboptions:
            text1:
                description: Custom text field of maximum size 500.
                type: str
            text2:
                description: Custom text field of maximum size 500.
                type: str
            text3:
                description: Custom text field of maximum size 500.
                type: str
            text4:
                description: Custom text field of maximum size 500.
                type: str
            text5:
                description: Custom text field of maximum size 500.
                type: str
            text6:
                description: Custom text field of maximum size 500.
                type: str
            text7:
                description: Custom text field of maximum size 500.
                type: str
            text8:
                description: Custom text field of maximum size 500.
                type: str
            text9:
                description: Custom text field of maximum size 500.
                type: str
            text10:
                description: Custom text field of maximum size 500.
                type: str
            text11:
                description: Custom text field of maximum size 500.
                type: str
            text12:
                description: Custom text field of maximum size 500.
                type: str
            text13:
                description: Custom text field of maximum size 500.
                type: str
            text14:
                description: Custom text field of maximum size 500.
                type: str
            text15:
                description: Custom text field of maximum size 500.
                type: str
            number1:
                description: Custom number field.
                type: float
            number2:
                description: Custom number field.
                type: float
            number3:
                description: Custom number field.
                type: float
            number4:
                description: Custom number field.
                type: float
            number5:
                description: Custom number field.
                type: float
            date1:
                description: Custom date field.
                type: str
            date2:
                description: Custom date field.
                type: str
            date3:
                description: Custom date field.
                type: str
            date4:
                description: Custom date field.
                type: str
            date5:
                description: Custom date field.
                type: str
            email1:
                description: Custom email field.
                type: str
            email2:
                description: Custom email field.
                type: str
            email3:
                description: Custom email field.
                type: str
            email4:
                description: Custom email field.
                type: str
            email5:
                description: Custom email field.
                type: str
            dropdown1:
                description: Custom dropdown field.
                type: str
            dropdown2:
                description: Custom dropdown field.
                type: str
            dropdown3:
                description: Custom dropdown field.
                type: str
            dropdown4:
                description: Custom dropdown field.
                type: str
            dropdown5:
                description: Custom dropdown field.
                type: str
    cert_expiry:
        description:
            - The date the certificate should be set to expire, as an RFC3339 compliant date or date-time. For example,
              C(2020-02-23), C(2020-02-23T15:00:00.05Z).
            - I(cert_expiry) is only supported for requests of C(request_type=new) or C(request_type=renew). If C(request_type=reissue),
              I(cert_expiry) will be used for the first certificate issuance, but subsequent issuances will have the same expiry as the initial
              certificate.
            - A reissued certificate will always have the same expiry as the original certificate.
            - Note that only the date (day, month, year) is supported for specifying expiry date. If you choose to specify an expiry time with the expiry date,
              the time will be adjusted to Eastern Standard Time (EST). This could have the unintended effect of moving your expiry date to the previous day.
            - Applies only to accounts with a pooling inventory model.
            - Only one of I(cert_expiry) or I(cert_lifetime) may be specified.
        type: str
    cert_lifetime:
        description:
            - The lifetime of the certificate.
            - Applies to all certificates for accounts with a non-pooling inventory model.
            - I(cert_lifetime) is only supported for requests of C(request_type=new) or C(request_type=renew). If C(request_type=reissue), I(cert_lifetime) will
              be used for the first certificate issuance, but subsequent issuances will have the same expiry as the initial certificate.
            - Applies to certificates of I(cert_type)=C(CDS_INDIVIDUAL, CDS_GROUP, CDS_ENT_LITE, CDS_ENT_PRO, SMIME_ENT) for accounts with a pooling inventory
              model.
            - C(P1Y) is a certificate with a 1 year lifetime.
            - C(P2Y) is a certificate with a 2 year lifetime.
            - C(P3Y) is a certificate with a 3 year lifetime.
            - Only one of I(cert_expiry) or I(cert_lifetime) may be specified.
        type: str
        choices: [ P1Y, P2Y, P3Y ]
seealso:
    - module: openssl_privatekey
      description: Can be used to create private keys (both for certificates and accounts).
    - module: openssl_csr
      description: Can be used to create a Certificate Signing Request (CSR).
extends_documentation_fragment:
    - ecs_credential
'''

EXAMPLES = r'''
- name: Request a new certificate from Entrust with bare minimum parameters.
        Will request a new certificate if current one is valid but within 30
        days of expiry. If replacing an existing file in path, will back it up.
  ecs_certificate:
    backup: true
    path: /etc/ssl/crt/ansible.com.crt
    full_chain_path: /etc/ssl/crt/ansible.com.chain.crt
    csr: /etc/ssl/csr/ansible.com.csr
    cert_type: EV_SSL
    requester_name: Jo Doe
    requester_email: jdoe@ansible.com
    requester_phone: 555-555-5555
    entrust_api_user: apiusername
    entrust_api_key: a^lv*32!cd9LnT
    entrust_api_client_cert_path: /etc/ssl/entrust/ecs-client.crt
    entrust_api_client_cert_key_path: /etc/ssl/entrust/ecs-client.key

- name: If there is no certificate present in path, request a new certificate
        of type EV_SSL. Otherwise, if there is an Entrust managed certificate
        in path and it is within 63 days of expiration, request a renew of that
        certificate.
  ecs_certificate:
    path: /etc/ssl/crt/ansible.com.crt
    csr: /etc/ssl/csr/ansible.com.csr
    cert_type: EV_SSL
    cert_expiry: '2020-08-20'
    request_type: renew
    remaining_days: 63
    requester_name: Jo Doe
    requester_email: jdoe@ansible.com
    requester_phone: 555-555-5555
    entrust_api_user: apiusername
    entrust_api_key: a^lv*32!cd9LnT
    entrust_api_client_cert_path: /etc/ssl/entrust/ecs-client.crt
    entrust_api_client_cert_key_path: /etc/ssl/entrust/ecs-client.key

- name: If there is no certificate present in path, download certificate
        specified by tracking_id if it is still valid. Otherwise, if the
        certificate is within 79 days of expiration, request a renew of that
        certificate and save it in path. This can be used to "migrate" a
        certificate to be Ansible managed.
  ecs_certificate:
    path: /etc/ssl/crt/ansible.com.crt
    csr: /etc/ssl/csr/ansible.com.csr
    tracking_id: 2378915
    request_type: renew
    remaining_days: 79
    entrust_api_user: apiusername
    entrust_api_key: a^lv*32!cd9LnT
    entrust_api_client_cert_path: /etc/ssl/entrust/ecs-client.crt
    entrust_api_client_cert_key_path: /etc/ssl/entrust/ecs-client.key

- name: Force a reissue of the certificate specified by tracking_id.
  ecs_certificate:
    path: /etc/ssl/crt/ansible.com.crt
    force: true
    tracking_id: 2378915
    request_type: reissue
    entrust_api_user: apiusername
    entrust_api_key: a^lv*32!cd9LnT
    entrust_api_client_cert_path: /etc/ssl/entrust/ecs-client.crt
    entrust_api_client_cert_key_path: /etc/ssl/entrust/ecs-client.key

- name: Request a new certificate with an alternative client. Note that the
        issued certificate will have it's Subject Distinguished Name use the
        organization details associated with that client, rather than what is
        in the CSR.
  ecs_certificate:
    path: /etc/ssl/crt/ansible.com.crt
    csr: /etc/ssl/csr/ansible.com.csr
    client_id: 2
    requester_name: Jo Doe
    requester_email: jdoe@ansible.com
    requester_phone: 555-555-5555
    entrust_api_user: apiusername
    entrust_api_key: a^lv*32!cd9LnT
    entrust_api_client_cert_path: /etc/ssl/entrust/ecs-client.crt
    entrust_api_client_cert_key_path: /etc/ssl/entrust/ecs-client.key

- name: Request a new certificate with a number of CSR parameters overridden
        and tracking information
  ecs_certificate:
    path: /etc/ssl/crt/ansible.com.crt
    full_chain_path: /etc/ssl/crt/ansible.com.chain.crt
    csr: /etc/ssl/csr/ansible.com.csr
    subject_alt_name:
      - ansible.testcertificates.com
      - www.testcertificates.com
    eku: SERVER_AND_CLIENT_AUTH
    ct_log: true
    org: Test Organization Inc.
    ou:
      - Administration
    tracking_info: "Submitted via Ansible"
    additional_emails:
      - itsupport@testcertificates.com
      - jsmith@ansible.com
    custom_fields:
      text1: Admin
      text2: Invoice 25
      number1: 342
      date1: '2018-01-01'
      email1: sales@ansible.testcertificates.com
      dropdown1: red
    cert_expiry: '2020-08-15'
    requester_name: Jo Doe
    requester_email: jdoe@ansible.com
    requester_phone: 555-555-5555
    entrust_api_user: apiusername
    entrust_api_key: a^lv*32!cd9LnT
    entrust_api_client_cert_path: /etc/ssl/entrust/ecs-client.crt
    entrust_api_client_cert_key_path: /etc/ssl/entrust/ecs-client.key

'''

RETURN = '''
filename:
    description: Path to the generated Certificate.
    returned: changed or success
    type: str
    sample: /etc/ssl/crt/www.ansible.com.crt
backup_file:
    description: Name of backup file created for the certificate.
    returned: changed and if I(backup) is C(true)
    type: str
    sample: /path/to/www.ansible.com.crt.2019-03-09@11:22~
backup_full_chain_file:
    description: Name of the backup file created for the certificate chain.
    returned: changed and if I(backup) is C(true) and I(full_chain_path) is set.
    type: str
    sample: /path/to/ca.chain.crt.2019-03-09@11:22~
tracking_id:
    description: The tracking ID to reference and track the certificate in ECS.
    returned: success
    type: int
    sample: 380079
serial_number:
    description: The serial number of the issued certificate.
    returned: success
    type: int
    sample: 1235262234164342
cert_days:
    description: The number of days the certificate remains valid.
    returned: success
    type: int
    sample: 253
cert_status:
    description:
        - The certificate status in ECS.
        - 'Current possible values (which may be expanded in the future) are: C(ACTIVE), C(APPROVED), C(DEACTIVATED), C(DECLINED), C(EXPIRED), C(NA),
          C(PENDING), C(PENDING_QUORUM), C(READY), C(REISSUED), C(REISSUING), C(RENEWED), C(RENEWING), C(REVOKED), C(SUSPENDED)'
    returned: success
    type: str
    sample: ACTIVE
cert_details:
    description:
        - The full response JSON from the Get Certificate call of the ECS API.
        - 'While the response contents are guaranteed to be forwards compatible with new ECS API releases, Entrust recommends that you do not make any
          playbooks take actions based on the content of this field. However it may be useful for debugging, logging, or auditing purposes.'
    returned: success
    type: dict

'''

from ansible.module_utils.ecs.api import (
    ecs_client_argument_spec,
    ECSClient,
    RestOperationException,
    SessionConfigurationException,
)

import datetime
import json
import os
import re
import time
import traceback
from distutils.version import LooseVersion

from ansible.module_utils import crypto as crypto_utils
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native, to_bytes

CRYPTOGRAPHY_IMP_ERR = None
try:
    import cryptography
    CRYPTOGRAPHY_VERSION = LooseVersion(cryptography.__version__)
except ImportError:
    CRYPTOGRAPHY_IMP_ERR = traceback.format_exc()
    CRYPTOGRAPHY_FOUND = False
else:
    CRYPTOGRAPHY_FOUND = True

MINIMAL_CRYPTOGRAPHY_VERSION = '1.6'


def validate_cert_expiry(cert_expiry):
    search_string_partial = re.compile(r'^([0-9]+)-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])\Z')
    search_string_full = re.compile(r'^([0-9]+)-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3]):([0-5][0-9]):'
                                    r'([0-5][0-9]|60)(.[0-9]+)?(([Zz])|([+|-]([01][0-9]|2[0-3]):[0-5][0-9]))\Z')
    if search_string_partial.match(cert_expiry) or search_string_full.match(cert_expiry):
        return True
    return False


def calculate_cert_days(expires_after):
    cert_days = 0
    if expires_after:
        expires_after_datetime = datetime.datetime.strptime(expires_after, '%Y-%m-%dT%H:%M:%SZ')
        cert_days = (expires_after_datetime - datetime.datetime.now()).days
    return cert_days


# Populate the value of body[dict_param_name] with the JSON equivalent of
# module parameter of param_name if that parameter is present, otherwise leave field
# out of resulting dict
def convert_module_param_to_json_bool(module, dict_param_name, param_name):
    body = {}
    if module.params[param_name] is not None:
        if module.params[param_name]:
            body[dict_param_name] = 'true'
        else:
            body[dict_param_name] = 'false'
    return body


class EcsCertificate(object):
    '''
    Entrust Certificate Services certificate class.
    '''

    def __init__(self, module):
        self.path = module.params['path']
        self.full_chain_path = module.params['full_chain_path']
        self.force = module.params['force']
        self.backup = module.params['backup']
        self.request_type = module.params['request_type']
        self.csr = module.params['csr']

        # All return values
        self.changed = False
        self.filename = None
        self.tracking_id = None
        self.cert_status = None
        self.serial_number = None
        self.cert_days = None
        self.cert_details = None
        self.backup_file = None
        self.backup_full_chain_file = None

        self.cert = None
        self.ecs_client = None
        if self.path and os.path.exists(self.path):
            try:
                self.cert = crypto_utils.load_certificate(self.path, backend='cryptography')
            except Exception as dummy:
                self.cert = None
        # Instantiate the ECS client and then try a no-op connection to verify credentials are valid
        try:
            self.ecs_client = ECSClient(
                entrust_api_user=module.params['entrust_api_user'],
                entrust_api_key=module.params['entrust_api_key'],
                entrust_api_cert=module.params['entrust_api_client_cert_path'],
                entrust_api_cert_key=module.params['entrust_api_client_cert_key_path'],
                entrust_api_specification_path=module.params['entrust_api_specification_path']
            )
        except SessionConfigurationException as e:
            module.fail_json(msg='Failed to initialize Entrust Provider: {0}'.format(to_native(e)))
        try:
            self.ecs_client.GetAppVersion()
        except RestOperationException as e:
            module.fail_json(msg='Please verify credential information. Received exception when testing ECS connection: {0}'.format(to_native(e.message)))

    # Conversion of the fields that go into the 'tracking' parameter of the request object
    def convert_tracking_params(self, module):
        body = {}
        tracking = {}
        if module.params['requester_name']:
            tracking['requesterName'] = module.params['requester_name']
        if module.params['requester_email']:
            tracking['requesterEmail'] = module.params['requester_email']
        if module.params['requester_phone']:
            tracking['requesterPhone'] = module.params['requester_phone']
        if module.params['tracking_info']:
            tracking['trackingInfo'] = module.params['tracking_info']
        if module.params['custom_fields']:
            # Omit custom fields from submitted dict if not present, instead of submitting them with value of 'null'
            # The ECS API does technically accept null without error, but it complicates debugging user escalations and is unnecessary bandwidth.
            custom_fields = {}
            for k, v in module.params['custom_fields'].items():
                if v is not None:
                    custom_fields[k] = v
            tracking['customFields'] = custom_fields
        if module.params['additional_emails']:
            tracking['additionalEmails'] = module.params['additional_emails']
        body['tracking'] = tracking
        return body

    def convert_cert_subject_params(self, module):
        body = {}
        if module.params['subject_alt_name']:
            body['subjectAltName'] = module.params['subject_alt_name']
        if module.params['org']:
            body['org'] = module.params['org']
        if module.params['ou']:
            body['ou'] = module.params['ou']
        return body

    def convert_general_params(self, module):
        body = {}
        if module.params['eku']:
            body['eku'] = module.params['eku']
        if self.request_type == 'new':
            body['certType'] = module.params['cert_type']
        body['clientId'] = module.params['client_id']
        body.update(convert_module_param_to_json_bool(module, 'ctLog', 'ct_log'))
        body.update(convert_module_param_to_json_bool(module, 'endUserKeyStorageAgreement', 'end_user_key_storage_agreement'))
        return body

    def convert_expiry_params(self, module):
        body = {}
        if module.params['cert_lifetime']:
            body['certLifetime'] = module.params['cert_lifetime']
        elif module.params['cert_expiry']:
            body['certExpiryDate'] = module.params['cert_expiry']
        # If neither cerTLifetime or certExpiryDate was specified and the request type is new, default to 365 days
        elif self.request_type != 'reissue':
            gmt_now = datetime.datetime.fromtimestamp(time.mktime(time.gmtime()))
            expiry = gmt_now + datetime.timedelta(days=365)
            body['certExpiryDate'] = expiry.strftime("%Y-%m-%dT%H:%M:%S.00Z")
        return body

    def set_tracking_id_by_serial_number(self, module):
        try:
            # Use serial_number to identify if certificate is an Entrust Certificate
            # with an associated tracking ID
            serial_number = "{0:X}".format(self.cert.serial_number)
            cert_results = self.ecs_client.GetCertificates(serialNumber=serial_number).get('certificates', {})
            if len(cert_results) == 1:
                self.tracking_id = cert_results[0].get('trackingId')
        except RestOperationException as dummy:
            # If we fail to find a cert by serial number, that's fine, we just don't set self.tracking_id
            return

    def set_cert_details(self, module):
        try:
            self.cert_details = self.ecs_client.GetCertificate(trackingId=self.tracking_id)
            self.cert_status = self.cert_details.get('status')
            self.serial_number = self.cert_details.get('serialNumber')
            self.cert_days = calculate_cert_days(self.cert_details.get('expiresAfter'))
        except RestOperationException as e:
            module.fail_json('Failed to get details of certificate with tracking_id="{0}", Error: '.format(self.tracking_id), to_native(e.message))

    def check(self, module):
        if self.cert:
            # We will only treat a certificate as valid if it is found as a managed entrust cert.
            # We will only set updated tracking ID based on certificate in "path" if it is managed by entrust.
            self.set_tracking_id_by_serial_number(module)

            if module.params['tracking_id'] and self.tracking_id and module.params['tracking_id'] != self.tracking_id:
                module.warn('tracking_id parameter of "{0}" provided, but will be ignored. Valid certificate was present in path "{1}" with '
                            'tracking_id of "{2}".'.format(module.params['tracking_id'], self.path, self.tracking_id))

        # If we did not end up setting tracking_id based on existing cert, get from module params
        if not self.tracking_id:
            self.tracking_id = module.params['tracking_id']

        if not self.tracking_id:
            return False

        self.set_cert_details(module)

        if self.cert_status == 'EXPIRED' or self.cert_status == 'SUSPENDED' or self.cert_status == 'REVOKED':
            return False
        if self.cert_days < module.params['remaining_days']:
            return False

        return True

    def request_cert(self, module):
        if not self.check(module) or self.force:
            body = {}

            # Read the CSR contents
            if self.csr and os.path.exists(self.csr):
                with open(self.csr, 'r') as csr_file:
                    body['csr'] = csr_file.read()

            # Check if the path is already a cert
            # tracking_id may be set as a parameter or by get_cert_details if an entrust cert is in 'path'. If tracking ID is null
            # We will be performing a reissue operation.
            if self.request_type != 'new' and not self.tracking_id:
                module.warn('No existing Entrust certificate found in path={0} and no tracking_id was provided, setting request_type to "new" for this task'
                            'run. Future playbook runs that point to the pathination file in {1} will use request_type={2}'
                            .format(self.path, self.path, self.request_type))
                self.request_type = 'new'
            elif self.request_type == 'new' and self.tracking_id:
                module.warn('Existing certificate being acted upon, but request_type is "new", so will be a new certificate issuance rather than a'
                            'reissue or renew')
            # Use cases where request type is new and no existing certificate, or where request type is reissue/renew and a valid
            # existing certificate is found, do not need warnings.

            body.update(self.convert_tracking_params(module))
            body.update(self.convert_cert_subject_params(module))
            body.update(self.convert_general_params(module))
            body.update(self.convert_expiry_params(module))

            if not module.check_mode:
                try:
                    if self.request_type == 'validate_only':
                        body['validateOnly'] = 'true'
                        result = self.ecs_client.NewCertRequest(Body=body)
                    if self.request_type == 'new':
                        result = self.ecs_client.NewCertRequest(Body=body)
                    elif self.request_type == 'renew':
                        result = self.ecs_client.RenewCertRequest(trackingId=self.tracking_id, Body=body)
                    elif self.request_type == 'reissue':
                        result = self.ecs_client.ReissueCertRequest(trackingId=self.tracking_id, Body=body)
                    self.tracking_id = result.get('trackingId')
                    self.set_cert_details(module)
                except RestOperationException as e:
                    module.fail_json(msg='Failed to request new certificate from Entrust (ECS) {0}'.format(e.message))

                if self.request_type != 'validate_only':
                    if self.backup:
                        self.backup_file = module.backup_local(self.path)
                    crypto_utils.write_file(module, to_bytes(self.cert_details.get('endEntityCert')))
                    if self.full_chain_path and self.cert_details.get('chainCerts'):
                        if self.backup:
                            self.backup_full_chain_file = module.backup_local(self.full_chain_path)
                        chain_string = '\n'.join(self.cert_details.get('chainCerts')) + '\n'
                        crypto_utils.write_file(module, to_bytes(chain_string), path=self.full_chain_path)
                    self.changed = True
        # If there is no certificate present in path but a tracking ID was specified, save it to disk
        elif not os.path.exists(self.path) and self.tracking_id:
            if not module.check_mode:
                crypto_utils.write_file(module, to_bytes(self.cert_details.get('endEntityCert')))
                if self.full_chain_path and self.cert_details.get('chainCerts'):
                    chain_string = '\n'.join(self.cert_details.get('chainCerts')) + '\n'
                    crypto_utils.write_file(module, to_bytes(chain_string), path=self.full_chain_path)
            self.changed = True

    def dump(self):
        result = {
            'changed': self.changed,
            'filename': self.path,
            'tracking_id': self.tracking_id,
            'cert_status': self.cert_status,
            'serial_number': self.serial_number,
            'cert_days': self.cert_days,
            'cert_details': self.cert_details,
        }
        if self.backup_file:
            result['backup_file'] = self.backup_file
            result['backup_full_chain_file'] = self.backup_full_chain_file
        return result


def custom_fields_spec():
    return dict(
        text1=dict(type='str'),
        text2=dict(type='str'),
        text3=dict(type='str'),
        text4=dict(type='str'),
        text5=dict(type='str'),
        text6=dict(type='str'),
        text7=dict(type='str'),
        text8=dict(type='str'),
        text9=dict(type='str'),
        text10=dict(type='str'),
        text11=dict(type='str'),
        text12=dict(type='str'),
        text13=dict(type='str'),
        text14=dict(type='str'),
        text15=dict(type='str'),
        number1=dict(type='float'),
        number2=dict(type='float'),
        number3=dict(type='float'),
        number4=dict(type='float'),
        number5=dict(type='float'),
        date1=dict(type='str'),
        date2=dict(type='str'),
        date3=dict(type='str'),
        date4=dict(type='str'),
        date5=dict(type='str'),
        email1=dict(type='str'),
        email2=dict(type='str'),
        email3=dict(type='str'),
        email4=dict(type='str'),
        email5=dict(type='str'),
        dropdown1=dict(type='str'),
        dropdown2=dict(type='str'),
        dropdown3=dict(type='str'),
        dropdown4=dict(type='str'),
        dropdown5=dict(type='str'),
    )


def ecs_certificate_argument_spec():
    return dict(
        backup=dict(type='bool', default=False),
        force=dict(type='bool', default=False),
        path=dict(type='path', required=True),
        full_chain_path=dict(type='path'),
        tracking_id=dict(type='int'),
        remaining_days=dict(type='int', default=30),
        request_type=dict(type='str', default='new', choices=['new', 'renew', 'reissue', 'validate_only']),
        cert_type=dict(type='str', choices=['STANDARD_SSL',
                                            'ADVANTAGE_SSL',
                                            'UC_SSL',
                                            'EV_SSL',
                                            'WILDCARD_SSL',
                                            'PRIVATE_SSL',
                                            'PD_SSL',
                                            'CODE_SIGNING',
                                            'EV_CODE_SIGNING',
                                            'CDS_INDIVIDUAL',
                                            'CDS_GROUP',
                                            'CDS_ENT_LITE',
                                            'CDS_ENT_PRO',
                                            'SMIME_ENT',
                                            ]),
        csr=dict(type='str'),
        subject_alt_name=dict(type='list', elements='str'),
        eku=dict(type='str', choices=['SERVER_AUTH', 'CLIENT_AUTH', 'SERVER_AND_CLIENT_AUTH']),
        ct_log=dict(type='bool'),
        client_id=dict(type='int', default=1),
        org=dict(type='str'),
        ou=dict(type='list', elements='str'),
        end_user_key_storage_agreement=dict(type='bool'),
        tracking_info=dict(type='str'),
        requester_name=dict(type='str', required=True),
        requester_email=dict(type='str', required=True),
        requester_phone=dict(type='str', required=True),
        additional_emails=dict(type='list', elements='str'),
        custom_fields=dict(type='dict', default=None, options=custom_fields_spec()),
        cert_expiry=dict(type='str'),
        cert_lifetime=dict(type='str', choices=['P1Y', 'P2Y', 'P3Y']),
    )


def main():
    ecs_argument_spec = ecs_client_argument_spec()
    ecs_argument_spec.update(ecs_certificate_argument_spec())
    module = AnsibleModule(
        argument_spec=ecs_argument_spec,
        required_if=(
            ['request_type', 'new', ['cert_type']],
            ['request_type', 'validate_only', ['cert_type']],
            ['cert_type', 'CODE_SIGNING', ['end_user_key_storage_agreement']],
            ['cert_type', 'EV_CODE_SIGNING', ['end_user_key_storage_agreement']],
        ),
        mutually_exclusive=(
            ['cert_expiry', 'cert_lifetime'],
        ),
        supports_check_mode=True,
    )

    if not CRYPTOGRAPHY_FOUND or CRYPTOGRAPHY_VERSION < LooseVersion(MINIMAL_CRYPTOGRAPHY_VERSION):
        module.fail_json(msg=missing_required_lib('cryptography >= {0}'.format(MINIMAL_CRYPTOGRAPHY_VERSION)),
                         exception=CRYPTOGRAPHY_IMP_ERR)

    # If validate_only is used, pointing to an existing tracking_id is an invalid operation
    if module.params['tracking_id']:
        if module.params['request_type'] == 'new' or module.params['request_type'] == 'validate_only':
            module.fail_json(msg='The tracking_id field is invalid when request_type="{0}".'.format(module.params['request_type']))

    # A reissued request can not specify an expiration date or lifetime
    if module.params['request_type'] == 'reissue':
        if module.params['cert_expiry']:
            module.fail_json(msg='The cert_expiry field is invalid when request_type="reissue".')
        elif module.params['cert_lifetime']:
            module.fail_json(msg='The cert_lifetime field is invalid when request_type="reissue".')
    # Only a reissued request can omit the CSR
    else:
        module_params_csr = module.params['csr']
        if module_params_csr is None:
            module.fail_json(msg='The csr field is required when request_type={0}'.format(module.params['request_type']))
        elif not os.path.exists(module_params_csr):
            module.fail_json(msg='The csr field of {0} was not a valid path. csr is required when request_type={1}'.format(
                module_params_csr, module.params['request_type']))

    if module.params['ou'] and len(module.params['ou']) > 1:
        module.fail_json(msg='Multiple "ou" values are not currently supported.')

    if module.params['end_user_key_storage_agreement']:
        if module.params['cert_type'] != 'CODE_SIGNING' and module.params['cert_type'] != 'EV_CODE_SIGNING':
            module.fail_json(msg='Parameter "end_user_key_storage_agreement" is valid only for cert_types "CODE_SIGNING" and "EV_CODE_SIGNING"')

    if module.params['org'] and module.params['client_id'] != 1 and module.params['cert_type'] != 'PD_SSL':
        module.fail_json(msg='The "org" parameter is not supported when client_id parameter is set to a value other than 1, unless cert_type is "PD_SSL".')

    if module.params['cert_expiry']:
        if not validate_cert_expiry(module.params['cert_expiry']):
            module.fail_json(msg='The "cert_expiry" parameter of "{0}" is not a valid date or date-time'.format(module.params['cert_expiry']))

    certificate = EcsCertificate(module)
    certificate.request_cert(module)
    result = certificate.dump()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
