# -*- coding: utf-8 -*-
# Copyright: (c) 2019 Gregory Thiemonge <gregory.thiemonge@gmail.com>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json

from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.urls import fetch_url


def lowercase_string(param):
    if not isinstance(param, str):
        return param
    return param.lower()


class GandiLiveDNSAPI:

    api_endpoint = 'https://dns.api.gandi.net/api/v5'
    changed = False

    error_strings = {
        400: 'Bad request',
        401: 'Permission denied',
        404: 'Resource not found',
    }

    def __init__(self, module):
        self.module = module
        self.api_key = module.params['api_key']

    def _gandi_api_call(self, api_call, method='GET', payload=None, error_on_404=True):
        headers = {'X-Api-Key': self.api_key,
                   'Content-Type': 'application/json'}
        data = None
        if payload:
            try:
                data = json.dumps(payload)
            except Exception as e:
                self.module.fail_json(msg="Failed to encode payload as JSON: %s " % to_native(e))

        resp, info = fetch_url(self.module,
                               self.api_endpoint + api_call,
                               headers=headers,
                               data=data,
                               method=method)

        error_msg = ''
        if info['status'] >= 400 and (info['status'] != 404 or error_on_404):
            err_s = self.error_strings.get(info['status'], '')

            error_msg = "API error {0}; Status: {1}; Method: {2}: Call: {3}".format(err_s, info['status'], method, api_call)

        result = None
        try:
            content = resp.read()
        except AttributeError:
            content = None

        if content:
            try:
                result = json.loads(to_text(content, errors='surrogate_or_strict'))
            except (getattr(json, 'JSONDecodeError', ValueError)) as e:
                error_msg += "; Failed to parse API response with error {0}: {1}".format(to_native(e), content)

        if error_msg:
            self.module.fail_json(msg=error_msg)

        return result, info['status']

    def build_result(self, result, zone=None, domain=None):
        if result is None:
            return None

        res = {}
        for k in ('name', 'type', 'ttl', 'values'):
            v = result.get('rrset_' + k, None)
            if v is not None:
                res[k] = v

        if zone:
            res['zone'] = zone
        else:
            res['domain'] = domain

        return res

    def build_results(self, results, zone=None, domain=None):
        if results is None:
            return []
        return [self.build_result(r, zone, domain) for r in results]

    def _get_zone_id(self, zone_name):
        for z in self.get_zones():
            if z['name'] == zone_name:
                return z['uuid']
        self.module.fail_json(msg="No zone found with name {0}".format(zone_name))

    def get_zones(self):
        zones, status = self._gandi_api_call('/zones')
        return zones

    def get_records(self, record, type, zone_id=None, domain=None):
        if zone_id:
            url = '/zones/%s' % (zone_id)
        else:
            url = '/domains/%s' % (domain)

        url += '/records'
        if record:
            url += '/%s' % (record)
            if type:
                url += '/%s' % (type)

        records, status = self._gandi_api_call(url, error_on_404=False)

        if status == 404:
            return None

        if not isinstance(records, list):
            records = [records]

        # filter by type if record is not set
        if not record and type:
            records = [r
                       for r in records
                       if r['rrset_type'] == type]

        return records

    def create_record(self, record, type, values, ttl, zone_id=None, domain=None):
        if zone_id:
            url = '/zones/%s' % (zone_id)
        else:
            url = '/domains/%s' % (domain)

        url += '/records'
        new_record = {
            'rrset_name': record,
            'rrset_type': type,
            'rrset_values': values,
            'rrset_ttl': ttl,
        }
        record, status = self._gandi_api_call(url, method='POST', payload=new_record)

        if status in (201,):
            return new_record

        return None

    def update_record(self, record, type, values, ttl, zone_id=None, domain=None):
        if zone_id:
            url = '/zones/%s' % (zone_id)
        else:
            url = '/domains/%s' % (domain)

        url += '/records/%s/%s' % (record, type)
        new_record = {
            'rrset_values': values,
            'rrset_ttl': ttl,
        }
        record, status = self._gandi_api_call(url, method='PUT', payload=new_record)
        return record

    def delete_record(self, record, type, zone_id=None, domain=None):
        if zone_id:
            url = '/zones/%s' % (zone_id)
        else:
            url = '/domains/%s' % (domain)
        url += '/records/%s/%s' % (record, type)

        cur_record, status = self._gandi_api_call(url, method='DELETE')

    def delete_dns_record(self, record, type, ttl, values, zone=None, domain=None):

        if type is None or record is None:
            self.module.fail_json(msg="You must provide a type and a record to delete a record")

        if zone:
            zone_id = self._get_zone_id(zone)
        else:
            zone_id = None

        records = self.get_records(record, type, zone_id=zone_id, domain=domain)

        if records:
            cur_record = records[0]

            if ttl is not None and cur_record['rrset_ttl'] != ttl:
                return None, self.changed
            if values is not None and set(cur_record['rrset_values']) != set(values):
                return None, self.changed

            self.changed = True
            if not self.module.check_mode:
                result = self.delete_record(record, type, zone_id=zone_id, domain=domain)
        else:
            cur_record = None

        return cur_record, self.changed

    def ensure_dns_record(self, record, type, ttl, values, zone=None, domain=None):

        if zone:
            zone_id = self._get_zone_id(zone)
        else:
            zone_id = None

        records = self.get_records(record, type, zone_id=zone_id, domain=domain)

        if records:
            cur_record = records[0]

            do_update = False
            if ttl is not None and cur_record['rrset_ttl'] != ttl:
                do_update = True
            if values is not None and set(cur_record['rrset_values']) != set(values):
                do_update = True

            if do_update:
                if self.module.check_mode:
                    result = cur_record
                else:
                    self.update_record(record, type, values, ttl, zone_id=zone_id, domain=domain)

                    records = self.get_records(record, type, zone_id=zone_id, domain=domain)
                    result = records[0]
                self.changed = True
                return result, self.changed
            else:
                return cur_record, self.changed

        if self.module.check_mode:
            new_record = dict(
                rrset_type=type,
                rrset_name=record,
                rrset_values=values,
                rrset_ttl=ttl
            )
            result = new_record
        else:
            result = self.create_record(record, type, values, ttl, zone_id=zone_id, domain=domain)

        self.changed = True
        return result, self.changed

    def get_dns_records(self, record, type, zone=None, domain=None):

        if zone:
            zone_id = self._get_zone_id(zone)
        else:
            zone_id = None

        return self.get_records(record, type, zone_id=zone_id, domain=domain)
