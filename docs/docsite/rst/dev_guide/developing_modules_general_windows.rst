.. _module_dev_tutorial_sample

Ansible Module Windows Development Walkthrough
==============================================

In this section, we will walk through developing, testing, and debugging an
Ansible Windows module.

Because Windows modules are written in Powershell and needs to be run on a
Windows host, this guide differs from the usual development walkthrough guide.

What's covered in this section:

-  `Environment setup <#environment-setup>`__
-  `New module development <#new-module-development>`__
-  `Playbook module testing <#playbook-module-testing>`__
-  `Debugging (remote) <#debugging-remote>`__
-  `Unit testing <#unit-testing>`__
-  `Integration testing <#integration-testing>`__
-  `Communication and development support
   <#communication-and-development-support>`__


Environment setup
=================

TODO: Add in more information on how to use Vagrant to setup a Windows host.


New module development
======================

When creating a new module there are a few things to keep in mind of

- Documentation for the module is contained in a python file of the same name
- Avoid using ``Write-Host/Debug/Verbose/Error`` in the module and add what needs to be returned to the ``$result`` variable
- When trying an exception use ``Fail-Json -obj $result -message "exception message here"`` instead
- Most new modules require check mode and integration tests before they are merged into the main Ansible codebase
- Avoid using try/catch statements over a bit code block, rather use then for individual calls so the error message can be more descriptive
- Avoid using PSCustomObjects unless necessary
- Look for common functions at ``./lib/ansible/module_utils/powershell/`` and use the code there instead of duplicating work, these can be imported by adding the line ``#Requires -Module *`` below ``#POWERHSELL_COMMON`` where * is the filename to import

A very basic powershell module template can be found found below

::

    #!powershell
    # This file is part of Ansible

    # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

    # WANT_JSON
    # POWERSHELL_COMMON

    $ErrorActionPreference = 'Stop'

    $params = Parse-Args -arguments $args -supports_check_mode $true
    $check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
    $diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

    # these are your module parameters
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

    Exit-Json -obj $result

::

When in doubt look at some of the core modules and see how things have been
implemented there.


Playbook module testing
=======================

To test a module you can do so with an Ansible playbook.

- Create a playbook in any directory ``$ touch testmodule.yml``
- Create an inventory file in the same directory ``$ touch hosts``
- Populate the inventory file with the variables required to connect to a Windows host(s).
- Add the following to the new playbook file::

    ---
    - name: test out windows module
      hosts: windows
      tasks:
      - name: test out module
        win_module:
          name: test name

- Run the playbook ``$ ansible-playbook -i hosts testmodule.yml``

This can be pretty high level and is useful for seeing how Ansible runs with
the new module end to end but there are better ways to test out the module as
shown below.


Debugging (remote)
==================

Debugging a module currently can only be done on a remote Windows host. This is
extemely useful when developing a new module or looking at bug fixes. These are
some steps that need to be followed to set this up.

- Copy the module script to the Windows server
- Copy ``./lib/ansible/module_utils/powershell/Ansible.ModuleUtils.PowerShellLegacy.psm1`` to the same directory as the script above
- To stop the script from exiting the editor on a successful run, in ``Ansible.ModuleUtils.PowerShellLegacy.psm1`` under the function ``Exit-Json``, replace the last two lines of the function with::

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
module can now be run on the remote server either directly through Powershell
or through an IDE.

There are multiple IDE's that can be used to debug a Powershell script, two of
the most popular are

- `Powershell ISE`_
- `Visual Studio Code`_

.. _Powershell ISE: https://msdn.microsoft.com/en-us/powershell/scripting/core-powershell/ise/how-to-debug-scripts-in-windows-powershell-ise
.. _Visual Studio Code: https://blogs.technet.microsoft.com/heyscriptingguy/2017/02/06/debugging-powershell-script-in-visual-studio-code-part-1/

To be able to view the arguments as passed by Ansible to the module follow
these steps.

- Before executing the Ansible command run ``$ export ANSIBLE_KEEP_REMOTE_FILES=1`` to get Ansible to keep the exec files on the server
- Run the Ansible command
- Run ``$ export ANSIBLE_KEEP_REMOTE_FILES=0`` to stop Ansible from filling up the temp space on the server
- Log onto the Windows server using the same user Ansible executed the module as
- Navigate to ``%TEMP%\..``, there should be a folder starting with ``ansible-temp-``
- Inside this folder open up the powershell script for the module
- In this script there is a raw JSON script under ``$json_raw`` which contains the module arguments under ``module_args``
- These args can be assigned manually to the ``$complex_args`` variable that is defined on your debug script


Unit testing
============

Currently there is no mechanism to develop unit tests for Powershell modules.
There is work in the pipeline to introduce this in the future, stay tuned.


Integration testing
===================

Integration tests for modules will be appropriately located in
``./test/integration/targets``. You must first set up your testing environment
and configure a test inventory for Ansible to connect to. In this example we
will setup a test inventory to connect to two hosts and run the integration
tests for win_stat.

- Create a copy of ``./test/integration/inventory.winrm.template`` and just call it ``inventory.winrm``
- Fill in entries under ``[windows]`` and set the required vars that are needed to connect to the host
- To run the integration tests run ``ansible-test windows-integration win_stat``, you can replace ``win_stat`` with the role you wish to test

This will go through all the tests currently written for that role. You can set
the verbosity level using the ``-v`` argument just as you would with
ansible-playbook.

When developing tests for a new module, it is recommended to test a scenario in
check mode and 2 times not in check mode. This ensure we test that check mode
does not make any changes but reports a change as well as the 2nd run stays
idempotent. This is an example of one way that this can be done

::

    # check mode tests for scenario
    - name: remove a file check
      win_file:
        path: C:\temp
        state: absent
      register: remove_file_check
      check_mode: yes
    
    - name: get actual of remove a file check
      win_command: powershell.exe "if (Test-Path -Path 'C:\temp') { 'true' } else { 'false' }"
      register: remove_file_actual_check
    
    - name: assert remove a file check
      assert:
        that:
        - remove_file_check|changed
        - remove_file_actual_check.stdout == 'true\r\n'

    # actual tests for scenario
    - name: remove a file
      win_file:
        path: C:\temp
        state: absent
      register: remove_file
    
    - name: get actual of remove a file
      win_command: powershell.exe "if (Test-Path -Path 'C:\temp') { 'true' } else { 'false' }"
      register: remove_file_actual
    
    - name: assert remove a file
      assert:
        that:
        - remove_file|changed
        - remove_file_actual.stdout == 'false\r\n'

    # idempotency checks for scenario
    - name: remove a file again
      win_file:
        path: C:\temp
        state: absent
      register: remove_file_again
    
    - name: assert remove a file again
      assert:
        that:
        - not remove_file_again|changed

::


Communication and development support
=====================================

Join the IRC channel ``#ansible-devel`` or ``#ansible-windows`` on freenode for
discussions surrounding Ansible development for Windows.

For questions and discussions pertaining to using the Ansible product,
use the ``#ansible`` channel.
