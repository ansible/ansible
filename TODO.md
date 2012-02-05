TODO list and plans
===================

Playbook TODO:

   * error codes and failure summaries
   * handle 'changed' attributes
   * fail nodes on errors, i.e. remove from host list, rather than continuing to pound them
   * further improve output
   * more conditional capability (if statement) (?)
   * very good logging

Command module:
   * magic to pull async & timeout options off of the command line and not feed them
     to the app we're executing
 
General:

   * better logging
   * async options
   * modules for users, groups, and files, using puppet style ensure mechanics
   * think about how to build idempotency (aka Puppet-style 'creates') around command module?

Bonus utilities:

   * ansible-inventory - gathering fact/hw info, storing in git, adding RSS
   * ansible-slurp - recursively rsync file trees for each host
   * maybe it's own fact engine, not required, that also feeds from facter

Not so interested really, but maybe:

   * list available modules from command line
   * add/remove/list hosts from the command line
   * filter exclusion (run this only if fact is true/false)
     -- should be doable with playbooks (i.e. not neccessary)

