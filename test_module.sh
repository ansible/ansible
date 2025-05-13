#!/bin/bash
ansible localhost -m my_own_module -a "path=/tmp/test.txt content='Hello, Ansible!'"
