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

A very basic powershell module `win_environment <https://github.com/ansible/ansible/blob/devel/lib/ansible/modules/windows/win_environment.ps1>`_ is included below. It demonstrates how to implement check-mode and diff-support, and also shows a warning to the user when a specific condition is met.

.. .. include:: ../../../../lib/ansible/modules/windows/win_environment.ps1
..    :code: powershell

.. literalinclude:: ../../../../lib/ansible/modules/windows/win_environment.ps1
   :language: powershell

A slightly more advanced module is `win_uri <https://github.com/ansible/ansible/blob/devel/lib/ansible/modules/windows/win_uri.ps1>`_ which additionally shows how to use different parameter types (bool, str, int, list, dict, path) and a selection of choices for parameters, how to fail a module and how to handle exceptions.

When in doubt, look at some of the other core modules and see how things have been
implemented there.

Sometimes there are multiple ways that Windows offers to complete a task; this
is the order to favour when writing modules:

- Native Powershell cmdlets like ``Remove-Item -Path C:\temp -Recurse``
- .NET classes like ``[System.IO.Path]::GetRandomFileName()``
- WMI objects through the ``New-CimInstance`` cmdlet
- COM objects through ``New-Object -ComObject`` cmdlet
- Calls to native executables like ``Secedit.exe``

PowerShell modules support a small subset of the ``#Requires`` options built
into PowerShell as well as some Ansible-specific requirements specified by
``#AnsibleRequires``. These statements can be placed at any point in the script,
but are most commonly near the top. They are used to make it easier to state the
requirements of the module without writing any of the checks. Each ``requires``
statement must be on its own line, but there can be multiple requires statements
in one script. 

These are the checks that can be used within Ansible modules:

- ``#Requires -Module Ansible.ModuleUtils.<module_util>``: Added in Ansible 2.4, specifies a module_util to load in for the module execution.
- ``#Requires -Version x.y``: Added in Ansible 2.5, specifies the version of PowerShell that is required by the module. The module will fail if this requirement is not met.
- ``#AnsibleRequires -OSVersion x.y``: Added in Ansible 2.5, specifies the OS build version that is required by the module and will fail if this requirement is not met. The actual OS version is derived from ``[Environment]::OSVersion.Version``.
- ``#AnsibleRequires -Become``: Added in Ansible 2.5, forces the exec runner to run the module with ``become``, which is primarily used to bypass WinRM restrictions. If ``ansible_become_user`` is not specified then the ``SYSTEM`` account is used instead.


Windows module utilities
========================

Like Python modules, PowerShell modules also provide a number of module
utilities that provide helper functions within PowerShell. These module_utils
can be imported by adding the following line to a PowerShell module:

.. code-block:: powershell

    #Requires -Module Ansible.ModuleUtils.Legacy

This will import the module_util at ``./lib/ansible/module_utils/powershell/Ansible.ModuleUtils.Legacy.psm1``
and enable calling all of its functions. 

The following is a list of module_utils that are packaged with Ansible and a general description of what
they do:

- ArgvParser: Utiliy used to convert a list of arguments to an escaped string compliant with the Windows argument parsing rules.
- CamelConversion: Utility used to convert camelCase strings/lists/dicts to snake_case.
- CommandUtil: Utility used to execute a Windows process and return the stdout/stderr and rc as separate objects.
- Legacy: General definitions and helper utilities for Ansible module.
- SID: Utilities used to convert a user or group to a Windows SID and vice versa.

For more details on any specific module utility and their requirements, please see the `Ansible 
module utilities source code <https://github.com/ansible/ansible/tree/devel/lib/ansible/module_utils/powershell>`_.

PowerShell module utilities can be stored outside of the standard Ansible
distribution for use with custom modules. Custom module_utils are placed in a
folder called ``module_utils`` located in the root folder of the playbook or role
directory.

The below example is a role structure that contains two custom module_utils
called ``Ansible.ModuleUtils.ModuleUtil1`` and
``Ansible.ModuleUtils.ModuleUtil2``::

    meta/
      main.yml
    defaults/
      main.yml
    module_utils/
      Ansible.ModuleUtils.ModuleUtil1.psm1
      Ansible.ModuleUtils.ModuleUtil2.psm1
    tasks/
      main.yml

