.. contents:: Topics


Callback Plugins
----------------

Callback plugins enable adding new behaviors to Ansible when responding to events.
By default, callback plugins control most of the output you see when running the command line programs,
but can also be used to add additional output, integrate with other tools and marshall the events to a storage backend.

.. _callback_examples:

Example Callback Plugins
++++++++++++++++++++++++

The :doc:`_plays <callback/log_plays>` callback is an example of how to record playbook events to a log file,
and the :doc:`mail <callback/mail>` callback sends email on playbook failures.

The :doc:`osx_say <callback/osx_say>` callback responds with computer synthesized speech on macOS in relation to playbook events.


.. _enabling_callbacks:

Enabling Callback Plugins
++++++++++++++++++++++++++

You can activate a custom callback by either dropping it into a ``callback_plugins`` directory adjacent to your play,  inside a role, or by putting it in one of the callback directory sources configured in :ref:`ansible.cfg <ansible_configuration_settings>`.

Plugins are loaded in alphanumeric order. For example, a plugin implemented in a file named `1_first.py` would run before a plugin file named `2_second.py`.

Most callbacks shipped with Ansible are disabled by default and need to be whitelisted in your :ref:`ansible.cfg <ansible_configuration_settings>` file in order to function. For example:

.. code-block:: ini

  #callback_whitelist = timer, mail, profile_roles


Managing stdout
```````````````

You can only have one plugin be the main manager of your console output. If you want to replace the default, you should define CALLBACK_TYPE = stdout in the subclass and then configure the stdout plugin in :ref:`ansible.cfg <ansible_configuration_settings>`. For example:

.. code-block:: ini

  stdout_callback = dense

or for my custom callback:

.. code-block:: ini

  stdout_callback = mycallback

This only affects :ref:`ansible-playbook` by default.

Managing AdHoc
``````````````

The :ref:`ansible` ad hoc command specifically uses a different callback plugin for stdout,
so there is an extra setting in :ref:`ansible_configuration_settings` you need to add to use the stdout callback defined above:

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

   :doc:`action`
       Ansible Action plugins
   :doc:`cache`
       Ansible cache plugins
   :doc:`connection`
       Ansible connection plugins
   :doc:`inventory`
       Ansible inventory plugins
   :doc:`shell`
       Ansible Shell plugins
   :doc:`strategy`
       Ansible Strategy plugins
   :doc:`vars`
       Ansible Vars plugins
   `User Mailing List <https://groups.google.com/forum/#!forum/ansible-devel>`_
       Have a question?  Stop by the google group!
   `webchat.freenode.net <https://webchat.freenode.net>`_
       #ansible IRC chat channel
