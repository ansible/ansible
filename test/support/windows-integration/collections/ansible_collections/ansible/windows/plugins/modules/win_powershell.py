#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r'''
---
module: win_powershell
version_added: 1.5.0
short_description: Run PowerShell scripts
description:
- Runs a PowerShell script and outputs the data in a structured format.
- Use M(ansible.windows.win_command) or M(ansible.windows.win_shell) to run a traditional PowerShell process with
  stdout, stderr, and rc results.
options:
  arguments:
    description:
    - A list of arguments to pass to I(executable) when running a script in another PowerShell process.
    - These are not arguments to pass to I(script), use I(parameters) for that purpose.
    type: list
    elements: str
  chdir:
    description:
    - The PowerShell location to set when starting the script.
    - This can be a location in any of the PowerShell providers.
    - The default location is dependent on many factors, if relative paths are used then set this option.
    type: str
  creates:
    description:
    - A path or path filter pattern; when the referenced path exists on the target host, the task will be skipped.
    type: str
  depth:
    description:
    - How deep the return values are serialized for C(result), C(output), and C(information[x].message_data).
    - This also controls the depth of the diff output set by C($Ansible.Diff).
    - Setting this to a higher value can dramatically increase the amount of data that needs to be returned.
    default: 2
    type: int
  error_action:
    description:
    - The C($ErrorActionPreference) to set before executing I(script).
    - C(silently_continue) will ignore any errors and exceptions raised.
    - C(continue) is the default behaviour in PowerShell, errors are present in the I(error) return value but only
      terminating exceptions will stop the script from continuing and set it as failed.
    - C(stop) will treat errors like exceptions, will stop the script and set it as failed.
    choices:
    - silently_continue
    - continue
    - stop
    default: continue
    type: str
  executable:
    description:
    - A custom PowerShell executable to run the script in.
    - When not defined the script will run in the current module PowerShell interpreter.
    - Both the remote PowerShell and the one specified by I(executable) must be running on PowerShell v5.1 or newer.
    - Setting this value may change the values returned in the C(output) return value depending on the underlying .NET
      type.
    type: str
  parameters:
    description:
    - Parameters to pass into the script as key value pairs.
    - The key corresponds to the parameter name and the value is the value for that parameter.
    type: dict
  path:
    description:
    - The path to a PowerShell script to run.
    - When O(remote_src=False), or unset, this path is searched on the Ansible host.
    - When O(remote_src=True), or set, this path is searched on the target host.
    - This option is mutually exclusive with O(script).
    - Scripts are expected to be saved with UTF-8 encoding, using a different encoding will result in non-ASCII
      characters being read as invalid characters.
    type: str
    version_added: 3.1.0
  remote_src:
    description:
    - When V(false), the O(path) specified will be searched on the Ansible host.
    - When V(true), the O(path) specified will be searched on the target host.
    default: false
    type: bool
    version_added: 3.1.0
  removes:
    description:
    - A path or path filter pattern; when the referenced path B(does not) exist on the target host, the task will be
      skipped.
    type: str
  script:
    description:
    - The PowerShell script to run.
    - This option is mutually exclusive with O(path).
    type: str
  sensitive_parameters:
    description:
    - Parameters to pass into the script as a SecureString or PSCredential.
    - Each sensitive value will be marked with C(no_log) to ensure they are
      not exposed in the module invocation args logs.
    - The I(value) suboption can be used to create a SecureString value while
      I(username) and I(password) can be used to create a PSCredential value.
    type: list
    elements: dict
    suboptions:
      name:
        description:
        - The name of the parameter to pass this value to.
        required: true
        type: str
      value:
        description:
        - The string to pass as a SecureString of the parameter specified by
          I(name).
        - This is mutually exclusive with I(username) and I(password).
        type: str
      username:
        description:
        - The C(UserName) for the PSCredential value.
        - This is mutually exclusive with I(value).
        - This value is B(NOT) added to the C(no_log) list.
        type: str
      password:
        description:
        - The C(Password) for the PSCredential value.
        - This is mutually exclusive with I(value) and must be set when
          I(username) is provided.
        type: str
