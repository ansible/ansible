#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2018 Fortinet, Inc.
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
#
# the lib use python logging can get it if the following is set in your
# Ansible config.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_antivirus_profile
short_description: Configure AntiVirus profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure antivirus feature and profile category.
      Examples includes all options and need to be adjusted to datasources before usage.
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
        default: false
    antivirus_profile:
        description:
            - Configure AntiVirus profiles.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            analytics-bl-filetype:
                description:
                    - Only submit files matching this DLP file-pattern to FortiSandbox. Source dlp.filepattern.id.
            analytics-db:
                description:
                    - Enable/disable using the FortiSandbox signature database to supplement the AV signature databases.
                choices:
                    - disable
                    - enable
            analytics-max-upload:
                description:
                    - Maximum size of files that can be uploaded to FortiSandbox (1 - 395 MBytes, default = 10).
            analytics-wl-filetype:
                description:
                    - Do not submit files matching this DLP file-pattern to FortiSandbox. Source dlp.filepattern.id.
            av-block-log:
                description:
                    - Enable/disable logging for AntiVirus file blocking.
                choices:
                    - enable
                    - disable
            av-virus-log:
                description:
                    - Enable/disable AntiVirus logging.
                choices:
                    - enable
                    - disable
            comment:
                description:
                    - Comment.
            content-disarm:
                description:
                    - AV Content Disarm and Reconstruction settings.
                suboptions:
                    cover-page:
                        description:
                            - Enable/disable inserting a cover page into the disarmed document.
                        choices:
                            - disable
                            - enable
                    detect-only:
                        description:
                            - Enable/disable only detect disarmable files, do not alter content.
                        choices:
                            - disable
                            - enable
                    office-embed:
                        description:
                            - Enable/disable stripping of embedded objects in Microsoft Office documents.
                        choices:
                            - disable
                            - enable
                    office-hylink:
                        description:
                            - Enable/disable stripping of hyperlinks in Microsoft Office documents.
                        choices:
                            - disable
                            - enable
                    office-linked:
                        description:
                            - Enable/disable stripping of linked objects in Microsoft Office documents.
                        choices:
                            - disable
                            - enable
                    office-macro:
                        description:
                            - Enable/disable stripping of macros in Microsoft Office documents.
                        choices:
                            - disable
                            - enable
                    original-file-destination:
                        description:
                            - Destination to send original file if active content is removed.
                        choices:
                            - fortisandbox
                            - quarantine
                            - discard
                    pdf-act-form:
                        description:
                            - Enable/disable stripping of actions that submit data to other targets in PDF documents.
                        choices:
                            - disable
                            - enable
                    pdf-act-gotor:
                        description:
                            - Enable/disable stripping of links to other PDFs in PDF documents.
                        choices:
                            - disable
                            - enable
                    pdf-act-java:
                        description:
                            - Enable/disable stripping of actions that execute JavaScript code in PDF documents.
                        choices:
                            - disable
                            - enable
                    pdf-act-launch:
                        description:
                            - Enable/disable stripping of links to external applications in PDF documents.
                        choices:
                            - disable
                            - enable
                    pdf-act-movie:
                        description:
                            - Enable/disable stripping of embedded movies in PDF documents.
                        choices:
                            - disable
                            - enable
                    pdf-act-sound:
                        description:
                            - Enable/disable stripping of embedded sound files in PDF documents.
                        choices:
                            - disable
                            - enable
                    pdf-embedfile:
                        description:
                            - Enable/disable stripping of embedded files in PDF documents.
                        choices:
                            - disable
                            - enable
                    pdf-hyperlink:
                        description:
                            - Enable/disable stripping of hyperlinks from PDF documents.
                        choices:
                            - disable
                            - enable
                    pdf-javacode:
                        description:
                            - Enable/disable stripping of JavaScript code in PDF documents.
                        choices:
                            - disable
                            - enable
            extended-log:
                description:
                    - Enable/disable extended logging for antivirus.
                choices:
                    - enable
                    - disable
            ftgd-analytics:
                description:
                    - Settings to control which files are uploaded to FortiSandbox.
                choices:
                    - disable
                    - suspicious
                    - everything
            ftp:
                description:
                    - Configure FTP AntiVirus options.
                suboptions:
                    archive-block:
                        description:
                            - Select the archive types to block.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    archive-log:
                        description:
                            - Select the archive types to log.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    emulator:
                        description:
                            - Enable/disable the virus emulator.
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - Enable/disable FTP AntiVirus scanning, monitoring, and quarantine.
                        choices:
                            - scan
                            - avmonitor
                            - quarantine
                    outbreak-prevention:
                        description:
                            - Enable FortiGuard Virus Outbreak Prevention service.
                        choices:
                            - disabled
                            - files
                            - full-archive
            http:
                description:
                    - Configure HTTP AntiVirus options.
                suboptions:
                    archive-block:
                        description:
                            - Select the archive types to block.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    archive-log:
                        description:
                            - Select the archive types to log.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    content-disarm:
                        description:
                            - Enable Content Disarm and Reconstruction for this protocol.
                        choices:
                            - disable
                            - enable
                    emulator:
                        description:
                            - Enable/disable the virus emulator.
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - Enable/disable HTTP AntiVirus scanning, monitoring, and quarantine.
                        choices:
                            - scan
                            - avmonitor
                            - quarantine
                    outbreak-prevention:
                        description:
                            - Enable FortiGuard Virus Outbreak Prevention service.
                        choices:
                            - disabled
                            - files
                            - full-archive
            imap:
                description:
                    - Configure IMAP AntiVirus options.
                suboptions:
                    archive-block:
                        description:
                            - Select the archive types to block.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    archive-log:
                        description:
                            - Select the archive types to log.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    content-disarm:
                        description:
                            - Enable Content Disarm and Reconstruction for this protocol.
                        choices:
                            - disable
                            - enable
                    emulator:
                        description:
                            - Enable/disable the virus emulator.
                        choices:
                            - enable
                            - disable
                    executables:
                        description:
                            - Treat Windows executable files as viruses for the purpose of blocking or monitoring.
                        choices:
                            - default
                            - virus
                    options:
                        description:
                            - Enable/disable IMAP AntiVirus scanning, monitoring, and quarantine.
                        choices:
                            - scan
                            - avmonitor
                            - quarantine
                    outbreak-prevention:
                        description:
                            - Enable FortiGuard Virus Outbreak Prevention service.
                        choices:
                            - disabled
                            - files
                            - full-archive
            inspection-mode:
                description:
                    - Inspection mode.
                choices:
                    - proxy
                    - flow-based
            mapi:
                description:
                    - Configure MAPI AntiVirus options.
                suboptions:
                    archive-block:
                        description:
                            - Select the archive types to block.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    archive-log:
                        description:
                            - Select the archive types to log.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    emulator:
                        description:
                            - Enable/disable the virus emulator.
                        choices:
                            - enable
                            - disable
                    executables:
                        description:
                            - Treat Windows executable files as viruses for the purpose of blocking or monitoring.
                        choices:
                            - default
                            - virus
                    options:
                        description:
                            - Enable/disable MAPI AntiVirus scanning, monitoring, and quarantine.
                        choices:
                            - scan
                            - avmonitor
                            - quarantine
                    outbreak-prevention:
                        description:
                            - Enable FortiGuard Virus Outbreak Prevention service.
                        choices:
                            - disabled
                            - files
                            - full-archive
            mobile-malware-db:
                description:
                    - Enable/disable using the mobile malware signature database.
                choices:
                    - disable
                    - enable
            nac-quar:
                description:
                    - Configure AntiVirus quarantine settings.
                suboptions:
                    expiry:
                        description:
                            - Duration of quarantine.
                    infected:
                        description:
                            - Enable/Disable quarantining infected hosts to the banned user list.
                        choices:
                            - none
                            - quar-src-ip
                    log:
                        description:
                            - Enable/disable AntiVirus quarantine logging.
                        choices:
                            - enable
                            - disable
            name:
                description:
                    - Profile name.
                required: true
            nntp:
                description:
                    - Configure NNTP AntiVirus options.
                suboptions:
                    archive-block:
                        description:
                            - Select the archive types to block.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    archive-log:
                        description:
                            - Select the archive types to log.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    emulator:
                        description:
                            - Enable/disable the virus emulator.
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - Enable/disable NNTP AntiVirus scanning, monitoring, and quarantine.
                        choices:
                            - scan
                            - avmonitor
                            - quarantine
                    outbreak-prevention:
                        description:
                            - Enable FortiGuard Virus Outbreak Prevention service.
                        choices:
                            - disabled
                            - files
                            - full-archive
            pop3:
                description:
                    - Configure POP3 AntiVirus options.
                suboptions:
                    archive-block:
                        description:
                            - Select the archive types to block.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    archive-log:
                        description:
                            - Select the archive types to log.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    content-disarm:
                        description:
                            - Enable Content Disarm and Reconstruction for this protocol.
                        choices:
                            - disable
                            - enable
                    emulator:
                        description:
                            - Enable/disable the virus emulator.
                        choices:
                            - enable
                            - disable
                    executables:
                        description:
                            - Treat Windows executable files as viruses for the purpose of blocking or monitoring.
                        choices:
                            - default
                            - virus
                    options:
                        description:
                            - Enable/disable POP3 AntiVirus scanning, monitoring, and quarantine.
                        choices:
                            - scan
                            - avmonitor
                            - quarantine
                    outbreak-prevention:
                        description:
                            - Enable FortiGuard Virus Outbreak Prevention service.
                        choices:
                            - disabled
                            - files
                            - full-archive
            replacemsg-group:
                description:
                    - Replacement message group customized for this profile. Source system.replacemsg-group.name.
            scan-mode:
                description:
                    - Choose between full scan mode and quick scan mode.
                choices:
                    - quick
                    - full
            smb:
                description:
                    - Configure SMB AntiVirus options.
                suboptions:
                    archive-block:
                        description:
                            - Select the archive types to block.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    archive-log:
                        description:
                            - Select the archive types to log.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    emulator:
                        description:
                            - Enable/disable the virus emulator.
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - Enable/disable SMB AntiVirus scanning, monitoring, and quarantine.
                        choices:
                            - scan
                            - avmonitor
                            - quarantine
                    outbreak-prevention:
                        description:
                            - Enable FortiGuard Virus Outbreak Prevention service.
                        choices:
                            - disabled
                            - files
                            - full-archive
            smtp:
                description:
                    - Configure SMTP AntiVirus options.
                suboptions:
                    archive-block:
                        description:
                            - Select the archive types to block.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    archive-log:
                        description:
                            - Select the archive types to log.
                        choices:
                            - encrypted
                            - corrupted
                            - partiallycorrupted
                            - multipart
                            - nested
                            - mailbomb
                            - fileslimit
                            - timeout
                            - unhandled
                    content-disarm:
                        description:
                            - Enable Content Disarm and Reconstruction for this protocol.
                        choices:
                            - disable
                            - enable
                    emulator:
                        description:
                            - Enable/disable the virus emulator.
                        choices:
                            - enable
                            - disable
                    executables:
                        description:
                            - Treat Windows executable files as viruses for the purpose of blocking or monitoring.
                        choices:
                            - default
                            - virus
                    options:
                        description:
                            - Enable/disable SMTP AntiVirus scanning, monitoring, and quarantine.
                        choices:
                            - scan
                            - avmonitor
                            - quarantine
                    outbreak-prevention:
                        description:
                            - Enable FortiGuard Virus Outbreak Prevention service.
                        choices:
                            - disabled
                            - files
                            - full-archive
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure AntiVirus profiles.
    fortios_antivirus_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      antivirus_profile:
        state: "present"
        analytics-bl-filetype: "3 (source dlp.filepattern.id)"
        analytics-db: "disable"
        analytics-max-upload: "5"
        analytics-wl-filetype: "6 (source dlp.filepattern.id)"
        av-block-log: "enable"
        av-virus-log: "enable"
        comment: "Comment."
        content-disarm:
            cover-page: "disable"
            detect-only: "disable"
            office-embed: "disable"
            office-hylink: "disable"
            office-linked: "disable"
            office-macro: "disable"
            original-file-destination: "fortisandbox"
            pdf-act-form: "disable"
            pdf-act-gotor: "disable"
            pdf-act-java: "disable"
            pdf-act-launch: "disable"
            pdf-act-movie: "disable"
            pdf-act-sound: "disable"
            pdf-embedfile: "disable"
            pdf-hyperlink: "disable"
            pdf-javacode: "disable"
        extended-log: "enable"
        ftgd-analytics: "disable"
        ftp:
            archive-block: "encrypted"
            archive-log: "encrypted"
            emulator: "enable"
            options: "scan"
            outbreak-prevention: "disabled"
        http:
            archive-block: "encrypted"
            archive-log: "encrypted"
            content-disarm: "disable"
            emulator: "enable"
            options: "scan"
            outbreak-prevention: "disabled"
        imap:
            archive-block: "encrypted"
            archive-log: "encrypted"
            content-disarm: "disable"
            emulator: "enable"
            executables: "default"
            options: "scan"
            outbreak-prevention: "disabled"
        inspection-mode: "proxy"
        mapi:
            archive-block: "encrypted"
            archive-log: "encrypted"
            emulator: "enable"
            executables: "default"
            options: "scan"
            outbreak-prevention: "disabled"
        mobile-malware-db: "disable"
        nac-quar:
            expiry: "<your_own_value>"
            infected: "none"
            log: "enable"
        name: "default_name_63"
        nntp:
            archive-block: "encrypted"
            archive-log: "encrypted"
            emulator: "enable"
            options: "scan"
            outbreak-prevention: "disabled"
        pop3:
            archive-block: "encrypted"
            archive-log: "encrypted"
            content-disarm: "disable"
            emulator: "enable"
            executables: "default"
            options: "scan"
            outbreak-prevention: "disabled"
        replacemsg-group: "<your_own_value> (source system.replacemsg-group.name)"
        scan-mode: "quick"
        smb:
            archive-block: "encrypted"
            archive-log: "encrypted"
            emulator: "enable"
            options: "scan"
            outbreak-prevention: "disabled"
        smtp:
            archive-block: "encrypted"
            archive-log: "encrypted"
            content-disarm: "disable"
            emulator: "enable"
            executables: "default"
            options: "scan"
            outbreak-prevention: "disabled"
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

