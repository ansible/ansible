#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: iam_cert
short_description: Manage server certificates for use on ELBs and CloudFront
description:
     - Allows for the management of server certificates
version_added: "2.0"
options:
  name:
    description:
      - Name of certificate to add, update or remove.
    required: true
    type: str
  new_name:
    description:
      - When state is present, this will update the name of the cert.
      - The cert, key and cert_chain parameters will be ignored if this is defined.
    type: str
  new_path:
    description:
      - When state is present, this will update the path of the cert.
      - The cert, key and cert_chain parameters will be ignored if this is defined.
    type: str
  state:
    description:
      - Whether to create(or update) or delete certificate.
      - If new_path or new_name is defined, specifying present will attempt to make an update these.
    required: true
    choices: [ "present", "absent" ]
    type: str
  path:
    description:
      - When creating or updating, specify the desired path of the certificate.
    default: "/"
    type: str
  cert_chain:
    description:
      - The path to, or content of the CA certificate chain in PEM encoded format.
        As of 2.4 content is accepted. If the parameter is not a file, it is assumed to be content.
    type: str
  cert:
    description:
      - The path to, or content of the certificate body in PEM encoded format.
        As of 2.4 content is accepted. If the parameter is not a file, it is assumed to be content.
    type: str
  key:
    description:
      - The path to, or content of the private key in PEM encoded format.
        As of 2.4 content is accepted. If the parameter is not a file, it is assumed to be content.
    type: str
  dup_ok:
    description:
      - By default the module will not upload a certificate that is already uploaded into AWS.
        If set to True, it will upload the certificate as long as the name is unique.
    default: False
    type: bool

requirements: [ "boto" ]
author: Jonathan I. Davila (@defionscode)
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Basic server certificate upload from local file
- iam_cert:
    name: very_ssl
    state: present
    cert: "{{ lookup('file', 'path/to/cert') }}"
    key: "{{ lookup('file', 'path/to/key') }}"
    cert_chain: "{{ lookup('file', 'path/to/certchain') }}"

# Basic server certificate upload
- iam_cert:
    name: very_ssl
    state: present
    cert: path/to/cert
    key: path/to/key
    cert_chain: path/to/certchain

# Server certificate upload using key string
- iam_cert:
    name: very_ssl
    state: present
    path: "/a/cert/path/"
    cert: body_of_somecert
    key: vault_body_of_privcertkey
    cert_chain: body_of_myverytrustedchain

# Basic rename of existing certificate
- iam_cert:
    name: very_ssl
    new_name: new_very_ssl
    state: present