seealso:
- module: ansible.windows.win_command
- module: ansible.windows.win_shell
notes:
- The module is set as failed when a terminating exception is throw, or C(error_action=stop) and a normal error record
  is raised.
- The output values are processed using a custom filter and while it mostly matches the C(ConvertTo-Json) result the
  following value types are different.
- C(DateTime) will be an ISO 8601 string in UTC, C(DateTimeOffset) will have the offset as specified by the value.
- C(Enum) will contain a dictionary with C(Type), C(String), C(Value) being the type name, string representation and
  raw integer value respectively.
- C(Type) will contain a dictionary with C(Name), C(FullName), C(AssemblyQualifiedName), C(BaseType) being the type
  name, the type name including the namespace, the full assembly name the type was defined in and the base type it
  derives from.
- The script has access to the C($Ansible) variable where it can set C(Result), C(Changed), C(Failed), C(Diff),
  or access C(Tmpdir).
- C($Ansible.Result) is a value that is returned back to the controller as is.
- C($Ansible.Diff) was added in the C(1.12.0) release of C(ansible.windows) and is a dictionary that is set to the diff
  result that can be interepreted by Ansible.
- C($Ansible.Changed) can be set to C(true) or C(false) to reflect whether the module made a change or not. By default
  this is set to C(true).
- C($Ansible.Failed) can be set to C(true) if the script wants to return the failure back to the controller.
- C($Ansible.Tmpdir) is the path to a temporary directory to use as a scratch location that is cleaned up after the
  module has finished.
- C($Ansible.Verbosity) reveals Ansible's verbosity level for this play. Allows the script to set VerbosePreference/DebugPreference
  based on verbosity. Added in C(1.9.0).
- Any host/console direct output like C(Write-Host) or C([Console]::WriteLine) is not considered an output object, they are
  returned as a string in I(host_out) and I(host_err).
- Any output stream object is instead returned as a list in I(output). This is true not only for C(Write-Output) and its
  built-in alias C(echo), but also for implicit output; i.e. C(Write-Output "foo") and C("foo") give the same result.
- The module will skip running the script when in check mode unless the script defines
  C([CmdletBinding(SupportsShouldProcess)]).
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: Run basic PowerShell script
  ansible.windows.win_powershell:
    script: |
      echo "Hello World"

- name: Run script located in the adjacent files directory
  ansible.windows.win_powershell:
    path: my-script.ps1

- name: Run script located on the target Windows host
  ansible.windows.win_powershell:
    path: C:\temp\my-script.ps1
    remote_src: true

- name: Run PowerShell script with parameters
  ansible.windows.win_powershell:
    script: |
      [CmdletBinding()]
      param (
          [String]
          $Path,

          [Switch]
          $Force
      )

      New-Item -Path $Path -ItemType Directory -Force:$Force
    parameters:
      Path: C:\temp
      Force: true

- name: Run PowerShell script that modifies the module changed result
  ansible.windows.win_powershell:
    script: |
      if (Get-Service -Name test -ErrorAction SilentlyContinue) {
          Remove-Service -Name test
      }
      else {
          $Ansible.Changed = $false
      }

- name: Run PowerShell script in PowerShell 7
  ansible.windows.win_powershell:
    script: |
      $PSVersionTable.PSVersion.Major
    executable: pwsh.exe
    arguments:
      - -ExecutionPolicy
      - ByPass
  register: pwsh_output
  failed_when:
    - pwsh_output.output[0] != 7

- name: Run code in check mode
  ansible.windows.win_powershell:
    script: |
      [CmdletBinding(SupportsShouldProcess)]
      param ()

      # Use $Ansible to detect check mode
      if ($Ansible.CheckMode) {
          echo 'running in check mode'
      }
      else {
          echo 'running in normal mode'
      }

      # Use builtin ShouldProcess (-WhatIf)
      if ($PSCmdlet.ShouldProcess('target')) {
          echo 'also running in normal mode'
      }
      else {
          echo 'also running in check mode'
      }
  check_mode: true

