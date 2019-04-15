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
module: bigip_gtm_topology_record
short_description: Manages GTM Topology Records
description:
  - Manages GTM Topology Records. Once created, only topology record C(weight) can be modified.
version_added: 2.8
options:
  source:
    description:
      - Specifies the origination of an incoming DNS request.
    suboptions:
      negate:
        description:
          - When set to c(yes) the system selects this topology record, when the request source does not match.
        type: bool
        default: no
      subnet:
        description:
          - An IP address and network mask in the CIDR format.
        type: str
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
          - Specifies a country.
          - In addition to the country full names, you may also specify their abbreviated
            form, such as C(US) instead of C(United States).
          - Valid country codes can be found here https://countrycode.org/.
        type: str
      state:
        description:
          - Specifies a state in a given country.
          - This parameter requires country option to be provided.
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
    type: dict
    required: True
  destination:
    description:
      - Specifies where the system directs the incoming DNS request.
    suboptions:
      negate:
        description:
          - When set to c(yes) the system selects this topology record, when the request destination does not match.
        type: bool
        default: no
      subnet:
        description:
          - An IP address and network mask in the CIDR format.
        type: str
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
          - Specifies a country.
          - Full continent names and their abbreviated versions are supported.
        type: str
      state:
        description:
          - Specifies a state in a given country.
          - This parameter requires country option to be provided.
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
    type: dict
    required: True
  weight:
     description:
       - Specifies the weight of the topology record.
       - The system finds the weight of the first topology record that matches the server object (pool or pool member)
         and the local DNS. The system then assigns that weight as the topology score for that server object.
       - The system load balances to the server object with the highest topology score.
       - If the system finds no topology record that matches both the server object and the local DNS,
         then the system assigns that server object a zero score.
       - If the option is not specified when the record is created the system will set it at a default value of C(1)
       - Valid range is (0 - 4294967295)
     type: int
  partition:
    description:
      - Device partition to manage resources on.
      - Partition parameter is taken into account when used in conjunction with C(pool), C(data_center),
        and C(region) parameters, it is ignored otherwise.
    type: str
    default: Common
  state:
    description:
      - When C(state) is C(present), ensures that the record exists.
      - When C(state) is C(absent), ensures that the record is removed.
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
- name: Create an IP Subnet and an ISP based topology record
  bigip_gtm_topology_record:
    source:
      - subnet: 192.168.1.0/24
    destination:
      - isp: AOL
    weight: 10
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Create a region and a pool based topology record
  bigip_gtm_topology_record:
    source:
      - region: Foo
    destination:
      - pool: FooPool
    partition: FooBar
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Create a negative region and a negative data center based topology record
  bigip_gtm_topology_record:
    source:
      - region: Baz
      - negate: yes
    destination:
      - datacenter: Baz-DC
      - negate: yes
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
weight:
  description: The weight of the topology record.
  returned: changed
  type: int
  sample: 20
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import iteritems

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.ipaddress import is_valid_ip_network
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip_network


class Parameters(AnsibleF5Parameters):
    api_map = {
        'score': 'weight',
    }

    api_attributes = [
        'score',
    ]

    returnables = [
        'weight',
        'name'
    ]

    updatables = [
        'weight',
    ]


