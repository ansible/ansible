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

  host:
    description:
      - The FortiManager's Address.
    required: true

  password:
    description:
      - The password associated with the username account.
    required: true

  username:
    description:
      - The username associated with the account.
    required: true

  mode:
    description:
      - Sets one of three modes for managing the object.
      - Mutually Exclusive with STATE parameter.
      - Allows use of soft-adds instead of overwriting existing values
    choices: ['add', 'set', 'delete', 'update']
    default: add

  scan_mode:
    type: str
    description:
      - Choose between full scan mode and quick scan mode.
      - choice | quick | Use quick mode scanning. Quick mode uses a smaller database and may be less accurate.
      - choice | full | Full mode virus scanning. More accurate than quick mode with similar performance.
    required: false
    choices: ["quick", "full"]

  replacemsg_group:
    type: dict
    description:
      - Replacement message group customized for this profile.
    required: false

  name:
    type: str
    description:
      - Profile name.
    required: false

  mobile_malware_db:
    type: str
    description:
      - Enable/disable using the mobile malware signature database.
      - choice | disable | Do not use the mobile malware signature database.
      - choice | enable | Also use the mobile malware signature database.
    required: false
    choices: ["disable", "enable"]

  inspection_mode:
    type: str
    description:
      - Inspection mode.
      - choice | proxy | Proxy-based inspection.
      - choice | flow-based | Flow-based inspection.
    required: false
    choices: ["proxy", "flow-based"]

  ftgd_analytics:
    type: str
    description:
      - Settings to control which files are uploaded to FortiSandbox.
      - choice | disable | Do not upload files to FortiSandbox.
      - choice | suspicious | Submit files supported by FortiSandbox
      - choice | everything | Submit all files scanned by AntiVirus to FortiSandbox. AntiVirus may not scan all files.
    required: false
    choices: ["disable", "suspicious", "everything"]

  extended_log:
    type: str
    description:
      - Enable/disable extended logging for antivirus.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  comment:
    type: str
    description:
      - Comment.
    required: false

  av_virus_log:
    type: str
    description:
      - Enable/disable AntiVirus logging.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  av_block_log:
    type: str
    description:
      - Enable/disable logging for AntiVirus file blocking.
      - choice | disable | Disable setting.
      - choice | enable | Enable setting.
    required: false
    choices: ["disable", "enable"]

  analytics_wl_filetype:
    type: dict
    description:
      - Do not submit files matching this DLP file-pattern to FortiSandbox.
    required: false

  analytics_max_upload:
    type: int
    description:
      - Maximum size of files that can be uploaded to FortiSandbox (1 - 395 MBytes, default = 10).
    required: false

  analytics_db:
    type: str
    description:
      - Enable/disable using the FortiSandbox signature database to supplement the AV signature databases.
      - choice | disable | Use only the standard AV signature databases.
      - choice | enable | Also use the FortiSandbox signature database.
    required: false
    choices: ["disable", "enable"]

  analytics_bl_filetype:
    type: dict
    description:
      - Only submit files matching this DLP file-pattern to FortiSandbox.
    required: false

  content_disarm_cover_page:
    type: str
    description:
      - Enable/disable inserting a cover page into the disarmed document.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  content_disarm_detect_only:
    type: str
    description:
      - Enable/disable only detect disarmable files, do not alter content.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  content_disarm_office_embed:
    type: str
    description:
      - Enable/disable stripping of embedded objects in Microsoft Office documents.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  content_disarm_office_hylink:
    type: str
    description:
      - Enable/disable stripping of hyperlinks in Microsoft Office documents.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  content_disarm_office_linked:
    type: str
    description:
      - Enable/disable stripping of linked objects in Microsoft Office documents.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  content_disarm_office_macro:
    type: str
    description:
      - Enable/disable stripping of macros in Microsoft Office documents.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  content_disarm_original_file_destination:
    type: str
    description:
      - Destination to send original file if active content is removed.
      - choice | fortisandbox | Send original file to configured FortiSandbox.
      - choice | quarantine | Send original file to quarantine.
      - choice | discard | Original file will be discarded after content disarm.
    required: false
    choices: ["fortisandbox", "quarantine", "discard"]

  content_disarm_pdf_act_form:
    type: str
    description:
      - Enable/disable stripping of actions that submit data to other targets in PDF documents.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  content_disarm_pdf_act_gotor:
    type: str
    description:
      - Enable/disable stripping of links to other PDFs in PDF documents.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  content_disarm_pdf_act_java:
    type: str
    description:
      - Enable/disable stripping of actions that execute JavaScript code in PDF documents.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  content_disarm_pdf_act_launch:
    type: str
    description:
      - Enable/disable stripping of links to external applications in PDF documents.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  content_disarm_pdf_act_movie:
    type: str
    description:
      - Enable/disable stripping of embedded movies in PDF documents.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  content_disarm_pdf_act_sound:
    type: str
    description:
      - Enable/disable stripping of embedded sound files in PDF documents.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  content_disarm_pdf_embedfile:
    type: str
    description:
      - Enable/disable stripping of embedded files in PDF documents.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  content_disarm_pdf_hyperlink:
    type: str
    description:
      - Enable/disable stripping of hyperlinks from PDF documents.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  content_disarm_pdf_javacode:
    type: str
    description:
      - Enable/disable stripping of JavaScript code in PDF documents.
      - choice | disable | Disable this Content Disarm and Reconstruction feature.
      - choice | enable | Enable this Content Disarm and Reconstruction feature.
    required: false
    choices: ["disable", "enable"]

  ftp_archive_block:
    type: str
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Block encrypted archives.
      - flag | corrupted | Block corrupted archives.
      - flag | multipart | Block multipart archives.
      - flag | nested | Block nested archives.
      - flag | mailbomb | Block mail bomb archives.
      - flag | unhandled | Block archives that FortiOS cannot open.
      - flag | partiallycorrupted | Block partially corrupted archives.
      - flag | fileslimit | Block exceeded archive files limit.
      - flag | timeout | Block scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  ftp_archive_log:
    type: str
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Log encrypted archives.
      - flag | corrupted | Log corrupted archives.
      - flag | multipart | Log multipart archives.
      - flag | nested | Log nested archives.
      - flag | mailbomb | Log mail bomb archives.
      - flag | unhandled | Log archives that FortiOS cannot open.
      - flag | partiallycorrupted | Log partially corrupted archives.
      - flag | fileslimit | Log exceeded archive files limit.
      - flag | timeout | Log scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  ftp_emulator:
    type: str
    description:
      - Enable/disable the virus emulator.
      - choice | disable | Disable the virus emulator.
      - choice | enable | Enable the virus emulator.
    required: false
    choices: ["disable", "enable"]

  ftp_options:
    type: str
    description:
      - Enable/disable FTP AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
      - flag | scan | Enable FTP antivirus scanning.
      - flag | quarantine | Enable FTP antivirus quarantine. Files are quarantined depending on quarantine settings.
      - flag | avmonitor | Enable FTP antivirus logging.
    required: false
    choices: ["scan", "quarantine", "avmonitor"]

  ftp_outbreak_prevention:
    type: str
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
      - choice | disabled | Disabled.
      - choice | files | Analyze files as sent, not the content of archives.
      - choice | full-archive | Analyze files including the content of archives.
    required: false
    choices: ["disabled", "files", "full-archive"]

  http_archive_block:
    type: str
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Block encrypted archives.
      - flag | corrupted | Block corrupted archives.
      - flag | multipart | Block multipart archives.
      - flag | nested | Block nested archives.
      - flag | mailbomb | Block mail bomb archives.
      - flag | unhandled | Block archives that FortiOS cannot open.
      - flag | partiallycorrupted | Block partially corrupted archives.
      - flag | fileslimit | Block exceeded archive files limit.
      - flag | timeout | Block scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  http_archive_log:
    type: str
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Log encrypted archives.
      - flag | corrupted | Log corrupted archives.
      - flag | multipart | Log multipart archives.
      - flag | nested | Log nested archives.
      - flag | mailbomb | Log mail bomb archives.
      - flag | unhandled | Log archives that FortiOS cannot open.
      - flag | partiallycorrupted | Log partially corrupted archives.
      - flag | fileslimit | Log exceeded archive files limit.
      - flag | timeout | Log scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  http_content_disarm:
    type: str
    description:
      - Enable Content Disarm and Reconstruction for this protocol.
      - choice | disable | Disable Content Disarm and Reconstruction for this protocol.
      - choice | enable | Enable Content Disarm and Reconstruction for this protocol.
    required: false
    choices: ["disable", "enable"]

  http_emulator:
    type: str
    description:
      - Enable/disable the virus emulator.
      - choice | disable | Disable the virus emulator.
      - choice | enable | Enable the virus emulator.
    required: false
    choices: ["disable", "enable"]

  http_options:
    type: str
    description:
      - Enable/disable HTTP AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
      - flag | scan | Enable HTTP antivirus scanning.
      - flag | quarantine | Enable HTTP antivirus quarantine. Files are quarantined depending on quarantine settings.
      - flag | avmonitor | Enable HTTP antivirus logging.
    required: false
    choices: ["scan", "quarantine", "avmonitor"]

  http_outbreak_prevention:
    type: str
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
      - choice | disabled | Disabled.
      - choice | files | Analyze files as sent, not the content of archives.
      - choice | full-archive | Analyze files including the content of archives.
    required: false
    choices: ["disabled", "files", "full-archive"]

  imap_archive_block:
    type: str
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Block encrypted archives.
      - flag | corrupted | Block corrupted archives.
      - flag | multipart | Block multipart archives.
      - flag | nested | Block nested archives.
      - flag | mailbomb | Block mail bomb archives.
      - flag | unhandled | Block archives that FortiOS cannot open.
      - flag | partiallycorrupted | Block partially corrupted archives.
      - flag | fileslimit | Block exceeded archive files limit.
      - flag | timeout | Block scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  imap_archive_log:
    type: str
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Log encrypted archives.
      - flag | corrupted | Log corrupted archives.
      - flag | multipart | Log multipart archives.
      - flag | nested | Log nested archives.
      - flag | mailbomb | Log mail bomb archives.
      - flag | unhandled | Log archives that FortiOS cannot open.
      - flag | partiallycorrupted | Log partially corrupted archives.
      - flag | fileslimit | Log exceeded archive files limit.
      - flag | timeout | Log scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  imap_content_disarm:
    type: str
    description:
      - Enable Content Disarm and Reconstruction for this protocol.
      - choice | disable | Disable Content Disarm and Reconstruction for this protocol.
      - choice | enable | Enable Content Disarm and Reconstruction for this protocol.
    required: false
    choices: ["disable", "enable"]

  imap_emulator:
    type: str
    description:
      - Enable/disable the virus emulator.
      - choice | disable | Disable the virus emulator.
      - choice | enable | Enable the virus emulator.
    required: false
    choices: ["disable", "enable"]

  imap_executables:
    type: str
    description:
      - Treat Windows executable files as viruses for the purpose of blocking or monitoring.
      - choice | default | Perform standard AntiVirus scanning of Windows executable files.
      - choice | virus | Treat Windows executables as viruses.
    required: false
    choices: ["default", "virus"]

  imap_options:
    type: str
    description:
      - Enable/disable IMAP AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
      - flag | scan | Enable IMAP antivirus scanning.
      - flag | quarantine | Enable IMAP antivirus quarantine. Files are quarantined depending on quarantine settings.
      - flag | avmonitor | Enable IMAP antivirus logging.
    required: false
    choices: ["scan", "quarantine", "avmonitor"]

  imap_outbreak_prevention:
    type: str
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
      - choice | disabled | Disabled.
      - choice | files | Analyze files as sent, not the content of archives.
      - choice | full-archive | Analyze files including the content of archives.
    required: false
    choices: ["disabled", "files", "full-archive"]

  mapi_archive_block:
    type: str
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Block encrypted archives.
      - flag | corrupted | Block corrupted archives.
      - flag | multipart | Block multipart archives.
      - flag | nested | Block nested archives.
      - flag | mailbomb | Block mail bomb archives.
      - flag | unhandled | Block archives that FortiOS cannot open.
      - flag | partiallycorrupted | Block partially corrupted archives.
      - flag | fileslimit | Block exceeded archive files limit.
      - flag | timeout | Block scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  mapi_archive_log:
    type: str
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Log encrypted archives.
      - flag | corrupted | Log corrupted archives.
      - flag | multipart | Log multipart archives.
      - flag | nested | Log nested archives.
      - flag | mailbomb | Log mail bomb archives.
      - flag | unhandled | Log archives that FortiOS cannot open.
      - flag | partiallycorrupted | Log partially corrupted archives.
      - flag | fileslimit | Log exceeded archive files limit.
      - flag | timeout | Log scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  mapi_emulator:
    type: str
    description:
      - Enable/disable the virus emulator.
      - choice | disable | Disable the virus emulator.
      - choice | enable | Enable the virus emulator.
    required: false
    choices: ["disable", "enable"]

  mapi_executables:
    type: str
    description:
      - Treat Windows executable files as viruses for the purpose of blocking or monitoring.
      - choice | default | Perform standard AntiVirus scanning of Windows executable files.
      - choice | virus | Treat Windows executables as viruses.
    required: false
    choices: ["default", "virus"]

  mapi_options:
    type: str
    description:
      - Enable/disable MAPI AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
      - flag | scan | Enable MAPI antivirus scanning.
      - flag | quarantine | Enable MAPI antivirus quarantine. Files are quarantined depending on quarantine settings.
      - flag | avmonitor | Enable MAPI antivirus logging.
    required: false
    choices: ["scan", "quarantine", "avmonitor"]

  mapi_outbreak_prevention:
    type: str
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
      - choice | disabled | Disabled.
      - choice | files | Analyze files as sent, not the content of archives.
      - choice | full-archive | Analyze files including the content of archives.
    required: false
    choices: ["disabled", "files", "full-archive"]

  nac_quar_expiry:
    type: str
    description:
      - Duration of quarantine.
    required: false

  nac_quar_infected:
    type: str
    description:
      - Enable/Disable quarantining infected hosts to the banned user list.
      - choice | none | Do not quarantine infected hosts.
      - choice | quar-src-ip | Quarantine all traffic from the infected hosts source IP.
    required: false
    choices: ["none", "quar-src-ip"]

  nac_quar_log:
    type: str
    description:
      - Enable/disable AntiVirus quarantine logging.
      - choice | disable | Disable AntiVirus quarantine logging.
      - choice | enable | Enable AntiVirus quarantine logging.
    required: false
    choices: ["disable", "enable"]

  nntp_archive_block:
    type: str
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Block encrypted archives.
      - flag | corrupted | Block corrupted archives.
      - flag | multipart | Block multipart archives.
      - flag | nested | Block nested archives.
      - flag | mailbomb | Block mail bomb archives.
      - flag | unhandled | Block archives that FortiOS cannot open.
      - flag | partiallycorrupted | Block partially corrupted archives.
      - flag | fileslimit | Block exceeded archive files limit.
      - flag | timeout | Block scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  nntp_archive_log:
    type: str
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Log encrypted archives.
      - flag | corrupted | Log corrupted archives.
      - flag | multipart | Log multipart archives.
      - flag | nested | Log nested archives.
      - flag | mailbomb | Log mail bomb archives.
      - flag | unhandled | Log archives that FortiOS cannot open.
      - flag | partiallycorrupted | Log partially corrupted archives.
      - flag | fileslimit | Log exceeded archive files limit.
      - flag | timeout | Log scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  nntp_emulator:
    type: str
    description:
      - Enable/disable the virus emulator.
      - choice | disable | Disable the virus emulator.
      - choice | enable | Enable the virus emulator.
    required: false
    choices: ["disable", "enable"]

  nntp_options:
    type: str
    description:
      - Enable/disable NNTP AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
      - flag | scan | Enable NNTP antivirus scanning.
      - flag | quarantine | Enable NNTP antivirus quarantine. Files are quarantined depending on quarantine settings.
      - flag | avmonitor | Enable NNTP antivirus logging.
    required: false
    choices: ["scan", "quarantine", "avmonitor"]

  nntp_outbreak_prevention:
    type: str
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
      - choice | disabled | Disabled.
      - choice | files | Analyze files as sent, not the content of archives.
      - choice | full-archive | Analyze files including the content of archives.
    required: false
    choices: ["disabled", "files", "full-archive"]

  pop3_archive_block:
    type: str
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Block encrypted archives.
      - flag | corrupted | Block corrupted archives.
      - flag | multipart | Block multipart archives.
      - flag | nested | Block nested archives.
      - flag | mailbomb | Block mail bomb archives.
      - flag | unhandled | Block archives that FortiOS cannot open.
      - flag | partiallycorrupted | Block partially corrupted archives.
      - flag | fileslimit | Block exceeded archive files limit.
      - flag | timeout | Block scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  pop3_archive_log:
    type: str
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Log encrypted archives.
      - flag | corrupted | Log corrupted archives.
      - flag | multipart | Log multipart archives.
      - flag | nested | Log nested archives.
      - flag | mailbomb | Log mail bomb archives.
      - flag | unhandled | Log archives that FortiOS cannot open.
      - flag | partiallycorrupted | Log partially corrupted archives.
      - flag | fileslimit | Log exceeded archive files limit.
      - flag | timeout | Log scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  pop3_content_disarm:
    type: str
    description:
      - Enable Content Disarm and Reconstruction for this protocol.
      - choice | disable | Disable Content Disarm and Reconstruction for this protocol.
      - choice | enable | Enable Content Disarm and Reconstruction for this protocol.
    required: false
    choices: ["disable", "enable"]

  pop3_emulator:
    type: str
    description:
      - Enable/disable the virus emulator.
      - choice | disable | Disable the virus emulator.
      - choice | enable | Enable the virus emulator.
    required: false
    choices: ["disable", "enable"]

  pop3_executables:
    type: str
    description:
      - Treat Windows executable files as viruses for the purpose of blocking or monitoring.
      - choice | default | Perform standard AntiVirus scanning of Windows executable files.
      - choice | virus | Treat Windows executables as viruses.
    required: false
    choices: ["default", "virus"]

  pop3_options:
    type: str
    description:
      - Enable/disable POP3 AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
      - flag | scan | Enable POP3 antivirus scanning.
      - flag | quarantine | Enable POP3 antivirus quarantine. Files are quarantined depending on quarantine settings.
      - flag | avmonitor | Enable POP3 antivirus logging.
    required: false
    choices: ["scan", "quarantine", "avmonitor"]

  pop3_outbreak_prevention:
    type: str
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
      - choice | disabled | Disabled.
      - choice | files | Analyze files as sent, not the content of archives.
      - choice | full-archive | Analyze files including the content of archives.
    required: false
    choices: ["disabled", "files", "full-archive"]

  smb_archive_block:
    type: str
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Block encrypted archives.
      - flag | corrupted | Block corrupted archives.
      - flag | multipart | Block multipart archives.
      - flag | nested | Block nested archives.
      - flag | mailbomb | Block mail bomb archives.
      - flag | unhandled | Block archives that FortiOS cannot open.
      - flag | partiallycorrupted | Block partially corrupted archives.
      - flag | fileslimit | Block exceeded archive files limit.
      - flag | timeout | Block scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  smb_archive_log:
    type: str
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Log encrypted archives.
      - flag | corrupted | Log corrupted archives.
      - flag | multipart | Log multipart archives.
      - flag | nested | Log nested archives.
      - flag | mailbomb | Log mail bomb archives.
      - flag | unhandled | Log archives that FortiOS cannot open.
      - flag | partiallycorrupted | Log partially corrupted archives.
      - flag | fileslimit | Log exceeded archive files limit.
      - flag | timeout | Log scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  smb_emulator:
    type: str
    description:
      - Enable/disable the virus emulator.
      - choice | disable | Disable the virus emulator.
      - choice | enable | Enable the virus emulator.
    required: false
    choices: ["disable", "enable"]

  smb_options:
    type: str
    description:
      - Enable/disable SMB AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
      - flag | scan | Enable SMB antivirus scanning.
      - flag | quarantine | Enable SMB antivirus quarantine. Files are quarantined depending on quarantine settings.
      - flag | avmonitor | Enable SMB antivirus logging.
    required: false
    choices: ["scan", "quarantine", "avmonitor"]

  smb_outbreak_prevention:
    type: str
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
      - choice | disabled | Disabled.
      - choice | files | Analyze files as sent, not the content of archives.
      - choice | full-archive | Analyze files including the content of archives.
    required: false
    choices: ["disabled", "files", "full-archive"]

  smtp_archive_block:
    type: str
    description:
      - Select the archive types to block.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Block encrypted archives.
      - flag | corrupted | Block corrupted archives.
      - flag | multipart | Block multipart archives.
      - flag | nested | Block nested archives.
      - flag | mailbomb | Block mail bomb archives.
      - flag | unhandled | Block archives that FortiOS cannot open.
      - flag | partiallycorrupted | Block partially corrupted archives.
      - flag | fileslimit | Block exceeded archive files limit.
      - flag | timeout | Block scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  smtp_archive_log:
    type: str
    description:
      - Select the archive types to log.
      - FLAG Based Options. Specify multiple in list form.
      - flag | encrypted | Log encrypted archives.
      - flag | corrupted | Log corrupted archives.
      - flag | multipart | Log multipart archives.
      - flag | nested | Log nested archives.
      - flag | mailbomb | Log mail bomb archives.
      - flag | unhandled | Log archives that FortiOS cannot open.
      - flag | partiallycorrupted | Log partially corrupted archives.
      - flag | fileslimit | Log exceeded archive files limit.
      - flag | timeout | Log scan timeout.
    required: false
    choices: ["encrypted", "corrupted", "multipart", "nested", "mailbomb", "unhandled",
    "partiallycorrupted", "fileslimit", "timeout"]

  smtp_content_disarm:
    type: str
    description:
      - Enable Content Disarm and Reconstruction for this protocol.
      - choice | disable | Disable Content Disarm and Reconstruction for this protocol.
      - choice | enable | Enable Content Disarm and Reconstruction for this protocol.
    required: false
    choices: ["disable", "enable"]

  smtp_emulator:
    type: str
    description:
      - Enable/disable the virus emulator.
      - choice | disable | Disable the virus emulator.
      - choice | enable | Enable the virus emulator.
    required: false
    choices: ["disable", "enable"]

  smtp_executables:
    type: str
    description:
      - Treat Windows executable files as viruses for the purpose of blocking or monitoring.
      - choice | default | Perform standard AntiVirus scanning of Windows executable files.
      - choice | virus | Treat Windows executables as viruses.
    required: false
    choices: ["default", "virus"]

  smtp_options:
    type: str
    description:
      - Enable/disable SMTP AntiVirus scanning, monitoring, and quarantine.
      - FLAG Based Options. Specify multiple in list form.
      - flag | scan | Enable SMTP antivirus scanning.
      - flag | quarantine | Enable SMTP antivirus quarantine. Files are quarantined depending on quarantine settings.
      - flag | avmonitor | Enable SMTP antivirus logging.
    required: false
    choices: ["scan", "quarantine", "avmonitor"]

  smtp_outbreak_prevention:
    type: str
    description:
      - Enable FortiGuard Virus Outbreak Prevention service.
      - choice | disabled | Disabled.
      - choice | files | Analyze files as sent, not the content of archives.
      - choice | full-archive | Analyze files including the content of archives.
    required: false
    choices: ["disabled", "files", "full-archive"]


