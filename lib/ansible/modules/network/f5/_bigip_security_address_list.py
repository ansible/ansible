#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_firewall_address_list
short_description: Manage address lists on BIG-IP AFM
description:
  - Manages the AFM address lists on a BIG-IP. This module can be used to add
    and remove address list entries.
version_added: 2.5
options:
  name:
    description:
      - Specifies the name of the address list.
    type: str
    required: True
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  description:
    description:
      - Description of the address list
    type: str
  geo_locations:
    description:
      - List of geolocations specified by their C(country) and C(region).
    suboptions:
      country:
        description:
          - The country name, or code, of the geolocation to use.
          - In addition to the country full names, you may also specify their abbreviated
            form, such as C(US) instead of C(United States).
          - Valid country codes can be found here https://countrycode.org/.
        type: str
        required: True
        choices:
          - Any valid 2 character ISO country code.
          - Any valid country name.
      region:
        description:
          - Region name of the country to use.
        type: str
    type: list
  addresses:
    description:
      - Individual addresses that you want to add to the list. These addresses differ
        from ranges, and lists of lists such as what can be used in C(address_ranges)
        and C(address_lists) respectively.
      - This list can also include networks that have CIDR notation.
    type: list
  address_ranges:
    description:
      - A list of address ranges where the range starts with a port number, is followed
        by a dash (-) and then a second number.
      - If the first address is greater than the second number, the numbers will be
        reversed so-as to be properly formatted. ie, C(2.2.2.2-1.1.1). would become
        C(1.1.1.1-2.2.2.2).
    type: list
  address_lists:
    description:
      - Simple list of existing address lists to add to this list. Address lists can be
        specified in either their fully qualified name (/Common/foo) or their short
        name (foo). If a short name is used, the C(partition) argument will automatically
        be prepended to the short name.
    type: list
  fqdns:
    description:
      - A list of fully qualified domain names (FQDNs).
      - An FQDN has at least one decimal point in it, separating the host from the domain.
      - To add FQDNs to a list requires that a global FQDN resolver be configured.
        At the moment, this must either be done via C(bigip_command), or, in the GUI
        of BIG-IP. If using C(bigip_command), this can be done with C(tmsh modify security
        firewall global-fqdn-policy FOO) where C(FOO) is a DNS resolver configured
        at C(tmsh create net dns-resolver FOO).
    type: list
  state:
    description:
      - When C(present), ensures that the address list and entries exists.
      - When C(absent), ensures the address list is removed.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create an address list
  bigip_firewall_address_list:
    name: foo
    addresses:
      - 3.3.3.3
      - 4.4.4.4
      - 5.5.5.5
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: The new description of the address list.
  returned: changed
  type: str
  sample: My address list
addresses:
  description: The new list of addresses applied to the address list.
  returned: changed
  type: list
  sample: [1.1.1.1, 2.2.2.2]
address_ranges:
  description: The new list of address ranges applied to the address list.
  returned: changed
  type: list
  sample: [1.1.1.1-2.2.2.2, 3.3.3.3-4.4.4.4]
address_lists:
  description: The new list of address list names applied to the address list.
  returned: changed
  type: list
  sample: [/Common/list1, /Common/list2]
fqdns:
  description: The new list of FQDN names applied to the address list.
  returned: changed
  type: list
  sample: [google.com, mit.edu]
geo_locations:
  description: The new list of geo locations applied to the address list.
  returned: changed
  type: complex
  contains:
    country:
      description: Country of the geo location.
      returned: changed
      type: str
      sample: US
    region:
      description: Region of the geo location.
      returned: changed
      type: str
      sample: California
