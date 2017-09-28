Desired State Configuration
===========================

.. contents:: Topics

What is Desired State Configuration?
````````````````````````````````````
Desired State Configuration, or DSC, is a tool built into Powershell that can
be used to define a Windows host setup through code. The overall purpose of DSC
is the same as Ansible but the benefits of Ansible is that it has it's own
modules and can leverage DSC. Since Ansible 2.4, the ``win_dsc`` module has
been created and can be used to leverage existing DSC resources when
interacting with a Windows host.

More details on DSC can be viewed at `DSC Overview <https://docs.microsoft.com/en-us/powershell/dsc/overview>`_.

Host Requirements
`````````````````
To use the ``win_dsc`` module, a Windows host must have Powershell v5.0 or
newer installed. All supported hosts, except for Server 2008 (non R2) can be
upgraded to Powershell v5.

To use DSC once the Powershell requirements have been met is as simple as
creating a task with the ``win_dsc`` module.

Why Use It?
```````````
DSC and Ansible modules have a common goal which is to define the state of a
resource and the code will ensure that resource meets that state. Because of
this resources like the `File <https://docs.microsoft.com/en-us/powershell/dsc/fileresource>`_
DSC resource and win_file can be used to achieve the same result. The question
is why would someone use DSC over an Ansible module and the answer is it
depends.

Reasons for using an Ansible module over a DSC resource are:

* The host does not support Powershell v5.0 or it cannot easily be upgraded
* The DSC resource does not offer a feature present in an Ansible module, e.g.
  win_regedit can manage the ``REG_NONE`` type where the DSC ``Registry``
  resource cannot
* DSC resources have limited check mode support where some modules have better
  checks
* DSC resources do not support diff mode, where some modules do
* Custom resources require further installation on the host where modules are
  in built with Ansible and no installation is required
* There are bug with a DSC resource where an Ansible module works

Reasons for using a DSC resource over an Ansible module are:

* The Ansible module does not support a feature present in a DSC resource
* The only alternative to a DSC resource is to run a command and not a module
* There are bugs with an existing module while DSC works

In the end, it doesn't matter how the task is done with DSC or an Ansible
module, what matters is that the task is performanced correctly and the code
is still readible. If someone has more experience with DSC over Ansible there
is no reason why DSC can't be used for every step that can use it.

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
used, in this case ``Registry``. The ``module_version`` can refer to a specific
version of the DSC resource but if left blank will default to the latest. The
other parameters are set word for word as the options of the resource like
``Key``, ``ValueName``, etc. The options in the task are not case sensitive but
it makes it easier to see what is for the DSC resource and what is an Ansible
option when they are kept as PascalCase.

Using the same example as what is in the Microsoft documentation for Registry,
this is what the Ansible task would look like::

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
For string types like ``[string]`` and ``[bool]`` this is a simple operation,
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

It is recommended to use ``no_log: true`` on the task definition in Ansible
to ensure any credentials used are not stored in any log file or console
output.

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
that Ansible run the module as. This means that to access resources that are
usually loaded with a user profile like ``HKEY_CURRENT_USER`` with the Registry
resource will be for the SYSTEM account. The parameter ``PsDscRunAsCredential``
is a parameter that can be set for every DSC resource to force the DSC engine
to run under a different account than SYSTEM. As ``PsDscRunAsCredential`` has a
type of ``PSCredential``, it is defined with the ``_username`` and
``_password`` suffix.

Using the Registry resource type as an example, this is how to define a type
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

Custom DSC Resources
````````````````````
DSC resources are not limited to the builtin options from Microsoft and custom
modules can be installed to manage other resources.

Finding Custom DSC Resource
---------------------------
The main source to find custom resources would be `PSGallery <https://www.powershellgallery.com/>`_,
this site can then link to further documentation or details on how to install
it manually.

The ``Find-DscResource`` cmdlet can also be used to find custom resources. An
example of this cmdlet is:

.. code-block:: powershell

    # find all DSC resources in the configured repositories
    Find-DscResource

    # find all DSC resources that relate to SQL
    Find-DscResource -ModuleName "*sql*"

.. Note:: DSC resources that start with ``x`` mean the module is experimental
    and comes with no support.

Installing Custom Resource
--------------------------
There are three ways that a DSC resource can be installed on a host:

* Manually with the ``Install-Module`` cmdlet
* Using the ``win_psmodule`` module
* Saving the module and installing it without internet access

This is an example of installing the ``xWebAdministration`` resources using
``win_psmodule``::

    - name: install xWebAdministration DSC resource
      win_psmodule:
        name: xWebAdministration
        state: present

Once installed, the win_dsc module will be able to use it by referencing it
with the ``resource_name`` option.

The methods above only work when the host has access to the internet but there
where a host without internet access requires a custom resource. To achieve
this the first step would be to save the module first on a Windows host that
has internet access. This can be done with the following command::

    Save-Module -Name xWebAdministration -Path C:\temp

This will create a folder called ``xWebAdministration`` in ``C:\temp`` which
can be copied to any host. On the host without internet access, this folder
must be copied to a directory under ``PSModulePath``. Usually the path
``C:\Program Files\WindowsPowerShell\Modules`` is under this path but it is
best to check this environment value before copying. Any modules that under the
``PSModulePath`` folder are accessible in Powershell.

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