- name: Create a file in a specific directory using chdir
  ansible.windows.win_powershell:
    script: |
      New-Item -Path 'created_by_ansible.txt' -ItemType File -Force
    chdir: 'C:\Temp'

- name: Return a failure back to Ansible
  ansible.windows.win_powershell:
    script: |
      if (Test-Path C:\bad.file) {
          $Ansible.Failed = $true
      }

- name: Define when the script made a change or not
  ansible.windows.win_powershell:
    script: |
      if ((Get-Item WSMan:\localhost\Service\Auth\Basic).Value -eq 'true') {
          Set-Item WSMan:\localhost\Service\Auth\Basic -Value false
      }
      else {
          $Ansible.Changed = $true
      }

- name: Define when to enable Verbose/Debug output
  ansible.windows.win_powershell:
    script: |
      if ($Ansible.Verbosity -ge 3) {
          $VerbosePreference = "Continue"
      }
      if ($Ansible.Verbosity -eq 5) {
          $DebugPreference = "Continue"
      }
      Write-Output "Hello World!"
      Write-Verbose "Hello World!"
      Write-Debug "Hello World!"

- name: Set sensitive parameter value as SecureString parameter
  ansible.windows.win_powershell:
    script: |
      param(
          [string]$Uri,
          [SecureString]$Token
      )

      Invoke-WebRequest -Uri $Uri -Token $Token
    parameters:
      Uri: foo
    sensitive_parameters:
      - name: Token
        value: '{{ sensitive_value }}'

- name: Set credential parameter
  ansible.windows.win_powershell:
    script: |
      param(
          [string]$Uri,
          [PSCredential]$Credential
      )

      Invoke-WebRequest -Uri $Uri -Credential $Credential
    parameters:
      Uri: foo
    sensitive_parameters:
      - name: Credential
        username: CredUserName
        password: '{{ sensitive_value }}'
'''

RETURN = r'''
result:
  description:
  - The values that were set by C($Ansible.Result) in the script.
  - Defaults to an empty dict but can be set to anything by the script.
  returned: always
  type: complex
  sample: {'key': 'value', 'other key': 1}
  contains: {}  # Satisfy the validate-modules sanity check
host_out:
  description:
  - The strings written to the host output, typically the stdout.
  - This is not the same as objects sent to the output stream in PowerShell.
  returned: always
  type: str
  sample: "Line 1\nLine 2"
host_err:
  description:
  - The strings written to the host error output, typically the stderr.
  - This is not the same as objects sent to the error stream in PowerShell.
  returned: always
  type: str
  sample: "Error 1\nError 2"
output:
  description:
  - A list containing all the objects outputted by the script.
  - The list elements can be anything as it is based on what was ran.
  returned: always
  type: list
  sample: ['output 1', 2, ['inner list'], {'key': 'value'}, None]
