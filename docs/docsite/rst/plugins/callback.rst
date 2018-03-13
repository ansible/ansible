.. contents:: Topics


Callback Plugins
----------------

Callback plugins enable adding new behaviors to Ansible when responding to events.
By default, callback plugins control most of the output you see when running the command line programs,
but can also be used to add additional output, integrate with other tools and marshall the events to a storage backend.

.. _callback_examples:

Example Callback Plugins
++++++++++++++++++++++++

The :doc:`log_plays <callback/log_plays>` callback is an example of how to record playbook events to a log file,
and the :doc:`mail <callback/mail>` callback sends email on playbook failures.

The :doc:`osx_say <callback/oxs_say>` callback responds with computer synthesized speech on OS X in relation to playbook events.


.. _enabling_callbacks:

Enabling Callback Plugins
++++++++++++++++++++++++++

You can activate a custom callback by either dropping it into a ``callback_plugins`` directory adjacent to your play,  inside a role, or by putting it in one of the callback directory sources configured in :doc:`ansible.cfg <../config>`.

Plugins are loaded in alphanumeric order. For example, a plugin implemented in a file named `1_first.py` would run before a plugin file named `2_second.py`.

Most callbacks shipped with Ansible are disabled by default and need to be whitelisted in your :doc:`ansible.cfg <../config>` file in order to function. For example:

.. code-block:: ini

  #callback_whitelist = timer, mail, profile_roles


Managing stdout
```````````````

You can only have one plugin be the main manager of your console output. If you want to replace the default, you should define CALLBACK_TYPE = stdout in the subclass and then configure the stdout plugin in :doc:`ansible.cfg <../config>`. For example:

.. code-block:: ini

  stdout_callback = dense

or for my custom callback:

.. code-block:: ini

  stdout_callback = mycallback

This only affects :doc:`../ansible-playbook` by default.

Managing AdHoc
``````````````

The :doc:`ansible <../ansible>` AdHoc command specifically uses a different callback plugin for stdout,
so there is an extra setting in :doc:`ansible.cfg <../config>` you need to add to use the stdout callback defined above:

.. code-block:: ini

    [defaults]
    bin_ansible_callbacks=True

You can also set this as an environment variable:

.. code-block:: shell

    export ANSIBLE_LOAD_CALLBACK_PLUGINS=1


.. _callback_plugin_list:

Plugin List
+++++++++++

You can use ``ansible-doc -t callback -l`` to see the list of available plugins. 
Use ``ansible-doc -t callback <plugin name>`` to see specific documents and examples.


.. toctree:: :maxdepth: 1
    :glob:

    callback/*


.. seealso::

   :doc:`../playbooks`
       An introduction to playbooks
   :doc:`inventory`
       Ansible inventory plugins
   :doc:`../playbooks_filters`
       Jinja2 filter plugins
   :doc:`../playbooks_tests`
       Jinja2 test plugins
   :doc:`../playbooks_lookups`
       Jinja2 lookup plugins
   :doc:`vars`
       Ansible vars plugins
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
