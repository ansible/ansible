.. _module_dev_conventions:

Conventions, Best Practices, and Pitfalls
`````````````````````````````````````````

As you develop your module, follow these basic conventions and guidelines:

* Modules should have a concise and well-defined functionality. Basically, follow the UNIX philosophy of doing one thing well.

* Each module should be self-contained in one file, so it can be be auto-transferred by Ansible.

* If your module is addressing an object, the parameter for that object should be called ``name`` whenever possible, or accept ``name`` as an alias.

* If you have a local module that returns facts specific to your installations, a good name for this module is ``site_facts``.

* Modules accepting boolean status should generally accept ``yes``, ``no``, ``true``, ``false``, or anything else a user may likely throw at them. The AnsibleModule common code supports this with ``type='bool'``.

* Eliminate or minimize dependencies. If your module has dependencies, document them at the top of the module file and raise JSON error messages when the import fails.

* If you package your module(s) in an RPM, install them on the control machine in ``/usr/share/ansible``. Packaging modules in RPMs is optional.

* Modules must output valid JSON only. The top level return type must be a hash (dictionary) although they can be nested. Lists or simple scalar values are not supported, though they can be trivially contained inside a dictionary.

* In the event of failure, a key of ``failed`` should be included, along with a string explanation in ``msg``.  Modules that raise tracebacks (stacktraces) are generally considered 'poor' modules, though Ansible can deal with these returns and will automatically convert anything unparseable into a failed result.  If you are using the AnsibleModule common Python code, the 'failed' element will be included for you automatically when you call ``fail_json``.

* Return codes from modules are used if 'failed' is missing, 0=success and non-zero=failure.

* As results from many hosts will be aggregated at once, modules should return only relevant output. Returning the entire contents of a log file is generally bad form.

* Modules should not require that a user know all the underlying options of an API/tool to be used. For instance, if the legal values for a required module parameter cannot be documented, that's a sign that the module would be rejected.

* Modules should encompass much of the logic for interacting with a resource. A lightweight wrapper around an API that does not contain much logic would likely cause users to offload too much logic into a playbook, and for this reason the module would be rejected. Instead try creating multiple modules for interacting with smaller individual pieces of the API.

Common Pitfalls
```````````````

You should never do this in a module:

.. code-block:: python

    print("some status message")

Because the output is supposed to be valid JSON.

Modules must not output anything on standard error, because the system will merge
standard out with standard error and prevent the JSON from parsing. Capturing standard
error and returning it as a variable in the JSON on standard out is fine, and is, in fact,
how the command module is implemented.

If a module returns stderr or otherwise fails to produce valid JSON, the actual output
will still be shown in Ansible, but the command will not succeed.

Don't write to files directly; use a temporary file and then use the `atomic_move` function from `ansible.module_utils.basic` to move the updated temporary file into place. This prevents data corruption and ensures that the correct context for the file is kept.

Avoid creating a module that does the work of other modules; this leads to code duplication and divergence, and makes things less uniform, unpredictable and harder to maintain. Modules should be the building blocks. Instead of creating a module that does the work of other modules, use Plays and Roles instead.  

Avoid creating 'caches'. Ansible is designed without a central server or authority, so you cannot guarantee it will not run with different permissions, options or locations. If you need a central authority, have it on top of Ansible (for example, using bastion/cm/ci server or tower); do not try to build it into modules.

Always use the hacking/test-module script when developing modules and it will warn you about these kind of things.