Each module_util must contain at least one function, and a list of functions, aliases and cmdlets to export for use
in a module. This can be a blanket export by using ``*``. For example:

.. code-block:: powershell

    Export-ModuleMember -Alias * -Function * -Cmdlet *


Windows playbook module testing
===============================

You can test a module with an Ansible playbook. For example:

- Create a playbook in any directory ``touch testmodule.yml``.
- Create an inventory file in the same directory ``touch hosts``.
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

This can be useful for seeing how Ansible runs with
the new module end to end. Other possible ways to test the module are
shown below.


Windows debugging
=================

Debugging a module currently can only be done on a Windows host. This can be
useful when developing a new module or implementing bug fixes. These
are some steps that need to be followed to set this up:

- Copy the module script to the Windows server
- Copy ``./lib/ansible/module_utils/powershell/Ansible.ModuleUtils.Legacy.psm1`` to the same directory as the script above
- To stop the script from exiting the editor on a successful run, in ``Ansible.ModuleUtils.Legacy.psm1`` under the function ``Exit-Json``, replace the last two lines of the function with::

    ConvertTo-Json -InputObject $obj -Depth 99

- To stop the script from exiting the editor on a failed run, in ``Ansible.ModuleUtils.Legacy.psm1`` under the function ``Fail-Json``, replace the last two lines of the function with::

    Write-Error -Message (ConvertTo-Json -InputObject $obj -Depth 99)

- Add the following to the start of the module script that was copied to the server::

    ### start setup code
    $complex_args = @{
        "_ansible_check_mode" = $false
        "_ansible_diff" = $false
        "path" = "C:\temp"
        "state" = "present"
    }

    Import-Module -Name .\Ansible.ModuleUtils.Legacy.psm1
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

- Prefix the Ansible command with :envvar:`ANSIBLE_KEEP_REMOTE_FILES=1` to specify that Ansible should keep the exec files on the server.
- Log onto the Windows server using the same user account that Ansible used to execute the module.
- Navigate to ``%TEMP%\..``. It should contain a folder starting with ``ansible-tmp-``.
- Inside this folder, open the PowerShell script for the module.
- In this script is a raw JSON script under ``$json_raw`` which contains the module arguments under ``module_args``. These args can be assigned manually to the ``$complex_args`` variable that is defined on your debug script.


Windows unit testing
====================

Currently there is no mechanism to run unit tests for Powershell modules under Ansible CI.


Windows integration testing
===========================

Integration tests for Ansible modules are typically written as Ansible roles. These test
roles are located in ``./test/integration/targets``. You must first set up your testing
environment, and configure a test inventory for Ansible to connect to. 

In this example we will set up a test inventory to connect to two hosts and run the integration
tests for win_stat:

- Create a copy of ``./test/integration/inventory.winrm.template`` and name it ``inventory.winrm``.
- Fill in entries under ``[windows]`` and set the required variables that are needed to connect to the host.
- To execute the integration tests, run ``ansible-test windows-integration win_stat``; you can replace ``win_stat`` with the role you wish to test.

This will execute all the tests currently defined for that role. You can set
the verbosity level using the ``-v`` argument just as you would with
ansible-playbook.

When developing tests for a new module, it is recommended to test a scenario once in
check mode and twice not in check mode. This ensures that check mode
does not make any changes but reports a change, as well as that the second run is
idempotent and does not report changes. For example:

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
        - remove_file_check is changed
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
        - remove_file is changed
        - remove_file_actual.stdout == 'false\r\n'

    - name: remove a file (idempotent)
      win_file:
        path: C:\temp
        state: absent
      register: remove_file_again
    
    - name: assert remove a file (idempotent)
      assert:
        that:
        - not remove_file_again is changed


Windows communication and development support
=============================================

Join the IRC channel ``#ansible-devel`` or ``#ansible-windows`` on freenode for
discussions about Ansible development for Windows.

For questions and discussions pertaining to using the Ansible product,
use the ``#ansible`` channel.
