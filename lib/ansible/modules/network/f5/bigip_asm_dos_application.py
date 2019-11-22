#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_asm_dos_application
short_description: Manage application settings for DOS profile
description:
  - Manages Application settings for ASM/AFM DOS profile.
version_added: 2.9
options:
  profile:
    description:
      - Specifies the name of the profile to manage application settings in.
    type: str
    required: True
  rtbh_duration:
    description:
      - Specifies the duration of the RTBH BGP route advertisement, in seconds.
      - The accepted range is between 0 and 4294967295 inclusive.
    type: int
  rtbh_enable:
    description:
      - Specifies whether to enable Remote Triggered Black Hole C(RTBH) of attacking IPs by advertising BGP routes.
    type: bool
  scrubbing_duration:
    description:
      - Specifies the duration of the Traffic Scrubbing BGP route advertisement, in seconds.
      - The accepted range is between 0 and 4294967295 inclusive.
    type: int
  scrubbing_enable:
    description:
      - Specifies whether to enable Traffic Scrubbing during attacks by advertising BGP routes.
    type: bool
  single_page_application:
    description:
      - Specifies, when C(yes), that the system supports a Single Page Applications.
    type: bool
  trigger_irule:
    description:
      - Specifies, when C(yes), that the system activates an Application DoS iRule event.
    type: bool
  geolocations:
    description:
      - Manages the geolocations countries whitelist, blacklist.
    type: dict
    suboptions:
      whitelist:
        description:
          - A list of countries to be put on whitelist, must not have overlapping elements with C(blacklist).
        type: list
      blacklist:
        description:
          - A list of countries to be put on blacklist, must not have overlapping elements with C(whitelist).
        type: list
  heavy_urls:
    description:
      - Manages Heavy URL protection.
      - Heavy URLs are a small number of site URLs that might consume considerable server resources per request.
    type: dict
    suboptions:
      auto_detect:
        description:
          - Enables or disables automatic heavy URL detection.
        type: bool
      latency_threshold:
        description:
          - Specifies the latency threshold for automatic heavy URL detection.
          - The accepted range is between 0 and 4294967295 milliseconds inclusive.
        type: int
      exclude:
        description:
          - Specifies a list of URLs or wildcards to exclude from the heavy URLs.
        type: list
      include:
        description:
          - Configures additional URLs to include in the heavy URLs that were auto detected.
        type: list
        suboptions:
          url:
            description:
              - Specifies the URL to be added to the list of heavy URLs, in addition to the automatically detected ones.
            type: str
          threshold:
            description:
              - Specifies the threshold of requests per second, where the URL in question is considered under attack.
              - The accepted range is between 1 and 4294967295 inclusive, or C(auto).
            type: str
  mobile_detection:
    description:
      - Configures detection of mobile applications built with the Anti-Bot Mobile SDK and defines how requests
        from these mobile application clients are handled.
    type: dict
    suboptions:
      enabled:
        description:
          - When C(yes), requests from mobile applications built with Anti-Bot Mobile SDK will be detected and handled
            according to the parameters set.
          - When C(no), these requests will be handled like any other request which may let attacks in, or cause false
            positives.
        type: bool
      allow_android_rooted_device:
        description:
          - When C(yes) device will allow traffic from rooted Android devices.
        type: bool
      allow_any_android_package:
        description:
          - When C(yes) allows any application publisher.
          - A publisher is identified by the certificate used to sign the application.
        type: bool
      allow_any_ios_package:
        description:
          - When C(yes) allows any iOS package.
          - A package name is the unique identifier of the mobile application.
        type: bool
      allow_jailbroken_devices:
        description:
          - When C(yes) allows traffic from jailbroken iOS devices.
        type: bool
      allow_emulators:
        description:
          - When C(yes) allows traffic from applications run on emulators.
        type: bool
      client_side_challenge_mode:
        description:
          - Action to take when a CAPTCHA or Client Side Integrity challenge needs to be presented.
          - The mobile application user will not see a CAPTCHA challenge and the mobile application will not be
            presented with the Client Side Integrity challenge. The such options for mobile applications are C(pass)
            or C(cshui).
          - When C(pass) the traffic is passed without incident.
          - When C(cshui) the SDK checks for human interactions with the screen in the last few seconds.
            If none are detected, the traffic is blocked.
        type: str
        choices:
          - pass
          - cshui
      ios_allowed_package_names:
        description:
          - Specifies the names of iOS packages to allow traffic on.
          - This option has no effect when C(allow_any_ios_package) is set to C(yes).
        type: list
      android_publishers:
        description:
          - This option has no effect when C(allow_any_android_package) is set to C(yes).
          - Specifies the allowed publisher certificates for android applications.
          - The publisher certificate needs to be installed on the BIG-IP beforehand.
          - "The certificate name located on a different partition than the one specified
            in C(partition) parameter needs to be provided in C(full_path) format C(/Foo/cert.crt)."
        type: list
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(state) is C(present), ensures that the Application object exists.
      - When C(state) is C(absent), ensures that the Application object is removed.
    type: str
    choices:
      - present
      - absent
    default: present
