.. _module_contribution:

===================================
Contributing Your Module to Ansible
===================================

If you want to contribute a module to Ansible, you must meet our objective and subjective requirements. Modules accepted into the `main project repo <https://github.com/ansible/ansible>`_ ship with every Ansible installation. However, contributing to the main project isn't the only way to distribute a module - you can embed modules in roles on Galaxy or simply share copies of your module code for :ref:`local use <developing_locally>`.

Objective requirements
----------------------

* write your module in either Python or Powershell for Windows
* use the ``AnsibleModule`` common code
* support Python 2.6 and Python 3.5 - if your module cannot support Python 2.6, explain the required minimum Python version and rationale in the requirements section in ``DOCUMENTATION`` ## TODO confirm required python versions
* use proper :ref:`Python-3 syntax <developing_python_3>`
* follow `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ Python style conventions - see :ref:`testing_pep8` for more information
* license your module with GPL 3
* conform to Ansible's :ref:`formatting and documentation <developing_modules_documenting>` standards
* include comprehensive :ref:`tests <developing_modules_testing>` for your module
* minimize module dependencies
* use consistent arguments, both within your module and across Ansible modules
* support :ref:`check_mode <check_mode_dry>` if possible

Please make sure your module meets these requirements before you submit your PR/proposal. If you have questions, reach out on IRC or the mailing list.

Subjective requirements
-----------------------

If your pull request to add your module to Ansible meets our objective requirements, we'll review your code to see if we think it's clear, concise, secure, and maintainable. We'll consider whether your module provides a good user experience, helpful error messages, reasonable defaults, and more. This process is subjective, and we can't list exact standards for acceptance. For the best chance of getting your module accepted into the Ansible repo, follow our best practices for module development.

* Validate upfront--fail fast and return useful and clear error messages.
* Use defensive programming--use a simple design for your module, handle errors gracefully, and avoid direct stacktraces.
* Fail predictably--if we must fail, do it in a way that is the most expected. Either mimic the underlying tool or the general way the system works.
* Use shared code whenever possible - don't reinvent the wheel. Ansible offers base functions for many common patterns (retry, throttling, etc). ## TODO where is shared code and how does a dev use it?
* Avoid ``action``/``command``, they are imperative and not declarative, there are other ways to express the same thing.
* When fetching URLs, use ``fetch_url`` or ``open_url`` from ``ansible.module_utils.urls``. Do not use ``urllib2``, which does not natively verify TLS certificates and so is insecure for https.
* Include a ``main`` function that wraps the normal execution.
* Call your :func:`main` from a conditional so we can import it into unit tests - for example:

	.. code-block:: python

	    if __name__ == '__main__':
	        main()

* Import ``ansible.module_utils`` code in the same place as you import other libraries.
* Do not use wildcards for importing other python modules (for example, ``from ansible.module_utils.basic import *``).
* Import custom packages in ``try``/``except`` and handle them with ``fail_json()`` in ``main()``. For example:

	.. code-block:: python

	    try:
	        import foo
	        HAS_LIB=True
	    except:
	        HAS_LIB=False


Follow standard Ansible patterns
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ansible uses patterns to provide a predictable user interface across all modules, playbooks, and roles. To follow standard Ansible patterns in your module development:

* Use consistent names across modules (yes, we have many legacy deviations - don't make the problem worse!).
* Normalize parameters with other modules - if Ansible and the API your module connects to use different names for the same parameter, add aliases to your module so the user can choose which names to use in tasks and playbooks.
* Return facts from ``*_facts`` modules in the ``ansible_facts`` field of the :ref:`result dictionary<common_return_values>` so other modules can access them.
* Implement ``check_mode`` in all ``*_facts`` modules. Playbooks which conditionalize based on fact information will only conditionalize correctly in ``check_mode`` if the facts are returned in ``check_mode``. Usually you can add ``check_mode=True`` when instantiating ``AnsibleModule``.
* Use module-specific environment variables. For example, if you use the helpers in ``module_utils.api`` for basic authentication with ``module_utils.urls.fetch_url()`` and you fall back on environment variables for default values, use module-specific environment variables like :code:`API_<MODULENAME>_USERNAME` to avoid conflict between modules.
* Keep module options simple and focused - if you're loading a lot of choices/states on an existing option, consider adding a new, simple option instead.
* Keep options small when possible. Passing a large data structure to an option might save us a few tasks, but it adds a complex requirement that we cannot easily validate before passing on to the module.
* If you want to pass complex data to an option, write an expert module that allows this, along with several smaller modules that provide a more 'atomic' operation against the underlying APIs and services. Complex operations require complex data. Let the user choose whether to reflect that complexity in tasks and plays or in  vars files.
* Implement declarative operations (not CRUD) so the user can ignore existing state and focus on final state. For example, use ``started/stopped``, ``present/absent``.
* Strive for a consistent final state (aka idempotency). If running your module twice in a row against the same system would result in two different states, see if you can redesign or rewrite to achieve consistent final state. If you can't, document the behavior and the reasons for it.
* Provide consistent return values within the standard Ansible return structure, even if NA/None are used for keys normally returned under other options.
* Follow additional guidelines that apply to families of modules if applicable. For example, AWS modules should follow ` the Amazon guidelines <https://github.com/ansible/ansible/blob/devel/lib/ansible/modules/cloud/amazon/GUIDELINES.md>`_


Windows modules checklist
=========================

For a checklist and details on how to write Windows modules please see :doc:`developing_modules_general_windows`
