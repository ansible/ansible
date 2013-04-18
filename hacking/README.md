The 'env-setup' script modifies your environment to allow you to run
ansible from a git checkout.

To use it from the root of a checkout:

    $ source ./hacking/env-setup

Then run ansible with

    $ ansible --version

and make sure you're seeing the same version of where HEAD is at (`git show HEAD`) 

# Prerequisits

First install some packages:

    $ sudo apt-get install python-setuptools python-dev build-essential python-virtualenv

Then run these commands in the ansible root directory:

    $ virtualenv .
    $ bin/pip install pyyaml
    $ bin/pip install jinja2

