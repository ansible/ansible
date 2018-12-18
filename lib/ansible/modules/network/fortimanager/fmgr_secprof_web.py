#!/usr/bin/python
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
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fmgr_secprof_web
version_added: "2.8"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manage web filter security profiles in FortiManager
description:
  -  Manage web filter security profiles in FortiManager through playbooks using the FMG API

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  host:
    description:
      - The FortiManager's Address.
    required: true

  username:
    description:
      - The username associated with the account.
    required: true

  password:
    description:
      - The password associated with the username account.
    required: true

  mode:
    description:
      - Sets one of three modes for managing the object.
      - Allows use of soft-adds instead of overwriting existing values
    choices: ['add', 'set', 'delete', 'update']
    required: false
    default: add

  youtube_channel_status:
    description:
      - YouTube channel filter status.
      - choice | disable | Disable YouTube channel filter.
      - choice | blacklist | Block matches.
      - choice | whitelist | Allow matches.
    required: false
    choices: ["disable", "blacklist", "whitelist"]

  wisp_servers:
    description:
      - WISP servers.
    required: false

  wisp_algorithm:
    description:
      - WISP server selection algorithm.
      - choice | auto-learning | Select the lightest loading healthy server.
      - choice | primary-secondary | Select the first healthy server in order.
      - choice | round-robin | Select the next healthy server.
    required: false
    choices: ["auto-learning", "primary-secondary", "round-robin"]

  wisp:
    description:
      - Enable/disable web proxy WISP.
      - choice | disable | Disable web proxy WISP.
      - choice | enable | Enable web proxy WISP.
    required: false
    choices: ["disable", "enable"]

  web_url_log:
    description:
      - Enable/disable logging URL filtering.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_invalid_domain_log:
    description:
      - Enable/disable logging invalid domain names.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_ftgd_quota_usage:
    description:
      - Enable/disable logging daily quota usage.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_ftgd_err_log:
    description:
      - Enable/disable logging rating errors.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_filter_vbs_log:
    description:
      - Enable/disable logging VBS scripts.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_filter_unknown_log:
    description:
      - Enable/disable logging unknown scripts.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_filter_referer_log:
    description:
      - Enable/disable logging referrers.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_filter_jscript_log:
    description:
      - Enable/disable logging JScripts.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_filter_js_log:
    description:
      - Enable/disable logging Java scripts.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_filter_cookie_removal_log:
    description:
      - Enable/disable logging blocked cookies.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_filter_cookie_log:
    description:
      - Enable/disable logging cookie filtering.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_filter_command_block_log:
    description:
      - Enable/disable logging blocked commands.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_filter_applet_log:
    description:
      - Enable/disable logging Java applets.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_filter_activex_log:
    description:
      - Enable/disable logging ActiveX.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_extended_all_action_log:
    description:
      - Enable/disable extended any filter action logging for web filtering.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_content_log:
    description:
      - Enable/disable logging logging blocked web content.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  replacemsg_group:
    description:
      - Replacement message group.
    required: false

  post_action:
    description:
      - Action taken for HTTP POST traffic.
      - choice | normal | Normal, POST requests are allowed.
      - choice | block | POST requests are blocked.
    required: false
    choices: ["normal", "block"]

  ovrd_perm:
    description:
      - FLAG Based Options. Specify multiple in list form.
      - flag | bannedword-override | Banned word override.
      - flag | urlfilter-override | URL filter override.
      - flag | fortiguard-wf-override | FortiGuard Web Filter override.
      - flag | contenttype-check-override | Content-type header override.
    required: false
    choices:
      - bannedword-override
      - urlfilter-override
      - fortiguard-wf-override
      - contenttype-check-override

  options:
    description:
      - FLAG Based Options. Specify multiple in list form.
      - flag | block-invalid-url | Block sessions contained an invalid domain name.
      - flag | jscript | Javascript block.
      - flag | js | JS block.
      - flag | vbs | VB script block.
      - flag | unknown | Unknown script block.
      - flag | wf-referer | Referring block.
      - flag | intrinsic | Intrinsic script block.
      - flag | wf-cookie | Cookie block.
      - flag | per-user-bwl | Per-user black/white list filter
      - flag | activexfilter | ActiveX filter.
      - flag | cookiefilter | Cookie filter.
      - flag | javafilter | Java applet filter.
    required: false
    choices:
      - block-invalid-url
      - jscript
      - js
      - vbs
      - unknown
      - wf-referer
      - intrinsic
      - wf-cookie
      - per-user-bwl
      - activexfilter
      - cookiefilter
      - javafilter

  name:
    description:
      - Profile name.
    required: false

  log_all_url:
    description:
      - Enable/disable logging all URLs visited.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  inspection_mode:
    description:
      - Web filtering inspection mode.
      - choice | proxy | Proxy.
      - choice | flow-based | Flow based.
    required: false
    choices: ["proxy", "flow-based"]

  https_replacemsg:
    description:
      - Enable replacement messages for HTTPS.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  extended_log:
    description:
      - Enable/disable extended logging for web filtering.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  comment:
    description:
      - Optional comments.
    required: false

  ftgd_wf:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  ftgd_wf_exempt_quota:
    description:
      - Do not stop quota for these categories.
    required: false

  ftgd_wf_max_quota_timeout:
    description:
      - Maximum FortiGuard quota used by single page view in seconds (excludes streams).
    required: false

  ftgd_wf_options:
    description:
      - Options for FortiGuard Web Filter.
      - FLAG Based Options. Specify multiple in list form.
      - flag | error-allow | Allow web pages with a rating error to pass through.
      - flag | rate-server-ip | Rate the server IP in addition to the domain name.
      - flag | connect-request-bypass | Bypass connection which has CONNECT request.
      - flag | ftgd-disable | Disable FortiGuard scanning.
    required: false
    choices: ["error-allow", "rate-server-ip", "connect-request-bypass", "ftgd-disable"]

  ftgd_wf_ovrd:
    description:
      - Allow web filter profile overrides.
    required: false

  ftgd_wf_rate_crl_urls:
    description:
      - Enable/disable rating CRL by URL.
      - choice | disable | Disable rating CRL by URL.
      - choice | enable | Enable rating CRL by URL.
    required: false
    choices: ["disable", "enable"]

  ftgd_wf_rate_css_urls:
    description:
      - Enable/disable rating CSS by URL.
      - choice | disable | Disable rating CSS by URL.
      - choice | enable | Enable rating CSS by URL.
    required: false
    choices: ["disable", "enable"]

  ftgd_wf_rate_image_urls:
    description:
      - Enable/disable rating images by URL.
      - choice | disable | Disable rating images by URL (blocked images are replaced with blanks).
      - choice | enable | Enable rating images by URL (blocked images are replaced with blanks).
    required: false
    choices: ["disable", "enable"]

  ftgd_wf_rate_javascript_urls:
    description:
      - Enable/disable rating JavaScript by URL.
      - choice | disable | Disable rating JavaScript by URL.
      - choice | enable | Enable rating JavaScript by URL.
    required: false
    choices: ["disable", "enable"]

  ftgd_wf_filters_action:
    description:
      - Action to take for matches.
      - choice | block | Block access.
      - choice | monitor | Allow access while logging the action.
      - choice | warning | Allow access after warning the user.
      - choice | authenticate | Authenticate user before allowing access.
    required: false
    choices: ["block", "monitor", "warning", "authenticate"]

  ftgd_wf_filters_auth_usr_grp:
    description:
      - Groups with permission to authenticate.
    required: false

  ftgd_wf_filters_category:
    description:
      - Categories and groups the filter examines.
    required: false

  ftgd_wf_filters_log:
    description:
      - Enable/disable logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  ftgd_wf_filters_override_replacemsg:
    description:
      - Override replacement message.
    required: false

  ftgd_wf_filters_warn_duration:
    description:
      - Duration of warnings.
    required: false

  ftgd_wf_filters_warning_duration_type:
    description:
      - Re-display warning after closing browser or after a timeout.
      - choice | session | After session ends.
      - choice | timeout | After timeout occurs.
    required: false
    choices: ["session", "timeout"]

  ftgd_wf_filters_warning_prompt:
    description:
      - Warning prompts in each category or each domain.
      - choice | per-domain | Per-domain warnings.
      - choice | per-category | Per-category warnings.
    required: false
    choices: ["per-domain", "per-category"]

  ftgd_wf_quota_category:
    description:
      - FortiGuard categories to apply quota to (category action must be set to monitor).
    required: false

  ftgd_wf_quota_duration:
    description:
      - Duration of quota.
    required: false

  ftgd_wf_quota_override_replacemsg:
    description:
      - Override replacement message.
    required: false

  ftgd_wf_quota_type:
    description:
      - Quota type.
      - choice | time | Use a time-based quota.
      - choice | traffic | Use a traffic-based quota.
    required: false
    choices: ["time", "traffic"]

  ftgd_wf_quota_unit:
    description:
      - Traffic quota unit of measurement.
      - choice | B | Quota in bytes.
      - choice | KB | Quota in kilobytes.
      - choice | MB | Quota in megabytes.
      - choice | GB | Quota in gigabytes.
    required: false
    choices: ["B", "KB", "MB", "GB"]

  ftgd_wf_quota_value:
    description:
      - Traffic quota value.
    required: false

  override:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  override_ovrd_cookie:
    description:
      - Allow/deny browser-based (cookie) overrides.
      - choice | deny | Deny browser-based (cookie) override.
      - choice | allow | Allow browser-based (cookie) override.
    required: false
    choices: ["deny", "allow"]

  override_ovrd_dur:
    description:
      - Override duration.
    required: false

  override_ovrd_dur_mode:
    description:
      - Override duration mode.
      - choice | constant | Constant mode.
      - choice | ask | Prompt for duration when initiating an override.
    required: false
    choices: ["constant", "ask"]

  override_ovrd_scope:
    description:
      - Override scope.
      - choice | user | Override for the user.
      - choice | user-group | Override for the user's group.
      - choice | ip | Override for the initiating IP.
      - choice | ask | Prompt for scope when initiating an override.
      - choice | browser | Create browser-based (cookie) override.
    required: false
    choices: ["user", "user-group", "ip", "ask", "browser"]

  override_ovrd_user_group:
    description:
      - User groups with permission to use the override.
    required: false

  override_profile:
    description:
      - Web filter profile with permission to create overrides.
    required: false

  override_profile_attribute:
    description:
      - Profile attribute to retrieve from the RADIUS server.
      - choice | User-Name | Use this attribute.
      - choice | NAS-IP-Address | Use this attribute.
      - choice | Framed-IP-Address | Use this attribute.
      - choice | Framed-IP-Netmask | Use this attribute.
      - choice | Filter-Id | Use this attribute.
      - choice | Login-IP-Host | Use this attribute.
      - choice | Reply-Message | Use this attribute.
      - choice | Callback-Number | Use this attribute.
      - choice | Callback-Id | Use this attribute.
      - choice | Framed-Route | Use this attribute.
      - choice | Framed-IPX-Network | Use this attribute.
      - choice | Class | Use this attribute.
      - choice | Called-Station-Id | Use this attribute.
      - choice | Calling-Station-Id | Use this attribute.
      - choice | NAS-Identifier | Use this attribute.
      - choice | Proxy-State | Use this attribute.
      - choice | Login-LAT-Service | Use this attribute.
      - choice | Login-LAT-Node | Use this attribute.
      - choice | Login-LAT-Group | Use this attribute.
      - choice | Framed-AppleTalk-Zone | Use this attribute.
      - choice | Acct-Session-Id | Use this attribute.
      - choice | Acct-Multi-Session-Id | Use this attribute.
    required: false
    choices:
      - User-Name
      - NAS-IP-Address
      - Framed-IP-Address
      - Framed-IP-Netmask
      - Filter-Id
      - Login-IP-Host
      - Reply-Message
      - Callback-Number
      - Callback-Id
      - Framed-Route
      - Framed-IPX-Network
      - Class
      - Called-Station-Id
      - Calling-Station-Id
      - NAS-Identifier
      - Proxy-State
      - Login-LAT-Service
      - Login-LAT-Node
      - Login-LAT-Group
      - Framed-AppleTalk-Zone
      - Acct-Session-Id
      - Acct-Multi-Session-Id

  override_profile_type:
    description:
      - Override profile type.
      - choice | list | Profile chosen from list.
      - choice | radius | Profile determined by RADIUS server.
    required: false
    choices: ["list", "radius"]

  url_extraction:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  url_extraction_redirect_header:
    description:
      - HTTP header name to use for client redirect on blocked requests
    required: false

  url_extraction_redirect_no_content:
    description:
      - Enable / Disable empty message-body entity in HTTP response
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  url_extraction_redirect_url:
    description:
      - HTTP header value to use for client redirect on blocked requests
    required: false

  url_extraction_server_fqdn:
    description:
      - URL extraction server FQDN (fully qualified domain name)
    required: false

  url_extraction_status:
    description:
      - Enable URL Extraction
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  web_blacklist:
    description:
      - Enable/disable automatic addition of URLs detected by FortiSandbox to blacklist.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_bword_table:
    description:
      - Banned word table ID.
    required: false

  web_bword_threshold:
    description:
      - Banned word score threshold.
    required: false

  web_content_header_list:
    description:
      - Content header list.
    required: false

  web_keyword_match:
    description:
      - Search keywords to log when match is found.
    required: false

  web_log_search:
    description:
      - Enable/disable logging all search phrases.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  web_safe_search:
    description:
      - Safe search type.
      - FLAG Based Options. Specify multiple in list form.
      - flag | url | Insert safe search string into URL.
      - flag | header | Insert safe search header.
    required: false
    choices: ["url", "header"]

  web_urlfilter_table:
    description:
      - URL filter table ID.
    required: false

  web_whitelist:
    description:
      - FortiGuard whitelist settings.
      - FLAG Based Options. Specify multiple in list form.
      - flag | exempt-av | Exempt antivirus.
      - flag | exempt-webcontent | Exempt web content.
      - flag | exempt-activex-java-cookie | Exempt ActiveX-JAVA-Cookie.
      - flag | exempt-dlp | Exempt DLP.
      - flag | exempt-rangeblock | Exempt RangeBlock.
      - flag | extended-log-others | Support extended log.
    required: false
    choices:
      - exempt-av
      - exempt-webcontent
      - exempt-activex-java-cookie
      - exempt-dlp
      - exempt-rangeblock
      - extended-log-others

  web_youtube_restrict:
    description:
      - YouTube EDU filter level.
      - choice | strict | Strict access for YouTube.
      - choice | none | Full access for YouTube.
      - choice | moderate | Moderate access for YouTube.
    required: false
    choices: ["strict", "none", "moderate"]

  youtube_channel_filter:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  youtube_channel_filter_channel_id:
    description:
      - YouTube channel ID to be filtered.
    required: false

  youtube_channel_filter_comment:
    description:
      - Comment.
    required: false


