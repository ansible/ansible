Windows Remote Management
=========================
Unlike Linux/Unix machine which use SSH by default, Windows machines are
configured with WinRM instead. This page will expand on WinRM in more detail
and how Ansible can be configured to use it.

.. contents:: Topics

What is WinRM?
``````````````
WinRM is a management protocol used by Windows to remotely communicate with
another server. It is a SOAP-based protocol that communicates over HTTP and is
included in all recent Windows operating systems on install. Since Windows
Server 2012 it has also been enabled by default but in most cases extra
configuration will be required for Ansible to use it.

Ansible uses the ``pywinrm_`` package to communicate with Windows servers over
WinRM. It is not installed by default with the Ansible package but can be
installed by running the following::

   pip install "pywinrm>=0.2.2"

.. Note:: on distributions with multiple python versions, use pip2 or pip2.x,
    where x matches the python minor version Ansible is running under.

.. _pywinrm: https://github.com/diyan/pywinrm

Authentication Options
``````````````````````
When connecting to a Windows host, there are different options that can be used
when authentication with an account.

The following matrix is a high level overview of the options:

+-------------+----------------+---------------------------+-----------------------+-----------------+
| Option      | Local Accounts | Active Directory Accounts | Credential Delegation | HTTP Encryption |
+=============+================+===========================+=======================+=================+
| Basic       | Yes            | No                        | No                    | No              |
+-------------+----------------+---------------------------+-----------------------+-----------------+
| Certificate | Yes            | No                        | No                    | No              |
+-------------+----------------+---------------------------+-----------------------+-----------------+
| Kerberos    | No             | Yes                       | Yes                   | Yes             |
+-------------+----------------+---------------------------+-----------------------+-----------------+
| NTLM        | Yes            | Yes                       | No                    | Yes             |
+-------------+----------------+---------------------------+-----------------------+-----------------+
| CredSSP     | Yes            | Yes                       | Yes                   | Yes             |
+-------------+----------------+---------------------------+-----------------------+-----------------+

Basic
-----
Basic authentication is one of the simplest authentication option to use but is
also the most insecure option. This is because the username and password are
base64 encoded and if the network traffic is not over TLS then it can be
decoded by anyone.

It can only be used for local accounts and has no native message encryption
support unless it is used over TLS.

To use basic authentication, the host vars are configured like so::

    ansible_user: LocalUsername
    ansible_password: Password
    ansible_connection: winrm
    ansible_winrm_transport: basic

Basic authentication is not enabled by default on a Windows host but can be
enabled by running the following in powershell:

.. code-block:: powershell

    Set-Item -Path WSMan:\localhost\Service\Auth\Basic -Value $true

Certificate
-----------
Certificate authentication is one of the lesser know authentication options
when it comes to WinRM. It uses certificates as keys similar to the SSH key
pairs but the file format and key generation process is different.

The use certificate authentication, the host vars are configured like so::

    ansible_connection: winrm
    ansible_winrm_cert_pem: /path/to/certificate/public/key.pem
    ansible_winrm_cert_key_pem: /path/to/certificate/private/key.pem
    ansible_winrm_transport: certificate

Certificate authentication is not enabled by default on a Windows host but can
be enabled by running the following in powershell:

.. code-block:: powershell

    Set-Item -Path WSMan:\localhost\Service\Auth\Certificate -Value $true

.. Note:: Encrypted private key's cannot be used as the urllib3 library that
    is used by Ansible for WinRM does not support this functionality as of yet.

Generate Certificate
++++++++++++++++++++
Before mapping a certificate to a local user it first needs to be generated.
This can be done through 3 different methods:

* With OpenSSL
* With Powershell by using the ``New-SelfSignedCertificate`` cmdlet
* With Active Directory Certificate Services

The third option using ADCS is out of scope in this documentation but might be
the best option to use when running in a domain environment.

.. Note:: Using the powershell cmdlet ``New-SelfSignedCertificate`` to generate
    a certificate for authentication only works when being generated from a
    Windows 10 or Server 2012 R2 host or later. OpenSSL is still required to
    extract the private key from the PFX certificate to a PEM file for Ansible
    to use.

Generating a certificate with ``OpenSSL``:

