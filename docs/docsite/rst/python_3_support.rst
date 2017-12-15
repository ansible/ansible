================
Python 3 Support
================

Ansible 2.2, 2.3, and 2.4 feature a tech preview of Python 3 support. This topic discusses how you can test to make sure your modules and playbooks work with Python 3.

.. note:: Ansible supports Python version 3.5 and above only.


.. note:: Technology preview features provide early access to upcoming product innovations,
   enabling you to test functionality and provide feedback during the development process.
   Please be aware that tech preview features may not be functionally complete and are not
   intended for production use. To report a Python 3 bug, please see `Community Information & Contributing <http://docs.ansible.com/ansible/community.html#i-d-like-to-report-a-bug>`_.

Testing Python 3 with commands and playbooks
--------------------------------------------

* Run Ansible 2.2+ - See :ref:`from_source`
* To test Python 3 on the controller, run your ansible command via
  ``python3``. For example:

.. code-block:: shell

    $ python3 /usr/bin/ansible localhost -m ping
    $ python3 /usr/bin/ansible-playbook sample-playbook.yml

You can also install Ansible using :program:`pip` for Python3 which will make the default
:command:`/usr/bin/ansible` run with Python3:

.. code-block:: shell

    $ virtualenv --python=python3 py3-ansible
    $ source ./py3-ansible/bin/activate
    $ pip3 install ansible
    $ ansible --version | grep "python version"
      python version = 3.6.2 (default, Sep 22 2017, 08:28:09) [GCC 7.2.1 20170915 (Red Hat 7.2.1-2)]

On systems with SELinux installed, such as Red Hat Enterprise Linux or Fedora, the SELinux Python libraries also need to be copied over.

.. code-block:: shell

    $ cp -r -v /usr/lib64/python3.*/site-packages/selinux/ ./py3-ansible/lib64/python3.*/site-packages/
    $ cp -v /usr/lib64/python3.*/site-packages/*selinux*.so ./py3-ansible/lib64/python3.*/site-packages/

.. note:: Individual Linux distribution packages may be packaged for Python2 or Python3.  When running from
    distro packages you'll only be able to use Ansible with the Python version for which it was
    installed.  Sometimes distros will provide a means of installing for several Python versions
    (via a separate package or via some commands that are run after install).  You'll need to check
    with your distro to see if that applies in your case.


Testing Python 3 module support
--------------------------------

* Set the ansible_python_interpreter configuration option to
  :command:`/usr/bin/python3`. The ``ansible_python_interpreter`` configuration option is
  usually set per-host as an inventory variable associated with a host or group of hosts:

.. code-block:: ini

    # Example inventory that makes an alias for localhost that uses python3
    [py3-hosts]
    localhost-py3 ansible_host=localhost ansible_connection=local

    [py3-hosts:vars]
    ansible_python_interpreter=/usr/bin/python3

See :doc:`intro_inventory` for more information.

* Run your command or playbook:

.. code-block:: shell

    $ ansible localhost-py3 -m ping
    $ ansible-playbook sample-playbook.yml


Note that you can also use the :option:`-e` command line option to manually
set the python interpreter when you run a command. For example:

.. code-block:: shell

    $ ansible localhost -m ping -e 'ansible_python_interpreter=/usr/bin/python3'
    $ ansible-playbook sample-playbook.yml -e 'ansible_python_interpreter=/usr/bin/python3'

What to do if an incompatibility is found
-----------------------------------------

If you find a bug while testing modules with Python3 you can submit a bug
report on `Ansible's GitHub project
<https://github.com/ansible/ansible/issues/>`_.  Be sure to mention Python3 in
the bug report so that the right people look at it.

If you would like to fix the code and submit a pull request on github, you can
refer to :doc:`dev_guide/developing_python3` for information on how we fix
common Python3 compatibility issues in the Ansible codebase.
