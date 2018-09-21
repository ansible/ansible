#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_iis_webhandler
short_description: Configures a IIS HTTP Handler
description:
- Creates, removes and configures IIS HTTP Handler.
version_added: '2.8'
options:
  applicationname:
    description:
    - Specifies name of web application where you want to create or edit HTTP Handler.
      This must be used with valid site name via I(sitename) parameter.
    type: str
  allowpathinfo:
    description:
    - Specifies whether the handler processes full path information in a URI,
      such as contoso/marketing/imageGallery.aspx. If the value is true, the handler
      processes the full path, contoso/marketing/imageGallery. If the value is false,
      the handler processes only the last section of the path, /imageGallery.
    type: bool
    default: 'false'
  modules:
    description:
    - Specifies the name of the module or modules to which you want to map the file name
      or file name with extension. If you specify more than one value, separate the values with a comma ','.
    type: str
    default: 'ManagedPipelineHandler'
  name:
    description:
    - Specifies the unique name of the handler.
    type: str
    required: yes
  path:
    description:
    - Specifies the file name or the file name extension for which the handler applies.
    - For example, to process all PHP files you should use '*.php' path value.
    - Whether to use full path or just last section of the path depends on I(allowpathinfo) parameter value.
    type: str
    required: yes
  precondition:
    description:
    - Specifies conditions under which the handler will run.
    - The preCondition attribute can be one or more of the following possible values.
      If you specify more than one value, separate the values with a comma ','.
    - If no value for I(precondition) parameter specified resulted value will be NULL.
    type: str
    choices: [ bitness32, bitness64, integratedMode, ISAPIMode, runtimeVersionv1.1, runtimeVersionv2.0 ]
  requireaccess:
    description:
    - Specifies the type of access that a handler requires to the resource.
    - The requireAccess attribute can be one or more of the following possible values.
      If you specify more than one value, separate the values with a comma ','.
    type: str
    default: 'Script'
    choices: [ None, Read, Write, Script, Execute ]
  resourcetype:
    description:
    - Specifies the type of resource to which the handler applies.
    type: str
    default: 'Unspecified'
    choices: [ Directory, Either, File, Script, Unspecified ]
  responsebufferlimit:
    description:
    - Specifies the maximum size, in bytes, of the response buffer for a request handler.
    type: int
    default: '4194304'
  scriptprocessor:
    description:
    - Specifies the physical path of the ISAPI extension .dll file or
      Common Gateway Interface 'CGI' .exe file that processes the request.
    - The scriptProcessor attribute is required only for script map handler mappings.
      When you map a handler to an ISAPI extension, you must specify ISAPIModule for
      the I(modules) attribute.
      When you map a handler to a CGI file, you must specify CGIModule for the I(modules) attribute.
    type: path
  sitename:
    description:
    - Specifies name of web site where you want to create or edit HTTP Handler.
      It can be used with valid web application which name specified via I(applicationname) parameter.
    type: str
  state:
    description:
    - When C(present), creates or updates HTTP Handler.
      When C(absent), removes the HTTP Handler if it exists.
    type: str
    choices: [ absent, present ]
    default: present
  type:
    description:
    - Specifies the namespace path of a managed handler.
      The type attribute is required only for managed handlers.
      If you want to specify several values, separate the values with a comma ','.
    - Examples of managed handler types are 'System.Web.HttpForbiddenHandler'
      or 'System.Web.Script.Services.ScriptHandlerFactory'.
    type: str
  verb:
    description:
    - Specifies the HTTP verbs for which the handler mapping applies.
    - If you want to specify all verbs, use '*' character.
      If you want to specify several verbs, separate the values with a comma ',',
      .e.g. 'GET,POST'.
    type: str
    required: yes
notes:
- This must be run on a host that has the WebAdministration powershell module installed.
- Works with Windows Server 2012 and newer.
- All parameter' description and other techical information was taken from
  U(https://docs.microsoft.com/en-us/iis/configuration/system.webserver/handlers/add) article.
author:
- Andrii Bilousko (@arestarh)
'''

EXAMPLES = r'''
- name: Create http handler to process php files
  win_iis_webhandler:
    name: 'php-fastcgi'
    scriptprocessor: 'C:\ProgramData\php\php-cgi.exe'
    modules: FastCgiModule
    path: '*.php'
    verb: '*'
    state: present

- name: Adds a handler named "testHandler" to the Default Web Site
  win_iis_webhandler:
    name: testHandler
    modules: IsapiModule
    path: '*.test'
    verb: 'GET,POST'
    sitename: 'Default Web Site'
    state: present
'''

RETURN = r'''
allowpathinfo:
    description: Whether the handler process full path in URI or just last section
    returned: hanlder exists
    type: boolean
    sample: true
modules:
    description: Name of the module(s) to which the file name or file name with extension is mapped.
    returned: hanlder exists
    type: string
    sample: ManagedPipelineHandler
name:
    description: Name of the handler to create, edit or remove
    returned: always
    type: string
    sample: php-handler
path:
    description: File name or the file name extension for which the handler applies
    returned: hanlder exists
    type: string
    sample: *.py
precondition:
    description: Conditions under which the handler will run
    returned: hanlder exists
    type: string
    sample: integratedMode
requireaccess:
    description: Type of access that a handler requires to the resource
    returned: hanlder exists
    type: string
    sample: Write
resourcetype:
    description: Type of resource to which the handler applies
    returned: hanlder exists
    type: string
    sample: Directory
responsebufferlimit:
    description: Maximum size of the response buffer for handler
    returned: hanlder exists
    type: int
    sample: 4194304
scriptprocessor:
    description: Physical path to .dll or .exe file that processes the request
    returned: hanlder exists
    type: string
    sample: C:\ProgramData\php\php-cgi.exe
state:
    description: The state of the handler
    returned: always
    type: string
    sample: present
type:
    description: Namespace path of a managed handler
    returned: hanlder exists
    type: string
    sample: System.Web.Script.Services.ScriptHandlerFactory
verb:
    description: HTTP verbs for which the handler mapping applies
    returned: hanlder exists
    type: string
    sample: OPTIONS
'''
