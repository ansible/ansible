Windows Ansible Module Development Walkthrough
==============================================

In this section, we will walk through developing, testing, and debugging an
Ansible Windows module.

Because Windows modules are written in Powershell and need to be run on a
Windows host, this guide differs from the usual development walkthrough guide.

What's covered in this section:

.. contents:: Topics


Windows environment setup
=========================

TODO: Add in more information on how to use Vagrant to setup a Windows host.


Windows new module development
==============================

When creating a new module there are a few things to keep in mind:

- Module code is in Powershell (.ps1) files while the documentation is contained in Python (.py) files of the same name
- Avoid using ``Write-Host/Debug/Verbose/Error`` in the module and add what needs to be returned to the ``$result`` variable
- When trying an exception use ``Fail-Json -obj $result -message "exception message here"`` instead
- Most new modules require check mode and integration tests before they are merged into the main Ansible codebase
- Avoid using try/catch statements over a large code block, rather use them for individual calls so the error message can be more descriptive
- Try and catch specific exceptions when using try/catch statements
- Avoid using PSCustomObjects unless necessary
- Look for common functions in ``./lib/ansible/module_utils/powershell/`` and use the code there instead of duplicating work. These can be imported by adding the line ``#Requires -Module *`` where * is the filename to import, and will be automatically included with the module code sent to the Windows target when run via Ansible
- Ensure the code runs under Powershell v3 and higher on Windows Server 2008 and higher; if higher minimum Powershell or OS versions are required, ensure the documentation reflects this clearly
- Ansible runs modules under strictmode version 2.0. Be sure to test with that enabled by putting ``Set-StrictMode -Version 2.0`` at the top of your dev script
- Favour native Powershell cmdlets over executable calls if possible
- If adding an object to ``$result``, ensure any trailing slashes are removed or escaped, as ``ConvertTo-Json`` will fail to convert it
- Use the full cmdlet name instead of aliases, e.g. ``Remove-Item`` over ``rm``
- Use named parameters with cmdlets, e.g. ``Remove-Item -Path C:\temp`` over ``Remove-Item C:\temp``

A very basic powershell module template can be found found below:

.. code-block:: powershell

    #!powershell
    # This file is part of Ansible

    # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

    #Requires -Module Ansible.ModuleUtils.Legacy

    $ErrorActionPreference = 'Stop'

    $params = Parse-Args -arguments $args -supports_check_mode $true
    $check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
    $diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

    # these are your module parameters, there are various types which can be
    # used to format your parameters. You can also set mandatory parameters
    # with -failifempty, set defaults with -default and set choices with
    # -validateset.
    $string = Get-AnsibleParam -obj $params -name "string" -type "str" -failifempty $true
    $bool = Get-AnsibleParam -obj $params -name "bool" -type "bool" -default $false
    $int = Get-AnsibleParam -obj $params -name "int" -type "int"
    $path = Get-AnsibleParam -obj $params -name "path" -type "path"
    $list = Get-AnsibleParam -obj $params -name "list" -type "list"
    $choices = Get-AnsibleParam -obj $params -name "choices" -type "str" -default "present" -validateset "absent","present"

    $result = @{
        changed = $false
    }

    if ($diff_mode) {
        $result.diff = @{}
    }

    # code goes here

    # you can add/set new result objects with
    $result.changed = $true
    $result.new_result = "Hi"

    Exit-Json -obj $result


When in doubt, look at some of the core modules and see how things have been
implemented there.

Sometimes there are multiple ways that Windows offers to complete a task; this
is the order to favour when writing modules:

- Native Powershell cmdlets like ``Remove-Item -Path C:\temp -Recurse``
- .NET classes like ``[System.IO.Path]::GetRandomFileName()``
- WMI objects through the ``New-CimInstance`` cmdlet
- COM objects through ``New-Object -ComObject`` cmdlet
- Calls to native executables like ``Secedit.exe``


Windows playbook module testing
===============================

To test a module you can do so with an Ansible playbook.

- Create a playbook in any directory ``touch testmodule.yml``
- Create an inventory file in the same directory ``touch hosts``
- Populate the inventory file with the variables required to connect to a Windows host(s).
- Add the following to the new playbook file::

    ---
    - name: test out windows module
      hosts: windows
      tasks:
      - name: test out module
        win_module:
          name: test name

- Run the playbook ``ansible-playbook -i hosts testmodule.yml``

This can be pretty high level and is useful for seeing how Ansible runs with
the new module end to end: but there are better ways to test out the module as
shown below.


Windows debugging
=================

Debugging a module currently can only be done on a Windows host. This is
extremely useful when developing a new module or looking at bug fixes. These
are some steps that need to be followed to set this up.