.. code-block:: shell

    # set the name of the local user that will have the key mapped to
    USERNAME="username"

    cat > openssl.conf << EOL
    distinguished_name = req_distinguished_name
    [req_distinguished_name]
    [v3_req_client]
    extendedKeyUsage = clientAuth
    subjectAltName = otherName:1.3.6.1.4.1.311.20.2.3;UTF8:$USERNAME@localhost
    EOL

    export OPENSSL_CONF=openssl.conf
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -out cert.pem -outform PEM -keyout cert_key.pem -subj "/CN=$USERNAME" -extensions v3_req_client
    rm openssl.conf


Generating a certificate with ``New-SelfSignedCertificate``:

.. code-block:: powershell

    # set the name of the local user that will have the key mapped to
    $username = "username"
    $output_path = "C:\temp"

    # instead of generating a file, the cert will be added to the personal
    # LocalComputer folder in the certificate store
    $cert = New-SelfSignedCertificate -Type Custom `
        -Subject "CN=$username" `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.2","2.5.29.17={text}upn=$username@localhost") `
        -KeyUsage DigitalSignature,KeyEncipherment `
        -KeyAlgorithm RSA `
        -KeyLength 2048
    
    # export the public key
    $pem_output = @()
    $pem_output += "-----BEGIN CERTIFICATE-----"
    $pem_output += [System.Convert]::ToBase64String($cert.RawData) -replace ".{64}", "$&`n"
    $pem_output += "-----END CERTIFICATE-----"
    [System.IO.File]::WriteAllLines("$output_path\cert.pem", $pem_output)

    # export the private key in a PFX file
    [System.IO.File]::WriteAllBytes("$output_path\cert.pfx", $cert.Export("Pfx"))


.. Note:: To convert the PFX file to a private key that pywinrm can use, run
    the following command with OpenSSL
    ``openssl pkcs12 -in cert.pfx -nocerts -nodes -out cert_key.pem -passin pass: -passout pass:``

Import Certificate to Certificate Store
+++++++++++++++++++++++++++++++++++++++
Once the certificate has been generated, the issuing certificate needs to be
imported into the ``Trusted Root Certificate Authorities`` of the
``LocalMachine`` store and the client certificate public key must be present
in the ``Trusted People`` folder of the ``LocalMachine`` store. In the case of
these examples both the issuing certificate and public key are the same.

The code to import the issuing certificate is:

.. code-block:: powershell

    $cert = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Certificate2
    $cert.Import("cert.pem")

    $store_name = [System.Security.Cryptography.X509Certificates.StoreName]::Root
    $store_location = [System.Security.Cryptography.X509Certificates.StoreLocation]::LocalMachine
    $store = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Store -ArgumentList $store_name, $store_location
    $store.Open("MaxAllowed")
    $store.Add($cert)
    $store.Close()


.. Note:: If using ADCS to generate the certificate, then the issuing
    certificate will already be imported and this step can be skipped.

The code to import the client certificate public key is:

.. code-block:: powershell

    $cert = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Certificate2
    $cert.Import("cert.pem")

    $store_name = [System.Security.Cryptography.X509Certificates.StoreName]::TrustedPeople
    $store_location = [System.Security.Cryptography.X509Certificates.StoreLocation]::LocalMachine
    $store = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Store -ArgumentList $store_name, $store_location
    $store.Open("MaxAllowed")
    $store.Add($cert)
    $store.Close()


Mapping Certificate to Account
++++++++++++++++++++++++++++++
Once the certificate has been import then it needs to be mapped to the relevant
local user account.

This can be done with the following powershell command:

