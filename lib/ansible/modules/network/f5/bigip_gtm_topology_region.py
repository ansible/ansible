#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_gtm_topology_region
short_description: Manages GTM Topology Regions
description:
  - Manages GTM Topology Regions.
version_added: 2.8
options:
  name:
    description:
      - Specifies the name of the region.
    required: True
  region_members:
    description:
      - Specifies the list of region members.
      - This list of members is all or nothing, in order to add or remove a member,
        you must specify the entire list of members.
      - The list will override what is on the device if different.
      - If C(none) value is specified the region members list will be removed.
    suboptions:
      negate:
        description:
          - When set to c(yes) the system selects this topology region, when the request source does not match.
          - Only a single list entry can be specified together with negate.
        type: bool
        default: no
      region:
        description:
          - Specifies the name of region already defined in the configuration.
        type: str
      continent:
        description:
          - Specifies one of the seven continents, along with the C(Unknown) setting.
          - Specifying C(Unknown) forces the system to use a default resolution
            if the system cannot determine the location of the local DNS making the request.
          - Full continent names and their abbreviated versions are supported.
        type: str
      country:
        description:
          - The country name, or code to use.
          - In addition to the country full names, you may also specify their abbreviated
            form, such as C(US) instead of C(United States).
          - Valid country codes can be found here https://countrycode.org/.
        type: str
      state:
        description:
          - Specifies a state in a given country.
        type: str
      pool:
        description:
          - Specifies the name of GTM pool already defined in the configuration.
        type: str
      datacenter:
        description:
          - Specifies the name of GTM data center already defined in the configuration.
        type: str
      isp:
        description:
          - Specifies an Internet service provider.
        type: str
        choices:
          - AOL
          - BeijingCNC
          - CNC
          - ChinaEducationNetwork
          - ChinaMobilNetwork
          - ChinaRailwayTelcom
          - ChinaTelecom
          - ChinaUnicom
          - Comcast
          - Earthlink
          - ShanghaiCNC
          - ShanghaiTelecom
      geo_isp:
        description:
          - Specifies a geolocation ISP
        type: str
    type: list
  partition:
    description:
      - Device partition to manage resources on.
      - Partition parameter is also taken into account when used in conjunction with C(pool), C(data_center),
        and C(region) parameters.
    type: str
    default: Common
  state:
    description:
      - When C(state) is C(present), ensures that the region exists.
      - When C(state) is C(absent), ensures that the region is removed.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
'''


EXAMPLES = r'''
- name: Create topology region
  bigip_gtm_topology_region:
    name: foobar
    region_members:
      - country: CN
        negate: yes
      - datacenter: baz
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Modify topology region
  bigip_gtm_topology_region:
    name: foobar
    region_members:
      - continent: EU
      - country: PL
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
name:
  description: The name value of the GTM region.
  returned: changed
  type: str
  sample: foobar
region_members:
  description: The list of members of the GTM region.
  returned: changed
  type: list
  sample: [{"continent": "EU"}, {"country": "PL"}]