notes:
  - Requires BIG-IP >= 13.1.0
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create an ASM dos application profile
  bigip_asm_dos_application:
    profile: dos_foo
    geolocations:
      blacklist:
        - Afghanistan
        - Andora
      whitelist:
        - Cuba
    heavy_urls:
      auto_detect: yes
      latency_threshold: 1000
    rtbh_duration: 3600
    rtbh_enable: yes
    single_page_application: yes
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Update an ASM dos application profile
  bigip_asm_dos_application:
    profile: dos_foo
    mobile_detection:
      enabled: yes
      allow_any_ios_package: yes
      allow_emulators: yes
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove an ASM dos application profile
  bigip_asm_dos_application:
    profile: dos_foo
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
rtbh_enable:
  description: Enables Remote Triggered Black Hole of attacking IPs.
  returned: changed
  type: bool
  sample: no
rtbh_duration:
  description: The duration of the RTBH BGP route advertisement.
  returned: changed
  type: int
  sample: 3600
scrubbing_enable:
  description: Enables Traffic Scrubbing during attacks.
  returned: changed
  type: bool
  sample: yes
scrubbing_duration:
  description: The duration of the Traffic Scrubbing BGP route advertisement.
  returned: changed
  type: int
  sample: 3600
single_page_application:
  description: Enables support of a Single Page Applications.
  returned: changed
  type: bool
  sample: no
trigger_irule:
  description: Activates an Application DoS iRule event.
  returned: changed
  type: bool
  sample: yes
geolocations:
  description: Specifies geolocations countries whitelist, blacklist.
  type: complex
  returned: changed
  contains:
    whitelist:
      description: A list of countries to be put on whitelist.
      returned: changed
      type: list
      sample: ['United States, United Kingdom']
    blacklist:
      description: A list of countries to be put on blacklist.
      returned: changed
      type: list
      sample: ['Russia', 'Germany']
  sample: hash/dictionary of values
heavy_urls:
  description: Manages Heavy URL protection.
  type: complex
  returned: changed
  contains:
    auto_detect:
      description: Enables or disables automatic heavy URL detection.
      returned: changed
      type: bool
      sample: yes
    latency_threshold:
      description: Specifies the latency threshold for automatic heavy URL detection.
      returned: changed
      type: int
      sample: 2000
    exclude:
      description: Specifies a list of URLs or wildcards to exclude from the heavy URLs.
      returned: changed
      type: list
      sample: ['/exclude.html', '/exclude2.html']
    include:
      description: Configures additional URLs to include in the heavy URLs.
      type: complex
      returned: changed
      contains:
        url:
          description: The URL to be added to the list of heavy URLs.
          returned: changed
          type: str
          sample: /include.html
        threshold:
          description: The threshold of requests per second
          returned: changed
          type: str
          sample: auto
      sample: hash/dictionary of values
  sample: hash/dictionary of values
