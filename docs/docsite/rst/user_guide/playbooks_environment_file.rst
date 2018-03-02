.. _playbooks_environment_file:

Setting the Environment with a file
===================================

.. versionadded:: 1.1

You may want to specify the possible environment vars by sourcing a file,
instead of specifying the vars one by one using the 'environment' keyword. To
achieve it, you can use the 'environment_file' keyword where you can specify a
path to a local file that will contain a set of vars in key=value pairs. Here is
an example::

    - hosts: all
      remote_user: root

      tasks:

        - apt: name=cobbler state=installed
          environment_file: /tmp/env_vars.sh

The environment file will have a set of vars as in the following example::

    ENV1_VAR=abc
    ENV2_VAR="def"
    # this will add another var after the comment
    ENV3_VAR=ghi

The file can support comments, and the vars may be quoted or not.

.. note::
   ``environment_file:`` is not currently supported for Windows targets

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_environment`
       An introduction to 'environment' keyword
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


