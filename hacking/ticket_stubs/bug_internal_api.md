Hi!

Thanks very much for your submission to Ansible.  It means a lot to us
to have an active community that is willing to submit feedback so that we can
continue to make Ansible better.

The Ansible Python API is considered internal and an unsupported aspect of Ansible,
as such this is not considered a bug unless it causes an issue with Ansible command line tools
(`ansible`, `ansible-playbook`, `ansible-doc`, etc).

We do support the provided API for use in developing plugins (modules, dynamic inventories, callbacks, strategies, etc),
but this does not seem to match that case.

If you really need a stable API target to use Ansible, consider using ansible-runner:

* <https://github.com/ansible/ansible-runner>

Because this project is very active, we're unlikely to see comments made on closed tickets and we lock them after some time.
If you or anyone else has any further questions, please let us know by using any of the communication methods listed in the page below:

* <https://docs.ansible.com/ansible/latest/community/communication.html>

Thank you once again for this and your interest in Ansible!
