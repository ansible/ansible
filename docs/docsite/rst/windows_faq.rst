Windows Frequently Asked Questions
==================================

Here are some commonly asked questions in regards to Ansible and Windows and
their answers.

.. note:: This document covers questions about managing Microsoft Windows servers with Ansible.
    For questions about Ansible Core, please see the
    `FAQ page <http://docs.ansible.com/ansible/latest/faq.html>`_.

Does Ansible work with Windows XP or Server 2003?
``````````````````````````````````````````````````
Ansible does not support managing Windows XP or Server 2003 hosts. The
supported operating system versions are:

* Windows Server 2008
* Windows Server 2008 R2
* Windows Server 2012
* Windows Server 2012 R2
* Windows Server 2016
* Windows 7
* Windows 8.1
* Windows 10

Ansible also has minimum PowerShell version requirements - please see 
:doc:`windows_setup` for the lastest information.

Can I Manage Windows Nano Server?
`````````````````````````````````
Windows Nano Server is not currently supported by Ansible, since it does
not have access to the full .NET Framework that is used by the majority of the
modules and internal components.

Can Ansible run on Windows?
```````````````````````````
No, Ansible cannot run on a Windows host and can only manage Windows hosts, but
Ansible can be run under the Windows Subsystem for Linux (WSL).

.. note:: The Windows Subsystem for Linux is not supported by Microsoft or
    Ansible and should not be used for production systems. 

To install Ansible on WSL, the following commands
can be run in the bash terminal:

.. code-block:: shell

    sudo apt-get update
    sudo apt-get install python-pyp git libffi-dev libssl-dev -y
    pip install ansible pywinrm

To run Ansible from source instead of a release on the WSL, simply uninstall the pip
installed version and then clone the git repo.

.. code-block:: shell

    pip uninstall ansible -y
    git clone https://github.com/ansible/ansible.git
    source ansible/hacking/env-setup

    # to enable Ansible on login, run the following
    echo ". ~/ansible/hacking/env-setup -q' >> ~/.bashrc

Can I use SSH keys to authenticate?
```````````````````````````````````
Windows uses WinRM as the transport protocol. WinRM supports a wide range of
authentication options. The closet option to SSH keys is to use the certificate
authentication option which maps an X509 certificate to a local user.

The way that these certificates are generated and mapped to a user is different
from the SSH implementation; consult the :doc:`windows_winrm` documentation for 
more information.

Why can I run a command locally that does not work under Ansible?
`````````````````````````````````````````````````````````````````
Ansible executes commands through WinRM. These processes are different from
running a command locally in these ways:

* Unless using an authentication option like CredSSP or Kerberos with
  credential delegation, the WinRM process does not have the ability to
  delegate the user's credentials to a network resource, causing ``Access is
  Denied`` errors.

* All processes run under WinRM are in a non-interactive session. Applications 
  that require an interactive session will not work.

* When running through WinRM, Windows restricts access to internal Windows
  APIs like the Windows Update API and DPAPI, which some installers and
  programs rely on.

Some ways to bypass these restrictions are to:

* Use ``become``, which runs a command as it would when run locally. This will
  bypass most WinRM restrictions, as Windows is unaware the process is running
  under WinRM when ``become`` is used. See the :doc:`become` documentation for more 
  information.

* Use a scheduled task, which can be created with ``win_scheduled_task``. Like
  ``become``, it will bypass all WinRM restrictions, but it can only be used to run
  commands, not modules.

* Use ``win_psexec`` to run a command on the host. PSExec does not use WinRM
  and so will bypass any of the restrictions.

* To access network resources without any of these workarounds, an
  authentication option that supports credential delegation can be used. Both
  CredSSP and Kerberos with credential delegation enabled can support this.

See :doc:`become` more info on how to use become. The limitations section at
:doc:`windows_winrm` has more details around WinRM limitations.

This program won't install with Ansible
```````````````````````````````````````
See `the question <http://docs.ansible.com/ansible/latest/windows_faq.html#i-can-run-this-command-locally-but-it-does-not-work-under-ansible>`_ for more information about WinRM limitations.

What modules are available?
```````````````````````````
Most of the Ansible modules in Ansible Core are written for a combination of
Linux/Unix machines and arbitrary web services. These modules are written in
Python and most of them do not work on Windows.

Because of this, there are dedicated Windows modules that are written in
PowerShell and are meant to be run on Windows hosts. A list of this modules
can be found `here <http://docs.ansible.com/list_of_windows_modules.html>`_.

In addition, the following Ansible Core modules/action-plugins work with Windows:

* add_host
* assert
* async_status
* debug
* fail
* fetch
* group_by
* include
* include_role
* include_vars
* meta
* pause
* raw
* script
* set_fact
* set_stats
* setup
* slurp
* template (also: win_tempate)
* wait_for_connection

Can I run Python modules?
`````````````````````````
No, the WinRM connection protocol is set to use PowerShell modules, so Python
modules will not work. A way to bypass this issue to use
``delegate_to: localhost`` to run a Python module on the Ansible controller.
This is useful if during a playbook, an external service needs to be contacted
and there is no equivalent Windows module available.

Can I connect over SSH?
```````````````````````
Microsoft has announced and is developing a fork of OpenSSH for Windows that
allows remote manage of Windows servers through the SSH protocol instead of
WinRM. While this can be installed and used right now for normal SSH clients,
it is still in beta from Microsoft and the required functionality has not been
developed within Ansible yet.

There are future plans on adding this feature and this page will be updated
once more information can be shared.

Why is connecting to the host via ssh failing?
``````````````````````````````````````````````
When trying to connect to a Windows host and the output error indicates that
SSH was used, then this is an indication that the connection vars are not set
properly or the host is not inheriting them correctly.

Make sure ``ansible_connection: winrm`` is set in the inventory for the Windows
host.

Why are my credentials are being rejected?
``````````````````````````````````````````
This can be due to a myriad of reasons unrelated to incorrect credentials.

See HTTP 401/Credentials Rejected at :doc:`windows_setup` for a more detailed
guide of this could mean.

Why am I getting an error SSL CERTIFICATE_VERIFY_FAILED?
````````````````````````````````````````````````````````
When the Ansible controller is running on Python 2.7.9+ or an older version of Python that
has backported SSLContext (like Python 2.7.5 on RHEL 7), the controller will attempt to
validate the certificate WinRM is using for an HTTPS connection. If the
certificate cannot be validated (such as in the case of a self signed cert), it will
fail the verification process.

To ignore certificate validation, add
``ansible_winrm_server_cert_validation: ignore`` to inventory for the Windows
host.

.. seealso::

   :doc:`index`
       The documentation index
   :doc:`windows`
       The Windows documentation index
   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_best_practices`
       Best practices advice
   `User Mailing List <http://groups.google.com/group/ansible-project>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
