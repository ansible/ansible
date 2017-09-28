Windows Frequently Asked Questions
==================================

Here are some commonly asked questions in regards to Ansible and Windows and
their answers.

.. note:: These are questions around managing Windows servers with Ansible,
    questions about Ansible itself can be found at the
    `faq <http://docs.ansible.com/ansible/latest/faq.html>`_ page.

Does Ansible work with Windows XP and Server 2003
`````````````````````````````````````````````````
Ansible does not support managing Windows XP hosts and Server 2003. The list of
supported hosts are:

* Windows Server 2008
* Windows Server 2008 R2
* Windows Server 2012
* Windows Server 2012 R2
* Windows Server 2016
* Windows 7
* Windows 8.1
* Windows 10

There is also a requirement on the version of Powershell that needs to be
installed.

See :doc:`windows_setup` for more information.

Can I Manage Windows Nano Server
````````````````````````````````
Windows Nano Server is not currently supported by Ansible right now. It does
not have access to the full .NET Framework that is used by the majority of the
modules and internal components and so will fail on a lot of cases.

Because it uses WinRM as a way to executing commands, it is technically
possible to achieve but right now it isn't tested as part of the Ansible test
suite.

Can Ansible run on Windows?
```````````````````````````
No, Ansible cannot run on a Windows host and can only manage Windows hosts.

.. Note:: Running Ansible from a Windows control machine directly is not a
    goal of the project. Refrain from asking for this feature, as it limits
    what technologies, features, and code we can use in the main project in the
    future.

While not supported by either Ansible or Microsoft, a popular option for
developers is to install Ansible with the Windows Subsystem for Linux (WSL).
WSL is a tool primarily for developers and it allows a Windows host to run
applications in a Linux environment.

.. Note:: The Windows Subsystem for Linux is not supported by Microsoft or
    Ansible and should not be used for production systems. It is primarily
    designed for development purposes.

Once WSL is installed and running, to install Ansible the following commands
can be run in the bash terminal.

.. code-block:: shell

    sudo apt-get update
    sudo apt-get install python-pyp git libffi-dev libssl-dev -y
    pip install ansible pywinrm

To run Ansible from source instead of a release, simply uninstall the pip
installed version and then clone the git repo.

.. code-block:: shell

    pip uninstall ansible -y
    git clone https://github.com/ansible/ansible.git
    source ansible/hacking/env-setup

    # to enable Ansible on login, run the following
    echo ". ~/ansible/hacking/env-setup -q' >> ~/.bashrc

Can I use SSH keys to Authenticate?
```````````````````````````````````
Windows uses WinRM as the transport protocol which supports a wide range of
authentication options. The closet option to SSH keys is to use the certificate
authentication option which is when an X509 certificate is mapped to a local
user.

The way that these certificates are generated and mapped to a user is different
from the SSH implementation so please read the documentation about this to set
it up correctly.

See section about certificate authentication in :doc:`windows_winrm` for more
info on how to set this up.

I can run this command locally but it does not work under Ansible?
``````````````````````````````````````````````````````````````````
Ansible executes commands through WinRM and these processes are different from
running a command locally in these ways:

* Unless using an authentication option like CredSSP or Kerberos with
  credential delegation, the WinRM process does not have the ability to
  delegate the user's credentials to a network resource causing access is
  denied errors.

* Each process over WinRM is run in an non-interactive process, any
  applications that rely on having an interactive session will not work.

* Wgeb running through WinRM, Windows restricts access to internal Windows
  API's like the Windows Update API and DPAPI which some installers and
  programs rely on.

Some ways to bypass these restrictions are to:

* Use ``become`` which runs a command as it would when run locally. This will
  bypass all WinRM restrictions as Windows is unaware the process is running
  under WinRM when become is used.

* Use a scheduled task, which can be created with ``win_scheduled_task``. Like
  become it will bypass all WinRM restrictions but it can only be used to run
  commands and not modules.

* Use ``win_psexec`` to run a command on the host. PSExec does not use WinRM
  and so will bypass any of the restrictions.

* To access network resources without any of the workarounds above, an
  authentication option that supports credential delegation can be used. Both
  CredSSP and Kerberos with credential delegation enabled can support this.

See :doc:`become` more info on how to use become. The limitations section at
:doc:`windows_winrm` has more details around limitation of WinRM.

This program won't install with Ansible
```````````````````````````````````````
See `above question <http://docs.ansible.com/ansible/latest/windows_faq.html#i-can-run-this-command-locally-but-it-does-not-work-under-ansible>`_
for more information around the limitations with WinRM.

What modules are available?
```````````````````````````
Most of the Ansible modules in core Ansible are written for a combination of
Linux/Unix machines and arbitrary web services. These modules are written in
Python and do not work on Windows for various reasons.

Because of this, there are dedicated Windows modules that are written in
Powershell and are meant to be run on Windows hosts which can be found
`here <http://docs.ansible.com/list_of_windows_modules.html>`_.

In addition, the following core modules/action-plugins work with Windows

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
No, the WinRM connection protocol is set to use powershell modules and Python
modules will not work. A way to bypass this issue to use
``delegate_to: localhost`` to run a Python module on the Ansible controller.
This is useful if during a playbook, an external service needs to be contacted
and there is no module available for Windows to do so.

Can I connect over SSH?
```````````````````````
Microsoft has announced and is developing a fork of OpenSSH for Windows that
allows remote manage of Windows servers through the SSH protocol instead of
WinRM. While this can be installed and used right now for normal SSH clients,
it is still in beta from Microsoft and the required functionality has not been
developed within Ansible yet.

There are future plans on adding this feature and this page will be updated
once more information can be shared.

Failed to connect to the host via ssh
`````````````````````````````````````
When trying to connect to a Windows host and the output error indicates that
SSH was used, then this is an indication that the connection vars are not set
properly or the host is not inheriting them correctly.

Make sure ``ansible_connection: winrm`` is set in the inventory for the Windows
host.

My Credentials are being Rejected
`````````````````````````````````
This can be due to a myriad of reasons unrelated to incorrect credentials.

See HTTP 401/Credentials Rejected at :doc:`windows_setup` for a more detailed
guide of this could mean.

I am getting an error SSL CERTIFICATE_VERIFY_FAILED
```````````````````````````````````````````````````
When the Ansible controller is running on Python 2.7.9+ or an older Python that
has backported SSLContext, e.g. Python 2.7.5 on RHEL 7, it will attempt to
validate the certificate WinRM is using for a HTTPS connection. If the
certificate cannot be validated, in the case of a self signed cert, it will
fail the verification process.

To ignore certificate validation add
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