'''
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, connect_to_aws
import os

try:
    import boto
    import boto.iam
    import boto.ec2
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


def cert_meta(iam, name):
    certificate = iam.get_server_certificate(name).get_server_certificate_result.server_certificate
    ocert = certificate.certificate_body
    opath = certificate.server_certificate_metadata.path
    ocert_id = certificate.server_certificate_metadata.server_certificate_id
    upload_date = certificate.server_certificate_metadata.upload_date
    exp = certificate.server_certificate_metadata.expiration
    arn = certificate.server_certificate_metadata.arn
    return opath, ocert, ocert_id, upload_date, exp, arn


def dup_check(module, iam, name, new_name, cert, orig_cert_names, orig_cert_bodies, dup_ok):
    update = False

    # IAM cert names are case insensitive
    names_lower = [n.lower() for n in [name, new_name] if n is not None]
    orig_cert_names_lower = [ocn.lower() for ocn in orig_cert_names]

    if any(ct in orig_cert_names_lower for ct in names_lower):
        for i_name in names_lower:
            if cert is not None:
                try:
                    c_index = orig_cert_names_lower.index(i_name)
                except NameError:
                    continue
                else:
                    # NOTE: remove the carriage return to strictly compare the cert bodies.
                    slug_cert = cert.replace('\r', '')
                    slug_orig_cert_bodies = orig_cert_bodies[c_index].replace('\r', '')
                    if slug_orig_cert_bodies == slug_cert:
                        update = True
                        break
                    elif slug_cert.startswith(slug_orig_cert_bodies):
                        update = True
                        break
                    else:
                        module.fail_json(changed=False, msg='A cert with the name %s already exists and'
                                         ' has a different certificate body associated'
                                         ' with it. Certificates cannot have the same name' % orig_cert_names[c_index])
            else:
                update = True
                break
    elif cert in orig_cert_bodies and not dup_ok:
        for crt_name, crt_body in zip(orig_cert_names, orig_cert_bodies):
            if crt_body == cert:
                module.fail_json(changed=False, msg='This certificate already'
                                                    ' exists under the name %s' % crt_name)

    return update


def cert_action(module, iam, name, cpath, new_name, new_path, state,
                cert, key, cert_chain, orig_cert_names, orig_cert_bodies, dup_ok):
    if state == 'present':
        update = dup_check(module, iam, name, new_name, cert, orig_cert_names,
                           orig_cert_bodies, dup_ok)
        if update:
            opath, ocert, ocert_id, upload_date, exp, arn = cert_meta(iam, name)
            changed = True
            if new_name and new_path:
                iam.update_server_cert(name, new_cert_name=new_name, new_path=new_path)
                module.exit_json(changed=changed, original_name=name, new_name=new_name,
                                 original_path=opath, new_path=new_path, cert_body=ocert,
                                 upload_date=upload_date, expiration_date=exp, arn=arn)
            elif new_name and not new_path:
                iam.update_server_cert(name, new_cert_name=new_name)
                module.exit_json(changed=changed, original_name=name, new_name=new_name,
                                 cert_path=opath, cert_body=ocert,
                                 upload_date=upload_date, expiration_date=exp, arn=arn)
            elif not new_name and new_path:
                iam.update_server_cert(name, new_path=new_path)
                module.exit_json(changed=changed, name=new_name,
                                 original_path=opath, new_path=new_path, cert_body=ocert,
                                 upload_date=upload_date, expiration_date=exp, arn=arn)
            else:
                changed = False
                module.exit_json(changed=changed, name=name, cert_path=opath, cert_body=ocert,
                                 upload_date=upload_date, expiration_date=exp, arn=arn,
                                 msg='No new path or name specified. No changes made')
        else:
            changed = True
            iam.upload_server_cert(name, cert, key, cert_chain=cert_chain, path=cpath)
            opath, ocert, ocert_id, upload_date, exp, arn = cert_meta(iam, name)
            module.exit_json(changed=changed, name=name, cert_path=opath, cert_body=ocert,
                             upload_date=upload_date, expiration_date=exp, arn=arn)
    elif state == 'absent':
        if name in orig_cert_names:
            changed = True
            iam.delete_server_cert(name)
            module.exit_json(changed=changed, deleted_cert=name)
        else:
            changed = False
            module.exit_json(changed=changed, msg='Certificate with the name %s already absent' % name)


def load_data(cert, key, cert_chain):
    # if paths are provided rather than lookups read the files and return the contents
    if cert and os.path.isfile(cert):
        with open(cert, 'r') as cert_fh:
            cert = cert_fh.read().rstrip()
    if key and os.path.isfile(key):
        with open(key, 'r') as key_fh:
            key = key_fh.read().rstrip()
    if cert_chain and os.path.isfile(cert_chain):
        with open(cert_chain, 'r') as cert_chain_fh:
            cert_chain = cert_chain_fh.read()
    return cert, key, cert_chain


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent']),
        name=dict(),
        cert=dict(),
        key=dict(no_log=True),
        cert_chain=dict(),
        new_name=dict(),
        path=dict(default='/'),
        new_path=dict(),
        dup_ok=dict(type='bool')
    )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['new_path', 'key'],
            ['new_path', 'cert'],
            ['new_path', 'cert_chain'],
            ['new_name', 'key'],
            ['new_name', 'cert'],
            ['new_name', 'cert_chain'],
        ],
    )

    if not HAS_BOTO:
        module.fail_json(msg="Boto is required for this module")

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    try:
        if region:
            iam = connect_to_aws(boto.iam, region, **aws_connect_kwargs)
        else:
            iam = boto.iam.connection.IAMConnection(**aws_connect_kwargs)
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json(msg=str(e))

    state = module.params.get('state')
    name = module.params.get('name')
    path = module.params.get('path')
    new_name = module.params.get('new_name')
    new_path = module.params.get('new_path')
    dup_ok = module.params.get('dup_ok')
    if state == 'present' and not new_name and not new_path:
        cert, key, cert_chain = load_data(cert=module.params.get('cert'),
                                          key=module.params.get('key'),
                                          cert_chain=module.params.get('cert_chain'))
    else:
        cert = key = cert_chain = None

    orig_cert_names = [ctb['server_certificate_name'] for ctb in
                       iam.get_all_server_certs().list_server_certificates_result.server_certificate_metadata_list]
    orig_cert_bodies = [iam.get_server_certificate(thing).get_server_certificate_result.certificate_body
                        for thing in orig_cert_names]
    if new_name == name:
        new_name = None
    if new_path == path:
        new_path = None

    changed = False
    try:
        cert_action(module, iam, name, path, new_name, new_path, state,
                    cert, key, cert_chain, orig_cert_names, orig_cert_bodies, dup_ok)
    except boto.exception.BotoServerError as err:
        module.fail_json(changed=changed, msg=str(err), debug=[cert, key])


if __name__ == '__main__':
    main()
