#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Brian Coca <bcoca@ansible.com>
#
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


DOCUMENTATION = '''
module: openweather_facts
author:
    - '"Brian Coca (@bcoca)" <bcoca@ansible.com>'
version_added: "2.3"
description:
    - Use the openweathermap API to retrieve the current weather at a location.
    - Even though none of the fields are required, you must supply one (and only one) for the query.
    - You can get more info on the return data and codes at U(http://openweathermap.org/current).
short_description: Get current weather
options:
  name:
    description:
      - Name of the city who's weather you want to know
    required: false
    default: null
    aliases: ['city', 'city_name']
  id:
    description:
      - ID of the city who's weather you want to know
    required: false
    default: null
    aliases: ['city_id']
  zipcode:
    description:
      - Postal Code of the area
    required: false
    default: null
    aliases: ['zip','pc']
  coordinates:
    description:
      - a tuple with latitude and longitude of the area you wish to query for.
    required: false
    default: null
  country_code:
    description:
      - a 2 letter ISO country code, used to disambiguate when querying by name and zipcodes
    required: false
    default: null
  units:
    description:
      - What units you want in the response, the default null is the same as specifying 'internal'
    required: False
    default: null
    choices: ['internal', 'metric', 'imperial']
note:
  - This module uses the free tier of U(http://openweathermap.org), it should be easy to expand to use a developer or higher tier
'''

EXAMPLES = '''
- name: Get weather for NYC
  openweather_facts: name="New York,us"
- name: get weather facts for London in metric
  openweather_facts: id=524901 units=metric
'''

RETURN="""
weather_5128638:
    id: 5128638
    name: New York
    cod: 200
    dt: 1432607845
    base: stations
    coord:
        lon: -75.5
        lat: 43
    sys:
        message: 0.6549
        country: US
        sunrise: 1432632523
        sunset: 1432686566}
    weather:
        - id: 803
          main: Clouds
          description: broken clouds
          icon: 04n
        - id: 801
          main: Clouds
          description: broken clouds
          icon: 04n
    main:
        temp: 296.334
        temp_min: 296.334
        temp_max: 296.334
        pressure: 1001.77
        sea_level: 1032.36
        grnd_level: 1001.77
        humidity: 51
    wind:
        speed: 3.46
        deg: 207.503
    clouds:
        all: 80
"""

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}
try:
    import json
except ImportError:
    import simplejson as json

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

def main():
    DEFAULT_URL='http://api.openweathermap.org/data/2.5/weather?'

    module = AnsibleModule(
        argument_spec={
            'name': {'required': False, 'aliases': ['city', 'city_name']},
            'id': {'required': False, 'aliases': ['city_id'], type: 'int'},
            'zipcode': {'required': False, 'aliases': ['zip', 'pc']},
            'coordinates': {'required': False, type: 'list'},
            'country_code': {'required': False,},
            'units': {'required': False, 'choices': ['internal', 'metric', 'imperial']},
        },
        required_one_of=[['name', 'id', 'zipcode', 'coordinates']],
    )

    weather = {}
    info = None
    uri = DEFAULT_URL

    # Create type object as namespace for module params
    p = type('Params', (), module.params)

    if p.name:
        uri += 'q=' + p.name
        if p.country_code:
            uri += ',' + p.country_code
    elif p.id:
        uri += 'id=' + p.id
    elif p.zipcode:
        uri += 'zip=' + p.zipcode
        if p.country_code:
            uri += ',' + p.country_code
    elif p.coordinates:
        uri += '?lat=%f&lon=%f' % p.coordinates


    if p.units:
        uri += '&units=' + p.units.lower()
    response,info = fetch_url(module, uri)

    if info['status'] != 200:
        module.fail_json(msg="Failed to get the weather: %s" % info['msg'])

    data = json.loads(response.read())
    weather['weather_' + str(data['id'])] = data

    module.exit_json(info=info, ansible_facts=weather, uri=uri)


if __name__ == '__main__':
    main()