'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_web:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: "Ansible_Web_Filter_Profile"
      mode: "delete"

  - name: CREATE Profile
    fmgr_secprof_web:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: "Ansible_Web_Filter_Profile"
      comment: "Created by Ansible Module TEST"
      mode: "set"
      extended_log: "enable"
      inspection_mode: "proxy"
      log_all_url: "enable"
      options: "js"
      ovrd_perm: "bannedword-override"
      post_action: "block"
      web_content_log: "enable"
      web_extended_all_action_log: "enable"
      web_filter_activex_log: "enable"
      web_filter_applet_log: "enable"
      web_filter_command_block_log: "enable"
      web_filter_cookie_log: "enable"
      web_filter_cookie_removal_log: "enable"
      web_filter_js_log: "enable"
      web_filter_jscript_log: "enable"
      web_filter_referer_log: "enable"
      web_filter_unknown_log: "enable"
      web_filter_vbs_log: "enable"
      web_ftgd_err_log: "enable"
      web_ftgd_quota_usage: "enable"
      web_invalid_domain_log: "enable"
      web_url_log: "enable"
      wisp: "enable"
      wisp_algorithm: "auto-learning"
      youtube_channel_status: "blacklist"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager


###############
# START METHODS
###############


def fmgr_webfilter_profile_addsetdelete(fmg, paramgram):

    mode = paramgram["mode"]
    adom = paramgram["adom"]

    response = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})
    url = ""
    datagram = {}

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/webfilter/profile'.format(adom=adom)
        datagram = fmgr_del_none(fmgr_prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    elif mode == "delete":
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/webfilter/profile/{name}'.format(adom=adom, name=paramgram["name"])
        datagram = {}

    # IF MODE = SET -- USE THE 'SET' API CALL MODE
    if mode == "set":
        response = fmg.set(url, datagram)
    # IF MODE = UPDATE -- USER THE 'UPDATE' API CALL MODE
    elif mode == "update":
        response = fmg.update(url, datagram)
    # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    elif mode == "add":
        response = fmg.add(url, datagram)
    # IF MODE = DELETE  -- USE THE DELETE URL AND API CALL MODE
    elif mode == "delete":
        response = fmg.delete(url, datagram)

    return response


# ADDITIONAL COMMON FUNCTIONS
def fmgr_logout(fmg, module, msg="NULL", results=(), good_codes=(0,), logout_on_fail=True, logout_on_success=False):
    """
    THIS METHOD CONTROLS THE LOGOUT AND ERROR REPORTING AFTER AN METHOD OR FUNCTION RUNS
    """
    # VALIDATION ERROR (NO RESULTS, JUST AN EXIT)
    if msg != "NULL" and len(results) == 0:
        try:
            fmg.logout()
        except Exception:
            pass
        module.fail_json(msg=msg)

    # SUBMISSION ERROR
    if len(results) > 0:
        if msg == "NULL":
            try:
                msg = results[1]['status']['message']
            except Exception:
                msg = "No status message returned from pyFMG. Possible that this was a GET with a tuple result."

        if results[0] not in good_codes:
            if logout_on_fail:
                fmg.logout()
                module.fail_json(msg=msg, **results[1])
        else:
            if logout_on_success:
                fmg.logout()
                module.exit_json(msg="API Called worked, but logout handler has been asked to logout on success",
                                 **results[1])
    return msg


# FUNCTION/METHOD FOR CONVERTING CIDR TO A NETMASK
# DID NOT USE IP ADDRESS MODULE TO KEEP INCLUDES TO A MINIMUM
def fmgr_cidr_to_netmask(cidr):
    cidr = int(cidr)
    mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
    return(str((0xff000000 & mask) >> 24) + '.' +
           str((0x00ff0000 & mask) >> 16) + '.' +
           str((0x0000ff00 & mask) >> 8) + '.' +
           str((0x000000ff & mask)))


# utility function: removing keys wih value of None, nothing in playbook for that key
def fmgr_del_none(obj):
    if isinstance(obj, dict):
        return type(obj)((fmgr_del_none(k), fmgr_del_none(v))
                         for k, v in obj.items() if k is not None and (v is not None and not fmgr_is_empty_dict(v)))
    else:
        return obj


# utility function: remove keys that are need for the logic but the FMG API won't accept them
def fmgr_prepare_dict(obj):
    list_of_elems = ["mode", "adom", "host", "username", "password"]
    if isinstance(obj, dict):
        obj = dict((key, fmgr_prepare_dict(value)) for (key, value) in obj.items() if key not in list_of_elems)
    return obj


def fmgr_is_empty_dict(obj):
    return_val = False
    if isinstance(obj, dict):
        if len(obj) > 0:
            for k, v in obj.items():
                if isinstance(v, dict):
                    if len(v) == 0:
                        return_val = True
                    elif len(v) > 0:
                        for k1, v1 in v.items():
                            if v1 is None:
                                return_val = True
                            elif v1 is not None:
                                return_val = False
                                return return_val
                elif v is None:
                    return_val = True
                elif v is not None:
                    return_val = False
                    return return_val
        elif len(obj) == 0:
            return_val = True

    return return_val


def fmgr_split_comma_strings_into_lists(obj):
    if isinstance(obj, dict):
        if len(obj) > 0:
            for k, v in obj.items():
                if isinstance(v, str):
                    new_list = list()
                    if "," in v:
                        new_items = v.split(",")
                        for item in new_items:
                            new_list.append(item.strip())
                        obj[k] = new_list

    return obj


#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(type="str", default="root"),
        host=dict(required=True, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True, required=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True, required=True),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),

        youtube_channel_status=dict(required=False, type="str", choices=["disable", "blacklist", "whitelist"]),
        wisp_servers=dict(required=False, type="str"),
        wisp_algorithm=dict(required=False, type="str", choices=["auto-learning", "primary-secondary", "round-robin"]),
        wisp=dict(required=False, type="str", choices=["disable", "enable"]),
        web_url_log=dict(required=False, type="str", choices=["disable", "enable"]),
        web_invalid_domain_log=dict(required=False, type="str", choices=["disable", "enable"]),
        web_ftgd_quota_usage=dict(required=False, type="str", choices=["disable", "enable"]),
        web_ftgd_err_log=dict(required=False, type="str", choices=["disable", "enable"]),
        web_filter_vbs_log=dict(required=False, type="str", choices=["disable", "enable"]),
        web_filter_unknown_log=dict(required=False, type="str", choices=["disable", "enable"]),
        web_filter_referer_log=dict(required=False, type="str", choices=["disable", "enable"]),
        web_filter_jscript_log=dict(required=False, type="str", choices=["disable", "enable"]),
        web_filter_js_log=dict(required=False, type="str", choices=["disable", "enable"]),
        web_filter_cookie_removal_log=dict(required=False, type="str", choices=["disable", "enable"]),
        web_filter_cookie_log=dict(required=False, type="str", choices=["disable", "enable"]),
        web_filter_command_block_log=dict(required=False, type="str", choices=["disable", "enable"]),
        web_filter_applet_log=dict(required=False, type="str", choices=["disable", "enable"]),
        web_filter_activex_log=dict(required=False, type="str", choices=["disable", "enable"]),
        web_extended_all_action_log=dict(required=False, type="str", choices=["disable", "enable"]),
        web_content_log=dict(required=False, type="str", choices=["disable", "enable"]),
        replacemsg_group=dict(required=False, type="str"),
        post_action=dict(required=False, type="str", choices=["normal", "block"]),
        ovrd_perm=dict(required=False, type="list", choices=["bannedword-override",
                                                             "urlfilter-override",
                                                             "fortiguard-wf-override",
                                                             "contenttype-check-override"]),
        options=dict(required=False, type="list", choices=["block-invalid-url",
                                                           "jscript",
                                                           "js",
                                                           "vbs",
                                                           "unknown",
                                                           "wf-referer",
                                                           "intrinsic",
                                                           "wf-cookie",
                                                           "per-user-bwl",
                                                           "activexfilter",
                                                           "cookiefilter",
                                                           "javafilter"]),
        name=dict(required=False, type="str"),
        log_all_url=dict(required=False, type="str", choices=["disable", "enable"]),
        inspection_mode=dict(required=False, type="str", choices=["proxy", "flow-based"]),
        https_replacemsg=dict(required=False, type="str", choices=["disable", "enable"]),
        extended_log=dict(required=False, type="str", choices=["disable", "enable"]),
        comment=dict(required=False, type="str"),
        ftgd_wf=dict(required=False, type="list"),
        ftgd_wf_exempt_quota=dict(required=False, type="str"),
        ftgd_wf_max_quota_timeout=dict(required=False, type="int"),
        ftgd_wf_options=dict(required=False, type="str", choices=["error-allow", "rate-server-ip",
                                                                  "connect-request-bypass", "ftgd-disable"]),
        ftgd_wf_ovrd=dict(required=False, type="str"),
        ftgd_wf_rate_crl_urls=dict(required=False, type="str", choices=["disable", "enable"]),
        ftgd_wf_rate_css_urls=dict(required=False, type="str", choices=["disable", "enable"]),
        ftgd_wf_rate_image_urls=dict(required=False, type="str", choices=["disable", "enable"]),
        ftgd_wf_rate_javascript_urls=dict(required=False, type="str", choices=["disable", "enable"]),

        ftgd_wf_filters_action=dict(required=False, type="str", choices=["block", "monitor",
                                                                         "warning", "authenticate"]),
        ftgd_wf_filters_auth_usr_grp=dict(required=False, type="str"),
        ftgd_wf_filters_category=dict(required=False, type="str"),
        ftgd_wf_filters_log=dict(required=False, type="str", choices=["disable", "enable"]),
        ftgd_wf_filters_override_replacemsg=dict(required=False, type="str"),
        ftgd_wf_filters_warn_duration=dict(required=False, type="str"),
        ftgd_wf_filters_warning_duration_type=dict(required=False, type="str", choices=["session", "timeout"]),
        ftgd_wf_filters_warning_prompt=dict(required=False, type="str", choices=["per-domain", "per-category"]),

        ftgd_wf_quota_category=dict(required=False, type="str"),
        ftgd_wf_quota_duration=dict(required=False, type="str"),
        ftgd_wf_quota_override_replacemsg=dict(required=False, type="str"),
        ftgd_wf_quota_type=dict(required=False, type="str", choices=["time", "traffic"]),
        ftgd_wf_quota_unit=dict(required=False, type="str", choices=["B", "KB", "MB", "GB"]),
        ftgd_wf_quota_value=dict(required=False, type="int"),
        override=dict(required=False, type="list"),
        override_ovrd_cookie=dict(required=False, type="str", choices=["deny", "allow"]),
        override_ovrd_dur=dict(required=False, type="str"),
        override_ovrd_dur_mode=dict(required=False, type="str", choices=["constant", "ask"]),
        override_ovrd_scope=dict(required=False, type="str", choices=["user", "user-group", "ip", "ask", "browser"]),
        override_ovrd_user_group=dict(required=False, type="str"),
        override_profile=dict(required=False, type="str"),
        override_profile_attribute=dict(required=False, type="list", choices=["User-Name",
                                                                              "NAS-IP-Address",
                                                                              "Framed-IP-Address",
                                                                              "Framed-IP-Netmask",
                                                                              "Filter-Id",
                                                                              "Login-IP-Host",
                                                                              "Reply-Message",
                                                                              "Callback-Number",
                                                                              "Callback-Id",
                                                                              "Framed-Route",
                                                                              "Framed-IPX-Network",
                                                                              "Class",
                                                                              "Called-Station-Id",
                                                                              "Calling-Station-Id",
                                                                              "NAS-Identifier",
                                                                              "Proxy-State",
                                                                              "Login-LAT-Service",
                                                                              "Login-LAT-Node",
                                                                              "Login-LAT-Group",
                                                                              "Framed-AppleTalk-Zone",
                                                                              "Acct-Session-Id",
                                                                              "Acct-Multi-Session-Id"]),
        override_profile_type=dict(required=False, type="str", choices=["list", "radius"]),
        url_extraction=dict(required=False, type="list"),
        url_extraction_redirect_header=dict(required=False, type="str"),
        url_extraction_redirect_no_content=dict(required=False, type="str", choices=["disable", "enable"]),
        url_extraction_redirect_url=dict(required=False, type="str"),
        url_extraction_server_fqdn=dict(required=False, type="str"),
        url_extraction_status=dict(required=False, type="str", choices=["disable", "enable"]),
        web=dict(required=False, type="list"),
        web_blacklist=dict(required=False, type="str", choices=["disable", "enable"]),
        web_bword_table=dict(required=False, type="str"),
        web_bword_threshold=dict(required=False, type="int"),
        web_content_header_list=dict(required=False, type="str"),
        web_keyword_match=dict(required=False, type="str"),
        web_log_search=dict(required=False, type="str", choices=["disable", "enable"]),
        web_safe_search=dict(required=False, type="str", choices=["url", "header"]),
        web_urlfilter_table=dict(required=False, type="str"),
        web_whitelist=dict(required=False, type="list", choices=["exempt-av",
                                                                 "exempt-webcontent",
                                                                 "exempt-activex-java-cookie",
                                                                 "exempt-dlp",
                                                                 "exempt-rangeblock",
                                                                 "extended-log-others"]),
        web_youtube_restrict=dict(required=False, type="str", choices=["strict", "none", "moderate"]),
        youtube_channel_filter=dict(required=False, type="list"),
        youtube_channel_filter_channel_id=dict(required=False, type="str"),
        youtube_channel_filter_comment=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=False)

    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "youtube-channel-status": module.params["youtube_channel_status"],
        "wisp-servers": module.params["wisp_servers"],
        "wisp-algorithm": module.params["wisp_algorithm"],
        "wisp": module.params["wisp"],
        "web-url-log": module.params["web_url_log"],
        "web-invalid-domain-log": module.params["web_invalid_domain_log"],
        "web-ftgd-quota-usage": module.params["web_ftgd_quota_usage"],
        "web-ftgd-err-log": module.params["web_ftgd_err_log"],
        "web-filter-vbs-log": module.params["web_filter_vbs_log"],
        "web-filter-unknown-log": module.params["web_filter_unknown_log"],
        "web-filter-referer-log": module.params["web_filter_referer_log"],
        "web-filter-jscript-log": module.params["web_filter_jscript_log"],
        "web-filter-js-log": module.params["web_filter_js_log"],
        "web-filter-cookie-removal-log": module.params["web_filter_cookie_removal_log"],
        "web-filter-cookie-log": module.params["web_filter_cookie_log"],
        "web-filter-command-block-log": module.params["web_filter_command_block_log"],
        "web-filter-applet-log": module.params["web_filter_applet_log"],
        "web-filter-activex-log": module.params["web_filter_activex_log"],
        "web-extended-all-action-log": module.params["web_extended_all_action_log"],
        "web-content-log": module.params["web_content_log"],
        "replacemsg-group": module.params["replacemsg_group"],
        "post-action": module.params["post_action"],
        "ovrd-perm": module.params["ovrd_perm"],
        "options": module.params["options"],
        "name": module.params["name"],
        "log-all-url": module.params["log_all_url"],
        "inspection-mode": module.params["inspection_mode"],
        "https-replacemsg": module.params["https_replacemsg"],
        "extended-log": module.params["extended_log"],
        "comment": module.params["comment"],
        "ftgd-wf": {
            "exempt-quota": module.params["ftgd_wf_exempt_quota"],
            "max-quota-timeout": module.params["ftgd_wf_max_quota_timeout"],
            "options": module.params["ftgd_wf_options"],
            "ovrd": module.params["ftgd_wf_ovrd"],
            "rate-crl-urls": module.params["ftgd_wf_rate_crl_urls"],
            "rate-css-urls": module.params["ftgd_wf_rate_css_urls"],
            "rate-image-urls": module.params["ftgd_wf_rate_image_urls"],
            "rate-javascript-urls": module.params["ftgd_wf_rate_javascript_urls"],
            "filters": {
                "action": module.params["ftgd_wf_filters_action"],
                "auth-usr-grp": module.params["ftgd_wf_filters_auth_usr_grp"],
                "category": module.params["ftgd_wf_filters_category"],
                "log": module.params["ftgd_wf_filters_log"],
                "override-replacemsg": module.params["ftgd_wf_filters_override_replacemsg"],
                "warn-duration": module.params["ftgd_wf_filters_warn_duration"],
                "warning-duration-type": module.params["ftgd_wf_filters_warning_duration_type"],
                "warning-prompt": module.params["ftgd_wf_filters_warning_prompt"],
            },
            "quota": {
                "category": module.params["ftgd_wf_quota_category"],
                "duration": module.params["ftgd_wf_quota_duration"],
                "override-replacemsg": module.params["ftgd_wf_quota_override_replacemsg"],
                "type": module.params["ftgd_wf_quota_type"],
                "unit": module.params["ftgd_wf_quota_unit"],
                "value": module.params["ftgd_wf_quota_value"],
            },
        },
        "override": {
            "ovrd-cookie": module.params["override_ovrd_cookie"],
            "ovrd-dur": module.params["override_ovrd_dur"],
            "ovrd-dur-mode": module.params["override_ovrd_dur_mode"],
            "ovrd-scope": module.params["override_ovrd_scope"],
            "ovrd-user-group": module.params["override_ovrd_user_group"],
            "profile": module.params["override_profile"],
            "profile-attribute": module.params["override_profile_attribute"],
            "profile-type": module.params["override_profile_type"],
        },
        "url-extraction": {
            "redirect-header": module.params["url_extraction_redirect_header"],
            "redirect-no-content": module.params["url_extraction_redirect_no_content"],
            "redirect-url": module.params["url_extraction_redirect_url"],
            "server-fqdn": module.params["url_extraction_server_fqdn"],
            "status": module.params["url_extraction_status"],
        },
        "web": {
            "blacklist": module.params["web_blacklist"],
            "bword-table": module.params["web_bword_table"],
            "bword-threshold": module.params["web_bword_threshold"],
            "content-header-list": module.params["web_content_header_list"],
            "keyword-match": module.params["web_keyword_match"],
            "log-search": module.params["web_log_search"],
            "safe-search": module.params["web_safe_search"],
            "urlfilter-table": module.params["web_urlfilter_table"],
            "whitelist": module.params["web_whitelist"],
            "youtube-restrict": module.params["web_youtube_restrict"],
        },
        "youtube-channel-filter": {
            "channel-id": module.params["youtube_channel_filter_channel_id"],
            "comment": module.params["youtube_channel_filter_comment"],
        }
    }

    list_overrides = ['ftgd-wf', 'override', 'url-extraction', 'web', 'youtube-channel-filter']
    for list_variable in list_overrides:
        override_data = list()
        try:
            override_data = module.params[list_variable]
        except Exception:
            pass
        try:
            if override_data:
                del paramgram[list_variable]
                paramgram[list_variable] = override_data
        except Exception:
            pass

    # CHECK IF THE HOST/USERNAME/PW EXISTS, AND IF IT DOES, LOGIN.
    host = module.params["host"]
    password = module.params["password"]
    username = module.params["username"]
    if host is None or username is None or password is None:
        module.fail_json(msg="Host and username and password are required")

    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])

    response = fmg.login()
    if response[1]['status']['code'] != 0:
        module.fail_json(msg="Connection to FortiManager Failed")

    results = fmgr_webfilter_profile_addsetdelete(fmg, paramgram)
    if results[0] != 0:
        fmgr_logout(fmg, module, results=results, good_codes=[0])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(msg="No results were returned from the API call.")


if __name__ == "__main__":
    main()
