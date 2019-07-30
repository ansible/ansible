#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2019 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_system_global
short_description: Configure global attributes in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify system feature and global category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.2
version_added: "2.8"
author:
    - Miguel Angel Munoz (@mamunozgonzalez)
    - Nicolas Thomas (@thomnico)
notes:
    - Requires fortiosapi library developed by Fortinet
    - Run as a local_action in your playbook
requirements:
    - fortiosapi>=0.9.8
options:
    host:
       description:
            - FortiOS or FortiGate ip address.
       required: true
    username:
        description:
            - FortiOS or FortiGate username.
        required: true
    password:
        description:
            - FortiOS or FortiGate password.
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS
              protocol
        type: bool
        default: true
    system_global:
        description:
            - Configure global attributes.
        default: null
        suboptions:
            admin-concurrent:
                description:
                    - Enable/disable concurrent administrator logins. (Use policy-auth-concurrent for firewall authenticated users.)
                choices:
                    - enable
                    - disable
            admin-console-timeout:
                description:
                    - Console login timeout that overrides the admintimeout value. (15 - 300 seconds) (15 seconds to 5 minutes). 0 the default, disables this
                       timeout.
            admin-https-pki-required:
                description:
                    - Enable/disable admin login method. Enable to force administrators to provide a valid certificate to log in if PKI is enabled. Disable to
                       allow administrators to log in with a certificate or password.
                choices:
                    - enable
                    - disable
            admin-https-ssl-versions:
                description:
                    - Allowed TLS versions for web administration.
                choices:
                    - tlsv1-0
                    - tlsv1-1
                    - tlsv1-2
            admin-lockout-duration:
                description:
                    - Amount of time in seconds that an administrator account is locked out after reaching the admin-lockout-threshold for repeated failed
                       login attempts.
            admin-lockout-threshold:
                description:
                    - Number of failed login attempts before an administrator account is locked out for the admin-lockout-duration.
            admin-login-max:
                description:
                    - Maximum number of administrators who can be logged in at the same time (1 - 100, default = 100)
            admin-maintainer:
                description:
                    - Enable/disable maintainer administrator login. When enabled, the maintainer account can be used to log in from the console after a hard
                       reboot. The password is "bcpb" followed by the FortiGate unit serial number. You have limited time to complete this login.
                choices:
                    - enable
                    - disable
            admin-port:
                description:
                    - Administrative access port for HTTP. (1 - 65535, default = 80).
            admin-restrict-local:
                description:
                    - Enable/disable local admin authentication restriction when remote authenticator is up and running. (default = disable)
                choices:
                    - enable
                    - disable
            admin-scp:
                description:
                    - Enable/disable using SCP to download the system configuration. You can use SCP as an alternative method for backing up the configuration.
                choices:
                    - enable
                    - disable
            admin-server-cert:
                description:
                    - Server certificate that the FortiGate uses for HTTPS administrative connections. Source certificate.local.name.
            admin-sport:
                description:
                    - Administrative access port for HTTPS. (1 - 65535, default = 443).
            admin-ssh-grace-time:
                description:
                    - Maximum time in seconds permitted between making an SSH connection to the FortiGate unit and authenticating (10 - 3600 sec (1 hour),
                       default 120).
            admin-ssh-password:
                description:
                    - Enable/disable password authentication for SSH admin access.
                choices:
                    - enable
                    - disable
            admin-ssh-port:
                description:
                    - Administrative access port for SSH. (1 - 65535, default = 22).
            admin-ssh-v1:
                description:
                    - Enable/disable SSH v1 compatibility.
                choices:
                    - enable
                    - disable
            admin-telnet-port:
                description:
                    - Administrative access port for TELNET. (1 - 65535, default = 23).
            admintimeout:
                description:
                    - Number of minutes before an idle administrator session times out (5 - 480 minutes (8 hours), default = 5). A shorter idle timeout is
                       more secure.
            alias:
                description:
                    - Alias for your FortiGate unit.
            allow-traffic-redirect:
                description:
                    - Disable to allow traffic to be routed back on a different interface.
                choices:
                    - enable
                    - disable
            anti-replay:
                description:
                    - Level of checking for packet replay and TCP sequence checking.
                choices:
                    - disable
                    - loose
                    - strict
            arp-max-entry:
                description:
                    - Maximum number of dynamically learned MAC addresses that can be added to the ARP table (131072 - 2147483647, default = 131072).
            asymroute:
                description:
                    - Enable/disable asymmetric route.
                choices:
                    - enable
                    - disable
            auth-cert:
                description:
                    - Server certificate that the FortiGate uses for HTTPS firewall authentication connections. Source certificate.local.name.
            auth-http-port:
                description:
                    - User authentication HTTP port. (1 - 65535, default = 80).
            auth-https-port:
                description:
                    - User authentication HTTPS port. (1 - 65535, default = 443).
            auth-keepalive:
                description:
                    - Enable to prevent user authentication sessions from timing out when idle.
                choices:
                    - enable
                    - disable
            auth-session-limit:
                description:
                    - Action to take when the number of allowed user authenticated sessions is reached.
                choices:
                    - block-new
                    - logout-inactive
            auto-auth-extension-device:
                description:
                    - Enable/disable automatic authorization of dedicated Fortinet extension devices.
                choices:
                    - enable
                    - disable
            av-affinity:
                description:
                    - Affinity setting for AV scanning (hexadecimal value up to 256 bits in the format of xxxxxxxxxxxxxxxx).
            av-failopen:
                description:
                    - Set the action to take if the FortiGate is running low on memory or the proxy connection limit has been reached.
                choices:
                    - pass
                    - off
                    - one-shot
            av-failopen-session:
                description:
                    - When enabled and a proxy for a protocol runs out of room in its session table, that protocol goes into failopen mode and enacts the
                       action specified by av-failopen.
                choices:
                    - enable
                    - disable
            batch-cmdb:
                description:
                    - Enable/disable batch mode, allowing you to enter a series of CLI commands that will execute as a group once they are loaded.
                choices:
                    - enable
                    - disable
            block-session-timer:
                description:
                    - Duration in seconds for blocked sessions (1 - 300 sec  (5 minutes), default = 30).
            br-fdb-max-entry:
                description:
                    - Maximum number of bridge forwarding database (FDB) entries.
            cert-chain-max:
                description:
                    - Maximum number of certificates that can be traversed in a certificate chain.
            cfg-revert-timeout:
                description:
                    - Time-out for reverting to the last saved configuration.
            cfg-save:
                description:
                    - Configuration file save mode for CLI changes.
                choices:
                    - automatic
                    - manual
                    - revert
            check-protocol-header:
                description:
                    - Level of checking performed on protocol headers. Strict checking is more thorough but may affect performance. Loose checking is ok in
                       most cases.
                choices:
                    - loose
                    - strict
            check-reset-range:
                description:
                    - Configure ICMP error message verification. You can either apply strict RST range checking or disable it.
                choices:
                    - strict
                    - disable
            cli-audit-log:
                description:
                    - Enable/disable CLI audit log.
                choices:
                    - enable
                    - disable
            clt-cert-req:
                description:
                    - Enable/disable requiring administrators to have a client certificate to log into the GUI using HTTPS.
                choices:
                    - enable
                    - disable
            compliance-check:
                description:
                    - Enable/disable global PCI DSS compliance check.
                choices:
                    - enable
                    - disable
            compliance-check-time:
                description:
                    - Time of day to run scheduled PCI DSS compliance checks.
            cpu-use-threshold:
                description:
                    - Threshold at which CPU usage is reported. (% of total CPU, default = 90).
            csr-ca-attribute:
                description:
                    - Enable/disable the CA attribute in certificates. Some CA servers reject CSRs that have the CA attribute.
                choices:
                    - enable
                    - disable
            daily-restart:
                description:
                    - Enable/disable daily restart of FortiGate unit. Use the restart-time option to set the time of day for the restart.
                choices:
                    - enable
                    - disable
            device-identification-active-scan-delay:
                description:
                    - Number of seconds to passively scan a device before performing an active scan. (20 - 3600 sec, (20 sec to 1 hour), default = 90).
            device-idle-timeout:
                description:
                    - Time in seconds that a device must be idle to automatically log the device user out. (30 - 31536000 sec (30 sec to 1 year), default =
                       300).
            dh-params:
                description:
                    - Number of bits to use in the Diffie-Hellman exchange for HTTPS/SSH protocols.
                choices:
                    - 1024
                    - 1536
                    - 2048
                    - 3072
                    - 4096
                    - 6144
                    - 8192
            dst:
                description:
                    - Enable/disable daylight saving time.
                choices:
                    - enable
                    - disable
            endpoint-control-fds-access:
                description:
                    - Enable/disable access to the FortiGuard network for non-compliant endpoints.
                choices:
                    - enable
                    - disable
            endpoint-control-portal-port:
                description:
                    - Endpoint control portal port (1 - 65535).
            failtime:
                description:
                    - Fail-time for server lost.
            fds-statistics:
                description:
                    - Enable/disable sending IPS, Application Control, and AntiVirus data to FortiGuard. This data is used to improve FortiGuard services and
                       is not shared with external parties and is protected by Fortinet's privacy policy.
                choices:
                    - enable
                    - disable
            fds-statistics-period:
                description:
                    - FortiGuard statistics collection period in minutes. (1 - 1440 min (1 min to 24 hours), default = 60).
            fgd-alert-subscription:
                description:
                    - Type of alert to retrieve from FortiGuard.
                choices:
                    - advisory
                    - latest-threat
                    - latest-virus
                    - latest-attack
                    - new-antivirus-db
                    - new-attack-db
            fortiextender:
                description:
                    - Enable/disable FortiExtender.
                choices:
                    - enable
                    - disable
            fortiextender-data-port:
                description:
                    - FortiExtender data port (1024 - 49150, default = 25246).
            fortiextender-vlan-mode:
                description:
                    - Enable/disable FortiExtender VLAN mode.
                choices:
                    - enable
                    - disable
            fortiservice-port:
                description:
                    - FortiService port (1 - 65535, default = 8013). Used by FortiClient endpoint compliance. Older versions of FortiClient used a different
                       port.
            gui-certificates:
                description:
                    - Enable/disable the System > Certificate GUI page, allowing you to add and configure certificates from the GUI.
                choices:
                    - enable
                    - disable
            gui-custom-language:
                description:
                    - Enable/disable custom languages in GUI.
                choices:
                    - enable
                    - disable
            gui-date-format:
                description:
                    - Default date format used throughout GUI.
                choices:
                    - yyyy/MM/dd
                    - dd/MM/yyyy
                    - MM/dd/yyyy
                    - yyyy-MM-dd
                    - dd-MM-yyyy
                    - MM-dd-yyyy
            gui-device-latitude:
                description:
                    - Add the latitude of the location of this FortiGate to position it on the Threat Map.
            gui-device-longitude:
                description:
                    - Add the longitude of the location of this FortiGate to position it on the Threat Map.
            gui-display-hostname:
                description:
                    - Enable/disable displaying the FortiGate's hostname on the GUI login page.
                choices:
                    - enable
                    - disable
            gui-ipv6:
                description:
                    - Enable/disable IPv6 settings on the GUI.
                choices:
                    - enable
                    - disable
            gui-lines-per-page:
                description:
                    - Number of lines to display per page for web administration.
            gui-theme:
                description:
                    - Color scheme for the administration GUI.
                choices:
                    - green
                    - red
                    - blue
                    - melongene
                    - mariner
            gui-wireless-opensecurity:
                description:
                    - Enable/disable wireless open security option on the GUI.
                choices:
                    - enable
                    - disable
            honor-df:
                description:
                    - Enable/disable honoring of Don't-Fragment (DF) flag.
                choices:
                    - enable
                    - disable
            hostname:
                description:
                    - FortiGate unit's hostname. Most models will truncate names longer than 24 characters. Some models support hostnames up to 35 characters.
            igmp-state-limit:
                description:
                    - Maximum number of IGMP memberships (96 - 64000, default = 3200).
            interval:
                description:
                    - Dead gateway detection interval.
            ip-src-port-range:
                description:
                    - IP source port range used for traffic originating from the FortiGate unit.
            ips-affinity:
                description:
                    - Affinity setting for IPS (hexadecimal value up to 256 bits in the format of xxxxxxxxxxxxxxxx; allowed CPUs must be less than total
                       number of IPS engine daemons).
            ipsec-asic-offload:
                description:
                    - Enable/disable ASIC offloading (hardware acceleration) for IPsec VPN traffic. Hardware acceleration can offload IPsec VPN sessions and
                       accelerate encryption and decryption.
                choices:
                    - enable
                    - disable
            ipsec-hmac-offload:
                description:
                    - Enable/disable offloading (hardware acceleration) of HMAC processing for IPsec VPN.
                choices:
                    - enable
                    - disable
            ipsec-soft-dec-async:
                description:
                    - Enable/disable software decryption asynchronization (using multiple CPUs to do decryption) for IPsec VPN traffic.
                choices:
                    - enable
                    - disable
            ipv6-accept-dad:
                description:
                    - Enable/disable acceptance of IPv6 Duplicate Address Detection (DAD).
            ipv6-allow-anycast-probe:
                description:
                    - Enable/disable IPv6 address probe through Anycast.
                choices:
                    - enable
                    - disable
            language:
                description:
                    - GUI display language.
                choices:
                    - english
                    - french
                    - spanish
                    - portuguese
                    - japanese
                    - trach
                    - simch
                    - korean
            ldapconntimeout:
                description:
                    - Global timeout for connections with remote LDAP servers in milliseconds (0 - 4294967295, default 500).
            lldp-transmission:
                description:
                    - Enable/disable Link Layer Discovery Protocol (LLDP) transmission.
                choices:
                    - enable
                    - disable
            log-ssl-connection:
                description:
                    - Enable/disable logging of SSL connection events.
                choices:
                    - enable
                    - disable
            log-uuid:
                description:
                    - Whether UUIDs are added to traffic logs. You can disable UUIDs, add firewall policy UUIDs to traffic logs, or add all UUIDs to traffic
                       logs.
                choices:
                    - disable
                    - policy-only
                    - extended
            login-timestamp:
                description:
                    - Enable/disable login time recording.
                choices:
                    - enable
                    - disable
            long-vdom-name:
                description:
                    - Enable/disable long VDOM name support.
                choices:
                    - enable
                    - disable
            management-vdom:
                description:
                    - Management virtual domain name. Source system.vdom.name.
            max-dlpstat-memory:
                description:
                    - Maximum DLP stat memory (0 - 4294967295).
            max-route-cache-size:
                description:
                    - Maximum number of IP route cache entries (0 - 2147483647).
            mc-ttl-notchange:
                description:
                    - Enable/disable no modification of multicast TTL.
                choices:
                    - enable
                    - disable
            memory-use-threshold-extreme:
                description:
                    - Threshold at which memory usage is considered extreme (new sessions are dropped) (% of total RAM, default = 95).
            memory-use-threshold-green:
                description:
                    - Threshold at which memory usage forces the FortiGate to exit conserve mode (% of total RAM, default = 82).
            memory-use-threshold-red:
                description:
                    - Threshold at which memory usage forces the FortiGate to enter conserve mode (% of total RAM, default = 88).
            miglog-affinity:
                description:
                    - Affinity setting for logging (64-bit hexadecimal value in the format of xxxxxxxxxxxxxxxx).
            miglogd-children:
                description:
                    - Number of logging (miglogd) processes to be allowed to run. Higher number can reduce performance; lower number can slow log processing
                       time. No logs will be dropped or lost if the number is changed.
            multi-factor-authentication:
                description:
                    - Enforce all login methods to require an additional authentication factor (default = optional).
                choices:
                    - optional
                    - mandatory
            multicast-forward:
                description:
                    - Enable/disable multicast forwarding.
                choices:
                    - enable
                    - disable
            ndp-max-entry:
                description:
                    - Maximum number of NDP table entries (set to 65,536 or higher; if set to 0, kernel holds 65,536 entries).
            per-user-bwl:
                description:
                    - Enable/disable per-user black/white list filter.
                choices:
                    - enable
                    - disable
            policy-auth-concurrent:
                description:
                    - Number of concurrent firewall use logins from the same user (1 - 100, default = 0 means no limit).
            post-login-banner:
                description:
                    - Enable/disable displaying the administrator access disclaimer message after an administrator successfully logs in.
                choices:
                    - disable
                    - enable
            pre-login-banner:
                description:
                    - Enable/disable displaying the administrator access disclaimer message on the login page before an administrator logs in.
                choices:
                    - enable
                    - disable
            private-data-encryption:
                description:
                    - Enable/disable private data encryption using an AES 128-bit key.
                choices:
                    - disable
                    - enable
            proxy-auth-lifetime:
                description:
                    - Enable/disable authenticated users lifetime control.  This is a cap on the total time a proxy user can be authenticated for after which
                       re-authentication will take place.
                choices:
                    - enable
                    - disable
            proxy-auth-lifetime-timeout:
                description:
                    - Lifetime timeout in minutes for authenticated users (5  - 65535 min, default=480 (8 hours)).
            proxy-auth-timeout:
                description:
                    - Authentication timeout in minutes for authenticated users (1 - 3600 sec, default = 300).
            proxy-cipher-hardware-acceleration:
                description:
                    - Enable/disable using content processor (CP8 or CP9) hardware acceleration to encrypt and decrypt IPsec and SSL traffic.
                choices:
                    - disable
                    - enable
            proxy-kxp-hardware-acceleration:
                description:
                    - Enable/disable using the content processor to accelerate KXP traffic.
                choices:
                    - disable
                    - enable
            proxy-re-authentication-mode:
                description:
                    - Control if users must re-authenticate after a session is closed, traffic has been idle, or from the point at which the user was first
                       created.
                choices:
                    - session
                    - traffic
                    - absolute
            proxy-worker-count:
                description:
                    - Proxy worker count.
            radius-port:
                description:
                    - RADIUS service port number.
            reboot-upon-config-restore:
                description:
                    - Enable/disable reboot of system upon restoring configuration.
                choices:
                    - enable
                    - disable
            refresh:
                description:
                    - Statistics refresh interval in GUI.
            remoteauthtimeout:
                description:
                    - Number of seconds that the FortiGate waits for responses from remote RADIUS, LDAP, or TACACS+ authentication servers. (0-300 sec,
                       default = 5, 0 means no timeout).
            reset-sessionless-tcp:
                description:
                    - Action to perform if the FortiGate receives a TCP packet but cannot find a corresponding session in its session table. NAT/Route mode
                       only.
                choices:
                    - enable
                    - disable
            restart-time:
                description:
                    - "Daily restart time (hh:mm)."
            revision-backup-on-logout:
                description:
                    - Enable/disable back-up of the latest configuration revision when an administrator logs out of the CLI or GUI.
                choices:
                    - enable
                    - disable
            revision-image-auto-backup:
                description:
                    - Enable/disable back-up of the latest configuration revision after the firmware is upgraded.
                choices:
                    - enable
                    - disable
            scanunit-count:
                description:
                    - Number of scanunits. The range and the default depend on the number of CPUs. Only available on FortiGate units with multiple CPUs.
            security-rating-result-submission:
                description:
                    - Enable/disable the submission of Security Rating results to FortiGuard.
                choices:
                    - enable
                    - disable
            security-rating-run-on-schedule:
                description:
                    - Enable/disable scheduled runs of Security Rating.
                choices:
                    - enable
                    - disable
            send-pmtu-icmp:
                description:
                    - Enable/disable sending of path maximum transmission unit (PMTU) - ICMP destination unreachable packet and to support PMTUD protocol on
                       your network to reduce fragmentation of packets.
                choices:
                    - enable
                    - disable
            snat-route-change:
                description:
                    - Enable/disable the ability to change the static NAT route.
                choices:
                    - enable
                    - disable
            special-file-23-support:
                description:
                    - Enable/disable IPS detection of HIBUN format files when using Data Leak Protection.
                choices:
                    - disable
                    - enable
            ssh-cbc-cipher:
                description:
                    - Enable/disable CBC cipher for SSH access.
                choices:
                    - enable
                    - disable
            ssh-hmac-md5:
                description:
                    - Enable/disable HMAC-MD5 for SSH access.
                choices:
                    - enable
                    - disable
            ssh-kex-sha1:
                description:
                    - Enable/disable SHA1 key exchange for SSH access.
                choices:
                    - enable
                    - disable
            ssl-min-proto-version:
                description:
                    - Minimum supported protocol version for SSL/TLS connections (default = TLSv1.2).
                choices:
                    - SSLv3
                    - TLSv1
                    - TLSv1-1
                    - TLSv1-2
            ssl-static-key-ciphers:
                description:
                    - Enable/disable static key ciphers in SSL/TLS connections (e.g. AES128-SHA, AES256-SHA, AES128-SHA256, AES256-SHA256).
                choices:
                    - enable
                    - disable
            sslvpn-cipher-hardware-acceleration:
                description:
                    - Enable/disable SSL VPN hardware acceleration.
                choices:
                    - enable
                    - disable
            sslvpn-kxp-hardware-acceleration:
                description:
                    - Enable/disable SSL VPN KXP hardware acceleration.
                choices:
                    - enable
                    - disable
            sslvpn-max-worker-count:
                description:
                    - Maximum number of SSL VPN processes. Upper limit for this value is the number of CPUs and depends on the model.
            sslvpn-plugin-version-check:
                description:
                    - Enable/disable checking browser's plugin version by SSL VPN.
                choices:
                    - enable
                    - disable
            strict-dirty-session-check:
                description:
                    - Enable to check the session against the original policy when revalidating. This can prevent dropping of redirected sessions when
                       web-filtering and authentication are enabled together. If this option is enabled, the FortiGate unit deletes a session if a routing or
                          policy change causes the session to no longer match the policy that originally allowed the session.
                choices:
                    - enable
                    - disable
            strong-crypto:
                description:
                    - Enable to use strong encryption and only allow strong ciphers (AES, 3DES) and digest (SHA1) for HTTPS/SSH/TLS/SSL functions.
                choices:
                    - enable
                    - disable
            switch-controller:
                description:
                    - Enable/disable switch controller feature. Switch controller allows you to manage FortiSwitch from the FortiGate itself.
                choices:
                    - disable
                    - enable
            switch-controller-reserved-network:
                description:
                    - Enable reserved network subnet for controlled switches. This is available when the switch controller is enabled.
            sys-perf-log-interval:
                description:
                    - Time in minutes between updates of performance statistics logging. (1 - 15 min, default = 5, 0 = disabled).
            tcp-halfclose-timer:
                description:
                    - Number of seconds the FortiGate unit should wait to close a session after one peer has sent a FIN packet but the other has not responded
                       (1 - 86400 sec (1 day), default = 120).
            tcp-halfopen-timer:
                description:
                    - Number of seconds the FortiGate unit should wait to close a session after one peer has sent an open session packet but the other has not
                       responded (1 - 86400 sec (1 day), default = 10).
            tcp-option:
                description:
                    - Enable SACK, timestamp and MSS TCP options.
                choices:
                    - enable
                    - disable
            tcp-timewait-timer:
                description:
                    - Length of the TCP TIME-WAIT state in seconds.
            tftp:
                description:
                    - Enable/disable TFTP.
                choices:
                    - enable
                    - disable
            timezone:
                description:
                    - Number corresponding to your time zone from 00 to 86. Enter set timezone ? to view the list of time zones and the numbers that represent
                       them.
                choices:
                    - 01
                    - 02
                    - 03
                    - 04
                    - 05
                    - 81
                    - 06
                    - 07
                    - 08
                    - 09
                    - 10
                    - 11
                    - 12
                    - 13
                    - 74
                    - 14
                    - 77
                    - 15
                    - 87
                    - 16
                    - 17
                    - 18
                    - 19
                    - 20
                    - 75
                    - 21
                    - 22
                    - 23
                    - 24
                    - 80
                    - 79
                    - 25
                    - 26
                    - 27
                    - 28
                    - 78
                    - 29
                    - 30
                    - 31
                    - 32
                    - 33
                    - 34
                    - 35
                    - 36
                    - 37
                    - 38
                    - 83
                    - 84
                    - 40
                    - 85
                    - 41
                    - 42
                    - 43
                    - 39
                    - 44
                    - 46
                    - 47
                    - 51
                    - 48
                    - 45
                    - 49
                    - 50
                    - 52
                    - 53
                    - 54
                    - 55
                    - 56
                    - 57
                    - 58
                    - 59
                    - 60
                    - 62
                    - 63
                    - 61
                    - 64
                    - 65
                    - 66
                    - 67
                    - 68
                    - 69
                    - 70
                    - 71
                    - 72
                    - 00
                    - 82
                    - 73
                    - 86
                    - 76
            tp-mc-skip-policy:
                description:
                    - Enable/disable skip policy check and allow multicast through.
                choices:
                    - enable
                    - disable
            traffic-priority:
                description:
                    - Choose Type of Service (ToS) or Differentiated Services Code Point (DSCP) for traffic prioritization in traffic shaping.
                choices:
                    - tos
                    - dscp
            traffic-priority-level:
                description:
                    - Default system-wide level of priority for traffic prioritization.
                choices:
                    - low
                    - medium
                    - high
            two-factor-email-expiry:
                description:
                    - Email-based two-factor authentication session timeout (30 - 300 seconds (5 minutes), default = 60).
            two-factor-fac-expiry:
                description:
                    - FortiAuthenticator token authentication session timeout (10 - 3600 seconds (1 hour), default = 60).
            two-factor-ftk-expiry:
                description:
                    - FortiToken authentication session timeout (60 - 600 sec (10 minutes), default = 60).
            two-factor-ftm-expiry:
                description:
                    - FortiToken Mobile session timeout (1 - 168 hours (7 days), default = 72).
            two-factor-sms-expiry:
                description:
                    - SMS-based two-factor authentication session timeout (30 - 300 sec, default = 60).
            udp-idle-timer:
                description:
                    - UDP connection session timeout. This command can be useful in managing CPU and memory resources (1 - 86400 seconds (1 day), default =
                       60).
            user-server-cert:
                description:
                    - Certificate to use for https user authentication. Source certificate.local.name.
            vdom-admin:
                description:
                    - Enable/disable support for multiple virtual domains (VDOMs).
                choices:
                    - enable
                    - disable
            vip-arp-range:
                description:
                    - Controls the number of ARPs that the FortiGate sends for a Virtual IP (VIP) address range.
                choices:
                    - unlimited
                    - restricted
            virtual-server-count:
                description:
                    - Maximum number of virtual server processes to create. The maximum is the number of CPU cores. This is not available on single-core CPUs.
            virtual-server-hardware-acceleration:
                description:
                    - Enable/disable virtual server hardware acceleration.
                choices:
                    - disable
                    - enable
            wad-affinity:
                description:
                    - Affinity setting for wad (hexadecimal value up to 256 bits in the format of xxxxxxxxxxxxxxxx).
            wad-csvc-cs-count:
                description:
                    - Number of concurrent WAD-cache-service object-cache processes.
            wad-csvc-db-count:
                description:
                    - Number of concurrent WAD-cache-service byte-cache processes.
            wad-source-affinity:
                description:
                    - Enable/disable dispatching traffic to WAD workers based on source affinity.
                choices:
                    - disable
                    - enable
            wad-worker-count:
                description:
                    - Number of explicit proxy WAN optimization daemon (WAD) processes. By default WAN optimization, explicit proxy, and web caching is
                       handled by all of the CPU cores in a FortiGate unit.
            wifi-ca-certificate:
                description:
                    - CA certificate that verifies the WiFi certificate. Source certificate.ca.name.
            wifi-certificate:
                description:
                    - Certificate to use for WiFi authentication. Source certificate.local.name.
            wimax-4g-usb:
                description:
                    - Enable/disable comparability with WiMAX 4G USB devices.
                choices:
                    - enable
                    - disable
            wireless-controller:
                description:
                    - Enable/disable the wireless controller feature to use the FortiGate unit to manage FortiAPs.
                choices:
                    - enable
                    - disable
            wireless-controller-port:
                description:
                    - Port used for the control channel in wireless controller mode (wireless-mode is ac). The data channel port is the control channel port
                       number plus one (1024 - 49150, default = 5246).
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure global attributes.
    fortios_system_global:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_global:
        admin-concurrent: "enable"
        admin-console-timeout: "4"
        admin-https-pki-required: "enable"
        admin-https-ssl-versions: "tlsv1-0"
        admin-lockout-duration: "7"
        admin-lockout-threshold: "8"
        admin-login-max: "9"
        admin-maintainer: "enable"
        admin-port: "11"
        admin-restrict-local: "enable"
        admin-scp: "enable"
        admin-server-cert: "<your_own_value> (source certificate.local.name)"
        admin-sport: "15"
        admin-ssh-grace-time: "16"
        admin-ssh-password: "enable"
        admin-ssh-port: "18"
        admin-ssh-v1: "enable"
        admin-telnet-port: "20"
        admintimeout: "21"
        alias: "<your_own_value>"
        allow-traffic-redirect: "enable"
        anti-replay: "disable"
        arp-max-entry: "25"
        asymroute: "enable"
        auth-cert: "<your_own_value> (source certificate.local.name)"
        auth-http-port: "28"
        auth-https-port: "29"
        auth-keepalive: "enable"
        auth-session-limit: "block-new"
        auto-auth-extension-device: "enable"
        av-affinity: "<your_own_value>"
        av-failopen: "pass"
        av-failopen-session: "enable"
        batch-cmdb: "enable"
        block-session-timer: "37"
        br-fdb-max-entry: "38"
        cert-chain-max: "39"
        cfg-revert-timeout: "40"
        cfg-save: "automatic"
        check-protocol-header: "loose"
        check-reset-range: "strict"
        cli-audit-log: "enable"
        clt-cert-req: "enable"
        compliance-check: "enable"
        compliance-check-time: "<your_own_value>"
        cpu-use-threshold: "48"
        csr-ca-attribute: "enable"
        daily-restart: "enable"
        device-identification-active-scan-delay: "51"
        device-idle-timeout: "52"
        dh-params: "1024"
        dst: "enable"
        endpoint-control-fds-access: "enable"
        endpoint-control-portal-port: "56"
        failtime: "57"
        fds-statistics: "enable"
        fds-statistics-period: "59"
        fgd-alert-subscription: "advisory"
        fortiextender: "enable"
        fortiextender-data-port: "62"
        fortiextender-vlan-mode: "enable"
        fortiservice-port: "64"
        gui-certificates: "enable"
        gui-custom-language: "enable"
        gui-date-format: "yyyy/MM/dd"
        gui-device-latitude: "<your_own_value>"
        gui-device-longitude: "<your_own_value>"
        gui-display-hostname: "enable"
        gui-ipv6: "enable"
        gui-lines-per-page: "72"
        gui-theme: "green"
        gui-wireless-opensecurity: "enable"
        honor-df: "enable"
        hostname: "myhostname"
        igmp-state-limit: "77"
        interval: "78"
        ip-src-port-range: "<your_own_value>"
        ips-affinity: "<your_own_value>"
        ipsec-asic-offload: "enable"
        ipsec-hmac-offload: "enable"
        ipsec-soft-dec-async: "enable"
        ipv6-accept-dad: "84"
        ipv6-allow-anycast-probe: "enable"
        language: "english"
        ldapconntimeout: "87"
        lldp-transmission: "enable"
        log-ssl-connection: "enable"
        log-uuid: "disable"
        login-timestamp: "enable"
        long-vdom-name: "enable"
        management-vdom: "<your_own_value> (source system.vdom.name)"
        max-dlpstat-memory: "94"
        max-route-cache-size: "95"
        mc-ttl-notchange: "enable"
        memory-use-threshold-extreme: "97"
        memory-use-threshold-green: "98"
        memory-use-threshold-red: "99"
        miglog-affinity: "<your_own_value>"
        miglogd-children: "101"
        multi-factor-authentication: "optional"
        multicast-forward: "enable"
        ndp-max-entry: "104"
        per-user-bwl: "enable"
        policy-auth-concurrent: "106"
        post-login-banner: "disable"
        pre-login-banner: "enable"
        private-data-encryption: "disable"
        proxy-auth-lifetime: "enable"
        proxy-auth-lifetime-timeout: "111"
        proxy-auth-timeout: "112"
        proxy-cipher-hardware-acceleration: "disable"
        proxy-kxp-hardware-acceleration: "disable"
        proxy-re-authentication-mode: "session"
        proxy-worker-count: "116"
        radius-port: "117"
        reboot-upon-config-restore: "enable"
        refresh: "119"
        remoteauthtimeout: "120"
        reset-sessionless-tcp: "enable"
        restart-time: "<your_own_value>"
        revision-backup-on-logout: "enable"
        revision-image-auto-backup: "enable"
        scanunit-count: "125"
        security-rating-result-submission: "enable"
        security-rating-run-on-schedule: "enable"
        send-pmtu-icmp: "enable"
        snat-route-change: "enable"
        special-file-23-support: "disable"
        ssh-cbc-cipher: "enable"
        ssh-hmac-md5: "enable"
        ssh-kex-sha1: "enable"
        ssl-min-proto-version: "SSLv3"
        ssl-static-key-ciphers: "enable"
        sslvpn-cipher-hardware-acceleration: "enable"
        sslvpn-kxp-hardware-acceleration: "enable"
        sslvpn-max-worker-count: "138"
        sslvpn-plugin-version-check: "enable"
        strict-dirty-session-check: "enable"
        strong-crypto: "enable"
        switch-controller: "disable"
        switch-controller-reserved-network: "<your_own_value>"
        sys-perf-log-interval: "144"
        tcp-halfclose-timer: "145"
        tcp-halfopen-timer: "146"
        tcp-option: "enable"
        tcp-timewait-timer: "148"
        tftp: "enable"
        timezone: "01"
        tp-mc-skip-policy: "enable"
        traffic-priority: "tos"
        traffic-priority-level: "low"
        two-factor-email-expiry: "154"
        two-factor-fac-expiry: "155"
        two-factor-ftk-expiry: "156"
        two-factor-ftm-expiry: "157"
        two-factor-sms-expiry: "158"
        udp-idle-timer: "159"
        user-server-cert: "<your_own_value> (source certificate.local.name)"
        vdom-admin: "enable"
        vip-arp-range: "unlimited"
        virtual-server-count: "163"
        virtual-server-hardware-acceleration: "disable"
        wad-affinity: "<your_own_value>"
        wad-csvc-cs-count: "166"
        wad-csvc-db-count: "167"
        wad-source-affinity: "disable"
        wad-worker-count: "169"
        wifi-ca-certificate: "<your_own_value> (source certificate.ca.name)"
        wifi-certificate: "<your_own_value> (source certificate.local.name)"
        wimax-4g-usb: "enable"
        wireless-controller: "enable"
        wireless-controller-port: "174"
