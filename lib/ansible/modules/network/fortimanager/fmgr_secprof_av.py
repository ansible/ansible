#!/usr/bin/python
# -*- coding: utf-8 -*-
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: fmgr_secprof_av
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manage security profile
description:
  -  Manage security profile groups for FortiManager objects

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  mode:
    description:
      - Sets one of three modes for managing the object.
      - Allows use of soft-adds instead of overwriting existing values
    choices: ['add', 'set', 'delete', 'update']
    required: false
    default: add

  scan_mode:
    description:
      - Choose between full scan mode and quick scan mode.
    required: false
    choices:
      - quick
      - full

  replacemsg_group:
    description:
      - Replacement message group customized for this profile.
    required: false

  name:
    description:
      - Profile name.
    required: false

  mobile_malware_db:
    description:
      - Enable/disable using the mobile malware signature database.
    required: false
    choices:
      - disable
      - enable

  inspection_mode:
    description:
      - Inspection mode.
    required: false
    choices:
      - proxy
      - flow-based

  ftgd_analytics:
    description:
      - Settings to control which files are uploaded to FortiSandbox.
    required: false
    choices:
      - disable
      - suspicious
      - everything

  extended_log:
    description:
      - Enable/disable extended logging for antivirus.
    required: false
    choices:
      - disable
      - enable

  comment:
    description:
      - Comment.
    required: false

  av_virus_log:
    description:
      - Enable/disable AntiVirus logging.
    required: false
    choices:
      - disable
      - enable

  av_block_log:
    description:
      - Enable/disable logging for AntiVirus file blocking.
    required: false
    choices:
      - disable
      - enable

  analytics_wl_filetype:
    description:
      - Do not submit files matching this DLP file-pattern to FortiSandbox.
    required: false

  analytics_max_upload:
    description:
      - Maximum size of files that can be uploaded to FortiSandbox (1 - 395 MBytes, default = 10).
    required: false

  analytics_db:
    description:
      - Enable/disable using the FortiSandbox signature database to supplement the AV signature databases.
    required: false
    choices:
      - disable
      - enable

  analytics_bl_filetype:
    description:
      - Only submit files matching this DLP file-pattern to FortiSandbox.
    required: false

  content_disarm:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  content_disarm_cover_page:
    description:
      - Enable/disable inserting a cover page into the disarmed document.
    required: false
    choices:
      - disable
      - enable

  content_disarm_detect_only:
    description:
      - Enable/disable only detect disarmable files, do not alter content.
    required: false
    choices:
      - disable
      - enable

  content_disarm_office_embed:
    description:
      - Enable/disable stripping of embedded objects in Microsoft Office documents.
    required: false
    choices:
      - disable
      - enable

  content_disarm_office_hylink:
    description:
      - Enable/disable stripping of hyperlinks in Microsoft Office documents.
    required: false
    choices:
      - disable
      - enable

  content_disarm_office_linked:
    description:
      - Enable/disable stripping of linked objects in Microsoft Office documents.
    required: false
    choices:
      - disable
      - enable

  content_disarm_office_macro:
    description:
      - Enable/disable stripping of macros in Microsoft Office documents.
    required: false
    choices:
      - disable
      - enable

  content_disarm_original_file_destination:
    description:
      - Destination to send original file if active content is removed.
    required: false
    choices:
      - fortisandbox
      - quarantine
      - discard

  content_disarm_pdf_act_form:
    description:
      - Enable/disable stripping of actions that submit data to other targets in PDF documents.
    required: false
    choices:
      - disable
      - enable

  content_disarm_pdf_act_gotor:
    description:
      - Enable/disable stripping of links to other PDFs in PDF documents.
    required: false
    choices:
      - disable
      - enable

  content_disarm_pdf_act_java:
    description:
      - Enable/disable stripping of actions that execute JavaScript code in PDF documents.
    required: false
    choices:
      - disable
      - enable

  content_disarm_pdf_act_launch:
    description:
      - Enable/disable stripping of links to external applications in PDF documents.
    required: false
    choices:
      - disable
      - enable

  content_disarm_pdf_act_movie:
    description:
      - Enable/disable stripping of embedded movies in PDF documents.
    required: false
    choices:
      - disable
      - enable

  content_disarm_pdf_act_sound:
    description:
      - Enable/disable stripping of embedded sound files in PDF documents.
    required: false
    choices:
      - disable
      - enable

  content_disarm_pdf_embedfile:
    description:
      - Enable/disable stripping of embedded files in PDF documents.
    required: false
    choices:
      - disable
      - enable

  content_disarm_pdf_hyperlink:
    description:
      - Enable/disable stripping of hyperlinks from PDF documents.
    required: false
    choices:
      - disable
      - enable

  content_disarm_pdf_javacode:
    description:
      - Enable/disable stripping of JavaScript code in PDF documents.
    required: false
    choices:
      - disable
      - enable

  ftp:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  ftp_archive_block:
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  ftp_archive_log:
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  ftp_emulator:
    description:
      - Enable/disable the virus emulator.
    required: false
    choices:
      - disable
      - enable

  ftp_options:
    description:
      - Enable/disable FTP AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - scan
      - quarantine
      - avmonitor

  ftp_outbreak_prevention:
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
    required: false
    choices:
      - disabled
      - files
      - full-archive

  http:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  http_archive_block:
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  http_archive_log:
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  http_content_disarm:
    description:
      - Enable Content Disarm and Reconstruction for this protocol.
    required: false
    choices:
      - disable
      - enable

  http_emulator:
    description:
      - Enable/disable the virus emulator.
    required: false
    choices:
      - disable
      - enable

  http_options:
    description:
      - Enable/disable HTTP AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - scan
      - quarantine
      - avmonitor

  http_outbreak_prevention:
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
    required: false
    choices:
      - disabled
      - files
      - full-archive

  imap:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  imap_archive_block:
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  imap_archive_log:
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  imap_content_disarm:
    description:
      - Enable Content Disarm and Reconstruction for this protocol.
    required: false
    choices:
      - disable
      - enable

  imap_emulator:
    description:
      - Enable/disable the virus emulator.
    required: false
    choices:
      - disable
      - enable

  imap_executables:
    description:
      - Treat Windows executable files as viruses for the purpose of blocking or monitoring.
    required: false
    choices:
      - default
      - virus

  imap_options:
    description:
      - Enable/disable IMAP AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - scan
      - quarantine
      - avmonitor

  imap_outbreak_prevention:
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
    required: false
    choices:
      - disabled
      - files
      - full-archive

  mapi:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  mapi_archive_block:
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  mapi_archive_log:
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  mapi_emulator:
    description:
      - Enable/disable the virus emulator.
    required: false
    choices:
      - disable
      - enable

  mapi_executables:
    description:
      - Treat Windows executable files as viruses for the purpose of blocking or monitoring.
    required: false
    choices:
      - default
      - virus

  mapi_options:
    description:
      - Enable/disable MAPI AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - scan
      - quarantine
      - avmonitor

  mapi_outbreak_prevention:
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
    required: false
    choices:
      - disabled
      - files
      - full-archive

  nac_quar:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  nac_quar_expiry:
    description:
      - Duration of quarantine.
    required: false

  nac_quar_infected:
    description:
      - Enable/Disable quarantining infected hosts to the banned user list.
    required: false
    choices:
      - none
      - quar-src-ip

  nac_quar_log:
    description:
      - Enable/disable AntiVirus quarantine logging.
    required: false
    choices:
      - disable
      - enable

  nntp:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  nntp_archive_block:
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  nntp_archive_log:
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  nntp_emulator:
    description:
      - Enable/disable the virus emulator.
    required: false
    choices:
      - disable
      - enable

  nntp_options:
    description:
      - Enable/disable NNTP AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - scan
      - quarantine
      - avmonitor

  nntp_outbreak_prevention:
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
    required: false
    choices:
      - disabled
      - files
      - full-archive

  pop3:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  pop3_archive_block:
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  pop3_archive_log:
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  pop3_content_disarm:
    description:
      - Enable Content Disarm and Reconstruction for this protocol.
    required: false
    choices:
      - disable
      - enable

  pop3_emulator:
    description:
      - Enable/disable the virus emulator.
    required: false
    choices:
      - disable
      - enable

  pop3_executables:
    description:
      - Treat Windows executable files as viruses for the purpose of blocking or monitoring.
    required: false
    choices:
      - default
      - virus

  pop3_options:
    description:
      - Enable/disable POP3 AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - scan
      - quarantine
      - avmonitor

  pop3_outbreak_prevention:
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
    required: false
    choices:
      - disabled
      - files
      - full-archive

  smb:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  smb_archive_block:
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  smb_archive_log:
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  smb_emulator:
    description:
      - Enable/disable the virus emulator.
    required: false
    choices:
      - disable
      - enable

  smb_options:
    description:
      - Enable/disable SMB AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - scan
      - quarantine
      - avmonitor

  smb_outbreak_prevention:
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
    required: false
    choices:
      - disabled
      - files
      - full-archive

  smtp:
    description:
      - EXPERTS ONLY! KNOWLEDGE OF FMGR JSON API IS REQUIRED!
      - List of multiple child objects to be added. Expects a list of dictionaries.
      - Dictionaries must use FortiManager API parameters, not the ansible ones listed below.
      - If submitted, all other prefixed sub-parameters ARE IGNORED.
      - This object is MUTUALLY EXCLUSIVE with its options.
      - We expect that you know what you are doing with these list parameters, and are leveraging the JSON API Guide.
      - WHEN IN DOUBT, USE THE SUB OPTIONS BELOW INSTEAD TO CREATE OBJECTS WITH MULTIPLE TASKS
    required: false

  smtp_archive_block:
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  smtp_archive_log:
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - encrypted
      - corrupted
      - multipart
      - nested
      - mailbomb
      - unhandled
      - partiallycorrupted
      - fileslimit
      - timeout

  smtp_content_disarm:
    description:
      - Enable Content Disarm and Reconstruction for this protocol.
    required: false
    choices:
      - disable
      - enable

  smtp_emulator:
    description:
      - Enable/disable the virus emulator.
    required: false
    choices:
      - disable
      - enable

  smtp_executables:
    description:
      - Treat Windows executable files as viruses for the purpose of blocking or monitoring.
    required: false
    choices:
      - default
      - virus

  smtp_options:
    description:
      - Enable/disable SMTP AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
    required: false
    choices:
      - scan
      - quarantine
      - avmonitor

  smtp_outbreak_prevention:
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
    required: false
    choices:
      - disabled
      - files
      - full-archive
