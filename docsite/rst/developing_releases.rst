Releases
========

.. contents:: Topics
   :local:

.. _schedule:

Release Schedule
````````````````
Ansible is on a 'flexible' 4 month release schedule, sometimes this can be extended if there is a major change that requires a longer cycle (i.e. 2.0 core rewrite).
Currently modules get released at the same time as the main Ansible repo, even though they are separated into ansible-modules-core and ansible-modules-extras.

The major features and bugs fixed in a release should be reflected in the CHANGELOG.md, minor ones will be in the commit history (FIXME: add git exmaple to list).
When a fix/feature gets added to the `devel` branch it will be part of the next release, some bugfixes can be backported to previous releases and might be part of a minor point release if it is deemed necessary.

Sometimes an RC can be extended by a few days if a bugfix makes a change that can have far reaching consequences, so users have enough time to find any new issues that may stem from this.

.. _methods:

Release methods
````````````````

Ansible normally goes through a 'release candidate', issuing an RC1 for a release, if no major bugs are discovered in it after 5 business days we'll get a final release.
Otherwise fixes will be applied and an RC2 will be provided for testing and if no bugs after 2 days, the final release will be made, iterating this last step and incrementing the candidate number as we find major bugs.


.. _freezing:

Release feature freeze
``````````````````````

During the release candidate process, the focus will be on bugfixes that affect the RC, new features will be delayed while we try to produce a final version. Some bugfixes that are minor or don't affect the RC will also be postponed until after the release is finalized.

.. seealso::

   :doc:`developing_api`
       Python API to Playbooks and Ad Hoc Task Execution
   :doc:`developing_modules`
       How to develop modules
   :doc:`developing_plugins`
       How to develop plugins
   `Ansible Tower <http://ansible.com/ansible-tower>`_
       REST API endpoint and GUI for Ansible, syncs with dynamic inventory
   `Development Mailing List <http://groups.google.com/group/ansible-devel>`_
       Mailing list for development topics
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
