Desired State Configuration
===========================

.. contents:: Topics

What is Desired State Configuration?
````````````````````````````````````
Desired State Configuration, or DSC, is a tool built into PowerShell that can
be used to define a Windows host setup through code. The overall purpose of DSC
is the same as Ansible, it is just executed in a different manner. Since
Ansible 2.4, the ``win_dsc`` module has been added and can be used to leverage
existing DSC resources when interacting with a Windows host.

More details on DSC can be viewed at `DSC Overview <https://docs.microsoft.com/en-us/powershell/dsc/overview>`_.

Host Requirements
`````````````````
To use the ``win_dsc`` module, a Windows host must have PowerShell v5.0 or
newer installed. All supported hosts, except for Server 2008 (non R2) can be
upgraded to PowerShell v5.

To use DSC once the PowerShell requirements have been met is as simple as
creating a task with the ``win_dsc`` module.

Why Use It?
```````````
DSC and Ansible modules have a common goal which is to define the state of a
resource and the code will ensure that resource meets that state. Because of
this resources like the `File <https://docs.microsoft.com/en-us/powershell/dsc/fileresource>`_
DSC resource and ``win_file`` can be used to achieve the same result. Why would
someone use DSC over an Ansible module? Well, it depends.

Reasons for using an Ansible module over a DSC resource are:

* The host does not support PowerShell v5.0 or it cannot easily be upgraded
* The DSC resource does not offer a feature present in an Ansible module, e.g.
  win_regedit can manage the ``REG_NONE`` property type where the DSC
  ``Registry`` resource cannot
* DSC resources have limited check mode support where some Ansible modules have
  better checks
* DSC resources do not support diff mode, where some Ansible modules do
* Custom resources require further installation steps to be run on the host
  beforehand, where Ansible modules are in built-in with Ansible
* There are bugs in a DSC resource where an Ansible module works

Reasons for using a DSC resource over an Ansible module are:

* The Ansible module does not support a feature present in a DSC resource
* There is no Ansible module available
* There are bugs in an existing module where a DSC resource works

In the end, it doesn't matter whether the task is performed with DSC or an
Ansible module, what matters is that the task is performed correctly and the
playbooks are still readable. If you have more experience with DSC over Ansible
and it does the job, just use DSC for that task.

How to use it?
``````````````
The ``win_dsc`` module takes in a free form of options so that it changes
according to the resource it is managing. A list of built in resource can be
found at `resources <https://docs.microsoft.com/en-us/powershell/dsc/resources>`_.

Using the the `Registry <https://docs.microsoft.com/en-us/powershell/dsc/registryresource>`_
resource as an example, this is the DSC definition as documented by Microsoft::

    Registry [string] #ResourceName
    {
        Key = [string]
        ValueName = [string]
        [ Ensure = [string] { Enable | Disable }  ]
        [ Force =  [bool]   ]
        [ Hex = [bool] ]
        [ DependsOn = [string[]] ]
        [ ValueData = [string[]] ]
        [ ValueType = [string] { Binary | Dword | ExpandString | MultiString | Qword | String }  ]
    }

When defining the task, ``resource_name`` must be set to the DSC resource being
used, in this case the ``resource_name`` should be set to ``Registry``. The
``module_version`` can refer to a specific version of the DSC resource
installed, if left blank it will default to the latest version. The other
options are parameters that are used to define the resource like ``Key``,
``ValueName``, etc. The options in the task are not case sensitive but,
keeping the case as is is recommended as it makes it easier to distiguish DSC
resources options with the builtin ``win_dsc`` options.

Using the same example as what is in the Microsoft documentation for the
Registry resource, this is what the Ansible task would look like::

    - name: use win_dsc module with the Registry DSC resource
      win_dsc:
        resource_name: Registry
        Ensure: Present
        Key: HKEY_LOCAL_MACHINE\SOFTWARE\ExampleKey
        ValueName: TestValue
        ValueData: TestData

Property Types
--------------
Each DSC resource property has a type that is associated with it and Ansible
will try and convert the options defined to the correct type during execution.
For simple types like ``[string]`` and ``[bool]`` this is a simple operation,
but complex types like ``[PSCredential]`` or arrays like ``[string[]]`` this
requires certain rules to be followed.

PSCredential
++++++++++++
A ``[PSCredential]`` object is used to store credentials in a secure way but
Ansible has no way to serialize this over JSON. To set a DSC property that has
the type of PSCredential, the definition of that parameter should have two
entries that are suffixed with ``_username`` and ``_password`` for the username
and password respectively. Here are some examples of setting a DSC parameter
that has the PSCredential type::

    PsDscRunAsCredential_username: '{{ansible_user}}'
    PsDscRunAsCredential_password: '{{ansible_password}}'

    SourceCredential_username: AdminUser
    SourceCredential_password: PasswordForAdminUser

.. Note:: It is recommended to use ``no_log: true`` on the task definition in
    Ansible to ensure any credentials used are not stored in any log file or
    console output.

Simple Type Arrays
++++++++++++++++++
Simple type arrays like ``[string[]]`` or ``[UInt32[]]`` are defined as a comma
separated string which are then casted to their type. This is an example of how
to defined a simple type array in Ansible::

    # [string[]]
    ValueData: entry1, entry2, entry3

    # [UInt32[]]
    ReturnCode: 0,3010