mobile_detection:
  description: Configures detection of mobile applications built with the Anti-Bot Mobile SDK.
  type: complex
  returned: changed
  contains:
    enable:
      description: Enables or disables automatic mobile detection.
      returned: changed
      type: bool
      sample: yes
    allow_android_rooted_device:
      description: Allows traffic from rooted Android devices.
      returned: changed
      type: bool
      sample: no
    allow_any_android_package:
      description: Allows any application publisher.
      returned: changed
      type: bool
      sample: no
    allow_any_ios_package:
      description: Allows any iOS package.
      returned: changed
      type: bool
      sample: yes
    allow_jailbroken_devices:
      description: Allows traffic from jailbroken iOS devices.
      returned: changed
      type: bool
      sample: no
    allow_emulators:
      description: Allows traffic from applications run on emulators.
      returned: changed
      type: bool
      sample: yes
    client_side_challenge_mode:
      description: Action to take when a CAPTCHA or Client Side Integrity challenge needs to be presented.
      returned: changed
      type: str
      sample: pass
    ios_allowed_package_names:
      description: The names of iOS packages to allow traffic on.
      returned: changed
      type: list
      sample: ['package1','package2']
    android_publishers:
      description: The allowed publisher certificates for android applications.
      returned: changed
      type: list
      sample: ['/Common/cert1.crt', '/Common/cert2.crt']
  sample: hash/dictionary of values
