TODO list and plans
===================

Playbook TODO:

   * error codes and failure summaries
   * create modules that return 'changed' attributes
   * fail nodes on errors, i.e. remove from host list, rather than continuing to pound them
   * further improve output
   * more conditional capability
   * very good logging

Command module:
   * allow additional key/value options to be passed to any module (via ENV vars?)
   * allow this to be expressed in playbook as a 4th option after the array options list
   * use this to pass timeout and async params to the command module
     default timeouts will be infinite, async False

General:

   * logging
   * async options
   * modules for users, groups, and files, using puppet style ensure mechanics
   * very simple option constructing/parsing for modules
   * templating module (how might this work syntax wise?) with facter/ohai awareness
      * probably could lay down a values.json file 
      * use copy capabilities to move files to tmp, run python templating
      * maybe support templating engine of choice
   * think about how to build idempotency guards around command module?
   * think about how to feed extra JSON data onto system

Bonus utilities:

   * ansible-inventory - gathering fact/hw info, storing in git, adding RSS
   * ansible-slurp - recursively rsync file trees for each host
   * maybe it's own fact engine, not required, that also feeds from facter

Not so interested really, but maybe:

   * list available modules from command line
   * add/remove/list hosts from the command line
   * filter exclusion (run this only if fact is true/false)
     -- should be doable with playbooks (i.e. not neccessary)

