# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2018, Simon Weald <ansible@simonweald.com>
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

from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.urls import open_url, urllib_error
from ansible.module_utils.basic import json


class Response(object):
    '''
    Create a response object to mimic that of requests.
    '''

    def __init__(self):
        self.content = None
        self.status_code = None

    def json(self):
        return json.loads(self.content)


def memset_api_call(api_key, api_method, payload=None):
    '''
    Generic function which returns results back to calling function.

    Requires an API key and an API method to assemble the API URL.
    Returns response text to be analysed.
    '''
    # instantiate a response object
    response = Response()

    # if we've already started preloading the payload then copy it
    # and use that, otherwise we need to isntantiate it.
    if payload is None:
        payload = dict()
    else:
        payload = payload.copy()

    payload['api_key'] = api_key
    # set some sane defaults
    has_failed = False
    msg = None

    data = urlencode(payload)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    api_uri_base = 'https://api.memset.com/v1/json/'
    api_uri = '{0}{1}/' . format(api_uri_base, api_method)

    try:
        resp = open_url(api_uri, data=data, headers=headers, method="POST")
        response.content = resp.read().decode('utf-8')
        response.status_code = resp.getcode()
    except urllib_error.HTTPError as e:
        try:
            errorcode = e.code
        except AttributeError:
            errorcode = None

        has_failed = True
        response.content = e.read().decode('utf8')
        response.status_code = errorcode

        if response.status_code is not None:
            msg = "Memset API returned a {0} response ({1}, {2})." . format(response.status_code, response.json()['error_type'], response.json()['error'])
        else:
            msg = "Memset API returned an error ({0}, {1})." . format(response.json()['error_type'], response.json()['error'])

    del payload['api_key']

    if msg is None:
        msg = response.json()

    return(has_failed, msg, response)


def check_zone_domain(data, domain):
    '''
    Returns true if domain already exists, and false if not.
    '''
    exists = False

    if data.status_code in [201, 200]:
        for zone_domain in data.json():
            if zone_domain['domain'] == domain:
                exists = True

    return(exists)


def check_zone(data, name):
    '''
    Returns true if zone already exists, and false if not.
    '''
    counter = 0
    exists = False

    if data.status_code in [201, 200]:
        for zone in data.json():
            if zone['nickname'] == name:
                counter += 1
        if counter == 1:
            exists = True

    return(exists, counter)


def get_zone_id(zone_name, current_zones):
    '''
    Returns the zone's id if it exists and is unique
    '''
    zone_exists = False
    zone_id, msg = None, None
    zone_list = []

    for zone in current_zones:
        if zone['nickname'] == zone_name:
            zone_list.append(zone['id'])

    counter = len(zone_list)

    if counter == 0:
        msg = 'No matching zone found'
    elif counter == 1:
        zone_id = zone_list[0]
        zone_exists = True
    elif counter > 1:
        zone_id = None
        msg = 'Zone ID could not be returned as duplicate zone names were detected'

    return(zone_exists, msg, counter, zone_id)
