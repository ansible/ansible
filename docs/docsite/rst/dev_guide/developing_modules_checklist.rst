.. _module_contribution:

===================================
Contributing Your Module to Ansible
===================================

High-quality modules with minimal dependencies
can be included in Ansible, but modules (just due to the programming
preferences of the developers) will need to be implemented in Python and use
the AnsibleModule common code, and should generally use consistent arguments with the rest of
the program.   Stop by the mailing list to inquire about requirements if you like, and submit
a github pull request to the `ansible <https://github.com/ansible/ansible>`_ project.
Included modules will ship with ansible, and also have a chance to be promoted to 'core' status, which
gives them slightly higher development priority (though they'll work in exactly the same way).

.. formerly marked with _module_dev_testing:

------------------------------
Contributing Modules Checklist
------------------------------

The following  checklist items are important guidelines for people who want to contribute to the development of modules to Ansible on GitHub. Please read the guidelines before you submit your PR/proposal.

* The shebang must always be ``#!/usr/bin/python``.  This allows ``ansible_python_interpreter`` to work
* Modules must be written to support Python 2.6. If this is not possible, required minimum Python version and rationale should be explained in the requirements section in ``DOCUMENTATION``.  In Ansible-2.3 the minimum requirement for modules was Python-2.4.
* Modules must be written to use proper Python-3 syntax.  At some point in the future we'll come up with rules for running on Python-3 but we're not there yet.  See :doc:`developing_python3` for help on how to do this.
* Modules must have a metadata section.  For the vast majority of new modules,
  the metadata should look exactly like this:

.. code-block:: python

    ANSIBLE_METADATA = {'status': ['preview'],
                        'supported_by': 'community',
                        'metadata_version': '1.0'}

The complete module metadata specification is here: `Ansible metadata block <https://docs.ansible.com/ansible/dev_guide/developing_modules_documenting.html#ansible-metadata-block>`_

* Documentation: Make sure it exists
    * Module documentation should briefly and accurately define what each module and option does, and how it works with others in the underlying system. Documentation should be written for broad audience--readable both by experts and non-experts. This documentation is not meant to teach a total novice, but it also should not be reserved for the Illuminati (hard balance).
    * Descriptions should always start with a capital letter and end with a full stop. Consistency always helps.
    * The `required` setting is only required when true, otherwise it is assumed to be false.
    * If `required` is false/missing, `default` may be specified (assumed 'null' if missing). Ensure that the default parameter in docs matches default parameter in code.
    * Documenting `default` is not needed for `required: true`.
    * Remove unnecessary doc like `aliases: []` or `choices: []`.
    * Do not use Boolean values in a choice list . For example, in the list `choices: ['no', 'verify', 'always]`, 'no' will be interpreted as a Boolean value (you can check basic.py for BOOLEANS_* constants to see the full list of Boolean keywords). If your option actually is a boolean, just use `type=bool`; there is no need to populate 'choices'.
    * For new modules or options in a module add version_added. The version should match the value of the current development version and is a string (not a float), so be sure to enclose it in quotes.
    * Verify that arguments in doc and module spec dict are identical.
    * For password / secret arguments no_log=True should be set.
    * Requirements should be documented, using the `requirements=[]` field.
    * Author should be set, with their name and their github id, at the least.
    * Ensure that you make use of `U()` for URLs, `I()` for option names, `C()` for files and option values, `M()` for module names.
    * If an optional parameter is sometimes required this need to be reflected in the documentation, e.g. "Required when C(state=present)."
    * Verify that a GPL 3 License header is included.
    * Does module use check_mode? Could it be modified to use it? Document it. Documentation is everyone's friend.
    * Examples--include them whenever possible and make sure they are reproducible.
    * Document the return structure of the module. Refer to :ref:`common_return_values` and :ref:`module_documenting` for additional information.
* Predictable user interface: This is a particularly important section as it is also an area where we need significant improvements.
    * Name consistency across modules (we’ve gotten better at this, but we still have many deviations).
    * Declarative operation (not CRUD)--this makes it easy for a user not to care what the existing state is, just about the final state. ``started/stopped``, ``present/absent``--don't overload options too much. It is preferable to add a new, simple option than to add choices/states that don't fit with existing ones.
    * Keep options small, having them take large data structures might save us a few tasks, but adds a complex requirement that we cannot easily validate before passing on to the module.
    * Allow an "expert mode". This may sound like the absolute opposite of the previous one, but it is always best to let expert users deal with complex data. This requires different modules in some cases, so that you end up having one (1) expert module and several 'piecemeal' ones (ec2_vpc_net?). The reason for this is not, as many users express, because it allows a single task and keeps plays small (which just moves the data complexity into vars files, leaving you with a slightly different structure in another YAML file). It does, however, allow for a more 'atomic' operation against the underlying APIs and services.
* Informative responses: Please note, that for  >= 2.0, it is required that return data to be documented.
    * Always return useful data, even when there is no change.
    * Be consistent about returns (some modules are too random), unless it is detrimental to the state/action.
    * Make returns reusable--most of the time you don't want to read it, but you do want to process it and re-purpose it.
    * Return diff if in diff mode. This is not required for all modules, as it won't make sense for certain ones, but please attempt to include this when applicable).
* Code: This applies to all code in general, but often seems to be missing from modules, so please keep the following in mind as you work.
    * Validate upfront--fail fast and return useful and clear error messages.
    * Defensive programming--modules should be designed simply enough that this should be easy. Modules should always handle errors gracefully and avoid direct stacktraces. Ansible deals with this better in 2.0 and returns them in the results.
    * Fail predictably--if we must fail, do it in a way that is the most expected. Either mimic the underlying tool or the general way the system works.
    * Modules should not do the job of other modules, that is what roles are for. Less magic is more.
    * Don't reinvent the wheel. Part of the problem is that code sharing is not that easy nor documented, we also need to expand our base functions to provide common patterns (retry, throttling, etc).
    * Support check mode. This is not required for all modules, as it won't make sense for certain ones, but please attempt to include this when applicable). For more information, refer to :ref:`check_mode_drift` and :ref:`check_mode_dry`.
* Exceptions: The module must handle them. (exceptions are bugs)
    * Give out useful messages on what you were doing and you can add the exception message to that.
    * Avoid catchall exceptions, they are not very useful unless the underlying API gives very good error messages pertaining the attempted action.
* Module-dependent guidelines: Additional module guidelines may exist for certain families of modules.
    * Be sure to check out the modules themselves for additional information.
        * `Amazon <https://github.com/ansible/ansible/blob/devel/lib/ansible/modules/cloud/amazon/GUIDELINES.md>`_
    * Modules should make use of the "extends_documentation_fragment" to ensure documentation available. For example, the AWS module should include::

        extends_documentation_fragment:
            - aws
            - ec2

* The module must not use sys.exit() --> use fail_json() from the module object.
* Import custom packages in try/except and handled with fail_json() in main() e.g.

.. code-block:: python

    try:
        import foo
        HAS_LIB=True
    except:
        HAS_LIB=False

* The return structure should be consistent, even if NA/None are used for keys normally returned under other options.
* Are module actions idempotent? If not document in the descriptions or the notes.
* Import ``ansible.module_utils`` code in the same place as you import other libraries.  In older code, this was done at the bottom of the file but that's no longer needed.
* Do not use wildcards for importing other python modules (ex: ``from ansible.module_utils.basic import *``).  This used to be required for code imported from ``ansible.module_utils`` but, from Ansible-2.1 onwards, it's just an outdated and bad practice.
* The module must have a `main` function that wraps the normal execution.
* Call your :func:`main` from a conditional so that it would be possible to
  import them into unittests in the future example

.. code-block:: python

    if __name__ == '__main__':
        main()

* Try to normalize parameters with other modules, you can have aliases for when user is more familiar with underlying API name for the option
* Being `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ compliant is a requirement. See :doc:`testing_pep8` for more information.
* Avoid '`action`/`command`', they are imperative and not declarative, there are other ways to express the same thing
* Do not add `list` or `info` state options to an existing module - create a new `_facts` module.
* If you are asking 'how can I have a module execute other modules' ... you want to write a role
* Return values must be able to be serialized as json via the python stdlib
  json library.  basic python types (strings, int, dicts, lists, etc) are
  serializable.  A common pitfall is to try returning an object via
  exit_json().  Instead, convert the fields you need from the object into the
  fields of a dictionary and return the dictionary.
* When fetching URLs, please use either fetch_url or open_url from ansible.module_utils.urls 
  rather than urllib2; urllib2 does not natively verify TLS certificates and so is insecure for https. 
* facts modules must return facts in the ansible_facts field of the result
  dictionary. :ref:`module_provided_facts`
* modules that are purely about fact gathering need to implement check_mode.
  they should not cause any changes anyway so it should be as simple as adding
  check_mode=True when instantiating AnsibleModule.  (The reason is that
  playbooks which conditionalize based on fact information will only
  conditionalize correctly in check_mode if the facts are returned in
  check_mode).
* Basic auth: module_utils.api has some helpers for doing basic auth with
  module_utils.urls.fetch_url().  If you use those you may find you also want
  to fallback on environment variables for default values.  If you do that,
  be sure to use non-generic environment variables (like
  :envvar:`API_<MODULENAME>_USERNAME`).  Using generic environment variables
  like :envvar:`API_USERNAME` would conflict between modules.

Windows modules checklist
=========================

For a checklist and details on how to write Windows modules please see :doc:`developing_modules_general_windows`


Deprecating and making module aliases
======================================

Starting in 1.8, you can deprecate modules by renaming them with a preceding ``_``, i.e. ``old_cloud.py`` to
``_old_cloud.py``. This keeps the module available, but hides it from the primary docs and listing.

When deprecating a module:

1) Set the ``ANSIBLE_METADATA`` `status` to `deprecated`.
2) In the ``DOCUMENTATION`` section, add a `deprecated` field along the lines of::

    deprecated: Deprecated in 2.3. Use M(whatmoduletouseinstead) instead.

3) Add the deprecation to CHANGELOG.md under the ``###Deprecations:`` section.

Alias module names
------------------

You can also rename modules and keep an alias to the old name by using a symlink that starts with _.
This example allows the stat module to be called with fileinfo, making the following examples equivalent::

    EXAMPLES = '''
    ln -s stat.py _fileinfo.py
    ansible -m stat -a "path=/tmp" localhost
    ansible -m fileinfo -a "path=/tmp" localhost
    '''
