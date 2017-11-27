# -*- coding: utf-8 -*-
#
# (c) 2017, Olivier Boukili <boukili.olivier@gmail.com> <olivier@malt.com>
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import json
from time import sleep
from ansible.module_utils.urls import fetch_url


class DynectAPI(object):
    '''DynDNS API endpoint.
    attributes:
        module -> ansible module instance (AnsibleModule object).
    '''

    def __init__(self, module):
        self.module = module
        self.dyn_customer_name = module.params['dyn_customer_name']
        self.dyn_user_name = module.params['dyn_user_name']
        self.dyn_password = module.params['dyn_password']
        self.api_retries = module.params['api_retries']
        self.api_timeout = module.params['api_timeout']
        self.api_uri = 'https://api.dynect.net'
        self.auth_token = self.getauthenticationtoken()

    def getauthenticationtoken(self):
        '''authenticate to Dynect API'''
        auth_payload = {
            'customer_name': self.dyn_customer_name,
            'user_name': self.dyn_user_name,
            'password': self.dyn_password
        }
        for retry in range(0, self.api_retries):
            try:
                response, info = fetch_url(self.module, self.api_uri + "/REST/Session/",
                                           method="post",
                                           data=self.module.jsonify(auth_payload),
                                           headers={'Content-Type': 'application/json'},
                                           timeout=self.api_timeout)
            except Exception as exception:
                self.module.fail_json(msg=str(exception))
            else:
                status_code = info['status']
                if status_code >= 400 and status_code != 429:
                    self.module.fail_json(msg=str(info['body']))
                # Did we hit the rate limit?
                elif status_code == 429:
                    sleep(1)
                else:
                    break
        else:
            self.module.fail_json(msg="Reached API retries limit.")

        body = response.read()
        return json.loads(body)['data']['token']

    def logout(self):
        '''Close the Dynect API session'''
        for retry in range(0, self.api_retries):
            try:
                response, info = fetch_url(self.module, self.api_uri + "/REST/Session/",
                                           method="delete",
                                           headers={'Content-Type': 'application/json', 'Auth-Token': self.auth_token},
                                           timeout=self.api_timeout)
            except Exception as exception:
                self.module.fail_json(msg=str(exception))
            else:
                status_code = info['status']
                if status_code >= 400 and status_code != 429:
                    self.module.fail_json(msg=str(info['body']))
                # Did we hit the rate limit?
                elif status_code == 429:
                    sleep(1)
                else:
                    break
        else:
            self.module.fail_json(msg="Reached API retries limit.")
        return response