'''

import copy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import string_types
from ansible.module_utils.six import iteritems

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.compare import cmp_simple_list
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import cmp_simple_list


class Parameters(AnsibleF5Parameters):
    api_map = {
        'regionMembers': 'region_members',
    }

    api_attributes = [
        'regionMembers',
    ]

    returnables = [
        'region_members',
    ]

    updatables = [
        'region_members',
    ]


class ApiParameters(Parameters):
    @property
    def region_members(self):
        members = self._values['region_members']
        if members is None:
            return None
        result = [member['name'] for member in members]
        return result


class ModuleParameters(Parameters):
    countries = {
        'Afghanistan': 'AF',
        'Aland Islands': 'AX',
        'Albania': 'AL',
        'Algeria': 'DZ',
        'American Samoa': 'AS',
        'Andorra': 'AD',
        'Angola': 'AO',
        'Anguilla': 'AI',
        'Antarctica': 'AQ',
        'Antigua and Barbuda': 'AG',
        'Argentina': 'AR',
        'Armenia': 'AM',
        'Aruba': 'AW',
        'Australia': 'AU',
        'Austria': 'AT',
        'Azerbaijan': 'AZ',
        'Bahamas': 'BS',
        'Bahrain': 'BH',
        'Bangladesh': 'BD',
        'Barbados': 'BB',
        'Belarus': 'BY',
        'Belgium': 'BE',
        'Belize': 'BZ',
        'Benin': 'BJ',
        'Bermuda': 'BM',
        'Bhutan': 'BT',
        'Bolivia': 'BO',
        'Bonaire, Sint Eustatius and Saba': 'BQ',
        'Bosnia and Herzegovina': 'BA',
        'Botswana': 'BW',
        'Bouvet Island': 'BV',
        'Brazil': 'BR',
        'British Indian Ocean Territory': 'IO',
        'Brunei Darussalam': 'BN',
        'Bulgaria': 'BG',
        'Burkina Faso': 'BF',
        'Burundi': 'BI',
        'Cape Verde': 'CV',
        'Cambodia': 'KH',
        'Cameroon': 'CM',
        'Canada': 'CA',
        'Cayman Islands': 'KY',
        'Central African Republic': 'CF',
        'Chad': 'TD',
        'Chile': 'CL',
        'China': 'CN',
        'Christmas Island': 'CX',
        'Cocos (Keeling) Islands': 'CC',
        'Colombia': 'CO',
        'Comoros': 'KM',
        'Congo': 'CG',
        'Congo, The Democratic Republic of the': 'CD',
        'Cook Islands': 'CK',
        'Costa Rica': 'CR',
        "Cote D'Ivoire": 'CI',
        'Croatia': 'HR',
        'Cuba': 'CU',
        'Curaçao': 'CW',
        'Cyprus': 'CY',
        'Czech Republic': 'CZ',
        'Denmark': 'DK',
        'Djibouti': 'DJ',
        'Dominica': 'DM',
        'Dominican Republic': 'DO',
        'Ecuador': 'EC',
        'Egypt': 'EG',
        'El Salvador': 'SV',
        'Equatorial Guinea': 'GQ',
        'Eritrea': 'ER',
        'Estonia': 'EE',
        'Ethiopia': 'ET',
        'Falkland Islands (Malvinas)': 'FK',
        'Faroe Islands': 'FO',
        'Fiji': 'FJ',
        'Finland': 'FI',
        'France': 'FR',
        'French Guiana': 'GF',
        'French Polynesia': 'PF',
        'French Southern Territories': 'TF',
        'Gabon': 'GA',
        'Gambia': 'GM',
        'Georgia': 'GE',
        'Germany': 'DE',
        'Ghana': 'GH',
        'Gibraltar': 'GI',
        'Greece': 'GR',
        'Greenland': 'GL',
        'Grenada': 'GD',
        'Guadeloupe': 'GP',
        'Guam': 'GU',
        'Guatemala': 'GT',
        'Guernsey': 'GG',
        'Guinea': 'GN',
        'Guinea-Bissau': 'GW',
        'Guyana': 'GY',
        'Haiti': 'HT',
        'Heard Island and McDonald Islands': 'HM',
        'Holy See (Vatican City State)': 'VA',
        'Honduras': 'HN',
        'Hong Kong': 'HK',
        'Hungary': 'HU',
        'Iceland': 'IS',
        'India': 'IN',
        'Indonesia': 'ID',
        'Iran, Islamic Republic of': 'IR',
        'Iraq': 'IQ',
        'Ireland': 'IE',
        'Isle of Man': 'IM',
        'Israel': 'IL',
        'Italy': 'IT',
        'Jamaica': 'JM',
        'Japan': 'JP',
        'Jersey': 'JE',
        'Jordan': 'JO',
        'Kazakhstan': 'KZ',
        'Kenya': 'KE',
        'Kiribati': 'KI',
        "Korea, Democratic People's Republic of": 'KP',
        'Korea, Republic of': 'KR',
        'Kuwait': 'KW',
        'Kyrgyzstan': 'KG',
        "Lao People's Democratic Republic": 'LA',
        'Latvia': 'LV',
        'Lebanon': 'LB',
        'Lesotho': 'LS',
        'Liberia': 'LR',
        'Libyan Arab Jamahiriya': 'LY',
        'Liechtenstein': 'LI',
        'Lithuania': 'LT',
        'Luxembourg': 'LU',
        'Macau': 'MO',
        'Macedonia': 'MK',
        'Madagascar': 'MG',
        'Malawi': 'MW',
        'Malaysia': 'MY',
        'Maldives': 'MV',
        'Mali': 'ML',
        'Malta': 'MT',
        'Marshall Islands': 'MH',
        'Martinique': 'MQ',
        'Mauritania': 'MR',
        'Mauritius': 'MU',
        'Mayotte': 'YT',
        'Mexico': 'MX',
        'Micronesia, Federated States of': 'FM',
        'Moldova, Republic of': 'MD',
        'Monaco': 'MC',
        'Mongolia': 'MN',
        'Montenegro': 'ME',
        'Montserrat': 'MS',
        'Morocco': 'MA',
        'Mozambique': 'MZ',
        'Myanmar': 'MM',
        'Namibia': 'NA',
        'Nauru': 'NR',
        'Nepal': 'NP',
        'Netherlands': 'NL',
        'New Caledonia': 'NC',
        'New Zealand': 'NZ',
        'Nicaragua': 'NI',
        'Niger': 'NE',
        'Nigeria': 'NG',
        'Niue': 'NU',
        'Norfolk Island': 'NF',
        'Northern Mariana Islands': 'MP',
        'Norway': 'NO',
        'Oman': 'OM',
        'Pakistan': 'PK',
        'Palau': 'PW',
        'Palestinian Territory': 'PS',
        'Panama': 'PA',
        'Papua New Guinea': 'PG',
        'Paraguay': 'PY',
        'Peru': 'PE',
        'Philippines': 'PH',
        'Pitcairn Islands': 'PN',
        'Poland': 'PL',
        'Portugal': 'PT',
        'Puerto Rico': 'PR',
        'Qatar': 'QA',
        'Reunion': 'RE',
        'Romania': 'RO',
        'Russian Federation': 'RU',
        'Rwanda': 'RW',
        'Saint Barthelemy': 'BL',
        'Saint Helena': 'SH',
        'Saint Kitts and Nevis': 'KN',
        'Saint Lucia': 'LC',
        'Saint Martin': 'MF',
        'Saint Pierre and Miquelon': 'PM',
        'Saint Vincent and the Grenadines': 'VC',
        'Samoa': 'WS',
        'San Marino': 'SM',
        'Sao Tome and Principe': 'ST',
        'Saudi Arabia': 'SA',
        'Senegal': 'SN',
        'Serbia': 'RS',
        'Seychelles': 'SC',
        'Sierra Leone': 'SL',
        'Singapore': 'SG',
        'Sint Maarten (Dutch part)': 'SX',
        'Slovakia': 'SK',
        'Slovenia': 'SI',
        'Solomon Islands': 'SB',
        'Somalia': 'SO',
        'South Africa': 'ZA',
        'South Georgia and the South Sandwich Islands': 'GS',
        'South Sudan': 'SS',
        'Spain': 'ES',
        'Sri Lanka': 'LK',
        'Sudan': 'SD',
        'Suriname': 'SR',
        'Svalbard and Jan Mayen': 'SJ',
        'Swaziland': 'SZ',
        'Sweden': 'SE',
        'Switzerland': 'CH',
        'Syrian Arab Republic': 'SY',
        'Taiwan': 'TW',
        'Tajikistan': 'TJ',
        'Tanzania, United Republic of': 'TZ',
        'Thailand': 'TH',
        'Timor-Leste': 'TL',
        'Togo': 'TG',
        'Tokelau': 'TK',
        'Tonga': 'TO',
        'Trinidad and Tobago': 'TT',
        'Tunisia': 'TN',
        'Turkey': 'TR',
        'Turkmenistan': 'TM',
        'Turks and Caicos Islands': 'TC',
        'Tuvalu': 'TV',
        'Uganda': 'UG',
        'Ukraine': 'UA',
        'United Arab Emirates': 'AE',
        'United Kingdom': 'GB',
        'United States': 'US',
        'United States Minor Outlying Islands': 'UM',
        'Uruguay': 'UY',
        'Uzbekistan': 'UZ',
        'Vanuatu': 'VU',
        'Venezuela': 'VE',
        'Vietnam': 'VN',
        'Virgin Islands, British': 'VG',
        'Virgin Islands, U.S.': 'VI',
        'Wallis and Futuna': 'WF',
        'Western Sahara': 'EH',
        'Yemen': 'YE',
        'Zambia': 'ZM',
        'Zimbabwe': 'ZW',
        'Unrecognized': 'N/A',
        'Asia/Pacific Region': 'AP',
        'Europe': 'EU',
        'Netherlands Antilles': 'AN',
        'France, Metropolitan': 'FX',
        'Anonymous Proxy': 'A1',
        'Satellite Provider': 'A2',
        'Other': 'O1',
    }

    continents = {
        'Antarctica': 'AN',
        'Asia': 'AS',
        'Africa': 'AF',
        'Europe': 'EU',
        'North America': 'NA',
        'South America': 'SA',
        'Oceania': 'OC',
        'Unknown': '--',
    }

    @property
    def region_members(self):
        result = list()
        negate = None
        if self._values['region_members'] is None:
            return None
        if isinstance(self._values['region_members'], string_types):
            return self._values['region_members']
        if not isinstance(self._values['region_members'], list):
            raise F5ModuleError(
                'Region members must be either type of string or list.'
            )
        members = copy.deepcopy(self._values['region_members'])
        for item in members:
            member = self._filter_params(item)
            if 'negate' in member.keys():
                if len(member.keys()) > 2:
                    raise F5ModuleError(
                        'You cannot specify negate and more than one option together.'
                    )

                negate = self._flatten_negate(member)

            for key, value in iteritems(member):
                if negate:
                    output = self._change_value(key, value)
                    item = "{0} {1} {2}".format(negate, output[0], output[1])
                    result.append(item)
                    negate = None
                else:
                    output = self._change_value(key, value)
                    item = "{0} {1}".format(output[0], output[1])
                    result.append(item)
        return result

    def _flatten_negate(self, item):
        result = flatten_boolean(item['negate'])
        item.pop('negate')
        if result == 'yes':
            return 'not'
        return None

    def _change_value(self, key, value):
        if key in ['region', 'pool', 'datacenter']:
            return key, fq_name(self.partition, value)
        if key == 'isp':
            return key, fq_name('Common', value)
        if key == 'continent':
            return key, self.continents.get(value, value)
        if key == 'country':
            return key, self.countries.get(value, value)
        if key == 'geo_isp':
            return 'geoip-isp', value
        return key, value


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    @property
    def region_members(self):
        members = self._values['region_members']
        if members is None:
            return None
        if not members:
            return 'none'
        return ' '.join(members)


class ReportableChanges(Changes):
    pass


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def region_members(self):
        return cmp_simple_list(self.want.region_members, self.have.region_members)


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/region/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        if self.changes.region_members:
            command = 'tmsh create gtm region {0} region-members add {{ {1} }} '.format(
                fq_name(self.want.partition, self.want.name),
                self.changes.region_members
            )
        else:
            command = 'tmsh create gtm region {0}'.format(
                fq_name(self.want.partition, self.want.name)
            )
        payload = {
            "command": "run",
            "utilCmdArgs": '-c "{0}"'.format(command)
        }
        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=payload)
        try:
            response = resp.json()
            if 'commandResult' in response:
                raise F5ModuleError(response['commandResult'])
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def update_on_device(self):
        param = self.changes.region_members
        if param:
            if param != 'none':
                command = 'tmsh modify gtm region {0} region-members replace-all-with {{ {1} }} '.format(
                    fq_name(self.want.partition, self.want.name),
                    param
                )
            else:
                command = 'tmsh modify gtm region {0} region-members {1} '.format(
                    fq_name(self.want.partition, self.want.name),
                    param
                )
        else:
            command = 'tmsh create gtm region {0}'.format(
                fq_name(self.want.partition, self.want.name)
            )

        payload = {
            "command": "run",
            "utilCmdArgs": '-c "{0}"'.format(command)
        }

        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=payload)
        try:
            response = resp.json()
            if 'commandResult' in response:
                raise F5ModuleError(response['commandResult'])
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/region/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/region/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return ApiParameters(params=response)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.choices = [
            'AOL', 'BeijingCNC', 'CNC', 'ChinaEducationNetwork',
            'ChinaMobilNetwork', 'ChinaRailwayTelcom', 'ChinaTelecom',
            'ChinaUnicom', 'Comcast', 'Earthlink', 'ShanghaiCNC',
            'ShanghaiTelecom',
        ]
        argument_spec = dict(
            name=dict(
                required=True
            ),
            region_members=dict(
                type='list',
                elements='dict',
                options=dict(
                    region=dict(),
                    continent=dict(),
                    country=dict(),
                    state=dict(),
                    pool=dict(),
                    datacenter=dict(),
                    isp=dict(
                        choices=self.choices
                    ),
                    geo_isp=dict(),
                    negate=dict(
                        type='bool',
                        default='no'
                    ),
                )
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
