Module Support
--------------

.. toctree:: :maxdepth: 1

Ansible has many modules, but not all of them are maintained by the core project committers. Each module should have associated metadata that indicates which of the following categories they fall into. This should be visible in each module's documentation.

Documentation updates for each module can also be edited directly in the module and by submitting a pull request to the module source code; just look for the "DOCUMENTATION" block in the source tree.

If you believe you have found a bug in a module and are already running the latest stable or development version of Ansible, first look in the `issue tracker at github.com/ansible/ansible <https://github.com/ansible/ansible/issues>`_ to see if a bug has already been filed.  If not, we would be grateful if you would file one.

Should you have a question rather than a bug report, inquiries are welcome on the `ansible-project google group <https://groups.google.com/forum/#!forum/ansible-project>`_ or on Ansible's "#ansible" channel, located on irc.freenode.net.

For development-oriented topics, use the `ansible-devel google group <https://groups.google.com/forum/#!forum/ansible-devel>`_  or Ansible's ``#ansible`` and ``#ansible-devel`` channels, located on irc.freenode.net.  You should also read :doc:`community`, :doc:`dev_guide/testing` and :doc:`dev_guide/developing_modules`.

The modules are hosted on GitHub in a subdirectory of the `ansible <https://github.com/ansible/ansible/tree/devel/lib/ansible/modules>`_ repo.

Core
````

These are modules that the core ansible team maintains and will always ship with ansible itself.
They will also receive slightly higher priority for all requests. Non-core modules are still fully usable.

Curated
```````

Some examples of Curated modules are submitted by other companies or maintained by the community. Maintainers of these types of modules must watch for any issues reported or pull requests raised against the module.

Core Committers will review all modules becoming Curated.  Core Committers will review proposed changes to existing Curated modules once the community maintainers of the module have approved the changes. Core committers will also ensure that any issues that arise due to Ansible engine changes will be remediated.
Also, it is strongly recommended (but not presently required) for these types of modules to have unit tests.

These modules are currently shipped with Ansible, but might be shipped separately in the future.

Community
`````````
These modules **are not** supported by Core Committers or by companies/partners associated to the module. They are maintained by the community.

They are still fully usable, but the response rate to issues is purely up to the community.  Best effort support will be provided but is not covered under any support contracts.

These modules are currently shipped with Ansible, but will most likely be shipped separately in the future.


.. seealso::

   :doc:`intro_adhoc`
       Examples of using modules in /usr/bin/ansible
   :doc:`playbooks`
       Examples of using modules with /usr/bin/ansible-playbook
   :doc:`dev_guide/developing_modules`
       How to write your own modules
   :doc:`dev_guide/developing_api`
       Examples of using modules with the Python API
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