.. code-block:: powershell

    $username = "username"
    $password = ConvertTo-SecureString -String "password" -AsPlainText -Force
    $credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $username, $password

    # this is the issuer thumbprint which in the case of a self generated cert
    # is the public key thumbprint, additional logic may be required for other
    # scenarios
    $thumbprint = (Get-ChildItem -Path cert:\LocalMachine\root | Where-Object { $_.Subject -eq "CN=$username" }).Thumbprint

    New-Item -Path WSMan:\localhost\ClientCertificate `
        -Subject "$username@localhost" `
        -URI * `
        -Issuer $thumbprint `
        -Credential $credential `
        -Force

Once this is complete, the hostvar ``ansible_winrm_cert_pem`` should be set to
the path of the public key and ``ansible_winrm_cert_key_pem`` should be set to
the path of the private key.

NTLM
----
NTLM is an older authentication mechanism used by Microsoft and can support
both local and domain accounts. By default NTLM is enabled on the WinRM
service so no actions are required before using it.

This is easiest authentication protocol to use and is more secure than
``Basic`` auth. If running in a domain environment, ``Kerberos`` should be used
in favour of NTLM. 

Some of the reasons why Kerberos is preferred over NTLM are:

* NTLM is an older protocol and as such does not support the newer encryption
  protocols
* NTLM is slower to authenticate as there are more round trips to the host in
  the authentication stage
* NTLM does not allow credential delegation while Kerberos does

To use NTLM authentication, the host vars are configured like so::

    ansible_user: LocalUsername
    ansible_password: Password
    ansible_connection: winrm
    ansible_winrm_transport: ntlm

Kerberos
--------
Kerberos is the recommended authentication option to use when running in a
domain environment. It supports extra features like credential delegation,
message encryption over HTTP and is one of the more secure options that
are available through WinRM.

Kerberos requires some more setup work on the Ansible host before it can be
used properly.

To use Kerberos authentication, the host vars are configured like so::

    ansible_user: username@MY.DOMAIN.COM
    ansible_password: Password
    ansible_connection: winrm
    ansible_winrm_transport: kerberos

As of Ansible 2.3, the Kerberos ticket will be created based on
``ansible_user`` and ``ansible_password``. If running on an older Ansible
release or when ``ansible_winrm_kinit_mode`` is ``manual`` then a Kerberos
ticket must already be obtained. See below for more details.

There are some extra host variables that can be set as shown below::

    ansible_winrm_kinit_mode: managed/manual (manual means Ansible will not obtain a ticket)
    ansible_winrm_kinit_cmd: the kinit binary to use to obtain a Kerberos ticket (default to kinit)
    ansible_winrm_keytab: the path to the keytab file
    ansible_winrm_kerberos_delegation: allows the credentials to traverse multiple hops
    ansible_winrm_kerberos_hostname_override: the hostname to be used for the kerberos exchange

Installing Kerberos Library
+++++++++++++++++++++++++++
In order to authenticate with Kerberos, their are some system dependencies that
must be installed first. The below script lists the dependencies based on the
distro:

.. code-block:: shell

    # Via Yum (RHEL/Centos/Fedora)
    yum -y install python-devel krb5-devel krb5-libs krb5-workstation

    # Via Apt (Ubuntu)
    sudo apt-get install python-dev libkrb5-dev krb5-user

    # Via Portage (Gentoo)
    emerge -av app-crypt/mit-krb5
    emerge -av dev-python/setuptools

    # Via Pkg (FreeBSD)
    sudo pkg install security/krb5

    # Via OpenCSW (Solaris)
    pkgadd -d http://get.opencsw.org/now
    /opt/csw/bin/pkgutil -U
    /opt/csw/bin/pkgutil -y -i libkrb5_3

    # Via Pacman (Arch Linux)
    pacman -S krb5


Once the dependencies have been installed, the ``python-kerberos`` wrapper can
be install via ``pip``:

.. code-block:: shell

    pip install pywinrm[kerberos]


Configuring Host Kerberos
+++++++++++++++++++++++++
Once the dependencies have been installed, it will need to be configured so
that it can communicate with a domain. This configuration is done through the
``/etc/krb5.conf`` file which should be installed as a result of installing the
packages above.

In the section that starts with:

::

    [realms]

Add the full domain name and the fully qualified domain names of the primary
and secondary Active Directory domain controllers. It should look something
like this:

::

    [realms]
        MY.DOMAIN.COM = {
            kdc = domain-controller1.my.domain.com
            kdc = domain-controller2.my.domain.com
        }

In the section that starts with:

::

    [domain_realm]

Add a line like the following for each domain that Ansible needs access for:

::

    [domain_realm]
        .my.domain.com = MY.DOMAIN.COM

You can configure other settings in this file such as the default domain, see
krb5.conf_ for more details

.. _krb5.conf: https://web.mit.edu/kerberos/krb5-1.12/doc/admin/conf_files/krb5_conf.html

Automatic Kerberos Ticket Management
++++++++++++++++++++++++++++++++++++
Since Ansible 2.3, it will default to automatically managing kerberos tickets
both ``ansible_user`` and ``ansible_password`` are specified for a host. In
this process a new ticket is created in a temporary credential cache for each
host. This is done before each task executes (to minimize the chance of ticket
expiration). The temporary credential caches are deleted after each task
completes and will not interfere with the default credential cache.

To disable automatic ticket management set ``ansible_winrm_kinit_mode=manual``
via the inventory.

Automatic ticket management requires a standard ``kinit`` binary on the control
host system path. To specify a different location or binary name, set the
``ansible_winrm_kinit_cmd`` hostvar to the fully qualified path to a MIT krbv5
``kinit``-compatible binary.

Manual Kerberos Ticket Management
+++++++++++++++++++++++++++++++++
To manually management Kerberos tickets, the ``kinit`` binary is used. To
obtain a new ticket the following command is used:

.. code-block:: shell

    kinit username@MY.DOMAIN.COM

.. Note:: The domain part has to be fully qualified and must be in upper case.

To see what tickets (if any) have been acquired, use the following command:

.. code-block:: shell

    klist

To destroy all the tickets that have been acquired, use the following command:

.. code-block:: shell

    kdestroy

Troubleshooting Kerberos
++++++++++++++++++++++++
Kerberos is higly reliant on the environment setup being correct for it to
work. If issues are occuring check the following:

* The hostname set for the Windows host is the FQDN and not an IP address

* The forward and reverse DNS lookups are working properly in the domain. To
  test this, ping the windows host by name and then use the ip address returned
  with ``nslookup``. The same name should be returned when using ``nslookup``
  on the IP address.

* The Anisble host's clock is synchronised with the domain controller. Kerberos
  is time sensitive and a little clock drift can cause the ticket generation
  process to fail.

* Check the real fully qualified domain name for the domain is configured in
  the ``krb5.conf`` file. To check this run::

    kinit -C username@MY.DOMAIN.COM
    klist

  If the domain name return by ``klist`` is different from the one requested,
  an alias is being used. The ``krb5.conf`` file needs to be updated so that
  the FQDN is used and not its alias.

CredSSP
-------
CredSSP authentication is a newer authentication protocol that allows
credential delegation. This is achieved by encrypting the username and password
after authentication has succeeded and sending that to the server using the
CredSSP protocol.

Because the username and password are sent to the server to be used for double
hop authentication, ensure the hosts that the Windows one communicates with are
not compromised and are trusted.

CredSSP can be used for both local and domain accounts and also supports
message encryption over HTTP.

To use CredSSP authentication, the host vars are configured like so::

    ansible_user: Username
    ansible_password: Password
    ansible_connection: winrm
    ansible_winrm_transport: credssp

There are some extra host variables that can be set as shown below::

    ansible_winrm_credssp_disable_tlsv1_2: when true will not use TLS 1.2 in the CredSSP auth process

CredSSP authentication is not enabled by default on a Windows host but can
be enabled by running the following in powershell:

.. code-block:: powershell

    Enable-WSManCredSSP -Role Server -Force

Installing CredSSP Library
++++++++++++++++++++++++++

The ``requests-credssp`` wrapper can be installed via ``pip``:

.. code-block:: bash

    pip install pywinrm[credssp]


CredSSP and TLS 1.2
+++++++++++++++++++
By default the ``requests-credssp`` library is configured to authenticate over
a TLS 1.2 protocol. TLS 1.2 is installed and enabled by default from Server 2012
and Windows 8 onwards. 

There are two ways that older hosts can be used with CredSSP, which are:

* Install and enable a hotfix to enable TLS 1.2 support. This is the
  recommended when using Server 2008 R2 and Windows 7.

* Set ``ansible_winrm_credssp_disable_tlsv1_2=True`` in the inventory to run
  over TLS 1.0. This is the only option when connecting to Server 2008 as it
  has no way of supporting TLS 1.2

To enable TLS 1.2 support on Server 2008 R2 and Windows 7, the optional update
KRB3080079_ needs to be installed. Once installed and the host rebooted, run
the following powershell commands to enable TLS 1.2:

.. code-block:: powershell

    $reg_path = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProvider\SCHANNEL\Protocols\TLS 1.2"
    New-Item -Path $reg_path
    New-Item -Path "$reg_path\Server"
    New-Item -Path "$reg_path\Client"

    New-ItemProperty -Path "$reg_path\Server" -Name "Enabled" -Value 1 -PropertyType DWord
    New-ItemProperty -Path "$reg_path\Server" -Name "DisabledByDefault" -Value 0 -PropertyType DWord
    New-ItemProperty -Path "$reg_path\Client" -Name "Enabled" -Value 1 -PropertyType DWord
    New-ItemProperty -Path "$reg_path\Client" -Name "DisabledByDefault" -Value 0 -PropertyType DWord

.. _KRB3080079: https://support.microsoft.com/en-us/help/3080079/update-to-add-rds-support-for-tls-1.1-and-tls-1.2-in-windows-7-or-windows-server-2008-r2

Set CredSSP Certificate
+++++++++++++++++++++++
CredSSP works by encrypting the credentials through the TLS protocol and by
default it uses a self signed certificate. The ``CertificateThumbprint`` option
under the WinRM service configuration can be used to specify the thumbprint of
another certificate.

.. Note:: This certificate thumbprint is different from the WinRM listener
    thumbprint and is completely indepenent from it. The message transport
    is still sent over the WinRM listener but all the TLS encryption processes
    are done with the certificate set by the service level certificate of that
    thumbprint.

To explicitly set the certificate to use for CredSSP, use the code below:

.. code-block:: powershell

    # note the value $certificate_thumbprint will be different in each
    # situation, this needs to be set based on the cert that is used.
    $certificate_thumbprint = "7C8DCBD5427AFEE6560F4AF524E325915F51172C"

    # set the thumbprint value
    Set-Item -Path WSMan:\localhost\Service\CertificateThumbprint -Value $certificate_thumbprint

Non Administrator Accounts
``````````````````````````
By default WinRM is configured to only allow accounts in the local
``Administrators`` group to run over WinRM. This restriction can be lifted by
running the following command:

.. code-block:: powershell

    winrm configSDDL default

In the box displayed after running the above, the new user/group must have the
``Read`` and ``Execute`` permissions for it to work.

While non administrator accounts can be used with WinRM, there is a lot less
that can be done with these accounts so it is not a common use cases and tested
with modules.

WinRM Encryption
````````````````
By default WinRM will fail to work when running over an unencrypted channel.
The WinRM protocol considers the channel to be encrypted if using TLS over HTTP
(HTTPS) or using message level encryption. Using WinRM with TLS is the
recommended option as it works with all authentication options but requires
a certificate to be created and used on the WinRM listener.

The ``ConfigureRemotingForAnsible.ps1`` creates a self signed certificate and
creates the listener with that certificate. If in a domain environment, ADCS
can also create a certificate for the host that is issued by the domain itself.

If using HTTPS is not an option then HTTP can be used when the authentication
option is ``NTLM``, ``Kerberos`` or ``CredSSP``. These protocols will encrypt
the WinRM payload with their own encryption method before sending it to the
server. The message level encryption is not used when running over HTTPS as the
encryption uses the more secure TLS protocol instead. If both transport and
message encryption is required, set ``ansible_winrm_message_encryption=always``
in the host vars.

A last resort is to disable the encryption check on the Windows host. This
should only be used for developmental and debugging purposes as anything sent
from Ansible can viewed by anyone on the network. To disable the encryption
check the following command can be run in powershell:

.. code-block:: powershell

    Set-Item -Path WSMan:\localhost\Service\AllowUnencrypted -Value $true

.. Note:: One final warning, do not disable the encryption check unless it is
    absolutey required. Doing so will leave any sensitive information such as
    credentials and secret files viewable by anyone on the network.


Inventory Options
`````````````````
Ansible's windows support relies on a few standard variables to indicate the
username, password, and connection type of the remote hosts. These variables
are most easily set up in the inventory but can be set on the ``host_vars``/
``group_vars`` level.

