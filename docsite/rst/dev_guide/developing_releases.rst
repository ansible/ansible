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

.. _methods:

Release methods
```````````````

Ansible normally goes through a 'release candidate', issuing an RC1 for a release, if no major bugs are discovered in it after 5 business days we'll get a final release.
Otherwise fixes will be applied and an RC2 will be provided for testing and if no bugs after 2 days, the final release will be made, iterating this last step and incrementing the candidate number as we find major bugs.

Sometimes an RC can be extended by a few days if a bugfix makes a change that can have far reaching consequences, so users have enough time to find any new issues that may stem from this.


.. _freezing:

Release feature freeze
``````````````````````

During the release candidate process, the focus will be on bugfixes that affect the RC, new features will be delayed while we try to produce a final version.
Subsequent release candidates will include fixes only for severe bugs or for bugs introduced by the new release.

.. _included:

Release types
`````````````

* Major release - e.g. Ansible 2.2 - will include all of the fixes and features added to the `devel` branch at the time of the feature freeze prior to the first release candidate.
* Current minor release - e.g. Ansible 2.1.2 - will include any bug fixes that are in the appropriate `stable` branch (e.g. `stable-2.1`)
  for the version at the time of the feature freeze for the first release candidate.
* Older minor releases - e.g. Ansible 2.0.3 - will include bug fixes for severe issues found in older versions of Ansible from the related `stable` branch (e.g. `stable-2.0`).

Before creating a minor release candidate, the closed PRs with a milestone for the release should be reviewed to check if they to check if they need cherry picking.
For example, candidates for the 2.1.3 release will be found at: https://github.com/ansible/ansible-modules-core/pulls?q=is%3Apr%20is%3Aclosed%20milestone%3A2.1.3%20label%3Abugfix_pull_request
At the same time, filter that same list with an `affects_2.0` label (or whatever the previous release is at the time) to see if there are any candidates for backporting to even older versions.
Open PRs with that milestone should be changed to either the next minor release or the next major release, depending on which is likely to be first.


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