fos = None


def login(data):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_antivirus_profile_data(json):
    option_list = ['analytics-bl-filetype', 'analytics-db', 'analytics-max-upload',
                   'analytics-wl-filetype', 'av-block-log', 'av-virus-log',
                   'comment', 'content-disarm', 'extended-log',
                   'ftgd-analytics', 'ftp', 'http',
                   'imap', 'inspection-mode', 'mapi',
                   'mobile-malware-db', 'nac-quar', 'name',
                   'nntp', 'pop3', 'replacemsg-group',
                   'scan-mode', 'smb', 'smtp']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def antivirus_profile(data, fos):
    vdom = data['vdom']
    antivirus_profile_data = data['antivirus_profile']
    filtered_data = filter_antivirus_profile_data(antivirus_profile_data)
    if antivirus_profile_data['state'] == "present":
        return fos.set('antivirus',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif antivirus_profile_data['state'] == "absent":
        return fos.delete('antivirus',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_antivirus(data, fos):
    login(data)

    methodlist = ['antivirus_profile']
    for method in methodlist:
        if data[method]:
            resp = eval(method)(data, fos)
            break

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": "False"},
        "antivirus_profile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "analytics-bl-filetype": {"required": False, "type": "int"},
                "analytics-db": {"required": False, "type": "str",
                                 "choices": ["disable", "enable"]},
                "analytics-max-upload": {"required": False, "type": "int"},
                "analytics-wl-filetype": {"required": False, "type": "int"},
                "av-block-log": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "av-virus-log": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "comment": {"required": False, "type": "str"},
                "content-disarm": {"required": False, "type": "dict",
                                   "options": {
                                       "cover-page": {"required": False, "type": "str",
                                                      "choices": ["disable", "enable"]},
                                       "detect-only": {"required": False, "type": "str",
                                                       "choices": ["disable", "enable"]},
                                       "office-embed": {"required": False, "type": "str",
                                                        "choices": ["disable", "enable"]},
                                       "office-hylink": {"required": False, "type": "str",
                                                         "choices": ["disable", "enable"]},
                                       "office-linked": {"required": False, "type": "str",
                                                         "choices": ["disable", "enable"]},
                                       "office-macro": {"required": False, "type": "str",
                                                        "choices": ["disable", "enable"]},
                                       "original-file-destination": {"required": False, "type": "str",
                                                                     "choices": ["fortisandbox", "quarantine", "discard"]},
                                       "pdf-act-form": {"required": False, "type": "str",
                                                        "choices": ["disable", "enable"]},
                                       "pdf-act-gotor": {"required": False, "type": "str",
                                                         "choices": ["disable", "enable"]},
                                       "pdf-act-java": {"required": False, "type": "str",
                                                        "choices": ["disable", "enable"]},
                                       "pdf-act-launch": {"required": False, "type": "str",
                                                          "choices": ["disable", "enable"]},
                                       "pdf-act-movie": {"required": False, "type": "str",
                                                         "choices": ["disable", "enable"]},
                                       "pdf-act-sound": {"required": False, "type": "str",
                                                         "choices": ["disable", "enable"]},
                                       "pdf-embedfile": {"required": False, "type": "str",
                                                         "choices": ["disable", "enable"]},
                                       "pdf-hyperlink": {"required": False, "type": "str",
                                                         "choices": ["disable", "enable"]},
                                       "pdf-javacode": {"required": False, "type": "str",
                                                        "choices": ["disable", "enable"]}
                                   }},
                "extended-log": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "ftgd-analytics": {"required": False, "type": "str",
                                   "choices": ["disable", "suspicious", "everything"]},
                "ftp": {"required": False, "type": "dict",
                        "options": {
                            "archive-block": {"required": False, "type": "str",
                                              "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                          "multipart", "nested", "mailbomb",
                                                          "fileslimit", "timeout", "unhandled"]},
                            "archive-log": {"required": False, "type": "str",
                                            "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                        "multipart", "nested", "mailbomb",
                                                        "fileslimit", "timeout", "unhandled"]},
                            "emulator": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                            "options": {"required": False, "type": "str",
                                        "choices": ["scan", "avmonitor", "quarantine"]},
                            "outbreak-prevention": {"required": False, "type": "str",
                                                    "choices": ["disabled", "files", "full-archive"]}
                        }},
                "http": {"required": False, "type": "dict",
                         "options": {
                             "archive-block": {"required": False, "type": "str",
                                               "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                           "multipart", "nested", "mailbomb",
                                                           "fileslimit", "timeout", "unhandled"]},
                             "archive-log": {"required": False, "type": "str",
                                             "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                         "multipart", "nested", "mailbomb",
                                                         "fileslimit", "timeout", "unhandled"]},
                             "content-disarm": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                             "emulator": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["scan", "avmonitor", "quarantine"]},
                             "outbreak-prevention": {"required": False, "type": "str",
                                                     "choices": ["disabled", "files", "full-archive"]}
                         }},
                "imap": {"required": False, "type": "dict",
                         "options": {
                             "archive-block": {"required": False, "type": "str",
                                               "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                           "multipart", "nested", "mailbomb",
                                                           "fileslimit", "timeout", "unhandled"]},
                             "archive-log": {"required": False, "type": "str",
                                             "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                         "multipart", "nested", "mailbomb",
                                                         "fileslimit", "timeout", "unhandled"]},
                             "content-disarm": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                             "emulator": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                             "executables": {"required": False, "type": "str",
                                             "choices": ["default", "virus"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["scan", "avmonitor", "quarantine"]},
                             "outbreak-prevention": {"required": False, "type": "str",
                                                     "choices": ["disabled", "files", "full-archive"]}
                         }},
                "inspection-mode": {"required": False, "type": "str",
                                    "choices": ["proxy", "flow-based"]},
                "mapi": {"required": False, "type": "dict",
                         "options": {
                             "archive-block": {"required": False, "type": "str",
                                               "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                           "multipart", "nested", "mailbomb",
                                                           "fileslimit", "timeout", "unhandled"]},
                             "archive-log": {"required": False, "type": "str",
                                             "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                         "multipart", "nested", "mailbomb",
                                                         "fileslimit", "timeout", "unhandled"]},
                             "emulator": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                             "executables": {"required": False, "type": "str",
                                             "choices": ["default", "virus"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["scan", "avmonitor", "quarantine"]},
                             "outbreak-prevention": {"required": False, "type": "str",
                                                     "choices": ["disabled", "files", "full-archive"]}
                         }},
                "mobile-malware-db": {"required": False, "type": "str",
                                      "choices": ["disable", "enable"]},
                "nac-quar": {"required": False, "type": "dict",
                             "options": {
                                 "expiry": {"required": False, "type": "str"},
                                 "infected": {"required": False, "type": "str",
                                              "choices": ["none", "quar-src-ip"]},
                                 "log": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]}
                             }},
                "name": {"required": True, "type": "str"},
                "nntp": {"required": False, "type": "dict",
                         "options": {
                             "archive-block": {"required": False, "type": "str",
                                               "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                           "multipart", "nested", "mailbomb",
                                                           "fileslimit", "timeout", "unhandled"]},
                             "archive-log": {"required": False, "type": "str",
                                             "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                         "multipart", "nested", "mailbomb",
                                                         "fileslimit", "timeout", "unhandled"]},
                             "emulator": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["scan", "avmonitor", "quarantine"]},
                             "outbreak-prevention": {"required": False, "type": "str",
                                                     "choices": ["disabled", "files", "full-archive"]}
                         }},
                "pop3": {"required": False, "type": "dict",
                         "options": {
                             "archive-block": {"required": False, "type": "str",
                                               "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                           "multipart", "nested", "mailbomb",
                                                           "fileslimit", "timeout", "unhandled"]},
                             "archive-log": {"required": False, "type": "str",
                                             "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                         "multipart", "nested", "mailbomb",
                                                         "fileslimit", "timeout", "unhandled"]},
                             "content-disarm": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                             "emulator": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                             "executables": {"required": False, "type": "str",
                                             "choices": ["default", "virus"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["scan", "avmonitor", "quarantine"]},
                             "outbreak-prevention": {"required": False, "type": "str",
                                                     "choices": ["disabled", "files", "full-archive"]}
                         }},
                "replacemsg-group": {"required": False, "type": "str"},
                "scan-mode": {"required": False, "type": "str",
                              "choices": ["quick", "full"]},
                "smb": {"required": False, "type": "dict",
                        "options": {
                            "archive-block": {"required": False, "type": "str",
                                              "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                          "multipart", "nested", "mailbomb",
                                                          "fileslimit", "timeout", "unhandled"]},
                            "archive-log": {"required": False, "type": "str",
                                            "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                        "multipart", "nested", "mailbomb",
                                                        "fileslimit", "timeout", "unhandled"]},
                            "emulator": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                            "options": {"required": False, "type": "str",
                                        "choices": ["scan", "avmonitor", "quarantine"]},
                            "outbreak-prevention": {"required": False, "type": "str",
                                                    "choices": ["disabled", "files", "full-archive"]}
                        }},
                "smtp": {"required": False, "type": "dict",
                         "options": {
                             "archive-block": {"required": False, "type": "str",
                                               "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                           "multipart", "nested", "mailbomb",
                                                           "fileslimit", "timeout", "unhandled"]},
                             "archive-log": {"required": False, "type": "str",
                                             "choices": ["encrypted", "corrupted", "partiallycorrupted",
                                                         "multipart", "nested", "mailbomb",
                                                         "fileslimit", "timeout", "unhandled"]},
                             "content-disarm": {"required": False, "type": "str",
                                                "choices": ["disable", "enable"]},
                             "emulator": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                             "executables": {"required": False, "type": "str",
                                             "choices": ["default", "virus"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["scan", "avmonitor", "quarantine"]},
                             "outbreak-prevention": {"required": False, "type": "str",
                                                     "choices": ["disabled", "files", "full-archive"]}
                         }}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_antivirus(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