When setting the inventory the following variables are requires to be set in
most cases::

    # it is suggested that tese be encrypted with ansible-vault:
    # ansible-vault edit group_vars/windows.yml
    
    ansible_user: Administrator
    ansible_password: SecretPasswordGoesHere
    ansible_connection: winrm

Using the variables above, Ansible will connect to the Windows host with Basic
authentication through HTTPS. If ``ansible_user`` has a SPN value like
``username@MY.DOMAIN.COM`` then the authentication option will be over
Kerberos.

As of Ansible 2.0, the following custom inventory variables are also supported
for additional configuration of WinRM connections:

* ``ansible_port``: The port WinRM will run over, HTTPS is ``5986`` which is
  the default while HTTP is ``5985``

* ``ansible_winrm_scheme``: Specify the connection scheme (``http`` or
  ``https``) to use for the WinRM connection. Ansible uses ``https`` by default
  unless ``ansible_port`` is ``5985``

* ``ansible_winrm_path``: Specify an alternate path to the WinRM endpoint,
  Ansible uses ``/wsman`` by default

* ``ansible_winrm_realm``: Specify the realm to use for Kerberos
  authentication. If ``ansible_user`` contains ``@``, Ansible will use the part
  of the username after ``@`` by default

* ``ansible_winrm_transport``: Specify one or more authentication transport
  options as a comma-separated list. By default, Ansible will use ``kerberos,
  basic`` if the ``kerberos`` module is installed and a realm is defined,
  otherwise it will be ``plaintext``

