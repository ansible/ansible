.. _playbooks_templating:

*******************
Templating (Jinja2)
*******************

Ansible uses Jinja2 templating to enable dynamic expressions and access to :ref:`variables <playbooks_variables>` and :ref:`facts <vars_and_facts>`.
You can use templating with the :ref:`template module <template_module>`.
For example, you can create a template for a configuration file, then deploy that configuration file to multiple environments and supply the correct data (IP address, hostname, version) for each environment.
You can also use templating in playbooks directly, by templating task names and more.
You can use all the :ref:`standard filters and tests <jinja2:builtin-filters>` included in Jinja2.
Ansible includes additional specialized filters for selecting and transforming data, tests for evaluating template expressions, and :ref:`lookup_plugins` for retrieving data from external sources such as files, APIs, and databases for use in templating.

All templating happens on the Ansible controller **before** the task is sent and executed on the target machine.
This approach minimizes the package requirements on the target (jinja2 is only required on the controller).
It also limits the amount of data Ansible passes to the target machine.
Ansible parses templates on the controller and passes only the information needed for each task to the target machine, instead of passing all the data on the controller and parsing it on the target.

.. note::

   Files and data used by the :ref:`template module <template_module>` must be utf-8 encoded.
   
Jinja2 Example
==================

In this example, we want to write the server hostname to its /tmp/hostname.

Our directory looks like this:
  
.. code-block:: 

    ├── hostname.yml
    ├── templates
        └── test.j2

Our hostname.yml:

.. code-block:: yaml

    ---
    - name: Write hostname
      hosts: all
      tasks:
      - name: write hostname using jinja2
        template:
           src: templates/test.j2
           dest: /tmp/hostname

Our test.j2:

.. code-block:: yaml

    My name is {{ ansible_facts['hostname'] }}
  

.. seealso::

   :ref:`playbooks_intro`
       An introduction to playbooks
   :ref:`playbook_tips`
       Tips and tricks for playbooks
   `Jinja2 Docs <https://jinja.palletsprojects.com/en/latest/templates/>`_
      Jinja2 documentation, includes the syntax and semantics of the templates
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   :ref:`communication_irc`
       How to join Ansible chat channels
