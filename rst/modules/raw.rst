.. _raw:

raw
``````````````````````````````



Executes a low-down and dirty SSH command, not going through the module subsystem. This is useful and should only be done in two cases. The first case is installing python-simplejson on older (Python 2.4 and before) hosts that need it as a dependency to run modules, since nearly all core modules require it. Another is speaking to any devices such as routers that do not have any Python installed. In any other case, using the ``shell`` or ``command`` module is much more appropriate. Arguments given to ``raw`` are run directly through the configured remote shell and only output is returned. There is no error detection or change handler support for this module 




.. raw:: html


    <p>Example from /usr/bin/ansible to bootstrap a legacy python 2.4 host</p>
    <p><pre>
    ansible newhost.example.com -m raw -a "yum -y install python-simplejson"</pre></p>

    <br/>

