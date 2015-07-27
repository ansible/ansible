Common Return Values
====================

.. contents:: Topics

Ansible modules normally return a data structure that can be registered into a variable, or seen directly when using
the `ansible` program as output. Here we document the values common to all modules, each module can optionally document
its own unique returns. If these docs exist they will be visible through ansible-doc and https://docs.ansible.com.

.. _facts:

Facts
`````

Some modules return 'facts' to ansible (i.e setup), this is done through a 'ansible_facts' key and anything inside
will automatically be available for the current host directly as a variable and there is no need to
register this data.


.. _status:

Status
``````

Every module must return a status, saying if the module was successful, if anything changed or not. Ansible itself
will return a status if it skips the module due to a user condition (when: ) or running in check mode when the module
does not support it.


.. _other:

Other common returns
````````````````````

It is common on failure or success to return a 'msg' that either explains the failure or makes a note about the execution.
Some modules, specifically those that execute shell or commands directly, will return stdout and stderr, if ansible sees
a stdout in the results it will append a stdout_lines which is just a list or the lines in stdout.

.. seealso::

   :doc:`modules`
       Learn about available modules
   `GitHub Core modules directory <https://github.com/ansible/ansible-modules-core/tree/devel>`_
       Browse source of core modules
   `Github Extras modules directory <https://github.com/ansible/ansible-modules-extras/tree/devel>`_
       Browse source of extras modules.
   `Mailing List <http://groups.google.com/group/ansible-devel>`_
       Development mailing list
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
