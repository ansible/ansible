Windows Remote Management
=========================

TODO: information about winrm such as authentication, double hop, limitations.

What is WinRM?
``````````````

Authentication Options
``````````````````````

Basic
-----

Certificate
-----------

NTLM
----

Kerberos
--------

CredSSP
-------

Configuration Options
`````````````````````
Info about some of the configuration options on the server side. (Should this
be here or windows_host_setup.rst?)

Limitations
```````````
Talk about the known limitations of WinRM and ways to bypass them.

Accessing Network Resources
---------------------------
Details on double hop auth/credential delegation

Interacting with Windows Update
-------------------------------
How it does not work over WinRM, use win_updates or become/scheduled_task

Installing Programs
-------------------
Some programs can't be installed because of it interacts with one of the above.
Use become/scheduled_task.
