Troubleshooting
===============

.. note::
   Work in progress. More should be added here.


What to do when your playbooks fail? Here are some tips.

Run ansible-playbook in the verbose mode
----------------------------------------

``ansible-playbook -vvvv ...`` will provide you with plenty of details of what is going on.
(Notice that additional v:s, starting from none, add more detail.)

Keep remote files and execute them manually
-------------------------------------------

Set the environment variable ``ANSIBLE_KEEP_REMOTE_FILES=1`` to keep files that Ansible
copied to the server so that you can execute them directly on the server yourself and thus
troubleshoot them better::

    $ export ANSIBLE_KEEP_REMOTE_FILES=1
    $ ansible-playbook ...

Then, on the server, in the home directory of the user used for ssh-ing, look into ``.ansible/tmp/ansible-<unique id>/<module name or "arguments">``. F.ex. to execute manually a command that has failed::

    $ python ./ansible-1392625678.65-85585787027596/command

Common issues
-------------

Ansible "freezes" while executing a command
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The command is perhaps waiting for user input. Always make sure to execute commands in a non-interactive mode if possible.

Try to find the command process on the server and kill it while running Ansible with ``-vvvv`` or/and use ``ANSIBLE_KEEP_REMOTE_FILES`` and run the Ansible files manually, as suggested above.