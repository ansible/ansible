'Hacking' directory tools
=========================

Env-setup
---------

The 'env-setup' script modifies your environment to allow you to run
ansible from a git checkout using python 2.6+.  (You may not use
python 3 at this time).

First, set up your environment to run from the checkout:

    $ source ./hacking/env-setup

You will need some basic prerequisites installed.  If you do not already have them
and do not wish to install them from your operating system package manager, you
can install them from pip

    $ easy_install pip               # if pip is not already available
    $ pip install -r requirements.txt

From there, follow ansible instructions on docs.ansible.com as normal.

Test-module
-----------

'test-module' is a simple program that allows module developers (or testers) to run
a module outside of the ansible program, locally, on the current machine.

Example:

    $ ./hacking/test-module -m lib/ansible/modules/commands/shell -a "echo hi"

This is a good way to insert a breakpoint into a module, for instance.

For more complex arguments such as the following yaml:

```yaml
parent:
  child:
    - item: first
      val: foo
    - item: second
      val: boo
```

Use:

    $ ./hacking/test-module -m module \
        -a '{"parent": {"child": [{"item": "first", "val": "foo"}, {"item": "second", "val": "bar"}]}}'

Module-formatter
----------------

The module formatter is a script used to generate manpages and online
module documentation.  This is used by the system makefiles and rarely
needs to be run directly.

Authors
-------
'authors' is a simple script that generates a list of everyone who has
contributed code to the ansible repository.


