Ansible Windows Setup
==================

In order to get Ansible to communicate with a Windows host there are a few
requirements that need to be met to enable this.

..contents:: Topics

Host Requirments
````````````````
For Ansible to communicate to a Windows host and use Windows modules, the
Windows host must meet the following requirements:

* The OS versions that are supported under Ansible fall under the same support
  agreement as Microsoft. If running a desktop OS, it must be Windows 7, 8.1 or
  10. If running a desktop OS it must be Windows Server 2008, 2008 R2, 2012,
  2012 R2 or 2016.

* Ansible requires Powershell 3.0 or newer and at least .NET 4.0 to be
  installed on the Windows host.

* A WinRM listener is created and is activated, more details for this can be
  found below.

.. note:: While these are the base requirements some modules have separate
    requirements where it may need a newer OS or the latest powershell
    version. Please read the notes section on a module to determine whether
    a host meets those requirements.

Upgrading Powershell
--------------------
TODO: info about upgrading to PS v3/4/5

Upgrading .NET Framework
------------------------
TODO: info about upgrading .NET

WinRM Memory Hotfix
-------------------
TODO: info about the WinRM hotfix for affected OS'.

WinRM Host Setup
```````````
TODO: information about setting up a WinRM listener. The below is a copy from intro_windows.rst

Setup WinRM Listener
--------------------
TODO

WinRM Configuration Options
---------------------------
TODO

Inventory
`````````
Info on how to setup Ansible inventory and what the vars mean