'''
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.compare import compare_complex_list
    from library.module_utils.network.f5.compare import cmp_simple_list
    from library.module_utils.network.f5.icontrol import tmos_version
    from library.module_utils.network.f5.icontrol import module_provisioned
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.compare import compare_complex_list
    from ansible.module_utils.network.f5.compare import cmp_simple_list
    from ansible.module_utils.network.f5.icontrol import tmos_version
    from ansible.module_utils.network.f5.icontrol import module_provisioned


class Parameters(AnsibleF5Parameters):
    api_map = {
        'rtbhDurationSec': 'rtbh_duration',
        'rtbhEnable': 'rtbh_enable',
        'scrubbingDurationSec': 'scrubbing_duration',
        'scrubbingEnable': 'scrubbing_enable',
        'singlePageApplication': 'single_page_application',
        'triggerIrule': 'trigger_irule',
        'heavyUrls': 'heavy_urls',
        'mobileDetection': 'mobile_detection',
    }

    api_attributes = [
        'geolocations',
        'rtbhDurationSec',
        'rtbhEnable',
        'scrubbingDurationSec',
        'scrubbingEnable',
        'singlePageApplication',
        'triggerIrule',
        'heavyUrls',
        'mobileDetection',
    ]

    returnables = [
        'rtbh_duration',
        'rtbh_enable',
        'scrubbing_duration',
        'scrubbing_enable',
        'single_page_application',
        'trigger_irule',
        'enable_mobile_detection',
        'allow_android_rooted_device',
        'allow_any_android_package',
        'allow_any_ios_package',
        'allow_jailbroken_devices',
        'allow_emulators',
        'client_side_challenge_mode',
        'ios_allowed_package_names',
        'android_publishers',
        'auto_detect',
        'latency_threshold',
        'hw_url_exclude',
        'hw_url_include',
        'geo_blacklist',
        'geo_whitelist',
    ]

    updatables = [
        'rtbh_duration',
        'rtbh_enable',
        'scrubbing_duration',
        'scrubbing_enable',
        'single_page_application',
        'trigger_irule',
        'enable_mobile_detection',
        'allow_android_rooted_device',
        'allow_any_android_package',
        'allow_any_ios_package',
        'allow_jailbroken_devices',
        'allow_emulators',
        'client_side_challenge_mode',
        'ios_allowed_package_names',
        'android_publishers',
        'auto_detect',
        'latency_threshold',
        'hw_url_exclude',
        'hw_url_include',
        'geo_blacklist',
        'geo_whitelist',
    ]


class ApiParameters(Parameters):
    @property
    def enable_mobile_detection(self):
        if self._values['mobile_detection'] is None:
            return None
        return self._values['mobile_detection']['enabled']

    @property
    def allow_android_rooted_device(self):
        if self._values['mobile_detection'] is None:
            return None
        return self._values['mobile_detection']['allowAndroidRootedDevice']

    @property
    def allow_any_android_package(self):
        if self._values['mobile_detection'] is None:
            return None
        return self._values['mobile_detection']['allowAnyAndroidPackage']

    @property
    def allow_any_ios_package(self):
        if self._values['mobile_detection'] is None:
            return None
        return self._values['mobile_detection']['allowAnyIosPackage']

    @property
    def allow_jailbroken_devices(self):
        if self._values['mobile_detection'] is None:
            return None
        return self._values['mobile_detection']['allowJailbrokenDevices']

    @property
    def allow_emulators(self):
        if self._values['mobile_detection'] is None:
            return None
        return self._values['mobile_detection']['allowEmulators']

    @property
    def client_side_challenge_mode(self):
        if self._values['mobile_detection'] is None:
            return None
        return self._values['mobile_detection']['clientSideChallengeMode']

    @property
    def ios_allowed_package_names(self):
        if self._values['mobile_detection'] is None:
            return None
        return self._values['mobile_detection'].get('iosAllowedPackageNames', None)

    @property
    def android_publishers(self):
        if self._values['mobile_detection'] is None or 'androidPublishers' not in self._values['mobile_detection']:
            return None
        result = [fq_name(publisher['partition'], publisher['name'])
                  for publisher in self._values['mobile_detection']['androidPublishers']]
        return result

    @property
    def auto_detect(self):
        if self._values['heavy_urls'] is None:
            return None
        return self._values['heavy_urls']['automaticDetection']

    @property
    def latency_threshold(self):
        if self._values['heavy_urls'] is None:
            return None
        return self._values['heavy_urls']['latencyThreshold']

    @property
    def hw_url_exclude(self):
        if self._values['heavy_urls'] is None:
            return None
        return self._values['heavy_urls'].get('exclude', None)

    @property
    def hw_url_include(self):
        if self._values['heavy_urls'] is None:
            return None
        return self._values['heavy_urls'].get('includeList', None)

    @property
    def geo_blacklist(self):
        if self._values['geolocations'] is None:
            return None
        result = list()
        for item in self._values['geolocations']:
            if 'blackListed' in item and item['blackListed'] is True:
                result.append(item['name'])
        if result:
            return result

    @property
    def geo_whitelist(self):
        if self._values['geolocations'] is None:
            return None
        result = list()
        for item in self._values['geolocations']:
            if 'whiteListed' in item and item['whiteListed'] is True:
                result.append(item['name'])
        if result:
            return result


class ModuleParameters(Parameters):
    @property
    def rtbh_duration(self):
        if self._values['rtbh_duration'] is None:
            return None
        if 0 <= self._values['rtbh_duration'] <= 4294967295:
            return self._values['rtbh_duration']
        raise F5ModuleError(
            "Valid 'rtbh_duration' must be in range 0 - 4294967295 seconds."
        )

    @property
    def rtbh_enable(self):
        result = flatten_boolean(self._values['rtbh_enable'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def scrubbing_duration(self):
        if self._values['scrubbing_duration'] is None:
            return None
        if 0 <= self._values['scrubbing_duration'] <= 4294967295:
            return self._values['scrubbing_duration']
        raise F5ModuleError(
            "Valid 'scrubbing_duration' must be in range 0 - 4294967295 seconds."
        )

    @property
    def scrubbing_enable(self):
        result = flatten_boolean(self._values['scrubbing_enable'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def single_page_application(self):
        result = flatten_boolean(self._values['single_page_application'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def trigger_irule(self):
        result = flatten_boolean(self._values['trigger_irule'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def enable_mobile_detection(self):
        if self._values['mobile_detection'] is None:
            return None
        result = flatten_boolean(self._values['mobile_detection']['enabled'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def allow_android_rooted_device(self):
        if self._values['mobile_detection'] is None:
            return None
        result = flatten_boolean(self._values['mobile_detection']['allow_android_rooted_device'])
        if result == 'yes':
            return 'true'
        if result == 'no':
            return 'false'
        return result

    @property
    def allow_any_android_package(self):
        if self._values['mobile_detection'] is None:
            return None
        result = flatten_boolean(self._values['mobile_detection']['allow_any_android_package'])
        if result == 'yes':
            return 'true'
        if result == 'no':
            return 'false'
        return result

    @property
    def allow_any_ios_package(self):
        if self._values['mobile_detection'] is None:
            return None
        result = flatten_boolean(self._values['mobile_detection']['allow_any_ios_package'])
        if result == 'yes':
            return 'true'
        if result == 'no':
            return 'false'
        return result

    @property
    def allow_jailbroken_devices(self):
        if self._values['mobile_detection'] is None:
            return None
        result = flatten_boolean(self._values['mobile_detection']['allow_jailbroken_devices'])
        if result == 'yes':
            return 'true'
        if result == 'no':
            return 'false'
        return result

    @property
    def allow_emulators(self):
        if self._values['mobile_detection'] is None:
            return None
        result = flatten_boolean(self._values['mobile_detection']['allow_emulators'])
        if result == 'yes':
            return 'true'
        if result == 'no':
            return 'false'
        return result

    @property
    def client_side_challenge_mode(self):
        if self._values['mobile_detection'] is None:
            return None
        return self._values['mobile_detection']['client_side_challenge_mode']

    @property
    def ios_allowed_package_names(self):
        if self._values['mobile_detection'] is None:
            return None
        return self._values['mobile_detection']['ios_allowed_package_names']

    @property
    def android_publishers(self):
        if self._values['mobile_detection'] is None or self._values['mobile_detection']['android_publishers'] is None:
            return None
        result = [fq_name(self.partition, item) for item in self._values['mobile_detection']['android_publishers']]
        return result

    @property
    def auto_detect(self):
        if self._values['heavy_urls'] is None:
            return None
        result = flatten_boolean(self._values['heavy_urls']['auto_detect'])
        if result == 'yes':
            return 'enabled'
        if result == 'no':
            return 'disabled'
        return result

    @property
    def latency_threshold(self):
        if self._values['heavy_urls'] is None or self._values['heavy_urls']['latency_threshold'] is None:
            return None
        if 0 <= self._values['heavy_urls']['latency_threshold'] <= 4294967295:
            return self._values['heavy_urls']['latency_threshold']
        raise F5ModuleError(
            "Valid 'latency_threshold' must be in range 0 - 4294967295 milliseconds."
        )

    @property
    def hw_url_exclude(self):
        if self._values['heavy_urls'] is None:
            return None
        return self._values['heavy_urls']['exclude']

    @property
    def hw_url_include(self):
        if self._values['heavy_urls'] is None or self._values['heavy_urls']['include'] is None:
            return None
        result = list()
        for item in self._values['heavy_urls']['include']:
            element = dict()
            element['url'] = self._correct_url(item['url'])
            element['name'] = 'URL{0}'.format(self._correct_url(item['url']))
            if 'threshold' in item:
                element['threshold'] = self._validate_threshold(item['threshold'])
            result.append(element)
        return result

    def _validate_threshold(self, item):
        if item == 'auto':
            return item
        if 1 <= int(item) <= 4294967295:
            return item
        raise F5ModuleError(
            "Valid 'url threshold' must be in range 1 - 4294967295 requests per second or 'auto'."
        )

    def _correct_url(self, item):
        if item.startswith('/'):
            return item
        return "/{0}".format(item)

    @property
    def geo_blacklist(self):
        if self._values['geolocations'] is None:
            return None
        whitelist = self.geo_whitelist
        blacklist = self._values['geolocations']['blacklist']
        if whitelist and blacklist:
            if not set(whitelist).isdisjoint(set(blacklist)):
                raise F5ModuleError('Cannot specify the same element in blacklist and whitelist.')
        return blacklist

    @property
    def geo_whitelist(self):
        if self._values['geolocations'] is None:
            return None
        return self._values['geolocations']['whitelist']


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
    def geolocations(self):
        if self._values['geo_blacklist'] is None and self._values['geo_whitelist'] is None:
            return None
        result = list()
        if self._values['geo_blacklist']:
            for item in self._values['geo_blacklist']:
                element = dict()
                element['name'] = item
                element['blackListed'] = True
                result.append(element)
        if self._values['geo_whitelist']:
            for item in self._values['geo_whitelist']:
                element = dict()
                element['name'] = item
                element['whiteListed'] = True
                result.append(element)
        if result:
            return result

    @property
    def heavy_urls(self):
        tmp = dict()
        tmp['automaticDetection'] = self._values['auto_detect']
        tmp['latencyThreshold'] = self._values['latency_threshold']
        tmp['exclude'] = self._values['hw_url_exclude']
        tmp['includeList'] = self._values['hw_url_include']
        result = self._filter_params(tmp)
        if result:
            return result

    @property
    def mobile_detection(self):
        tmp = dict()
        tmp['enabled'] = self._values['enable_mobile_detection']
        tmp['allowAndroidRootedDevice'] = self._values['allow_android_rooted_device']
        tmp['allowAnyAndroidPackage'] = self._values['allow_any_android_package']
        tmp['allowAnyIosPackage'] = self._values['allow_any_ios_package']
        tmp['allowJailbrokenDevices'] = self._values['allow_jailbroken_devices']
        tmp['allowEmulators'] = self._values['allow_emulators']
        tmp['clientSideChallengeMode'] = self._values['client_side_challenge_mode']
        tmp['iosAllowedPackageNames'] = self._values['ios_allowed_package_names']
        tmp['androidPublishers'] = self._values['android_publishers']
        result = self._filter_params(tmp)
        if result:
            return result


class ReportableChanges(Changes):
    returnables = [
        'rtbh_duration',
        'rtbh_enable',
        'scrubbing_duration',
        'scrubbing_enable',
        'single_page_application',
        'trigger_irule',
        'heavy_urls',
        'mobile_detection',
        'geolocations',
    ]

    def _convert_include_list(self, items):
        result = list()
        for item in items:
            element = dict()
            element['url'] = item['url']
            if 'threshold' in item:
                element['threshold'] = item['threshold']
            result.append(element)
        if result:
            return result

    @property
    def geolocations(self):
        tmp = dict()
        tmp['blacklist'] = self._values['geo_blacklist']
        tmp['whitelist'] = self._values['geo_whitelist']
        result = self._filter_params(tmp)
        if result:
            return result

    @property
    def heavy_urls(self):
        tmp = dict()
        tmp['auto_detect'] = flatten_boolean(self._values['auto_detect'])
        tmp['latency_threshold'] = self._values['latency_threshold']
        tmp['exclude'] = self._values['hw_url_exclude']
        tmp['include'] = self._convert_include_list(self._values['hw_url_include'])
        result = self._filter_params(tmp)
        if result:
            return result

    @property
    def mobile_detection(self):
        tmp = dict()
        tmp['enabled'] = flatten_boolean(self._values['enable_mobile_detection'])
        tmp['allow_android_rooted_device'] = flatten_boolean(self._values['allow_android_rooted_device'])
        tmp['allow_any_android_package'] = flatten_boolean(self._values['allow_any_android_package'])
        tmp['allow_any_ios_package'] = flatten_boolean(self._values['allow_any_ios_package'])
        tmp['allow_jailbroken_devices'] = flatten_boolean(self._values['allow_jailbroken_devices'])
        tmp['allow_emulators'] = flatten_boolean(self._values['allow_emulators'])
        tmp['client_side_challenge_mode'] = self._values['client_side_challenge_mode']
        tmp['ios_allowed_package_names'] = self._values['ios_allowed_package_names']
        tmp['android_publishers'] = self._values['android_publishers']
        result = self._filter_params(tmp)
        if result:
            return result

    @property
    def rtbh_enable(self):
        result = flatten_boolean(self._values['rtbh_enable'])
        return result

    @property
    def scrubbing_enable(self):
        result = flatten_boolean(self._values['scrubbing_enable'])
        return result

    @property
    def single_page_application(self):
        result = flatten_boolean(self._values['single_page_application'])
        return result

    @property
    def trigger_irule(self):
        result = flatten_boolean(self._values['trigger_irule'])
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
    def hw_url_include(self):
        if self.want.hw_url_include is None:
            return None
        if self.have.hw_url_include is None and self.want.hw_url_include == []:
            return None
        if self.have.hw_url_include is None:
            return self.want.hw_url_include

        wants = self.want.hw_url_include
        haves = list()
        # First we remove extra keys in have for the same elements
        for want in wants:
            for have in self.have.hw_url_include:
                if want['url'] == have['url']:
                    entry = self._filter_have(want, have)
                    haves.append(entry)
        # Next we do compare the lists as normal
        result = compare_complex_list(wants, haves)
        return result

    def _filter_have(self, want, have):
        to_check = set(want.keys()).intersection(set(have.keys()))
        result = dict()
        for k in list(to_check):
            result[k] = have[k]
        return result

    @property
    def hw_url_exclude(self):
        result = cmp_simple_list(self.want.hw_url_exclude, self.have.hw_url_exclude)
        return result

    @property
    def geo_blacklist(self):
        result = cmp_simple_list(self.want.geo_blacklist, self.have.geo_blacklist)
        return result

    @property
    def geo_whitelist(self):
        result = cmp_simple_list(self.want.geo_whitelist, self.have.geo_whitelist)
        return result

    @property
    def android_publishers(self):
        result = cmp_simple_list(self.want.android_publishers, self.have.android_publishers)
        return result

    @property
    def ios_allowed_package_names(self):
        result = cmp_simple_list(self.want.ios_allowed_package_names, self.have.ios_allowed_package_names)
        return result


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
        if not module_provisioned(self.client, 'asm'):
            raise F5ModuleError(
                "ASM must be provisioned to use this module."
            )

        if self.version_less_than_13_1():
            raise F5ModuleError('Module supported on TMOS versions 13.1.x and above')

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

    def version_less_than_13_1(self):
        version = tmos_version(self.client)
        if LooseVersion(version) < LooseVersion('13.1.0'):
            return True
        return False

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

    def profile_exists(self):
        uri = "https://{0}:{1}/mgmt/tm/security/dos/profile/{2}/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile),
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def exists(self):
        if not self.profile_exists():
            raise F5ModuleError(
                'Specified DOS profile: {0} on partition: {1} does not exist.'.format(
                    self.want.profile, self.want.partition)
            )
        uri = "https://{0}:{1}/mgmt/tm/security/dos/profile/{2}/application/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile),
            self.want.profile
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
        params['name'] = self.want.profile
        uri = "https://{0}:{1}/mgmt/tm/security/dos/profile/{2}/application/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile),
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 409]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/security/dos/profile/{2}/application/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile),
            self.want.profile
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
        uri = "https://{0}:{1}/mgmt/tm/security/dos/profile/{2}/application/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile),
            self.want.profile
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/security/dos/profile/{2}/application/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.profile),
            self.want.profile
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
            profile=dict(
                required=True,
            ),
            geolocations=dict(
                type='dict',
                options=dict(
                    blacklist=dict(type='list'),
                    whitelist=dict(type='list'),
                ),
            ),
            heavy_urls=dict(
                type='dict',
                options=dict(
                    auto_detect=dict(type='bool'),
                    latency_threshold=dict(type='int'),
                    exclude=dict(type='list'),
                    include=dict(
                        type='list',
                        elements='dict',
                        options=dict(
                            url=dict(required=True),
                            threshold=dict(),
                        ),
                    )
                ),
            ),
            mobile_detection=dict(
                type='dict',
                options=dict(
                    enabled=dict(type='bool'),
                    allow_android_rooted_device=dict(type='bool'),
                    allow_any_android_package=dict(type='bool'),
                    allow_any_ios_package=dict(type='bool'),
                    allow_jailbroken_devices=dict(type='bool'),
                    allow_emulators=dict(type='bool'),
                    client_side_challenge_mode=dict(choices=['cshui', 'pass']),
                    ios_allowed_package_names=dict(type='list'),
                    android_publishers=dict(type='list')
                )
            ),
            rtbh_duration=dict(type='int'),
            rtbh_enable=dict(type='bool'),
            scrubbing_duration=dict(type='int'),
            scrubbing_enable=dict(type='bool'),
            single_page_application=dict(type='bool'),
            trigger_irule=dict(type='bool'),
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