'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_av:
      name: "Ansible_AV_Profile"
      mode: "delete"

  - name: CREATE Profile
    fmgr_secprof_av:
      name: "Ansible_AV_Profile"
      comment: "Created by Ansible Module TEST"
      mode: "set"
      inspection_mode: "proxy"
      ftgd_analytics: "everything"
      av_block_log: "enable"
      av_virus_log: "enable"
      scan_mode: "full"
      mobile_malware_db: "enable"
      ftp_archive_block: "encrypted"
      ftp_outbreak_prevention: "files"
      ftp_archive_log: "timeout"
      ftp_emulator: "disable"
      ftp_options: "scan"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGRCommon
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG
from ansible.module_utils.network.fortimanager.common import prepare_dict
from ansible.module_utils.network.fortimanager.common import scrub_dict

###############
# START METHODS
###############


def fmgr_antivirus_profile_modify(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]

    response = DEFAULT_RESULT_OBJ
    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/antivirus/profile'.format(adom=adom)
        datagram = scrub_dict(prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    else:
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/antivirus/profile/{name}'.format(adom=adom, name=paramgram["name"])
        datagram = {}

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response

#############
# END METHODS
#############


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str", default="root"),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),

        scan_mode=dict(required=False, type="str", choices=["quick", "full"]),
        replacemsg_group=dict(required=False, type="dict"),
        name=dict(required=False, type="str"),
        mobile_malware_db=dict(required=False, type="str", choices=["disable", "enable"]),
        inspection_mode=dict(required=False, type="str", choices=["proxy", "flow-based"]),
        ftgd_analytics=dict(required=False, type="str", choices=["disable", "suspicious", "everything"]),
        extended_log=dict(required=False, type="str", choices=["disable", "enable"]),
        comment=dict(required=False, type="str"),
        av_virus_log=dict(required=False, type="str", choices=["disable", "enable"]),
        av_block_log=dict(required=False, type="str", choices=["disable", "enable"]),
        analytics_wl_filetype=dict(required=False, type="dict"),
        analytics_max_upload=dict(required=False, type="int"),
        analytics_db=dict(required=False, type="str", choices=["disable", "enable"]),
        analytics_bl_filetype=dict(required=False, type="dict"),
        content_disarm=dict(required=False, type="list"),
        content_disarm_cover_page=dict(required=False, type="str", choices=["disable", "enable"]),
        content_disarm_detect_only=dict(required=False, type="str", choices=["disable", "enable"]),
        content_disarm_office_embed=dict(required=False, type="str", choices=["disable", "enable"]),
        content_disarm_office_hylink=dict(required=False, type="str", choices=["disable", "enable"]),
        content_disarm_office_linked=dict(required=False, type="str", choices=["disable", "enable"]),
        content_disarm_office_macro=dict(required=False, type="str", choices=["disable", "enable"]),
        content_disarm_original_file_destination=dict(required=False, type="str", choices=["fortisandbox",
                                                                                           "quarantine",
                                                                                           "discard"]),
        content_disarm_pdf_act_form=dict(required=False, type="str", choices=["disable", "enable"]),
        content_disarm_pdf_act_gotor=dict(required=False, type="str", choices=["disable", "enable"]),
        content_disarm_pdf_act_java=dict(required=False, type="str", choices=["disable", "enable"]),
        content_disarm_pdf_act_launch=dict(required=False, type="str", choices=["disable", "enable"]),
        content_disarm_pdf_act_movie=dict(required=False, type="str", choices=["disable", "enable"]),
        content_disarm_pdf_act_sound=dict(required=False, type="str", choices=["disable", "enable"]),
        content_disarm_pdf_embedfile=dict(required=False, type="str", choices=["disable", "enable"]),
        content_disarm_pdf_hyperlink=dict(required=False, type="str", choices=["disable", "enable"]),
        content_disarm_pdf_javacode=dict(required=False, type="str", choices=["disable", "enable"]),
        ftp=dict(required=False, type="list"),
        ftp_archive_block=dict(required=False, type="str", choices=["encrypted",
                                                                    "corrupted",
                                                                    "multipart",
                                                                    "nested",
                                                                    "mailbomb",
                                                                    "unhandled",
                                                                    "partiallycorrupted",
                                                                    "fileslimit",
                                                                    "timeout"]),
        ftp_archive_log=dict(required=False, type="str", choices=["encrypted",
                                                                  "corrupted",
                                                                  "multipart",
                                                                  "nested",
                                                                  "mailbomb",
                                                                  "unhandled",
                                                                  "partiallycorrupted",
                                                                  "fileslimit",
                                                                  "timeout"]),
        ftp_emulator=dict(required=False, type="str", choices=["disable", "enable"]),
        ftp_options=dict(required=False, type="str", choices=["scan", "quarantine", "avmonitor"]),
        ftp_outbreak_prevention=dict(required=False, type="str", choices=["disabled", "files", "full-archive"]),
        http=dict(required=False, type="list"),
        http_archive_block=dict(required=False, type="str", choices=["encrypted",
                                                                     "corrupted",
                                                                     "multipart",
                                                                     "nested",
                                                                     "mailbomb",
                                                                     "unhandled",
                                                                     "partiallycorrupted",
                                                                     "fileslimit",
                                                                     "timeout"]),
        http_archive_log=dict(required=False, type="str", choices=["encrypted",
                                                                   "corrupted",
                                                                   "multipart",
                                                                   "nested",
                                                                   "mailbomb",
                                                                   "unhandled",
                                                                   "partiallycorrupted",
                                                                   "fileslimit",
                                                                   "timeout"]),
        http_content_disarm=dict(required=False, type="str", choices=["disable", "enable"]),
        http_emulator=dict(required=False, type="str", choices=["disable", "enable"]),
        http_options=dict(required=False, type="str", choices=["scan", "quarantine", "avmonitor"]),
        http_outbreak_prevention=dict(required=False, type="str", choices=["disabled", "files", "full-archive"]),
        imap=dict(required=False, type="list"),
        imap_archive_block=dict(required=False, type="str", choices=["encrypted",
                                                                     "corrupted",
                                                                     "multipart",
                                                                     "nested",
                                                                     "mailbomb",
                                                                     "unhandled",
                                                                     "partiallycorrupted",
                                                                     "fileslimit",
                                                                     "timeout"]),
        imap_archive_log=dict(required=False, type="str", choices=["encrypted",
                                                                   "corrupted",
                                                                   "multipart",
                                                                   "nested",
                                                                   "mailbomb",
                                                                   "unhandled",
                                                                   "partiallycorrupted",
                                                                   "fileslimit",
                                                                   "timeout"]),
        imap_content_disarm=dict(required=False, type="str", choices=["disable", "enable"]),
        imap_emulator=dict(required=False, type="str", choices=["disable", "enable"]),
        imap_executables=dict(required=False, type="str", choices=["default", "virus"]),
        imap_options=dict(required=False, type="str", choices=["scan", "quarantine", "avmonitor"]),
        imap_outbreak_prevention=dict(required=False, type="str", choices=["disabled", "files", "full-archive"]),
        mapi=dict(required=False, type="list"),
        mapi_archive_block=dict(required=False, type="str", choices=["encrypted",
                                                                     "corrupted",
                                                                     "multipart",
                                                                     "nested",
                                                                     "mailbomb",
                                                                     "unhandled",
                                                                     "partiallycorrupted",
                                                                     "fileslimit",
                                                                     "timeout"]),
        mapi_archive_log=dict(required=False, type="str", choices=["encrypted",
                                                                   "corrupted",
                                                                   "multipart",
                                                                   "nested",
                                                                   "mailbomb",
                                                                   "unhandled",
                                                                   "partiallycorrupted",
                                                                   "fileslimit",
                                                                   "timeout"]),
        mapi_emulator=dict(required=False, type="str", choices=["disable", "enable"]),
        mapi_executables=dict(required=False, type="str", choices=["default", "virus"]),
        mapi_options=dict(required=False, type="str", choices=["scan", "quarantine", "avmonitor"]),
        mapi_outbreak_prevention=dict(required=False, type="str", choices=["disabled", "files", "full-archive"]),
        nac_quar=dict(required=False, type="list"),
        nac_quar_expiry=dict(required=False, type="str"),
        nac_quar_infected=dict(required=False, type="str", choices=["none", "quar-src-ip"]),
        nac_quar_log=dict(required=False, type="str", choices=["disable", "enable"]),
        nntp=dict(required=False, type="list"),
        nntp_archive_block=dict(required=False, type="str", choices=["encrypted",
                                                                     "corrupted",
                                                                     "multipart",
                                                                     "nested",
                                                                     "mailbomb",
                                                                     "unhandled",
                                                                     "partiallycorrupted",
                                                                     "fileslimit",
                                                                     "timeout"]),
        nntp_archive_log=dict(required=False, type="str", choices=["encrypted",
                                                                   "corrupted",
                                                                   "multipart",
                                                                   "nested",
                                                                   "mailbomb",
                                                                   "unhandled",
                                                                   "partiallycorrupted",
                                                                   "fileslimit",
                                                                   "timeout"]),
        nntp_emulator=dict(required=False, type="str", choices=["disable", "enable"]),
        nntp_options=dict(required=False, type="str", choices=["scan", "quarantine", "avmonitor"]),
        nntp_outbreak_prevention=dict(required=False, type="str", choices=["disabled", "files", "full-archive"]),
        pop3=dict(required=False, type="list"),
        pop3_archive_block=dict(required=False, type="str", choices=["encrypted",
                                                                     "corrupted",
                                                                     "multipart",
                                                                     "nested",
                                                                     "mailbomb",
                                                                     "unhandled",
                                                                     "partiallycorrupted",
                                                                     "fileslimit",
                                                                     "timeout"]),
        pop3_archive_log=dict(required=False, type="str", choices=["encrypted",
                                                                   "corrupted",
                                                                   "multipart",
                                                                   "nested",
                                                                   "mailbomb",
                                                                   "unhandled",
                                                                   "partiallycorrupted",
                                                                   "fileslimit",
                                                                   "timeout"]),
        pop3_content_disarm=dict(required=False, type="str", choices=["disable", "enable"]),
        pop3_emulator=dict(required=False, type="str", choices=["disable", "enable"]),
        pop3_executables=dict(required=False, type="str", choices=["default", "virus"]),
        pop3_options=dict(required=False, type="str", choices=["scan", "quarantine", "avmonitor"]),
        pop3_outbreak_prevention=dict(required=False, type="str", choices=["disabled", "files", "full-archive"]),
        smb=dict(required=False, type="list"),
        smb_archive_block=dict(required=False, type="str", choices=["encrypted",
                                                                    "corrupted",
                                                                    "multipart",
                                                                    "nested",
                                                                    "mailbomb",
                                                                    "unhandled",
                                                                    "partiallycorrupted",
                                                                    "fileslimit",
                                                                    "timeout"]),
        smb_archive_log=dict(required=False, type="str", choices=["encrypted",
                                                                  "corrupted",
                                                                  "multipart",
                                                                  "nested",
                                                                  "mailbomb",
                                                                  "unhandled",
                                                                  "partiallycorrupted",
                                                                  "fileslimit",
                                                                  "timeout"]),
        smb_emulator=dict(required=False, type="str", choices=["disable", "enable"]),
        smb_options=dict(required=False, type="str", choices=["scan", "quarantine", "avmonitor"]),
        smb_outbreak_prevention=dict(required=False, type="str", choices=["disabled", "files", "full-archive"]),
        smtp=dict(required=False, type="list"),
        smtp_archive_block=dict(required=False, type="str", choices=["encrypted",
                                                                     "corrupted",
                                                                     "multipart",
                                                                     "nested",
                                                                     "mailbomb",
                                                                     "unhandled",
                                                                     "partiallycorrupted",
                                                                     "fileslimit",
                                                                     "timeout"]),
        smtp_archive_log=dict(required=False, type="str", choices=["encrypted",
                                                                   "corrupted",
                                                                   "multipart",
                                                                   "nested",
                                                                   "mailbomb",
                                                                   "unhandled",
                                                                   "partiallycorrupted",
                                                                   "fileslimit",
                                                                   "timeout"]),
        smtp_content_disarm=dict(required=False, type="str", choices=["disable", "enable"]),
        smtp_emulator=dict(required=False, type="str", choices=["disable", "enable"]),
        smtp_executables=dict(required=False, type="str", choices=["default", "virus"]),
        smtp_options=dict(required=False, type="str", choices=["scan", "quarantine", "avmonitor"]),
        smtp_outbreak_prevention=dict(required=False, type="str", choices=["disabled", "files", "full-archive"]),

    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    # MODULE PARAMGRAM
    paramgram = {
        "mode": module.params["mode"],
        "adom": module.params["adom"],
        "scan-mode": module.params["scan_mode"],
        "replacemsg-group": module.params["replacemsg_group"],
        "name": module.params["name"],
        "mobile-malware-db": module.params["mobile_malware_db"],
        "inspection-mode": module.params["inspection_mode"],
        "ftgd-analytics": module.params["ftgd_analytics"],
        "extended-log": module.params["extended_log"],
        "comment": module.params["comment"],
        "av-virus-log": module.params["av_virus_log"],
        "av-block-log": module.params["av_block_log"],
        "analytics-wl-filetype": module.params["analytics_wl_filetype"],
        "analytics-max-upload": module.params["analytics_max_upload"],
        "analytics-db": module.params["analytics_db"],
        "analytics-bl-filetype": module.params["analytics_bl_filetype"],
        "content-disarm": {
            "cover-page": module.params["content_disarm_cover_page"],
            "detect-only": module.params["content_disarm_detect_only"],
            "office-embed": module.params["content_disarm_office_embed"],
            "office-hylink": module.params["content_disarm_office_hylink"],
            "office-linked": module.params["content_disarm_office_linked"],
            "office-macro": module.params["content_disarm_office_macro"],
            "original-file-destination": module.params["content_disarm_original_file_destination"],
            "pdf-act-form": module.params["content_disarm_pdf_act_form"],
            "pdf-act-gotor": module.params["content_disarm_pdf_act_gotor"],
            "pdf-act-java": module.params["content_disarm_pdf_act_java"],
            "pdf-act-launch": module.params["content_disarm_pdf_act_launch"],
            "pdf-act-movie": module.params["content_disarm_pdf_act_movie"],
            "pdf-act-sound": module.params["content_disarm_pdf_act_sound"],
            "pdf-embedfile": module.params["content_disarm_pdf_embedfile"],
            "pdf-hyperlink": module.params["content_disarm_pdf_hyperlink"],
            "pdf-javacode": module.params["content_disarm_pdf_javacode"],
        },
        "ftp": {
            "archive-block": module.params["ftp_archive_block"],
            "archive-log": module.params["ftp_archive_log"],
            "emulator": module.params["ftp_emulator"],
            "options": module.params["ftp_options"],
            "outbreak-prevention": module.params["ftp_outbreak_prevention"],
        },
        "http": {
            "archive-block": module.params["http_archive_block"],
            "archive-log": module.params["http_archive_log"],
            "content-disarm": module.params["http_content_disarm"],
            "emulator": module.params["http_emulator"],
            "options": module.params["http_options"],
            "outbreak-prevention": module.params["http_outbreak_prevention"],
        },
        "imap": {
            "archive-block": module.params["imap_archive_block"],
            "archive-log": module.params["imap_archive_log"],
            "content-disarm": module.params["imap_content_disarm"],
            "emulator": module.params["imap_emulator"],
            "executables": module.params["imap_executables"],
            "options": module.params["imap_options"],
            "outbreak-prevention": module.params["imap_outbreak_prevention"],
        },
        "mapi": {
            "archive-block": module.params["mapi_archive_block"],
            "archive-log": module.params["mapi_archive_log"],
            "emulator": module.params["mapi_emulator"],
            "executables": module.params["mapi_executables"],
            "options": module.params["mapi_options"],
            "outbreak-prevention": module.params["mapi_outbreak_prevention"],
        },
        "nac-quar": {
            "expiry": module.params["nac_quar_expiry"],
            "infected": module.params["nac_quar_infected"],
            "log": module.params["nac_quar_log"],
        },
        "nntp": {
            "archive-block": module.params["nntp_archive_block"],
            "archive-log": module.params["nntp_archive_log"],
            "emulator": module.params["nntp_emulator"],
            "options": module.params["nntp_options"],
            "outbreak-prevention": module.params["nntp_outbreak_prevention"],
        },
        "pop3": {
            "archive-block": module.params["pop3_archive_block"],
            "archive-log": module.params["pop3_archive_log"],
            "content-disarm": module.params["pop3_content_disarm"],
            "emulator": module.params["pop3_emulator"],
            "executables": module.params["pop3_executables"],
            "options": module.params["pop3_options"],
            "outbreak-prevention": module.params["pop3_outbreak_prevention"],
        },
        "smb": {
            "archive-block": module.params["smb_archive_block"],
            "archive-log": module.params["smb_archive_log"],
            "emulator": module.params["smb_emulator"],
            "options": module.params["smb_options"],
            "outbreak-prevention": module.params["smb_outbreak_prevention"],
        },
        "smtp": {
            "archive-block": module.params["smtp_archive_block"],
            "archive-log": module.params["smtp_archive_log"],
            "content-disarm": module.params["smtp_content_disarm"],
            "emulator": module.params["smtp_emulator"],
            "executables": module.params["smtp_executables"],
            "options": module.params["smtp_options"],
            "outbreak-prevention": module.params["smtp_outbreak_prevention"],
        }
    }

    module.paramgram = paramgram
    fmgr = None
    if module._socket_path:
        connection = Connection(module._socket_path)
        fmgr = FortiManagerHandler(connection, module)
        fmgr.tools = FMGRCommon()
    else:
        module.fail_json(**FAIL_SOCKET_MSG)

    list_overrides = ["content-disarm", "ftp", "http", "imap", "mapi", "nac-quar", "nntp", "pop3", "smb", "smtp"]
    paramgram = fmgr.tools.paramgram_child_list_override(list_overrides=list_overrides,
                                                         paramgram=paramgram, module=module)
    module.paramgram = paramgram

    results = DEFAULT_RESULT_OBJ

    try:
        results = fmgr_antivirus_profile_modify(fmgr, paramgram)
        fmgr.govern_response(module=module, results=results,
                             ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
