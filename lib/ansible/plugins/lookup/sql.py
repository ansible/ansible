# (c) 2018, Adam Howard <ahoward0920@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: sql
    author: Adam Howard <ahoward0920@gmail.com>
    version_added: "1.9"
    short_description: query an SQL database using sqlalchemy
    requirements:
        - sqlalchemy (python library, http://www.sqlalchemy.org/)
    description:
        - Uses the sqlalchemy python library to run a query against an SQL database.
        - Supports ``postgres``, ``mysql``, ``sqlite``, and any other database dialects
          sqlalchemy supports.
    options:
        db_url:
            description: RFC1738-compliant URL for the database to query
            required: True
        query:
            description: the SQL query to perform
            required: True
"""

EXAMPLES = """
    - name: Get all widgets from a local Postgres database
      debug: msg="{{ lookup('sql', 'postgres://user:pass@localhost/testdb' 'SELECT * FROM widgets') }}"

    - name: Get all widgets from a SQLite database using a relative path
      debug: msg="{{ lookup('sql', 'sqlite:///testdb.sqlite' 'SELECT * FROM widgets') }}"

    - name: Get all widgets from a SQLite database using an absolute path
      debug: msg="{{ lookup('sql', 'sqlite:////path/to/testdb.sqlite' 'SELECT * FROM widgets') }}"
"""

RETURN = """
    _list:
        description:
            - list of dictionaries, where each of which maps to a row in the
              query's results. Keys in each dictionary are the columns of the
              query.
"""

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase

try:
    import sqlalchemy
except ImportError:
    sqlalchemy = None


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        if sqlalchemy is None:
            raise AnsibleError("sqlalchemy is not installed")

        db_url, query = terms[0:2]
        try:
            engine = sqlalchemy.create_engine(db_url)
        except sqlalchemy.exc.ArgumentError as err:
            raise AnsibleError("db_url: '{0}' is not valid".format(db_url))

        try:
            with engine.begin() as conn:
                result = conn.execute(query)
                return [dict(row) for row in result.fetchall()]
        except sqlalchemy.exc.SQLAlchemyError as err:
            raise AnsibleError("SQLAlchemy error occured: {0}".format(err))
