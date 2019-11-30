#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Oleg Tarassov <oleg.tarassov@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = r"""
---
module: phoenix_query
short_description: Run Phoenix queries
description:
  - Runs arbitrary Phoenix queries via the Phoenix Query Server.
version_added: "2.9"
author:
  - "Oleg Tarassov (@olegTarassov)"
options:
  host:
    description:
      - Phoenix query server FQDN or IP
    type: str
    required: True
  port:
    description:
      - Phoenix Query Server Port
    type: int
    required: False
    default: 8765
  query:
    description:
      - SQL query to run, syntax U(https://phoenix.apache.org/language/index.html)
    type: str
    required: True
notes:
    - check_mode not supported because RPC does not support transactions.
    - http mode (hbase-unsecure) only supported
    - Works on HDP 2.x and Phoenix version 4.x
requirements:
    - phoenixdb
seealso:
  - name: Python Driver for Phoenix
    description: Python Library used to perform queries
    link: https://phoenix.apache.org/python.html
"""

EXAMPLES = r"""
- name: Select Query to Phoenix
  phoenix_query:
    host: hostname.domain.com
    query: select * from TABLE
  register: result

- name: Execute Query from files
  phoenix_query:
    host: hostname.domain.com
    port: 8765
    query: "{{ lookup('template', item.name) }}"
  loop:
    - name: create_tables.sql.j2
    - name: alter_ttl.sql.j2
"""

RETURN = r"""
query:
  description:
    - The original query passed to Phoenix
  type: str
  returned: always
query_result:
  description:
    - List of dictionaries items.
  returned: changed
  type: list
  sample: [{"Column": "Value1"},{"Column": "Value2"}]
"""

import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

LIB_IMP_ERR = None

try:
    import phoenixdb

    HAS_LIB_PHOENIX = True
except ImportError:
    HAS_LIB_PHOENIX = False
    LIB_IMP_ERR = traceback.format_exc()


def run_module():
    module_args = dict(
        host=dict(type="str", required=True),
        port=dict(type="int", required=False, default=8765),
        query=dict(type="str", required=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    query = module.params["query"].replace(";", "")
    host = module.params["host"].strip("http://")
    port = module.params["port"]

    result = dict(
        changed=False,
        query=query,
        query_result=[{}]
    )

    if not HAS_LIB_PHOENIX:
        module.fail_json(msg=missing_required_lib("phoenixdb"), exception=LIB_IMP_ERR)

    if not query:
        module.fail_json(msg="Query cannot be empty")

    if module.check_mode:
        module.exit_json(**result)

    database_url = "http://{0}:{1}/".format(host, port)
    database_conn = phoenixdb.connect(database_url, autocommit=True)
    cursor = database_conn.cursor(cursor_factory=phoenixdb.cursor.DictCursor)

    try:
        cursor.execute(query)

        result["changed"] = True
        result["query_result"] = cursor.fetchall()

    except phoenixdb.errors.ProgrammingError as e:
        if "no select statement was executed" in str(e):
            pass
        else:
            module.fail_json(msg="Cursor Error with :{0}".format(query), exception=e)

    except Exception as e:
        module.fail_json(msg="Cannot execute query:{0}".format(query), exception=e)

    finally:
        if cursor:
            cursor.close()
        if database_conn:
            database_conn.close()

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
