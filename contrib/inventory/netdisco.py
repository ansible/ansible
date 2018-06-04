#!/usr/bin/python
# -*- coding: utf-8 -*-
# Dynamic inventory script for the web-based network management tool
# Netdisco. Created by Maksim Nikiforov.
# All information is extracted from Netdisco's  PostgreSQL database

import json
import psycopg2


def main():
    """Create JSON output for Ansible"""
    conn_string = \
        "host='localhost' dbname='netdisco' user='netdisco' password='redhat'"

    # Make the connection
    conn = psycopg2.connect(conn_string)
    # Return a cursor object to perform queries
    cursor = conn.cursor()

    # Execute query
    cursor.execute('SELECT vendor,name,ip FROM device')

    inventory = {'_meta': {'hostvars': {}}}
    for row in cursor.fetchall():
        group = row[0]
        host = row[1] or 'ungrouped'
        ip = row[2]

        # Create the group if it doesn't exist

        if group not in inventory:
            inventory[group] = {'hosts': [], 'vars': {}}

        # Add the host to the group

        inventory[group]['hosts'].append(host)

        # Add a hostvars record for the host if it doesn't exist

        if host not in inventory['_meta']['hostvars']:
            inventory['_meta']['hostvars'][host] = {}

            # Add the role variable for this host to hostvars

        inventory['_meta']['hostvars'][host]['ip'] = ip
    print json.dumps(inventory, indent=4)


if __name__ == '__main__':
    main()