Run As Another User
-------------------
By default, DSC runs each resource as the SYSTEM account and not the account
that Ansible runs the module as. This means that resources that are dynamically
loaded based on a user profile, like the ``HKEY_CURRENT_USER`` registry hive,
will be loaded under the ``SYSTEM`` profile. The parameter 
`PsDscRunAsCredential`` is a parameter that can be set for every DSC resource
force the DSC engine to run under a different account. As
``PsDscRunAsCredential`` has a type of ``PSCredential``, it is defined with the
``_username`` and ``_password`` suffix.

Using the Registry resource type as an example, this is how to define a task
to access the ``HKEY_CURRENT_USER`` hive of the Ansible user::

    - name: use win_dsc with PsDscRunAsCredential to run as a different user
      win_dsc:
        resource_name: Registry
        Ensure: Present
        Key: HKEY_CURRENT_USER\ExampleKey
        ValueName: TestValue
        ValueData: TestData
        PsDscRunAsCredential_username: '{{ansible_user}}'
        PsDscRunAsCredential_password: '{{ansible_password}}'
      no_log: true

Custom DSC Resources
````````````````````
DSC resources are not limited to the builtin options from Microsoft and custom
modules can be installed to manage other resources not usually available.

Finding Custom DSC Resource
---------------------------
The main source to use for finding custom resources would be the
`PSGallery <https://www.powershellgallery.com/>`_. This site can then link to
further documentation or details on how to install it the resource on a Windows
host.

The ``Find-DscResource`` cmdlet can also be used to find custom resources. An
example of how to use this cmdlet is:

.. code-block:: powershell

    # find all DSC resources in the configured repositories
    Find-DscResource

    # find all DSC resources that relate to SQL
    Find-DscResource -ModuleName "*sql*"

.. Note:: DSC resources developed by Microsoft that start with ``x``, means the
    resource is experimental and comes with no support.

Installing Custom Resource
--------------------------
There are three ways that a DSC resource can be installed on a host:

* Manually with the ``Install-Module`` cmdlet
* Using the ``win_psmodule`` Ansible module
* Saving the module manually and copying it another host

This is an example of installing the ``xWebAdministration`` resources using
``win_psmodule``::

    - name: install xWebAdministration DSC resource
      win_psmodule:
        name: xWebAdministration
        state: present

Once installed, the win_dsc module will be able to use it by referencing it
with the ``resource_name`` option.

The first two methods above only work when the host has access to the internet.
When a host does not have internet access, the module must first be installed
using the methods above on another host with internet access and then copied
across. To save a module to a local filepath, the following PowerShell cmdlet
can be run::

    Save-Module -Name xWebAdministration -Path C:\temp

This will create a folder called ``xWebAdministration`` in ``C:\temp`` which
can be copied to any host. For PowerShell to see this offline resource, it must
be copied to a directory set in the ``PSModulePath`` environment variable.
In most cases the path ``C:\Program Files\WindowsPowerShell\Module`` is set
through this variable but the ``win_path`` module can be used to add different
paths.

Examples
````````
Extract a zip file
------------------

.. code-block:: yaml

  - name: extract a zip file
    win_dsc:
      resource_name: Archive
      Destination: c:\temp\output
      Path: C:\temp\zip.zip
      Ensure: Present

Create a directory
------------------

.. code-block:: yaml

    - name: create file with some text
      win_dsc:
        resource_name: File
        DestinationPath: C:\temp\file
        Contents: |
            Hello
            World
        Ensure: Present
        Type: File

    - name: create directory that is hidden is set with the System attribute
      win_dsc:
        resource_name: File
        DestinationPath: C:\temp\hidden-directory
        Attributes: Hidden,System
        Ensure: Present
        Type: Directory

Interact with Azure
-------------------

.. code-block:: yaml

    - name: install xAzure DSC resources
      win_psmodule:
        name: xAzure
        state: present
    
    - name: create virtual machine in Azure
      win_dsc:
        resource_name: xAzureVM
        ImageName: a699494373c04fc0bc8f2bb1389d6106__Windows-Server-2012-R2-201409.01-en.us-127GB.vhd
        Name: DSCHOST01
        ServiceName: ServiceName
        StorageAccountName: StorageAccountName
        InstanceSize: Medium
        Windows: True
        Ensure: Present
        Credential_username: '{{ansible_user}}'
        Credential_password: '{{ansible_password}}'

Setup IIS Website
-----------------

.. code-block:: yaml

    - name: install xWebAdministration module
      win_psmodule:
        name: xWebAdministration
        state: present

    - name: install IIS features that are required
      win_dsc:
        resource_name: WindowsFeature
        Name: '{{item}}'
        Ensure: Present
      with_items:
      - Web-Server
      - Web-Asp-Net45
    
    - name: remove Default Web Site
      win_dsc:
        resource_name: xWebsite
        Name: Default Web Site
        Ensure: Absent

    - name: setup web content
      win_dsc:
        resource_name: File
        DestinationPath: C:\inetpub\IISSite\index.html
        Type: File
        Contents: |
          <html>
          <head><title>IIS Site</title></head>
          <body>This is the body</body>
          </html>
        Ensure: present
    
    - name: create new website
      win_dsc:
        resource_name: xWebsite
        Name: NewIISSite
        State: Started
        PhysicalPath: C:\inetpub\IISSite\index.html

.. seealso::

   :doc:`index`
       The documentation index
   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_best_practices`
       Best practices advice
   `List of Windows Modules <http://docs.ansible.com/list_of_windows_modules.html>`_
       Windows specific module list, all implemented in PowerShell
   `User Mailing List <http://groups.google.com/group/ansible-project>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
