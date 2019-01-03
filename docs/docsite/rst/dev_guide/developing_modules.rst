.. _developing_modules:
.. _module_dev_should_you:

****************************
Should you develop a module?
****************************

Developing Ansible modules is easy, but often it isn't necessary. Before you start writing a new module, ask:

1. Does a similar module already exist?

An existing module may cover the functionality you want. Ansible Core includes thousands of modules. Search our :ref:`list of existing modules <all_modules>` to see if there's a module that does what you need.

2. Does a Pull Request already exist?

An existing Pull Request may cover the functionality you want. If someone else has already started developing a similar module, you can review and test it. There are a few ways to find open module Pull Requests:

* `GitHub new module PRs <https://github.com/ansible/ansible/labels/new_module>`_
* `All updates to modules <https://github.com/ansible/ansible/labels/module>`_
* `New module PRs listed by directory <https://ansible.sivel.net/pr/byfile.html>`_ search for `lib/ansible/modules/`

If you find an existing PR that looks like it addresses your needs, please provide feedback on the PR. Community feedback speeds up the review and merge process.

3. Should you use or develop an action plugin instead?

An action plugin may be the best way to get the functionality you want. Action plugins run on the control node instead of on the managed node, and their functionality is available to all modules. For more information about developing plugins, read the :ref:`developing plugins page <developing_plugins>`.

4. Should you use a role instead?

A combination of existing modules may cover the functionality you want. You can write a role for this type of use case. Check out the :ref:`roles documentation<playbooks_reuse_roles>`.

5. Should you write multiple modules instead of one module?

The functionality you want may be too large for a single module. If you want to connect Ansible to a new cloud provider, database, or network platform, you may need to :ref:`develop a related group of modules<developing_modules_in_groups>`.

* Modules should have a concise and well defined functionality. Basically, follow the UNIX philosophy of doing one thing well.

* Modules should not require that a user know all the underlying options of an API/tool to be used. For instance, if the legal values for a required module parameter cannot be documented, that's a sign that the module would be rejected.

* Modules should typically encompass much of the logic for interacting with a resource. A lightweight wrapper around an API that does not contain much logic would likely cause users to offload too much logic into a playbook, and for this reason the module would be rejected. Instead try creating multiple modules for interacting with smaller individual pieces of the API.

If your use case isn't covered by an existing module, an open PR, an action plugin, or a role, and you don't need to create multiple modules, then you're ready to start developing a new module. Choose from the topics below for next steps:

* I want to :ref:`get started on a new module <developing_modules_general>`.
* I want to review :ref:`tips and conventions for developing good modules <developing_modules_best_practices>`.
* I want to :ref:`write a Windows module <developing_modules_general_windows>`.
* I want :ref:`an overview of Ansible's architecture <developing_program_flow_modules>`.
* I want to :ref:`document my module <developing_modules_documenting>`.
* I want to :ref:`contribute my module back to Ansible Core <developing_modules_checklist>`.
* I want to :ref:`add unit and integration tests to my module <developing_testing>`.
* I want to :ref:`add Python 3 support to my module <developing_python_3>`.
* I want to :ref:`write multiple modules <developing_modules_in_groups>`.

.. seealso::

   :ref:`all_modules`
       Learn about available modules
   `GitHub modules directory <https://github.com/ansible/ansible/tree/devel/lib/ansible/modules>`_
       Browse module source code
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       Development mailing list
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