'''

RETURN = '''
build:
  description: Build number of the fortigate image
  returned: always
  type: str
  sample: '1547'
http_method:
  description: Last method used to provision the content into FortiGate
  returned: always
  type: str
  sample: 'PUT'
http_status:
  description: Last result given by FortiGate on last operation applied
  returned: always
  type: str
  sample: "200"
mkey:
  description: Master key (id) used in the last call to FortiGate
  returned: success
  type: str
  sample: "id"
name:
  description: Name of the table used to fulfill the request
  returned: always
  type: str
  sample: "urlfilter"
path:
  description: Path of the table used to fulfill the request
  returned: always
  type: str
  sample: "webfilter"
revision:
  description: Internal revision number
  returned: always
  type: str
  sample: "17.0.2.10658"
serial:
  description: Serial number of the unit
  returned: always
  type: str
  sample: "FGVMEVYYQT3AB5352"
status:
  description: Indication of the operation's result
  returned: always
  type: str
  sample: "success"
vdom:
  description: Virtual domain used
  returned: always
  type: str
  sample: "root"
version:
  description: Version of the FortiGate
  returned: always
  type: str
  sample: "v5.6.3"

'''

from ansible.module_utils.basic import AnsibleModule


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_system_global_data(json):
    option_list = ['admin-concurrent', 'admin-console-timeout', 'admin-https-pki-required',
                   'admin-https-ssl-versions', 'admin-lockout-duration', 'admin-lockout-threshold',
                   'admin-login-max', 'admin-maintainer', 'admin-port',
                   'admin-restrict-local', 'admin-scp', 'admin-server-cert',
                   'admin-sport', 'admin-ssh-grace-time', 'admin-ssh-password',
                   'admin-ssh-port', 'admin-ssh-v1', 'admin-telnet-port',
                   'admintimeout', 'alias', 'allow-traffic-redirect',
                   'anti-replay', 'arp-max-entry', 'asymroute',
                   'auth-cert', 'auth-http-port', 'auth-https-port',
                   'auth-keepalive', 'auth-session-limit', 'auto-auth-extension-device',
                   'av-affinity', 'av-failopen', 'av-failopen-session',
                   'batch-cmdb', 'block-session-timer', 'br-fdb-max-entry',
                   'cert-chain-max', 'cfg-revert-timeout', 'cfg-save',
                   'check-protocol-header', 'check-reset-range', 'cli-audit-log',
                   'clt-cert-req', 'compliance-check', 'compliance-check-time',
                   'cpu-use-threshold', 'csr-ca-attribute', 'daily-restart',
                   'device-identification-active-scan-delay', 'device-idle-timeout', 'dh-params',
                   'dst', 'endpoint-control-fds-access', 'endpoint-control-portal-port',
                   'failtime', 'fds-statistics', 'fds-statistics-period',
                   'fgd-alert-subscription', 'fortiextender', 'fortiextender-data-port',
                   'fortiextender-vlan-mode', 'fortiservice-port', 'gui-certificates',
                   'gui-custom-language', 'gui-date-format', 'gui-device-latitude',
                   'gui-device-longitude', 'gui-display-hostname', 'gui-ipv6',
                   'gui-lines-per-page', 'gui-theme', 'gui-wireless-opensecurity',
                   'honor-df', 'hostname', 'igmp-state-limit',
                   'interval', 'ip-src-port-range', 'ips-affinity',
                   'ipsec-asic-offload', 'ipsec-hmac-offload', 'ipsec-soft-dec-async',
                   'ipv6-accept-dad', 'ipv6-allow-anycast-probe', 'language',
                   'ldapconntimeout', 'lldp-transmission', 'log-ssl-connection',
                   'log-uuid', 'login-timestamp', 'long-vdom-name',
                   'management-vdom', 'max-dlpstat-memory', 'max-route-cache-size',
                   'mc-ttl-notchange', 'memory-use-threshold-extreme', 'memory-use-threshold-green',
                   'memory-use-threshold-red', 'miglog-affinity', 'miglogd-children',
                   'multi-factor-authentication', 'multicast-forward', 'ndp-max-entry',
                   'per-user-bwl', 'policy-auth-concurrent', 'post-login-banner',
                   'pre-login-banner', 'private-data-encryption', 'proxy-auth-lifetime',
                   'proxy-auth-lifetime-timeout', 'proxy-auth-timeout', 'proxy-cipher-hardware-acceleration',
                   'proxy-kxp-hardware-acceleration', 'proxy-re-authentication-mode', 'proxy-worker-count',
                   'radius-port', 'reboot-upon-config-restore', 'refresh',
                   'remoteauthtimeout', 'reset-sessionless-tcp', 'restart-time',
                   'revision-backup-on-logout', 'revision-image-auto-backup', 'scanunit-count',
                   'security-rating-result-submission', 'security-rating-run-on-schedule', 'send-pmtu-icmp',
                   'snat-route-change', 'special-file-23-support', 'ssh-cbc-cipher',
                   'ssh-hmac-md5', 'ssh-kex-sha1', 'ssl-min-proto-version',
                   'ssl-static-key-ciphers', 'sslvpn-cipher-hardware-acceleration', 'sslvpn-kxp-hardware-acceleration',
                   'sslvpn-max-worker-count', 'sslvpn-plugin-version-check', 'strict-dirty-session-check',
                   'strong-crypto', 'switch-controller', 'switch-controller-reserved-network',
                   'sys-perf-log-interval', 'tcp-halfclose-timer', 'tcp-halfopen-timer',
                   'tcp-option', 'tcp-timewait-timer', 'tftp',
                   'timezone', 'tp-mc-skip-policy', 'traffic-priority',
                   'traffic-priority-level', 'two-factor-email-expiry', 'two-factor-fac-expiry',
                   'two-factor-ftk-expiry', 'two-factor-ftm-expiry', 'two-factor-sms-expiry',
                   'udp-idle-timer', 'user-server-cert', 'vdom-admin',
                   'vip-arp-range', 'virtual-server-count', 'virtual-server-hardware-acceleration',
                   'wad-affinity', 'wad-csvc-cs-count', 'wad-csvc-db-count',
                   'wad-source-affinity', 'wad-worker-count', 'wifi-ca-certificate',
                   'wifi-certificate', 'wimax-4g-usb', 'wireless-controller',
                   'wireless-controller-port']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = [[u'admin-https-ssl-versions']]

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


def system_global(data, fos):
    vdom = data['vdom']
    system_global_data = data['system_global']
    system_global_data = flatten_multilists_attributes(system_global_data)
    filtered_data = filter_system_global_data(system_global_data)

    return fos.set('system',
                   'global',
                   data=filtered_data,
                   vdom=vdom)


def fortios_system(data, fos):
    login(data, fos)

    if data['system_global']:
        resp = system_global(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "system_global": {
            "required": False, "type": "dict",
            "options": {
                "admin-concurrent": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "admin-console-timeout": {"required": False, "type": "int"},
                "admin-https-pki-required": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "admin-https-ssl-versions": {"required": False, "type": "list",
                                             "choices": ["tlsv1-0", "tlsv1-1", "tlsv1-2"]},
                "admin-lockout-duration": {"required": False, "type": "int"},
                "admin-lockout-threshold": {"required": False, "type": "int"},
                "admin-login-max": {"required": False, "type": "int"},
                "admin-maintainer": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "admin-port": {"required": False, "type": "int"},
                "admin-restrict-local": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "admin-scp": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "admin-server-cert": {"required": False, "type": "str"},
                "admin-sport": {"required": False, "type": "int"},
                "admin-ssh-grace-time": {"required": False, "type": "int"},
                "admin-ssh-password": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "admin-ssh-port": {"required": False, "type": "int"},
                "admin-ssh-v1": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "admin-telnet-port": {"required": False, "type": "int"},
                "admintimeout": {"required": False, "type": "int"},
                "alias": {"required": False, "type": "str"},
                "allow-traffic-redirect": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "anti-replay": {"required": False, "type": "str",
                                "choices": ["disable", "loose", "strict"]},
                "arp-max-entry": {"required": False, "type": "int"},
                "asymroute": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "auth-cert": {"required": False, "type": "str"},
                "auth-http-port": {"required": False, "type": "int"},
                "auth-https-port": {"required": False, "type": "int"},
                "auth-keepalive": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "auth-session-limit": {"required": False, "type": "str",
                                       "choices": ["block-new", "logout-inactive"]},
                "auto-auth-extension-device": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "av-affinity": {"required": False, "type": "str"},
                "av-failopen": {"required": False, "type": "str",
                                "choices": ["pass", "off", "one-shot"]},
                "av-failopen-session": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "batch-cmdb": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "block-session-timer": {"required": False, "type": "int"},
                "br-fdb-max-entry": {"required": False, "type": "int"},
                "cert-chain-max": {"required": False, "type": "int"},
                "cfg-revert-timeout": {"required": False, "type": "int"},
                "cfg-save": {"required": False, "type": "str",
                             "choices": ["automatic", "manual", "revert"]},
                "check-protocol-header": {"required": False, "type": "str",
                                          "choices": ["loose", "strict"]},
                "check-reset-range": {"required": False, "type": "str",
                                      "choices": ["strict", "disable"]},
                "cli-audit-log": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "clt-cert-req": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "compliance-check": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "compliance-check-time": {"required": False, "type": "str"},
                "cpu-use-threshold": {"required": False, "type": "int"},
                "csr-ca-attribute": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "daily-restart": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "device-identification-active-scan-delay": {"required": False, "type": "int"},
                "device-idle-timeout": {"required": False, "type": "int"},
                "dh-params": {"required": False, "type": "str",
                              "choices": ["1024", "1536", "2048",
                                          "3072", "4096", "6144",
                                          "8192"]},
                "dst": {"required": False, "type": "str",
                        "choices": ["enable", "disable"]},
                "endpoint-control-fds-access": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                "endpoint-control-portal-port": {"required": False, "type": "int"},
                "failtime": {"required": False, "type": "int"},
                "fds-statistics": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "fds-statistics-period": {"required": False, "type": "int"},
                "fgd-alert-subscription": {"required": False, "type": "str",
                                           "choices": ["advisory", "latest-threat", "latest-virus",
                                                       "latest-attack", "new-antivirus-db", "new-attack-db"]},
                "fortiextender": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "fortiextender-data-port": {"required": False, "type": "int"},
                "fortiextender-vlan-mode": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "fortiservice-port": {"required": False, "type": "int"},
                "gui-certificates": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "gui-custom-language": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "gui-date-format": {"required": False, "type": "str",
                                    "choices": ["yyyy/MM/dd", "dd/MM/yyyy", "MM/dd/yyyy",
                                                "yyyy-MM-dd", "dd-MM-yyyy", "MM-dd-yyyy"]},
                "gui-device-latitude": {"required": False, "type": "str"},
                "gui-device-longitude": {"required": False, "type": "str"},
                "gui-display-hostname": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "gui-ipv6": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "gui-lines-per-page": {"required": False, "type": "int"},
                "gui-theme": {"required": False, "type": "str",
                              "choices": ["green", "red", "blue",
                                          "melongene", "mariner"]},
                "gui-wireless-opensecurity": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "honor-df": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "hostname": {"required": False, "type": "str"},
                "igmp-state-limit": {"required": False, "type": "int"},
                "interval": {"required": False, "type": "int"},
                "ip-src-port-range": {"required": False, "type": "str"},
                "ips-affinity": {"required": False, "type": "str"},
                "ipsec-asic-offload": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "ipsec-hmac-offload": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "ipsec-soft-dec-async": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "ipv6-accept-dad": {"required": False, "type": "int"},
                "ipv6-allow-anycast-probe": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                "language": {"required": False, "type": "str",
                             "choices": ["english", "french", "spanish",
                                         "portuguese", "japanese", "trach",
                                         "simch", "korean"]},
                "ldapconntimeout": {"required": False, "type": "int"},
                "lldp-transmission": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "log-ssl-connection": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "log-uuid": {"required": False, "type": "str",
                             "choices": ["disable", "policy-only", "extended"]},
                "login-timestamp": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "long-vdom-name": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "management-vdom": {"required": False, "type": "str"},
                "max-dlpstat-memory": {"required": False, "type": "int"},
                "max-route-cache-size": {"required": False, "type": "int"},
                "mc-ttl-notchange": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "memory-use-threshold-extreme": {"required": False, "type": "int"},
                "memory-use-threshold-green": {"required": False, "type": "int"},
                "memory-use-threshold-red": {"required": False, "type": "int"},
                "miglog-affinity": {"required": False, "type": "str"},
                "miglogd-children": {"required": False, "type": "int"},
                "multi-factor-authentication": {"required": False, "type": "str",
                                                "choices": ["optional", "mandatory"]},
                "multicast-forward": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "ndp-max-entry": {"required": False, "type": "int"},
                "per-user-bwl": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "policy-auth-concurrent": {"required": False, "type": "int"},
                "post-login-banner": {"required": False, "type": "str",
                                      "choices": ["disable", "enable"]},
                "pre-login-banner": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "private-data-encryption": {"required": False, "type": "str",
                                            "choices": ["disable", "enable"]},
                "proxy-auth-lifetime": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "proxy-auth-lifetime-timeout": {"required": False, "type": "int"},
                "proxy-auth-timeout": {"required": False, "type": "int"},
                "proxy-cipher-hardware-acceleration": {"required": False, "type": "str",
                                                       "choices": ["disable", "enable"]},
                "proxy-kxp-hardware-acceleration": {"required": False, "type": "str",
                                                    "choices": ["disable", "enable"]},
                "proxy-re-authentication-mode": {"required": False, "type": "str",
                                                 "choices": ["session", "traffic", "absolute"]},
                "proxy-worker-count": {"required": False, "type": "int"},
                "radius-port": {"required": False, "type": "int"},
                "reboot-upon-config-restore": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "refresh": {"required": False, "type": "int"},
                "remoteauthtimeout": {"required": False, "type": "int"},
                "reset-sessionless-tcp": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "restart-time": {"required": False, "type": "str"},
                "revision-backup-on-logout": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "revision-image-auto-backup": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "scanunit-count": {"required": False, "type": "int"},
                "security-rating-result-submission": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                "security-rating-run-on-schedule": {"required": False, "type": "str",
                                                    "choices": ["enable", "disable"]},
                "send-pmtu-icmp": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "snat-route-change": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "special-file-23-support": {"required": False, "type": "str",
                                            "choices": ["disable", "enable"]},
                "ssh-cbc-cipher": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "ssh-hmac-md5": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "ssh-kex-sha1": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "ssl-min-proto-version": {"required": False, "type": "str",
                                          "choices": ["SSLv3", "TLSv1", "TLSv1-1",
                                                      "TLSv1-2"]},
                "ssl-static-key-ciphers": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "sslvpn-cipher-hardware-acceleration": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                "sslvpn-kxp-hardware-acceleration": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                "sslvpn-max-worker-count": {"required": False, "type": "int"},
                "sslvpn-plugin-version-check": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                "strict-dirty-session-check": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "strong-crypto": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "switch-controller": {"required": False, "type": "str",
                                      "choices": ["disable", "enable"]},
                "switch-controller-reserved-network": {"required": False, "type": "str"},
                "sys-perf-log-interval": {"required": False, "type": "int"},
                "tcp-halfclose-timer": {"required": False, "type": "int"},
                "tcp-halfopen-timer": {"required": False, "type": "int"},
                "tcp-option": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "tcp-timewait-timer": {"required": False, "type": "int"},
                "tftp": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "timezone": {"required": False, "type": "str",
                             "choices": ["01", "02", "03",
                                         "04", "05", "81",
                                         "06", "07", "08",
                                         "09", "10", "11",
                                         "12", "13", "74",
                                         "14", "77", "15",
                                         "87", "16", "17",
                                         "18", "19", "20",
                                         "75", "21", "22",
                                         "23", "24", "80",
                                         "79", "25", "26",
                                         "27", "28", "78",
                                         "29", "30", "31",
                                         "32", "33", "34",
                                         "35", "36", "37",
                                         "38", "83", "84",
                                         "40", "85", "41",
                                         "42", "43", "39",
                                         "44", "46", "47",
                                         "51", "48", "45",
                                         "49", "50", "52",
                                         "53", "54", "55",
                                         "56", "57", "58",
                                         "59", "60", "62",
                                         "63", "61", "64",
                                         "65", "66", "67",
                                         "68", "69", "70",
                                         "71", "72", "00",
                                         "82", "73", "86",
                                         "76"]},
                "tp-mc-skip-policy": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "traffic-priority": {"required": False, "type": "str",
                                     "choices": ["tos", "dscp"]},
                "traffic-priority-level": {"required": False, "type": "str",
                                           "choices": ["low", "medium", "high"]},
                "two-factor-email-expiry": {"required": False, "type": "int"},
                "two-factor-fac-expiry": {"required": False, "type": "int"},
                "two-factor-ftk-expiry": {"required": False, "type": "int"},
                "two-factor-ftm-expiry": {"required": False, "type": "int"},
                "two-factor-sms-expiry": {"required": False, "type": "int"},
                "udp-idle-timer": {"required": False, "type": "int"},
                "user-server-cert": {"required": False, "type": "str"},
                "vdom-admin": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "vip-arp-range": {"required": False, "type": "str",
                                  "choices": ["unlimited", "restricted"]},
                "virtual-server-count": {"required": False, "type": "int"},
                "virtual-server-hardware-acceleration": {"required": False, "type": "str",
                                                         "choices": ["disable", "enable"]},
                "wad-affinity": {"required": False, "type": "str"},
                "wad-csvc-cs-count": {"required": False, "type": "int"},
                "wad-csvc-db-count": {"required": False, "type": "int"},
                "wad-source-affinity": {"required": False, "type": "str",
                                        "choices": ["disable", "enable"]},
                "wad-worker-count": {"required": False, "type": "int"},
                "wifi-ca-certificate": {"required": False, "type": "str"},
                "wifi-certificate": {"required": False, "type": "str"},
                "wimax-4g-usb": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "wireless-controller": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "wireless-controller-port": {"required": False, "type": "int"}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_system(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