* ``ansible_winrm_server_cert_validation``: Specify the server certificate
  validation mode (``ignore`` or ``validate``). Ansible defaults to
  ``validate`` on Python 2.7.9 and higher, which will result in certificate
  validation errors against the Windows self-signed certificates. Unless
  verifiable certificates have been configured on the WinRM listeners, this
  should be set to ``ignore``

* ``ansible_winrm_operation_timeout_sec``: Increase the default timeout for
  WinRM operations, Ansible uses ``20`` by default

* ``ansible_winrm_read_timeout_sec``: Increase the WinRM read timeout, Ansible
  uses ``30`` by default. Useful if there are intermittent network issues and
  read timeout errors keep occurring

* ``ansible_winrm_message_encryption``: Specify the message encryption
  operation (``auto``, ``always``, ``never``) to use, Ansible used ``auto`` by
  default. ``auto`` means message encryption is only used when
  ``ansible_winrm_scheme`` is ``http`` and ``ansible_winrm_transport`` supports
  message encryption. ``always`` means message encryption will always be used
  and ``never`` means message encryption will never be used

* ``ansible_winrm_*``: Any additional keywork arguments supported by
  ``winrm.Protocol`` may be provided in place of ``*``

As well as the above list, there are also specific variables that are are set
for an authentication option. See the auth section for that option for more
details.