class DynDnsZone(object):
    '''DynDNS zone control.
    attributes:
        module -> ansible module instance (AnsibleModule object).
    '''

    def __init__(self, module):
        self.module = module
        self.zone = module.params['zone']
        self.session = DynectAPI(module)

    def recordget(self, node, record_type, **kwargs):
        '''Gets a record, or a list of records matching the node, from the zone'''
        if 'record_id' not in kwargs:
            for retry in range(0, self.session.api_retries):
                try:
                    response, info = fetch_url(self.module, self.session.api_uri + "/REST/" +
                                               str(record_type).upper() + "Record/" +
                                               str(self.zone) + "/" + str(node) + "." + str(self.zone) + "/",
                                               method="get",
                                               headers={'Content-Type': 'application/json', 'Auth-Token': self.session.auth_token},
                                               timeout=self.session.api_timeout)
                except Exception as exception:
                    self.module.fail_json(msg=str(exception))
                else:
                    status_code = info['status']
                    if status_code >= 400 and status_code not in [404, 429]:
                        self.module.fail_json(msg=str(info['body']))
                    # Did we hit the rate limit?
                    elif status_code == 429:
                        sleep(1)
                    else:
                        break
            else:
                self.module.fail_json(msg="Reached API retries limit.")

            body = response.read()
            records = json.loads(body)['data']

            for record_path in records:
                singlerecord = self.recordgetfromid(record_path)
                if 'rdata' in kwargs and singlerecord['rdata'] == kwargs['rdata']:
                    return singlerecord
                elif 'rdata' not in kwargs:
                    return singlerecord
            return {}
        else:
            self.recordgetfromid(record_path)

    def recordgetfromid(self, record_id):
        '''Get a record details from its record id path'''
        for retry in range(0, self.session.api_retries):
            try:
                response, info = fetch_url(self.module, self.session.api_uri +
                                           str(record_id),
                                           method="get",
                                           headers={'Content-Type': 'application/json', 'Auth-Token': self.session.auth_token},
                                           timeout=self.session.api_timeout)
            except Exception as exception:
                self.module.fail_json(msg=str(exception))

            else:
                if info['status'] >= 400 and info['status'] != 429:
                    self.module.fail_json(msg=str(info['body']))
                # Did we hit the rate limit?
                elif info['status'] == 429:
                    sleep(1)
                else:
                    break
        else:
            self.module.fail_json(msg="Reached API retries limit.")

        body = response.read()
        return json.loads(body)['data']

    def recordadd(self, record_type, node, rdata, ttl=0):
        '''Adds a non-existing record within the zone'''
        payload = {'rdata': rdata, 'ttl': int(ttl)}
        for retry in range(0, self.session.api_retries):
            try:
                response, info = fetch_url(self.module, self.session.api_uri + "/REST/" +
                                           str(record_type).upper() + "Record/" +
                                           str(self.zone) + "/" + str(node) + "." +
                                           str(self.zone) + "/",
                                           method="post",
                                           data=self.module.jsonify(payload),
                                           headers={'Content-Type': 'application/json', 'Auth-Token': self.session.auth_token},
                                           timeout=self.session.api_timeout)
            except Exception as exception:
                self.module.fail_json(msg=str(exception))
            else:
                if info['status'] >= 400 and info['status'] != 429:
                    self.module.fail_json(msg=str(info))
                # Did we hit the rate limit?
                elif info['status'] == 429:
                    sleep(1)
                else:
                    break
        else:
            self.module.fail_json(msg="Reached API retries limit.")

        body = response.read()
        new_record = json.loads(body)['data']
        return {'old_record': {}, 'new_record': new_record}

    def recordupdate(self, record_type, node, rdata, record_id, ttl=0, old_record=None):
        '''Updates an existing record within the zone'''
        payload = {'rdata': rdata, 'ttl': int(ttl)}
        for retry in range(0, self.session.api_retries):
            try:
                response, info = fetch_url(self.module, self.session.api_uri + "/REST/" +
                                           str(record_type).upper() + "Record/" +
                                           str(self.zone) + "/" + str(node) + "." +
                                           str(self.zone) + "/" +
                                           str(record_id),
                                           method="put",
                                           data=self.module.jsonify(payload),
                                           headers={'Content-Type': 'application/json', 'Auth-Token': self.session.auth_token})
            except Exception as exception:
                self.module.fail_json(msg=str(exception))
            else:
                if info['status'] >= 400 and info['status'] != 429:
                    self.module.fail_json(msg=str(info))
                # Did we hit the rate limit?
                elif info['status'] == 429:
                    sleep(1)
                else:
                    break
        else:
            self.module.fail_json(msg="Reached API retries limit.")

        body = response.read()
        new_record = json.loads(body)['data']
        if old_record is not None:
            return {'old_record': old_record, 'new_record': new_record}
        return {'new_record': new_record}

    def recordaddorupdate(self, record_type, node, rdata, ttl=0):
        '''Adds/Updates a record within the zone'''
        # Check whether the record exists to either update or create it.
        matchingrecord = self.recordget(node, record_type, rdata=rdata)

        if matchingrecord != {}:
            return {'old_record': matchingrecord, 'new_record': matchingrecord}
        elif not self.module.params['force_duplicate']:
            foundrecord = self.recordget(node, record_type)
            # Format the record payload.
            if foundrecord == {}:
                return self.recordadd(record_type, node, rdata, ttl)
            else:
                if foundrecord['rdata'] != rdata or (foundrecord['ttl'] != ttl and ttl != 0):
                    return self.recordupdate(record_type, node, rdata, ttl=ttl,
                                             record_id=foundrecord['record_id'],
                                             old_record=foundrecord)
                return {'old_record': foundrecord, 'new_record': foundrecord}
        else:
            return self.recordadd(record_type, node, rdata, ttl)

    def recorddelete(self, node, record_type, rdata=None):
        '''Deletes a record within the zone'''
        # Check whether the record exists to delete it afterwards.
        foundrecord = self.recordget(node, record_type, rdata=rdata)

        if foundrecord == {}:
            return {'deleted': False}

        for retry in range(0, self.session.api_retries):
            try:
                response, info = fetch_url(self.module, self.session.api_uri + "/REST/" +
                                           str(record_type).upper() + "Record/" +
                                           str(self.zone) + "/" + str(node) + "." +
                                           str(self.zone) + "/" +
                                           str(foundrecord['record_id']),
                                           method="delete",
                                           headers={'Content-Type': 'application/json', 'Auth-Token': self.session.auth_token})
            except Exception as exception:
                self.module.fail_json(msg=str(exception))
            else:
                if info['status'] >= 400 and info['status'] != 429:
                    self.module.fail_json(msg=str(info))
                # Did we hit the rate limit?
                elif info['status'] == 429:
                    sleep(1)
                else:
                    break
        else:
            self.module.fail_json(msg="Reached API retries limit.")
        return {'deleted': True}

    def publish(self):
        '''Publish pending zone changes'''
        payload = {'publish': True, 'notes': str(self.module.params['notes'])}

        for retry in range(0, self.session.api_retries):
            try:
                response, info = fetch_url(self.module, self.session.api_uri + "/REST/Zone/" +
                                           str(self.zone) + "/",
                                           method="put",
                                           data=self.module.jsonify(payload),
                                           headers={'Content-Type': 'application/json', 'Auth-Token': self.session.auth_token})
            except Exception as exception:
                self.module.fail_json(msg=str(exception))
            else:
                if info['status'] >= 400 and info['status'] != 429:
                    self.module.fail_json(msg=str(info))
                # Did we hit the rate limit?
                elif info['status'] == 429:
                    sleep(1)
                else:
                    break
        else:
            self.module.fail_json(msg="Reached API retries limit.")

        body = response.read()
        return json.loads(body)
