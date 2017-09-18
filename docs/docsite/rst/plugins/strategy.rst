Strategy Plugins
----------------

Strategy plugins control the flow of play execution, they handle task and host scheduleing.


Enabling Cache Plugins
++++++++++++++++++++++

Only one stragy plugin can be used in a play, but you can use different ones for each play in a playbook or ansible run.
The default is the :doc:`linear strategy/linear` plugin, you can change this default via :doc:`.configuration  ./config`.:

.. code-block:: shell

    export ANSIBLE_STRATEGY=free

or in the `ansible.cfg` file:

.. code-block:: ini

    [defaults]
    strategy=linear

Or you can just speicfy the plugin in the play via the :ref:`strategy` keyword::

  - hosts: all
    strategy: debug
    tasks:
      - copy: src=myhosts dest=/etc/hosts
        notify: restart_tomcat

      - package: name=tomcat state=present

    handlers:
      - name: restart_tomcat
        service: name=tomcat state=restarted


You can use ``ansible-doc -t strategy -l`` to see the list of available plugins,
use ``ansible-doc -t strategy <plugin name>`` to see specific documents and examples.


.. toctree:: :maxdepth: 1
    :glob:

    strategy/*

.. seealso::

   :doc:`../playbooks`
       An introduction to playbooks
   :doc:`inventory`
       Ansible inventory plugins
   :doc:`callback`
       Ansible callback plugins
   :doc:`../playbooks_filters`
       Jinja2 filter plugins
   :doc:`../playbooks_tests`
       Jinja2 test plugins
   :doc:`../playbooks_lookups`
       Jinja2 lookup plugins
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