error:
  description:
  - A list of error records created by the script.
  returned: always
  type: list
  elements: dict
  contains:
    output:
      description:
      - The formatted error record message as typically seen in a PowerShell console.
      type: str
      returned: always
      sample: |
        Write-Error "error" : error
            + CategoryInfo          : NotSpecified: (:) [Write-Error], WriteErrorException
            + FullyQualifiedErrorId : Microsoft.PowerShell.Commands.WriteErrorException
    error_details:
      description:
      - Additional details about an ErrorRecord.
      - Can be null if there are not additional details.
      type: dict
      contains:
        message:
          description:
          - Message for the error record.
          returned: always
          type: str
          sample: Specific error message
        recommended_action:
          description:
          - Recommended action in the even that this error occurs.
          - This is empty unless the code which generates the error adds this explicitly.
          returned: always
          type: str
          sample: Delete file
    exception:
      description:
      - Details about the exception behind the error record.
      type: dict
      contains:
        message:
          description:
          - The exception message.
          type: str
          returned: always
          sample: The method ran into an error
        type:
          description:
          - The full .NET type of the Exception class.
          type: str
          returned: always
          sample: System.Exception
        help_link:
          description:
          - A link to the help details for the exception.
          - May not be set as it's dependent on whether the .NET exception class provides this info.
          type: str
          returned: always
          sample: http://docs.ansible.com/
        source:
          description:
          - Name of the application or object that causes the error.
          - This may be an empty string as it's dependent on the code that raises the exception.
          type: str
          returned: always
          sample: C:\Windows
        hresult:
          description:
          - The signed integer assigned to this exception.
          - May not be set as it's dependent on whether the .NET exception class provides this info.
          type: int
          returned: always
          sample: -1
        inner_exception:
          description:
          - The inner exception details if there is one present.
          - The dict contains the same keys as a normal exception.
          returned: always
          type: dict
    target_object:
      description:
      - The object which the error occured.
      - May be null if no object was specified when the record was created.
      - Type type of this object depends on the error record itself.
      - If the value is a complex type, it will follow the C(depth) limit specified.
      type: raw
      returned: always
      sample: C:\Windows
    category_info:
      description:
      - More information about the error record.
      type: dict
      contains:
        category:
          description:
          - The category name of the error record.
          type: str
          returned: always
          sample: NotSpecified
        category_id:
          description:
          - The integer representation of the category.
          type: int
          returned: always
          sample: 0
        activity:
          description:
          - Description of the operation which encountered the error.
          type: str
          returned: always
          sample: Write-Error
        reason:
          description:
          - Description of the error.
          type: str
          returned: always
          sample: WriteErrorException
        target_name:
          description:
          - Description of the target object.
          - Can be an empty string if no target was specified.
          type: str
          returned: always
          sample: C:\Windows
        target_type:
          description:
          - Description of the type of the target object.
          - Can be an empty string if no target object was specified.
          type: str
          returned: always
          sample: String
    fully_qualified_error_id:
      description:
      - The unique identifier for the error condition
      - May be null if no id was specified when the record was created.
      type: str
      returned: always
      sample: ParameterBindingFailed
    script_stack_trace:
      description:
      - The script stack trace for the error record.
      type: str
      returned: always
      sample: 'at <ScriptBlock>, <No file>: line 1'
    pipeline_iteration_info:
      description:
      - The status of the pipeline when this record was created.
      - The values are 0 index based.
      - Each element entry represents the command index in a pipeline statement.
      - The value of each element represents the pipeline input idx in that command.
      - For Example C('C:\Windows', 'C:\temp' | Get-ChildItem | Get-Item), C([1, 2, 9]) represents an error occured
        with the 2nd output, 3rd, and 9th output of the 1st, 2nd, and 3rd command in that pipeline respectively.
      type: list
      elements: int
      returned: always
      sample: [0, 0]
warning:
  description:
  - A list of warning messages created by the script.
  - Warning messages only appear when C($WarningPreference = 'Continue').
  returned: always
  type: list
  elements: str
  sample: ['warning record']
verbose:
  description:
  - A list of warning messages created by the script.
  - Verbose messages only appear when C($VerbosePreference = 'Continue').
  returned: always
  type: list
  elements: str
  sample: ['verbose record']
debug:
  description:
  - A list of warning messages created by the script.
  - Debug messages only appear when C($DebugPreference = 'Continue').
  returned: always
  type: list
  elements: str
  sample: ['debug record']
information:
  description:
  - A list of information records created by the script.
  - The information stream was only added in PowerShell v5, older versions will always have an empty list as a value.
  returned: always
  type: list
  elements: dict
  contains:
    message_data:
      description:
      - Message data associated with the record.
      - The value here can be of any type.
      type: complex
      returned: always
      sample: information record
      contains: {}  # Satisfy the validate-modules sanity check
    source:
      description:
      - The source of the record.
      type: str
      returned: always
      sample: Write-Information
    time_generated:
      description:
      - The time the record was generated.
      - This is the time in UTC as an ISO 8601 formatted string.
      type: str
      returned: always
      sample: '2021-02-11T04:46:00.4694240Z'
    tags:
      description:
      - A list of tags associated with the record.
      type: list
      elements: str
      returned: always
      sample: ['Host']
'''
