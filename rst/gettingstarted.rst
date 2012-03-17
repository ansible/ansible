Downloads & Getting Started
===========================

How to download ansible and get started using it

Requirements
````````````

Requirements for Ansible are extremely minimal.

If you are running python 2.6 on the **overlord** machine (the machine
that you'll be talking to the other machines from), you will need:

* ``paramiko``
* ``PyYAML``
* ``python-jinja2`` (for playbooks)

If you are running less than Python 2.6, you will also need:

* The Python 2.4 or 2.5 backport of the ``multiprocessing`` module

  - `Installation and Testing Instructions <http://code.google.com/p/python-multiprocessing/wiki/Install>`_

* ``simplejson``

On the managed nodes, to use templating, you will need:

* ``python-jinja2`` (you can install this with ansible)

Developer Requirements
``````````````````````

For developers, you may wish to have:

* ``asciidoc`` (for rebuilding manpage files)
* ``python-sphinx`` (for rebuilding content for the ansible.github.com docs project only)


Getting Ansible
```````````````

Tagged releases are available as tar.gz files from the Ansible github
project page:

* `Ansible/downloads <https://github.com/ansible/ansible/downloads>`_

As the project is still pretty new, you will probably just want to clone
the git checkout instead, so you can keep up with all of the latest features,
and also contribute easily back to the project (if you want).  
Instructions for installing from source are below.

You may also wish to follow the `Github project <https://github.com/ansible/>`_ if
you have a github account.  This is also where we keep the issue tracker for sharing
bugs or feature ideas.


Make Install
++++++++++++

You can install Ansible using "make install".  This is done through python distutils::

    $ git clone git://github.com/ansible/ansible.git
    $ cd ./ansible
    $ sudo make install


Via RPM
+++++++

In the near future, pre-built RPMs will be available through your
distribution. Until that time you can use the ``make rpm`` command::

    $ git clone git://github.com/ansible/ansible.git
    $ cd ./ansible
    $ make rpm
    $ sudo rpm -Uvh ~/rpmbuild/RPMS/noarch/ansible-*.noarch.rpm

If you are tracking the upstream source (i.e. git), the RPM revision may not be 
bumped with every source code change.  To get around this, you can use
rpm `-Uvh` with `--force` when RPM tells you the package is still at the
same version.

Your first commands
```````````````````

Edit (or create) /etc/ansible/hosts and put one or more remote systems in it, for
which you have your SSH key in ``authorized_keys``::

    192.168.1.50
    aserver.example.org
    bserver.example.org

Set up SSH agent to avoid retyping passwords::

    ssh-agent bash
    ssh-add ~/.ssh/id_rsa

Now ping all your nodes::

    ansible all -m ping

Now run a live command on all of your nodes::
  
    ansible all -a "/bin/echo hello"

Congratulations.  You've just contacted your nodes with Ansible.  It's
now time to read some of the more real-world :doc:`examples`, and explore
what you can do with different modules, as well as the Ansible
:doc:`playbooks` language.  Ansible is not just about running commands, but
you already have a working infrastructure!


.. seealso::

   :doc:`examples`
       Examples of basic commands
   :doc:`playbooks`
       Learning ansible's configuration management language
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

