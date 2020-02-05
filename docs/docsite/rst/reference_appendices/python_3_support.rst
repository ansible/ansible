================
Python 3 Support
================

Ansible 2.5 and above work with Python 3. Previous to 2.5, using Python 3 was
considered a tech preview.  This topic discusses how to set up your controller and managed machines
to use Python 3.

.. note:: On the controller we support Python 3.5 or greater and Python 2.7 or greater. Module-side, we support Python 3.5 or greater and Python 2.6 or greater.

On the controller side
----------------------

The easiest way to run :command:`/usr/bin/ansible` under Python 3 is to install it with the Python3
version of pip.  This will make the default :command:`/usr/bin/ansible` run with Python3:

.. code-block:: shell

    $ pip3 install ansible
    $ ansible --version | grep "python version"
      python version = 3.6.2 (default, Sep 22 2017, 08:28:09) [GCC 7.2.1 20170915 (Red Hat 7.2.1-2)]

If you are running Ansible :ref:`from_source` and want to use Python 3 with your source checkout, run your
command via ``python3``.  For example:

.. code-block:: shell

    $ source ./hacking/env-setup
    $ python3 $(which ansible) localhost -m ping
    $ python3 $(which ansible-playbook) sample-playbook.yml

.. note:: Individual Linux distribution packages may be packaged for Python2 or Python3.  When running from
    distro packages you'll only be able to use Ansible with the Python version for which it was
    installed.  Sometimes distros will provide a means of installing for several Python versions
    (via a separate package or via some commands that are run after install).  You'll need to check
    with your distro to see if that applies in your case.


Using Python 3 on the managed machines with commands and playbooks
------------------------------------------------------------------

* Ansible will automatically detect and use Python 3 on many platforms that ship with it. To explicitly configure a
  Python 3 interpreter, set the ``ansible_python_interpreter`` inventory variable at a group or host level to the
  location of a Python 3 interpreter, such as :command:`/usr/bin/python3`. The default interpreter path may also be
  set in ``ansible.cfg``.

.. seealso:: :ref:`interpreter_discovery` for more information.

.. code-block:: ini

    # Example inventory that makes an alias for localhost that uses Python3
    localhost-py3 ansible_host=localhost ansible_connection=local ansible_python_interpreter=/usr/bin/python3

    # Example of setting a group of hosts to use Python3
    [py3-hosts]
    ubuntu16
    fedora27

    [py3-hosts:vars]
    ansible_python_interpreter=/usr/bin/python3

.. seealso:: :ref:`intro_inventory` for more information.

* Run your command or playbook:

.. code-block:: shell

    $ ansible localhost-py3 -m ping
    $ ansible-playbook sample-playbook.yml


Note that you can also use the `-e` command line option to manually
set the python interpreter when you run a command.   This can be useful if you want to test whether
a specific module or playbook has any bugs under Python 3.  For example:

.. code-block:: shell

    $ ansible localhost -m ping -e 'ansible_python_interpreter=/usr/bin/python3'
    $ ansible-playbook sample-playbook.yml -e 'ansible_python_interpreter=/usr/bin/python3'

What to do if an incompatibility is found
-----------------------------------------

We have spent several releases squashing bugs and adding new tests so that Ansible's core feature
set runs under both Python 2 and Python 3.  However, bugs may still exist in edge cases and many of
the modules shipped with Ansible are maintained by the community and not all of those may be ported
yet.

If you find a bug running under Python 3 you can submit a bug report on `Ansible's GitHub project
<https://github.com/ansible/ansible/issues/>`_.  Be sure to mention Python3 in the bug report so
that the right people look at it.

If you would like to fix the code and submit a pull request on github, you can
refer to :ref:`developing_python_3` for information on how we fix
common Python3 compatibility issues in the Ansible codebase.
