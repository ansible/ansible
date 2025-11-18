'Hacking' directory tools
=========================

quickstart.sh
-------------

The 'quickstart.sh' script automates the complete setup process for new Ansible
contributors. It is the recommended way to get started.

```shell
./hacking/quickstart.sh
```

This script will:
- Check system requirements (Python 3.12+, pip, git)
- Optionally create and activate a virtual environment
- Run the env-setup script to configure your environment
- Install all required dependencies from requirements.txt
- Verify the installation is working correctly
- Create a convenience activation script for future sessions

For automated/non-interactive setup (useful in CI/CD):

```shell
./hacking/quickstart.sh --silent
```

For more options, see:

```shell
./hacking/quickstart.sh --help
```

env-setup
---------

The 'env-setup' script modifies your environment to allow you to run
ansible from a git checkout using a supported Python version.

Note: If you are setting up a development environment for the first time,
consider using quickstart.sh instead, which automates this process.

First, set up your environment to run from the checkout:

```shell
source ./hacking/env-setup
```

You will need some basic prerequisites installed.  If you do not already have them
and do not wish to install them from your operating system package manager, you
can install them from pip

```shell
python -Im ensurepip  # if pip is not already available
pip install -r requirements.txt
```

From there, follow ansible instructions on docs.ansible.com as normal.

test-module.py
--------------

'test-module.py' is a simple program that allows module developers (or testers) to run
a module outside of the ansible program, locally, on the current machine.

Example:

```shell
./hacking/test-module.py -m lib/ansible/modules/command.py -a "echo hi"
```

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

```shell
./hacking/test-module.py -m module \
  -a '{"parent": {"child": [{"item": "first", "val": "foo"}, {"item": "second", "val": "bar"}]}}'
```

return_skeleton_generator.py
----------------------------

return_skeleton_generator.py helps in generating the RETURNS section of a module. It takes
JSON output of a module provided either as a file argument or via stdin.