'''

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.compat.ipaddress import ip_address
    from library.module_utils.compat.ipaddress import ip_interface
    from library.module_utils.network.f5.ipaddress import is_valid_ip
    from library.module_utils.network.f5.ipaddress import is_valid_ip_interface
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.compat.ipaddress import ip_address
    from ansible.module_utils.compat.ipaddress import ip_interface
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip_interface


class Parameters(AnsibleF5Parameters):
    api_map = {
        'addressLists': 'address_lists',
        'geo': 'geo_locations',
    }

    api_attributes = [
        'addressLists',
        'addresses',
        'description',
        'fqdns',
        'geo',
    ]

    returnables = [
        'addresses',
        'address_ranges',
        'address_lists',
        'description',
        'fqdns',
        'geo_locations',
    ]

    updatables = [
        'addresses',
        'address_ranges',
        'address_lists',
        'description',
        'fqdns',
        'geo_locations',
    ]


class ApiParameters(Parameters):
    @property
    def address_ranges(self):
        if self._values['addresses'] is None:
            return None
        result = []
        for address_range in self._values['addresses']:
            if '-' not in address_range['name']:
                continue
            result.append(address_range['name'].strip())
        result = sorted(result)
        return result

    @property
    def address_lists(self):
        if self._values['address_lists'] is None:
            return None
        result = []
        for x in self._values['address_lists']:
            item = '/{0}/{1}'.format(x['partition'], x['name'])
            result.append(item)
        result = sorted(result)
        return result

    @property
    def addresses(self):
        if self._values['addresses'] is None:
            return None
        result = [x['name'] for x in self._values['addresses'] if '-' not in x['name']]
        result = sorted(result)
        return result

    @property
    def fqdns(self):
        if self._values['fqdns'] is None:
            return None
        result = [str(x['name']) for x in self._values['fqdns']]
        result = sorted(result)
        return result

    @property
    def geo_locations(self):
        if self._values['geo_locations'] is None:
            return None
        result = [str(x['name']) for x in self._values['geo_locations']]
        result = sorted(result)
        return result


class ModuleParameters(Parameters):
    def __init__(self, params=None):
        super(ModuleParameters, self).__init__(params=params)
        self.country_iso_map = {
            'Afghanistan': 'AF',
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
            'Bosnia and Herzegovina': 'BA',
            'Botswana': 'BW',
            'Brazil': 'BR',
            'Brunei': 'BN',
            'Bulgaria': 'BG',
            'Burkina Faso': 'BF',
            'Burundi': 'BI',
            'Cameroon': 'CM',
            'Canada': 'CA',
            'Cape Verde': 'CV',
            'Central African Republic': 'CF',
            'Chile': 'CL',
            'China': 'CN',
            'Christmas Island': 'CX',
            'Cocos Islands': 'CC',
            'Colombia': 'CO',
            'Cook Islands': 'CK',
            'Costa Rica': 'CR',
            'Cuba': 'CU',
            'Curacao': 'CW',
            'Cyprus': 'CY',
            'Czech Republic': 'CZ',
            'Democratic Republic of the Congo': 'CD',
            'Denmark': 'DK',
            'Djibouti': 'DJ',
            'Dominica': 'DM',
            'Dominican Republic': 'DO',
            'Ecuador': 'EC',
            'Egypt': 'EG',
            'Eritrea': 'ER',
            'Estonia': 'EE',
            'Ethiopia': 'ET',
            'Falkland Islands': 'FK',
            'Faroe Islands': 'FO',
            'Fiji': 'FJ',
            'Finland': 'FI',
            'France': 'FR',
            'French Polynesia': 'PF',
            'Gabon': 'GA',
            'Gambia': 'GM',
            'Georgia': 'GE',
            'Germany': 'DE',
            'Ghana': 'GH',
            'Gilbraltar': 'GI',
            'Greece': 'GR',
            'Greenland': 'GL',
            'Grenada': 'GD',
            'Guam': 'GU',
            'Guatemala': 'GT',
            'Guernsey': 'GG',
            'Guinea': 'GN',
            'Guinea-Bissau': 'GW',
            'Guyana': 'GY',
            'Haiti': 'HT',
            'Honduras': 'HN',
            'Hong Kong': 'HK',
            'Hungary': 'HU',
            'Iceland': 'IS',
            'India': 'IN',
            'Indonesia': 'ID',
            'Iran': 'IR',
            'Iraq': 'IQ',
            'Ireland': 'IE',
            'Isle of Man': 'IM',
            'Israel': 'IL',
            'Italy': 'IT',
            'Ivory Coast': 'CI',
            'Jamaica': 'JM',
            'Japan': 'JP',
            'Jersey': 'JE',
            'Jordan': 'JO',
            'Kazakhstan': 'KZ',
            'Laos': 'LA',
            'Latvia': 'LV',
            'Lebanon': 'LB',
            'Lesotho': 'LS',
            'Liberia': 'LR',
            'Libya': 'LY',
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
            'Mauritania': 'MR',
            'Mauritius': 'MU',
            'Mayotte': 'YT',
            'Mexico': 'MX',
            'Micronesia': 'FM',
            'Moldova': 'MD',
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
            'Netherlands Antilles': 'AN',
            'New Caledonia': 'NC',
            'New Zealand': 'NZ',
            'Nicaragua': 'NI',
            'Niger': 'NE',
            'Nigeria': 'NG',
            'Niue': 'NU',
            'North Korea': 'KP',
            'Northern Mariana Islands': 'MP',
            'Norway': 'NO',
            'Oman': 'OM',
            'Pakistan': 'PK',
            'Palau': 'PW',
            'Palestine': 'PS',
            'Panama': 'PA',
            'Papua New Guinea': 'PG',
            'Paraguay': 'PY',
            'Peru': 'PE',
            'Philippines': 'PH',
            'Pitcairn': 'PN',
            'Poland': 'PL',
            'Portugal': 'PT',
            'Puerto Rico': 'PR',
            'Qatar': 'QA',
            'Republic of the Congo': 'CG',
            'Reunion': 'RE',
            'Romania': 'RO',
            'Russia': 'RU',
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
            'Sint Maarten': 'SX',
            'Slovakia': 'SK',
            'Slovenia': 'SI',
            'Solomon Islands': 'SB',
            'Somalia': 'SO',
            'South Africa': 'ZA',
            'South Korea': 'KR',
            'South Sudan': 'SS',
            'Spain': 'ES',
            'Sri Lanka': 'LK',
            'Sudan': 'SD',
            'Suriname': 'SR',
            'Svalbard and Jan Mayen': 'SJ',
            'Swaziland': 'SZ',
            'Sweden': 'SE',
            'Switzerland': 'CH',
            'Syria': 'SY',
            'Taiwan': 'TW',
            'Tajikstan': 'TJ',
            'Tanzania': 'TZ',
            'Thailand': 'TH',
            'Togo': 'TG',
            'Tokelau': 'TK',
            'Tonga': 'TO',
            'Trinidad and Tobago': 'TT',
            'Tunisia': 'TN',
            'Turkey': 'TR',
            'Turkmenistan': 'TM',
            'Turks and Caicos Islands': 'TC',
            'Tuvalu': 'TV',
            'U.S. Virgin Islands': 'VI',
            'Uganda': 'UG',
            'Ukraine': 'UA',
            'United Arab Emirates': 'AE',
            'United Kingdom': 'GB',
            'United States': 'US',
            'Uruguay': 'UY',
            'Uzbekistan': 'UZ',
            'Vanuatu': 'VU',
            'Vatican': 'VA',
            'Venezuela': 'VE',
            'Vietnam': 'VN',
            'Wallis and Futuna': 'WF',
            'Western Sahara': 'EH',
            'Yemen': 'YE',
            'Zambia': 'ZM',
            'Zimbabwe': 'ZW'
        }
        self.choices_iso_codes = self.country_iso_map.values()

    def is_valid_hostname(self, host):
        """Reasonable attempt at validating a hostname

        Compiled from various paragraphs outlined here
        https://tools.ietf.org/html/rfc3696#section-2
        https://tools.ietf.org/html/rfc1123

        Notably,
        * Host software MUST handle host names of up to 63 characters and
          SHOULD handle host names of up to 255 characters.
        * The "LDH rule", after the characters that it permits. (letters, digits, hyphen)
        * If the hyphen is used, it is not permitted to appear at
          either the beginning or end of a label

        :param host:
        :return:
        """
        if len(host) > 255:
            return False
        host = host.rstrip(".")
        allowed = re.compile(r'(?!-)[A-Z0-9-]{1,63}(?<!-)$', re.IGNORECASE)
        return all(allowed.match(x) for x in host.split("."))

    @property
    def addresses(self):
        if self._values['addresses'] is None:
            return None
        result = []
        for x in self._values['addresses']:
            if is_valid_ip(x):
                result.append(str(ip_address(u'{0}'.format(x))))
            elif is_valid_ip_interface(x):
                result.append(str(ip_interface(u'{0}'.format(x))))
            else:
                raise F5ModuleError(
                    "Address {0} must be either an IPv4 or IPv6 address or network.".format(x)
                )
        result = sorted(result)
        return result

    @property
    def address_ranges(self):
        if self._values['address_ranges'] is None:
            return None
        result = []
        for address_range in self._values['address_ranges']:
            start, stop = address_range.split('-')
            start = start.strip()
            stop = stop.strip()

            start = ip_address(u'{0}'.format(start))
            stop = ip_address(u'{0}'.format(stop))
            if start.version != stop.version:
                raise F5ModuleError(
                    "When specifying a range, IP addresses must be of the same type; IPv4 or IPv6."
                )
            if int(start) > int(stop):
                stop, start = start, stop
            item = '{0}-{1}'.format(str(start), str(stop))
            result.append(item)
        result = sorted(result)
        return result

    @property
    def address_lists(self):
        if self._values['address_lists'] is None:
            return None
        result = []
        for x in self._values['address_lists']:
            item = fq_name(self.partition, x)
            result.append(item)
        result = sorted(result)
        return result

    @property
    def fqdns(self):
        if self._values['fqdns'] is None:
            return None
        result = []
        for x in self._values['fqdns']:
            if self.is_valid_hostname(x):
                result.append(x)
            else:
                raise F5ModuleError(
                    "The hostname '{0}' looks invalid.".format(x)
                )
        result = sorted(result)
        return result

    @property
    def geo_locations(self):
        if self._values['geo_locations'] is None:
            return None
        result = []
        for x in self._values['geo_locations']:
            if x['region'] is not None and x['region'].strip() != '':
                tmp = '{0}:{1}'.format(x['country'], x['region'])
            else:
                tmp = x['country']
            result.append(tmp)
        result = sorted(result)
        return result


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


class ReportableChanges(Changes):
    @property
    def addresses(self):
        result = []
        for item in self._values['addresses']:
            if '-' in item['name']:
                continue
            result.append(item['name'])
        return result

    @property
    def address_ranges(self):
        result = []
        for item in self._values['addresses']:
            if '-' not in item['name']:
                continue
            start, stop = item['name'].split('-')
            start = start.strip()
            stop = stop.strip()

            start = ip_address(u'{0}'.format(start))
            stop = ip_address(u'{0}'.format(stop))
            if start.version != stop.version:
                raise F5ModuleError(
                    "When specifying a range, IP addresses must be of the same type; IPv4 or IPv6."
                )
            if int(start) > int(stop):
                stop, start = start, stop
            item = '{0}-{1}'.format(str(start), str(stop))
            result.append(item)
        result = sorted(result)
        return result

    @property
    def address_lists(self):
        result = []
        for x in self._values['address_lists']:
            item = '/{0}/{1}'.format(x['partition'], x['name'])
            result.append(item)
        result = sorted(result)
        return result


class UsableChanges(Changes):
    @property
    def addresses(self):
        if self._values['addresses'] is None and self._values['address_ranges'] is None:
            return None
        result = []
        if self._values['addresses']:
            result += [dict(name=str(x)) for x in self._values['addresses']]
        if self._values['address_ranges']:
            result += [dict(name=str(x)) for x in self._values['address_ranges']]
        return result

    @property
    def address_lists(self):
        if self._values['address_lists'] is None:
            return None
        result = []
        for x in self._values['address_lists']:
            partition, name = x.split('/')[1:]
            result.append(dict(
                name=name,
                partition=partition
            ))
        return result


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
    def addresses(self):
        if self.want.addresses is None:
            return None
        elif self.have.addresses is None:
            return self.want.addresses
        if sorted(self.want.addresses) != sorted(self.have.addresses):
            return self.want.addresses

    @property
    def address_lists(self):
        if self.want.address_lists is None:
            return None
        elif self.have.address_lists is None:
            return self.want.address_lists
        if sorted(self.want.address_lists) != sorted(self.have.address_lists):
            return self.want.address_lists

    @property
    def address_ranges(self):
        if self.want.address_ranges is None:
            return None
        elif self.have.address_ranges is None:
            return self.want.address_ranges
        if sorted(self.want.address_ranges) != sorted(self.have.address_ranges):
            return self.want.address_ranges

    @property
    def fqdns(self):
        if self.want.fqdns is None:
            return None
        elif self.have.fqdns is None:
            return self.want.fqdns
        if sorted(self.want.fqdns) != sorted(self.have.fqdns):
            return self.want.fqdns


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

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

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

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

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        if self.exists():
            return self.remove()
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
        self.have = ApiParameters()
        self._update_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/address-list/{2}".format(
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
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/address-list/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/address-list/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/address-list/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True
        raise F5ModuleError(resp.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/security/firewall/address-list/{2}".format(
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
        argument_spec = dict(
            description=dict(),
            name=dict(required=True),
            addresses=dict(type='list'),
            address_ranges=dict(type='list'),
            address_lists=dict(type='list'),
            geo_locations=dict(
                type='list',
                elements='dict',
                options=dict(
                    country=dict(
                        required=True,
                    ),
                    region=dict()
                )
            ),
            fqdns=dict(type='list'),
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
        supports_check_mode=spec.supports_check_mode
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
