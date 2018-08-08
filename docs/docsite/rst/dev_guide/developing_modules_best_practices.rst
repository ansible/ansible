.. _module_dev_conventions:

Conventions, Best Practices, and Pitfalls
`````````````````````````````````````````

As you develop your module, follow these basic conventions and best practices:

* Each module should be self-contained in one file, so it can be be auto-transferred by Ansible.

* Always use the ``hacking/test-module`` script when developing modules - it will warn you about common pitfalls.

* If your module is addressing an object, the parameter for that object should be called ``name`` whenever possible, or accept ``name`` as an alias.

* If you have a local module that returns facts specific to your installations, a good name for this module is ``site_facts``.

* Modules accepting boolean status should generally accept ``yes``, ``no``, ``true``, ``false``, or anything else a user may likely throw at them. The AnsibleModule common code supports this with ``type='bool'``.

* Eliminate or minimize dependencies. If your module has dependencies, document them at the top of the module file and raise JSON error messages when dependency import fails.

* If you package your module(s) in an RPM, install the modules on the control machine in ``/usr/share/ansible``. Packaging modules in RPMs is optional.

* As results from many hosts will be aggregated at once, modules should return only relevant output. Returning the entire contents of a log file is generally bad form.

* Don't write to files directly; use a temporary file and then use the `atomic_move` function from `ansible.module_utils.basic` to move the updated temporary file into place. This prevents data corruption and ensures that the correct context for the file is kept.

* Avoid creating caches. Ansible is designed without a central server or authority, so you cannot guarantee it will not run with different permissions, options or locations. If you need a central authority, have it on top of Ansible (for example, using bastion/cm/ci server or tower); do not try to build it into modules.

* Handle exceptions (bugs) gracefully
    * Give out a useful message on what you were doing and add exception messages to that.
    * Avoid catchall exceptions, they are not very useful unless the underlying API gives very good error messages pertaining the attempted action.

Scoping your module(s)
```````````````````````

Especially if you want to contribute your module back to Ansible Core, make sure it includes enough logic and functionality, but not too much. If you're finding these guidelines tricky, consider :ref:`whether you really need to write a module <module_dev_should_you>` at all.

* Each module should have a concise and well-defined functionality. Basically, follow the UNIX philosophy of doing one thing well.

* Do not add `list` or `info` state options to an existing module - create a new `_facts` module.

* Modules should not require that a user know all the underlying options of an API/tool to be used. For instance, if the legal values for a required module parameter cannot be documented, the module does not belong in Ansible Core.

* Modules should encompass much of the logic for interacting with a resource. A lightweight wrapper around a complex API forces users to offload too much logic into their playbooks. If you want to connect Ansible to a complex API, create multiple modules that interact with smaller individual pieces of the API.

* Avoid creating a module that does the work of other modules; this leads to code duplication and divergence, and makes things less uniform, unpredictable and harder to maintain. Modules should be the building blocks. If you are asking 'how can I have a module execute other modules' ... you want to write a role. 
Instead of creating a module that does the work of other modules, use Plays and Roles to meet your needs.

Handling module failures
`````````````````````````````````````````

When you module fails, help users understand what went wrong. If you are using the AnsibleModule common Python code, the 'failed' element will be included for you automatically when you call ``fail_json``. For polite module failure behavior:

* Include a key of ``failed`` along with a string explanation in ``msg``. If you don't do this, Ansible will use standard return codes: 0=success and non-zero=failure.
* Don't raise a traceback (stacktrace). Ansible can deal with stacktraces and automatically converts anything unparseable into a failed result, but raising a stacktrace on module failure is not user-friendly.
* Do not use ``sys.exit()``. Use ``fail_json()`` from the module object.

Creating correct and informative module output
`````````````````````````````````````````````````````````````````

Modules must output valid JSON only. Follow these guidelines for creating correct, useful module output:

* Make your top-level return type a hash (dictionary).
* Nest complex return values within the top-level hash.
* Incorporate any lists or simple scalar values within the top-level return hash.
* Do not send module output to standard error, because the system will merge standard out with standard error and prevent the JSON from parsing.
* Capture standard error and return it as a variable in the JSON on standard out. This is how the command module is implemented.
* Never do ``print("some status message")`` in a module, because it will not produce valid JSON output.
* Always return useful data, even when there is no change.
* Be consistent about returns (some modules are too random), unless it is detrimental to the state/action.
* Make returns reusable--most of the time you don't want to read it, but you do want to process it and re-purpose it.
* Return diff if in diff mode. This is not required for all modules, as it won't make sense for certain ones, but please include it when applicable.
* Enable your return values to be serialized as JSON with Python's standard `JSON encoder and decoder <https://docs.python.org/3/library/json.html>`_ library. Basic python types (strings, int, dicts, lists, etc) are serializable.  
* Do not return an object via exit_json(). Instead, convert the fields you need from the object into the fields of a dictionary and return the dictionary.

If a module returns stderr or otherwise fails to produce valid JSON, the actual output will still be shown in Ansible, but the command will not succeed.