class ApiParameters(Parameters):
    pass


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
    def src_negate(self):
        src_negate = self._values['source'].get('negate', None)
        result = flatten_boolean(src_negate)
        if result == 'yes':
            return 'not'
        return None

    @property
    def src_subnet(self):
        src_subnet = self._values['source'].get('subnet', None)
        if src_subnet is None:
            return None
        if is_valid_ip_network(src_subnet):
            return src_subnet
        raise F5ModuleError(
            "Specified 'subnet' is not a valid subnet."
        )

    @property
    def src_region(self):
        src_region = self._values['source'].get('region', None)
        if src_region is None:
            return None
        return fq_name(self.partition, src_region)

    @property
    def src_continent(self):
        src_continent = self._values['source'].get('continent', None)
        if src_continent is None:
            return None
        result = self.continents.get(src_continent, src_continent)
        return result

    @property
    def src_country(self):
        src_country = self._values['source'].get('country', None)
        if src_country is None:
            return None
        result = self.countries.get(src_country, src_country)
        return result

    @property
    def src_state(self):
        src_country = self._values['source'].get('country', None)
        src_state = self._values['source'].get('state', None)
        if src_state is None:
            return None
        if src_country is None:
            raise F5ModuleError(
                'Country needs to be provided when specifying state'
            )
        result = '{0}/{1}'.format(src_country, src_state)
        return result

    @property
    def src_isp(self):
        src_isp = self._values['source'].get('isp', None)
        if src_isp is None:
            return None
        return fq_name('Common', src_isp)

    @property
    def src_geo_isp(self):
        src_geo_isp = self._values['source'].get('geo_isp', None)
        return src_geo_isp

    @property
    def dst_negate(self):
        dst_negate = self._values['destination'].get('negate', None)
        result = flatten_boolean(dst_negate)
        if result == 'yes':
            return 'not'
        return None

    @property
    def dst_subnet(self):
        dst_subnet = self._values['destination'].get('subnet', None)
        if dst_subnet is None:
            return None
        if is_valid_ip_network(dst_subnet):
            return dst_subnet
        raise F5ModuleError(
            "Specified 'subnet' is not a valid subnet."
        )

    @property
    def dst_region(self):
        dst_region = self._values['destination'].get('region', None)
        if dst_region is None:
            return None
        return fq_name(self.partition, dst_region)

    @property
    def dst_continent(self):
        dst_continent = self._values['destination'].get('continent', None)
        if dst_continent is None:
            return None
        result = self.continents.get(dst_continent, dst_continent)
        return result

    @property
    def dst_country(self):
        dst_country = self._values['destination'].get('country', None)
        if dst_country is None:
            return None
        result = self.countries.get(dst_country, dst_country)
        return result

    @property
    def dst_state(self):
        dst_country = self.dst_country
        dst_state = self._values['destination'].get('state', None)
        if dst_state is None:
            return None
        if dst_country is None:
            raise F5ModuleError(
                'Country needs to be provided when specifying state'
            )
        result = '{0}/{1}'.format(dst_country, dst_state)
        return result

    @property
    def dst_isp(self):
        dst_isp = self._values['destination'].get('isp', None)
        if dst_isp is None:
            return None
        return fq_name('Common', dst_isp)

    @property
    def dst_geo_isp(self):
        dst_geo_isp = self._values['destination'].get('geo_isp', None)
        return dst_geo_isp

    @property
    def dst_pool(self):
        dst_pool = self._values['destination'].get('pool', None)
        if dst_pool is None:
            return None
        return fq_name(self.partition, dst_pool)

    @property
    def dst_datacenter(self):
        dst_datacenter = self._values['destination'].get('datacenter', None)
        if dst_datacenter is None:
            return None
        return fq_name(self.partition, dst_datacenter)

    @property
    def source(self):
        options = {
            'negate': self.src_negate,
            'subnet': self.src_subnet,
            'region': self.src_region,
            'continent': self.src_continent,
            'country': self.src_country,
            'state': self.src_state,
            'isp': self.src_isp,
            'geoip-isp': self.src_geo_isp,
        }
        result = 'ldns: {0}'.format(self._format_options(options))
        return result

    @property
    def destination(self):
        options = {
            'negate': self.dst_negate,
            'subnet': self.dst_subnet,
            'region': self.dst_region,
            'continent': self.dst_continent,
            'country': self.dst_country,
            'state': self.dst_state,
            'datacenter': self.dst_datacenter,
            'pool': self.dst_pool,
            'isp': self.dst_isp,
            'geoip-isp': self.dst_geo_isp,
        }
        result = 'server: {0}'.format(self._format_options(options))
        return result

    @property
    def name(self):
        result = '{0} {1}'.format(self.source, self.destination)
        return result

    def _format_options(self, options):
        negate = None
        cleaned = dict((k, v) for k, v in iteritems(options) if v is not None)
        if 'country' and 'state' in cleaned.keys():
            del cleaned['country']
        if 'negate' in cleaned.keys():
            negate = cleaned['negate']
            del cleaned['negate']
        name, value = cleaned.popitem()
        if negate:
            result = '{0} {1} {2}'.format(negate, name, value)
            return result
        result = '{0} {1}'.format(name, value)
        return result

    @property
    def weight(self):
        weight = self._values['weight']
        if weight is None:
            return None
        if 0 <= weight <= 4294967295:
            return weight
        raise F5ModuleError(
            "Valid weight must be in range 0 - 4294967295"
        )


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
    pass


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
            self.client.module.deprecate(
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
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def exists(self):
        name = self.want.name
        uri = "https://{0}:{1}/mgmt/tm/gtm/topology/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            name.replace(' ', '%20').replace('/', '~')
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
        uri = "https://{0}:{1}/mgmt/tm/gtm/topology/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        name = self.want.name
        uri = "https://{0}:{1}/mgmt/tm/gtm/topology/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            name.replace(' ', '%20').replace('/', '~')
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
        name = self.want.name
        uri = "https://{0}:{1}/mgmt/tm/gtm/topology/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            name.replace(' ', '%20').replace('/', '~')
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        name = self.want.name
        uri = "https://{0}:{1}/mgmt/tm/gtm/topology/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            name.replace(' ', '%20').replace('/', '~')
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
            source=dict(
                required=True,
                type='dict',
                options=dict(
                    subnet=dict(),
                    region=dict(),
                    continent=dict(),
                    country=dict(),
                    state=dict(),
                    isp=dict(
                        choices=self.choices
                    ),
                    geo_isp=dict(),
                    negate=dict(
                        type='bool',
                        default='no'
                    ),
                ),
                mutually_exclusive=[
                    ['subnet', 'region', 'continent', 'country', 'isp', 'geo_isp']
                ]
            ),
            destination=dict(
                required=True,
                type='dict',
                options=dict(
                    subnet=dict(),
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
                ),
                mutually_exclusive=[
                    ['subnet', 'region', 'continent', 'country', 'pool', 'datacenter', 'isp', 'geo_isp']
                ]
            ),
            weight=dict(type='int'),
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
