#!/usr/bin/python

# (c) 2016, Marcin Skarbek <github@skarbek.name>
# (c) 2016, Andreas Olsson <andreas@arrakis.se>
# (c) 2017, Loic Blot <loic.blot@unix-experience.fr>
#
# This module was ported from https://github.com/mskarbek/ansible-nsupdate
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: nsupdate

short_description: Manage DNS records.
description:
    - Create, update and remove DNS records using DDNS updates
    - DDNS works well with both bind and Microsoft DNS (see https://technet.microsoft.com/en-us/library/cc961412.aspx)
version_added: "2.3"
requirements:
  - dnspython
author: "Loic Blot (@nerzhul)"
options:
    state:
        description:
            - Manage DNS record.
        choices: ['present', 'absent']
        default: 'present'
    server:
        description:
            - Apply DNS modification on this server.
        required: true
    key_name:
        description:
            - Use TSIG key name to authenticate against DNS C(server)
    key_secret:
        description:
            - Use TSIG key secret, associated with C(key_name), to authenticate against C(server)
    key_algorithm:
        description:
            - Specify key algorithm used by C(key_secret).
        choices: ['HMAC-MD5.SIG-ALG.REG.INT', 'hmac-md5', 'hmac-sha1', 'hmac-sha224', 'hmac-sha256', 'hamc-sha384',
                  'hmac-sha512']
        default: 'hmac-md5'
    zone:
        description:
            - DNS record will be modified on this C(zone).
        required: true
    record:
        description:
            - Sets the DNS record to modify.
        required: true
    type:
        description:
            - Sets the record type.
        default: 'A'
    ttl:
        description:
            - Sets the record TTL.
        default: 3600
    value:
        description:
            - Sets the record value.
        default: None

'''

EXAMPLES = '''
- name: Add or modify ansible.example.org A to 192.168.1.1"
  nsupdate:
    key_name: "nsupdate"
    key_secret: "+bFQtBCta7j2vWkjPkAFtgA=="
    server: "10.1.1.1"
    zone: "example.org"
    record: "ansible"
    value: "192.168.1.1"

- name: Remove puppet.example.org CNAME
  nsupdate:
    key_name: "nsupdate"
    key_secret: "+bFQtBCta7j2vWkjPkAFtgA=="
    server: "10.1.1.1"
    zone: "example.org"
    record: "puppet"
    type: "CNAME"
    state: absent
'''

RETURN = '''
changed:
    description: If module has modified record
    returned: success
    type: string
record:
    description: DNS record
    returned: success
    type: string
    sample: 'ansible'
ttl:
    description: DNS record TTL
    returned: success
    type: int
    sample: 86400
type:
    description: DNS record type
    returned: success
    type: string
    sample: 'CNAME'
value:
    description: DNS record value
    returned: success
    type: string
    sample: '192.168.1.1'
zone:
    description: DNS record zone
    returned: success
    type: string
    sample: 'example.org.'
dns_rc:
    description: dnspython return code
    returned: always
    type: int
    sample: 4
dns_rc_str:
    description: dnspython return code (string representation)
    returned: always
    type: string
    sample: 'REFUSED'
'''

from binascii import Error as binascii_error
from socket import error as socket_error

try:
    import dns.update
    import dns.query
    import dns.tsigkeyring
    import dns.message
    import dns.resolver

    HAVE_DNSPYTHON = True
except ImportError:
    HAVE_DNSPYTHON = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class RecordManager(object):
    def __init__(self, module):
        self.module = module

        if module.params['zone'][-1] != '.':
            self.zone = module.params['zone'] + '.'
        else:
            self.zone = module.params['zone']

        if module.params['key_name']:
            try:
                self.keyring = dns.tsigkeyring.from_text({
                    module.params['key_name']: module.params['key_secret']
                })
            except TypeError:
                module.fail_json(msg='Missing key_secret')
            except binascii_error as e:
                module.fail_json(msg='TSIG key error: %s' % to_native(e))
        else:
            self.keyring = None

        if module.params['key_algorithm'] == 'hmac-md5':
            self.algorithm = 'HMAC-MD5.SIG-ALG.REG.INT'
        else:
            self.algorithm = module.params['key_algorithm']

        self.dns_rc = 0

    def __do_update(self, update):
        response = None
        try:
            response = dns.query.tcp(update, self.module.params['server'], timeout=10)
        except (dns.tsig.PeerBadKey, dns.tsig.PeerBadSignature) as e:
            self.module.fail_json(msg='TSIG update error (%s): %s' % (e.__class__.__name__, to_native(e)))
        except (socket_error, dns.exception.Timeout) as e:
            self.module.fail_json(msg='DNS server error: (%s): %s' % (e.__class__.__name__, to_native(e)))
        return response

    def create_or_update_record(self):
        result = {'changed': False, 'failed': False}

        exists = self.record_exists()
        if exists in [0, 2]:
            if self.module.check_mode:
                self.module.exit_json(changed=True)

            if exists == 0:
                self.dns_rc = self.create_record()
                if self.dns_rc != 0:
                    result['msg'] = "Failed to create DNS record (rc: %d)" % self.dns_rc

            elif exists == 2:
                self.dns_rc = self.modify_record()
                if self.dns_rc != 0:
                    result['msg'] = "Failed to update DNS record (rc: %d)" % self.dns_rc

            if self.dns_rc != 0:
                result['failed'] = True
            else:
                result['changed'] = True

        else:
            result['changed'] = False

        return result

    def create_record(self):
        update = dns.update.Update(self.zone, keyring=self.keyring, keyalgorithm=self.algorithm)
        try:
            update.add(self.module.params['record'],
                       self.module.params['ttl'],
                       self.module.params['type'],
                       self.module.params['value'])
        except AttributeError:
            self.module.fail_json(msg='value needed when state=present')
        except dns.exception.SyntaxError:
            self.module.fail_json(msg='Invalid/malformed value')

        response = self.__do_update(update)
        return dns.message.Message.rcode(response)

    def modify_record(self):
        update = dns.update.Update(self.zone, keyring=self.keyring, keyalgorithm=self.algorithm)
        update.replace(self.module.params['record'],
                       self.module.params['ttl'],
                       self.module.params['type'],
                       self.module.params['value'])

        response = self.__do_update(update)
        return dns.message.Message.rcode(response)

    def remove_record(self):
        result = {'changed': False, 'failed': False}

        if self.record_exists() == 0:
            return result

        # Check mode and record exists, declared fake change.
        if self.module.check_mode:
            self.module.exit_json(changed=True)

        update = dns.update.Update(self.zone, keyring=self.keyring, keyalgorithm=self.algorithm)
        update.delete(self.module.params['record'], self.module.params['type'])

        response = self.__do_update(update)
        self.dns_rc = dns.message.Message.rcode(response)

        if self.dns_rc != 0:
            result['failed'] = True
            result['msg'] = "Failed to delete record (rc: %d)" % self.dns_rc
        else:
            result['changed'] = True

        return result

    def record_exists(self):
        update = dns.update.Update(self.zone, keyring=self.keyring, keyalgorithm=self.algorithm)
        try:
            update.present(self.module.params['record'], self.module.params['type'])
        except dns.rdatatype.UnknownRdatatype as e:
            self.module.fail_json(msg='Record error: {0}'.format(to_native(e)))

        response = self.__do_update(update)
        self.dns_rc = dns.message.Message.rcode(response)
        if self.dns_rc == 0:
            if self.module.params['state'] == 'absent':
                return 1
            try:
                update.present(self.module.params['record'], self.module.params['type'], self.module.params['value'])
            except AttributeError:
                self.module.fail_json(msg='value needed when state=present')
            except dns.exception.SyntaxError:
                self.module.fail_json(msg='Invalid/malformed value')
            response = self.__do_update(update)
            self.dns_rc = dns.message.Message.rcode(response)
            if self.dns_rc == 0:
                return 1
            else:
                return 2
        else:
            return 0


def main():
    tsig_algs = ['HMAC-MD5.SIG-ALG.REG.INT', 'hmac-md5', 'hmac-sha1', 'hmac-sha224',
                 'hmac-sha256', 'hamc-sha384', 'hmac-sha512']

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=False, default='present', choices=['present', 'absent'], type='str'),
            server=dict(required=True, type='str'),
            key_name=dict(required=False, type='str'),
            key_secret=dict(required=False, type='str', no_log=True),
            key_algorithm=dict(required=False, default='hmac-md5', choices=tsig_algs, type='str'),
            zone=dict(required=True, type='str'),
            record=dict(required=True, type='str'),
            type=dict(required=False, default='A', type='str'),
            ttl=dict(required=False, default=3600, type='int'),
            value=dict(required=False, default=None, type='str')
        ),
        supports_check_mode=True
    )

    if not HAVE_DNSPYTHON:
        module.fail_json(msg='python library dnspython required: pip install dnspython')

    if len(module.params["record"]) == 0:
        module.fail_json(msg='record cannot be empty.')

    record = RecordManager(module)
    result = {}
    if module.params["state"] == 'absent':
        result = record.remove_record()
    elif module.params["state"] == 'present':
        result = record.create_or_update_record()

    result['dns_rc'] = record.dns_rc
    result['dns_rc_str'] = dns.rcode.to_text(record.dns_rc)
    if result['failed']:
        module.fail_json(**result)
    else:
        result['record'] = dict(zone=record.zone,
                                record=module.params['record'],
                                type=module.params['type'],
                                ttl=module.params['ttl'],
                                value=module.params['value'])

        module.exit_json(**result)


if __name__ == '__main__':
    main()