'''

EXAMPLES = '''
  - name: DELETE Profile
    fmgr_secprof_av:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: "Ansible_AV_Profile"
      mode: "delete"

  - name: CREATE Profile
    fmgr_secprof_av:
      host: "{{inventory_hostname}}"
      username: "{{ username }}"
      password: "{{ password }}"
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
  type: string
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager

# check for pyFMG lib
try:
    from pyFMG.fortimgr import FortiManager
    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False

###############
# START METHODS
###############


def fmgr_antivirus_profile_addsetdelete(fmg, paramgram):
    """
    fmgr_antivirus_profile -- Manage antivirus security profiles in FMG
    """

    mode = paramgram["mode"]
    adom = paramgram["adom"]

    response = (-100000, {"msg": "Illegal or malformed paramgram discovered. System Exception"})

    # EVAL THE MODE PARAMETER FOR SET OR ADD
    if mode in ['set', 'add', 'update']:
        url = '/pm/config/adom/{adom}/obj/antivirus/profile'.format(adom=adom)
        datagram = fmgr_del_none(fmgr_prepare_dict(paramgram))

    # EVAL THE MODE PARAMETER FOR DELETE
    else:
        # SET THE CORRECT URL FOR DELETE
        url = '/pm/config/adom/{adom}/obj/antivirus/profile/{name}'.format(adom=adom, name=paramgram["name"])
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
# FUNCTION/METHOD FOR LOGGING OUT AND ANALYZING ERROR CODES
def fmgr_logout(fmg, module, msg="NULL", results=(), good_codes=(0,), logout_on_fail=True, logout_on_success=False):
    """
    THIS METHOD CONTROLS THE LOGOUT AND ERROR REPORTING AFTER AN METHOD OR FUNCTION RUNS
    """

    # VALIDATION ERROR (NO RESULTS, JUST AN EXIT)
    if msg != "NULL" and len(results) == 0:
        try:
            fmg.logout()
        except BaseException:
            pass
        module.fail_json(msg=msg)

    # SUBMISSION ERROR
    if len(results) > 0:
        if msg == "NULL":
            try:
                msg = results[1]['status']['message']
            except BaseException:
                msg = "No status message returned from pyFMG. Possible that this was a GET with a tuple result."

            if results[0] not in good_codes:
                if logout_on_fail:
                    fmg.logout()
                    module.fail_json(msg=msg, **results[1])
                else:
                    return_msg = msg + " -- LOGOUT ON FAIL IS OFF, MOVING ON"
                    # return return_msg
            else:
                if logout_on_success:
                    fmg.logout()
                    module.exit_json(msg=msg, **results[1])
                else:
                    return_msg = msg + " -- LOGOUT ON SUCCESS IS OFF, MOVING ON TO REST OF CODE"
                    # return return_msg

    else:
        return "Unexpected returned results, function failure"


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
        adom=dict(required=False, type="str", default="root"),
        host=dict(required=True, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True, required=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True, required=True),
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

        nac_quar_expiry=dict(required=False, type="str"),
        nac_quar_infected=dict(required=False, type="str", choices=["none", "quar-src-ip"]),
        nac_quar_log=dict(required=False, type="str", choices=["disable", "enable"]),

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

    module = AnsibleModule(argument_spec, supports_check_mode=False)

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

    results = fmgr_antivirus_profile_addsetdelete(fmg, paramgram)
    if results[0] != 0:
        fmgr_logout(fmg, module, results=results, good_codes=[0])

    fmg.logout()

    if results is not None:
        return module.exit_json(**results[1])
    else:
        return module.exit_json(msg="No results were returned from the API call.")


if __name__ == "__main__":
    main()
