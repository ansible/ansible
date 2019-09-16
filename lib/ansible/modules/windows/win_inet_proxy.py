#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_inet_proxy
version_added: '2.8'
short_description: Manages proxy settings for WinINet and Internet Explorer
description:
- Used to set or remove proxy settings for Windows INet which includes Internet
  Explorer.
- WinINet is a framework used by interactive applications to submit web
  requests through.
- The proxy settings can also be used by other applications like Firefox,
  Chrome, and others but there is no definitive list.
options:
  auto_detect:
    description:
    - Whether to configure WinINet to automatically detect proxy settings
      through Web Proxy Auto-Detection C(WPAD).
    - This corresponds to the checkbox I(Automatically detect settings) in the
      connection settings window.
    default: yes
    type: bool
  auto_config_url:
    description:
    - The URL of a proxy configuration script.
    - Proxy configuration scripts are typically JavaScript files with the
      C(.pac) extension that implement the C(FindProxyForURL(url, host)
      function.
    - Omit, set to null or an empty string to remove the auto config URL.
    - This corresponds to the checkbox I(Use automatic configuration script) in
      the connection settings window.
    type: str
  bypass:
    description:
    - A list of hosts that will bypass the set proxy when being accessed.
    - Use C(<local>) to match hostnames that are not fully qualified domain
      names. This is useful when needing to connect to intranet sites using
      just the hostname. If defined, this should be the last entry in the
      bypass list.
    - Use C(<-loopback>) to stop automatically bypassing the proxy when
      connecting through any loopback address like C(127.0.0.1), C(localhost),
      or the local hostname.
    - Omit, set to null or an empty string/list to remove the bypass list.
    - If this is set then I(proxy) must also be set.
    type: list
  connection:
    description:
    - The name of the IE connection to set the proxy settings for.
    - These are the connections under the I(Dial-up and Virtual Private Network)
      header in the IE settings.
    - When omitted, the default LAN connection is used.
    type: str
  proxy:
    description:
    - A string or dict that specifies the proxy to be set.
    - If setting a string, should be in the form C(hostname), C(hostname:port),
      or C(protocol=hostname:port).
    - If the port is undefined, the default port for the protocol in use is
      used.
    - If setting a dict, the keys should be the protocol and the values should
      be the hostname and/or port for that protocol.
    - Valid protocols are C(http), C(https), C(ftp), and C(socks).
    - Omit, set to null or an empty string to remove the proxy settings.
notes:
- This is not the same as the proxy settings set in WinHTTP through the
  C(netsh) command. Use the M(win_http_proxy) module to manage that instead.
- These settings are by default set per user and not system wide. A registry
  property must be set independently from this module if you wish to apply the
  proxy for all users. See examples for more detail.
- If per user proxy settings are desired, use I(become) to become any local
  user on the host. No password is needed to be set for this to work.
- If the proxy requires authentication, set the credentials using the
  M(win_credential) module. This requires I(become) to be used so the
  credential store can be accessed.
seealso:
- module: win_http_proxy
- module: win_credential
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
# This should be set before running the win_inet_proxy module
- name: Configure IE proxy settings to apply to all users
  win_regedit:
    path: HKLM:\SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\Internet Settings
    name: ProxySettingsPerUser
    data: 0
    type: dword
    state: present

# This should be set before running the win_inet_proxy module
- name: Configure IE proxy settings to apply per user
  win_regedit:
    path: HKLM:\SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\Internet Settings
    name: ProxySettingsPerUser
    data: 1
    type: dword
    state: present

- name: Configure IE proxy to use auto detected settings without an explicit proxy
  win_inet_proxy:
    auto_detect: yes

- name: Configure IE proxy to use auto detected settings with a configuration script
  win_inet_proxy:
    auto_detect: yes
    auto_config_url: http://proxy.ansible.com/proxy.pac

- name: Configure IE to use explicit proxy host
  win_inet_proxy:
    auto_detect: yes
    proxy: ansible.proxy

- name: Configure IE to use explicit proxy host with port and without auto detection
  win_inet_proxy:
    auto_detect: no
    proxy: ansible.proxy:8080

- name: Configure IE to use a specific proxy per protocol
  win_inet_proxy:
    proxy:
      http: ansible.proxy:8080
      https: ansible.proxy:8443

- name: Configure IE to use a specific proxy per protocol using a string
  win_inet_proxy:
    proxy: http=ansible.proxy:8080;https=ansible.proxy:8443

- name: Set a proxy with a bypass list
  win_inet_proxy:
    proxy: ansible.proxy
    bypass:
    - server1
    - server2
    - <-loopback>
    - <local>

- name: Remove any explicit proxies that are set
  win_inet_proxy:
    proxy: ''
    bypass: ''

# This should be done after setting the IE proxy with win_inet_proxy
- name: Import IE proxy configuration to WinHTTP
  win_http_proxy:
    source: ie

# Explicit credentials can only be set per user and require become to work
- name: Set credential to use for proxy auth
  win_credential:
    name: ansible.proxy  # The name should be the FQDN of the proxy host
    type: generic_password
    username: proxyuser
    secret: proxypass
    state: present
  become: yes
  become_user: '{{ ansible_user }}'
  become_method: runas
'''

RETURN = r'''
#
'''
