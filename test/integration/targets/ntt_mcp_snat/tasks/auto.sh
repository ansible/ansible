#!/bin/bash

ansible-playbook main.yml --check -t create
ansible-playbook main.yml -t create
ansible-playbook main.yml -t create
ansible-playbook main.yml --check -t update
ansible-playbook main.yml -t update
ansible-playbook main.yml -t create_invalid
ansible-playbook main.yml --check -t delete
ansible-playbook main.yml -t delete
ansible-playbook main.yml -t delete_by_id
ansible-playbook main.yml -t delete_noexist