- Copy the module script to the Windows server
- Copy ``./lib/ansible/module_utils/powershell/Ansible.ModuleUtils.PowerShellLegacy.psm1`` to the same directory as the script above
- To stop the script from exiting the editor on a successful run, in ``Ansible.ModuleUtils.Legacy.psm1`` under the function ``Exit-Json``, replace the last two lines of the function with::

    ConvertTo-Json -InputObject $obj -Depth 99

- To stop the script from exiting the editor on a failed run, in ``Ansible.ModuleUtils.PowerShellLegacy.psm1`` under the function ``Fail-Json``, replace the last two lines of the function with::

    Write-Error -Message (ConvertTo-Json -InputObject $obj -Depth 99)

- Add the following to the start of the module script that was copied to the server::

    ### start setup code
    $complex_args = @{
        "_ansible_check_mode" = $false
        "_ansible_diff" = $false
        "path" = "C:\temp"
        "state" = "present"
    }

    Import-Module -Name .\Ansible.ModuleUtils.PowershellLegacy.psm1
    ### end setup code

You can add more args to ``$complex_args`` as required by the module. The
module can now be run on the Windows host either directly through Powershell
or through an IDE.

There are multiple IDEs that can be used to debug a Powershell script, two of
the most popular are

- `Powershell ISE`_
- `Visual Studio Code`_

.. _Powershell ISE: https://msdn.microsoft.com/en-us/powershell/scripting/core-powershell/ise/how-to-debug-scripts-in-windows-powershell-ise
.. _Visual Studio Code: https://blogs.technet.microsoft.com/heyscriptingguy/2017/02/06/debugging-powershell-script-in-visual-studio-code-part-1/

To be able to view the arguments as passed by Ansible to the module follow
these steps.

- Prefix the Ansible command with ``ANSIBLE_KEEP_REMOTE_FILES=1`` to get Ansible to keep the exec files on the server
- Log onto the Windows server using the same user Ansible executed the module as
- Navigate to ``%TEMP%\..``, there should be a folder starting with ``ansible-tmp-``
- Inside this folder open up the powershell script for the module
- In this script there is a raw JSON script under ``$json_raw`` which contains the module arguments under ``module_args``
- These args can be assigned manually to the ``$complex_args`` variable that is defined on your debug script


Windows unit testing
====================

Currently there is no mechanism to run unit tests for Powershell modules under Ansible CI.
There is work in the pipeline to introduce this in the future, stay tuned.


Windows integration testing
===========================

Integration tests for Ansible modules are typically written as Ansible roles. The test
roles are located in ``./test/integration/targets``. You must first set up your testing
environment, and configure a test inventory for Ansible to connect to. In this example we
will set up a test inventory to connect to two hosts and run the integration
tests for win_stat.

- Create a copy of ``./test/integration/inventory.winrm.template`` and just call it ``inventory.winrm``
- Fill in entries under ``[windows]`` and set the required vars that are needed to connect to the host
- To execute the integration tests, run ``ansible-test windows-integration win_stat``- you can replace ``win_stat`` with the role you wish to test

This will execute all the tests currently defined for that role. You can set
the verbosity level using the ``-v`` argument just as you would with
ansible-playbook.

When developing tests for a new module, it is recommended to test a scenario in
check mode and 2 times not in check mode. This ensures that check mode
does not make any changes but reports a change, as well as that the 2nd run is
idempotent and does not report changes. Following is an example of one way that this can be done:

.. code-block:: yaml

    - name: remove a file (check mode)
      win_file:
        path: C:\temp
        state: absent
      register: remove_file_check
      check_mode: yes
    
    - name: get result of remove a file (check mode)
      win_command: powershell.exe "if (Test-Path -Path 'C:\temp') { 'true' } else { 'false' }"
      register: remove_file_actual_check
    
    - name: assert remove a file (check mode)
      assert:
        that:
        - remove_file_check|changed
        - remove_file_actual_check.stdout == 'true\r\n'

    - name: remove a file
      win_file:
        path: C:\temp
        state: absent
      register: remove_file
    
    - name: get result of remove a file
      win_command: powershell.exe "if (Test-Path -Path 'C:\temp') { 'true' } else { 'false' }"
      register: remove_file_actual
    
    - name: assert remove a file
      assert:
        that:
        - remove_file|changed
        - remove_file_actual.stdout == 'false\r\n'

    - name: remove a file (idempotent)
      win_file:
        path: C:\temp
        state: absent
      register: remove_file_again
    
    - name: assert remove a file (idempotent)
      assert:
        that:
        - not remove_file_again|changed


Windows communication and development support
=============================================

Join the IRC channel ``#ansible-devel`` or ``#ansible-windows`` on freenode for
discussions surrounding Ansible development for Windows.

For questions and discussions pertaining to using the Ansible product,
use the ``#ansible`` channel.
