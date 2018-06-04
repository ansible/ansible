#!/usr/bin/python
import json
import psycopg2
import sys
import pprint
from psycopg2.extras import RealDictCursor


def main():
        conn_string = "host='localhost' dbname='netdisco' user='netdisco' password='redhat'")

        # Make the connection
        conn = psycopg2.connect(conn_string)

        # conn.cursor will return a cursor object, you can use this cursor to perform queries
        cursor = conn.cursor()

        # execute the query
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
        print json.dumps(inventory, indent=4)

if __name__ == "__main__":
        main()