.. Note:: Ansible 2.0 has deprecated the "ssh" from ``ansible_ssh_user``,
    ``ansible_ssh_pass``, ``ansible_ssh_host``, and ``ansible_ssh_port`` to
    become ``ansible_user``, ``ansible_password``, ``ansible_host``, and
    ``ansible_port``. If using a version of Ansible prior to 2.0, the older
    style (``ansible_ssh_*``) should be used instead. The shorter variables
    are ignored, without warning, in older versions of Ansible.

.. Note:: ``ansible_winrm_message_encryption`` is different from transport
    encryption done over TLS. The WinRM payload is still encrypted with TLS
    when run over HTTPS, even if ``ansible_winrm_message_encryption=never``.

Limitations
```````````
Due to the design of the protocol by Microsoft, there are a few limitations
when using WinRM that can cause issues when creating playbooks for Ansible.

Some of the major limitations of WinRM are:

* Credentials are not delegated on every authentication transport which causes
  authentication errors when accessing network resources or installing certain
  programs

* A lot of calls to the Windows Update API are blocked when running over WinRM

* Some programs fail to install with WinRM due to no credential delegation or
  they access forbidden Windows API like WUA over WinRM

* Commands under WinRM are done under a non interactive session which can break
  certain commands or executables from running

* Run a process that interacts with ``DPAPI``, this can include installers that
  call this like the SQL Server installer

There are three ways in which these issues can be bypassed which are:

* Set ``ansible_winrm_transport`` to ``credssp`` or ``kerberos`` (with
  ``ansible_winrm_kerberos_delegation=true``) to bypass the double hop issue
  and access network resources

* Use ``become`` to bypass all WinRM restrictions and run a command as it would
  locally. Unlike using an authentication transport like ``credssp`` this will
  also remove the non-interactive restriction and API restrictions like WUA and
  DPAPI

* Use a scheduled task to run a command which can be created with the
  ``win_scheduled_task`` module. Like ``become`` this bypasses all WinRM
  restrictions but can only run a command and not modules.

.. seealso::

   `List of Windows Modules <http://docs.ansible.com/list_of_windows_modules.html>`_
       Windows specific module list, all implemented in PowerShell
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
