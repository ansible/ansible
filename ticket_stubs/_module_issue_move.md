Module Repo Information
=======================

Hi!

Thanks very much for your interest in Ansible.  It sincerely means a lot to us. 

On September 26, 2014, due to enormous levels of contribution to the project Ansible decided to reorganize module repos, making it easier
for developers to work on the project and for us to more easily manage new contributions and tickets.

We split modules from the main project off into two repos, http://github.com/ansible/ansible-modules-core and http://github.com/ansible/ansible-modules-extras

If you would still like this ticket attended to, we will need your help in having it reopened in one of the two new repos, and instructions are provided below.

We apologize that we are not able to make this transition happen seamlessly, though this is a one-time change and your help is greatly appreciated -- 
this will greatly improve velocity going forward.

Both sets of modules will ship with Ansible, though they'll receive slightly different ticket handling.

To locate where a module lives between 'core' and 'extras'

   * Find the module at http://docs.ansible.com/list_of_all_modules.html
   * Open the documentation page for that module
   * If the bottom of the docs say "This is an extras module", submit your ticket to https://github.com/ansible/ansible-modules-extras
   * Otherwise, submit your pull request to update the existing module to https://github.com/ansible/ansible-modules-core
   * action_plugins (modules with server side components) still live in the main repo.  If your ticket affects both, open the ticket
     on the module repo just the same.

Additionally, should you need more help with this, you can ask questions on:

   * the ansible-project mailing list: https://groups.google.com/forum/#!forum/ansible-project

Thank you very much!


