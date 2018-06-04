#!/usr/bin/python
# Dynamic inventory script for the web-based network management tool
# Netdisco. Created by Maksim Nikiforov.
# All information is extracted from Netdisco's  PostgreSQL database
import json
import psycopg2

"""
This dynamic inventory script imports the network inventory from
Netdisco. Netdisco is a web-based network management tool suitable for
small to very large networks. IP and MAC address data is
collected into a PostgreSQL database using SNMP, CLI, or device APIs.
"""

def main():
    '''Import inventory in JSON format for Ansible'''
    conn_string = \
        "host='localhost' dbname='netdisco' user='netdisco' password='redhat'"
    # print the connection string we will use to connect
    # print "Connecting to database\n       ->%s" % (conn_string)

    # get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    cursor = conn.cursor()

    # execute our Query
    cursor.execute("SELECT vendor,name,ip FROM device")

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
    print(json.dumps(inventory, indent=4))

    # retrieve the records from the database
    # for row in cursor.fetchall(): group = row[1] if group is None: group = 'ungrouped'
    # print json.dumps(cursor.fetchall(), sort_keys=True, indent=2)

    # print out the records using pretty print
    # note that the NAMES of the columns are not shown, instead just indexes.
    # for most people this isn't very useful so we'll show you how to return
    # columns as a dictionary (hash) in the next example.


if __name__ == "__main__":
    main()
