Lookups
-------

Lookup plugins allow access of data in Ansible from outside sources. Like all templating, these plugins are evaluated on the Ansible control
machine, and can include reading the filesystem but also contacting external datastores and services.
These values are then made available using the standard templating system in Ansible, and are typically used to load variables or templates with information from those systems.

.. note:: This is considered an advanced feature, and many users will probably not rely on these features.

.. note:: Lookups occur on the local computer, not on the remote computer.

.. note:: Lookups are executed with a cwd relative to the role or play, as opposed to local tasks which are executed with the cwd of the executed script.

.. note:: Since 1.9 you can pass wantlist=True to lookups to use in jinja2 template "for" loops.

.. warning:: Some lookups pass arguments to a shell. When using variables from a remote/untrusted source, use the `|quote` filter to ensure safe usage.

.. contents:: Topics

.. _getting_file_contents:

Intro to Lookups: Getting File Contents
```````````````````````````````````````

The file lookup is the most basic lookup type.

Contents can be read off the filesystem as follows::

    ---
    - hosts: all
      vars:
         contents: "{{ lookup('file', '/etc/foo.txt') }}"

      tasks:

         - debug: msg="the value of foo.txt is {{ contents }}"

.. _password_lookup:

The Password Lookup
```````````````````

.. note::

    A great alternative to the password lookup plugin, if you don't need to generate random passwords on a per-host basis, would be to use :doc:`playbooks_vault`.  Read the documentation there and consider using it first, it will be more desirable for most applications.

``password`` generates a random plaintext password and stores it in
a file at a given filepath.  

(Docs about crypted save modes are pending)
 
If the file exists previously, it will retrieve its contents, behaving just like with_file. Usage of variables like "{{ inventory_hostname }}" in the filepath can be used to set
up random passwords per host (which simplifies password management in 'host_vars' variables).

A special case is using ``/dev/null`` as a path. The password lookup will generate a new random password each time, but will not write it to ``/dev/null``. This can be used when you need a password
without storing it on the controller.

Generated passwords contain a random mix of upper and lowercase ASCII letters, the
numbers 0-9 and punctuation (". , : - _"). The default length of a generated password is 20 characters.
This length can be changed by passing an extra parameter::

    ---
    - hosts: all

      tasks:

        - name: create a mysql user with a random password
          mysql_user:
            name: "{{ client }}"
            password: "{{ lookup('password', 'credentials/' + client + '/' + tier + '/' + role + '/mysqlpassword length=15') }}"
            priv: "{{ client }}_{{ tier }}_{{ role }}.*:ALL"

        # (...)

.. note:: If the file already exists, no data will be written to it. If the file has contents, those contents will be read in as the password. Empty files cause the password to return as an empty string.

Caution: Since this runs on the ansible host as the user running the playbook, and "become" does not apply, the target file must be readable by the playbook user, or, if it does not exist, the playbook user must have sufficient privileges to create it. (So, for example, attempts to write into areas such as /etc will fail unless the entire playbook is being run as root).

Starting in version 1.4, password accepts a "chars" parameter to allow defining a custom character set in the generated passwords. It accepts comma separated list of names that are either string module attributes (ascii_letters,digits, etc) or are used literally::

    ---
    - hosts: all

      tasks:

        - name: create a mysql user with a random password using only ascii letters
          mysql_user: name={{ client }} password="{{ lookup('password', '/tmp/passwordfile chars=ascii_letters') }}" priv={{ client }}_{{ tier }}_{{ role }}.*:ALL

        - name: create a mysql user with a random password using only digits
          mysql_user:
            name: "{{ client }}"
            password: "{{ lookup('password', '/tmp/passwordfile chars=digits') }}"
            priv: "{{ client }}_{{ tier }}_{{ role }}.*:ALL"

        - name: create a mysql user with a random password using many different char sets
          mysql_user:
            name: "{{ client }}"
            password" "{{ lookup('password', '/tmp/passwordfile chars=ascii_letters,digits,hexdigits,punctuation') }}"
            priv: "{{ client }}_{{ tier }}_{{ role }}.*:ALL"

        # (...)

To enter comma use two commas ',,' somewhere - preferably at the end. Quotes and double quotes are not supported.

.. _passwordstore_lookup:

The Passwordstore Lookup
````````````````````````
.. versionadded:: 2.3

The ``passwordstore`` lookup enables Ansible to retrieve, create or update passwords from
the passwordstore.org_ ``pass`` utility. It also retrieves YAML style keys stored as multilines
in the passwordfile.

.. _passwordstore.org: https://www.passwordstore.org

Examples
--------
Basic lookup. Fails if example/test doesn't exist::

    password="{{ lookup('passwordstore', 'example/test')}}"

Create pass with random 16 character password. If password exists just give the password::

    password="{{ lookup('passwordstore', 'example/test create=true')}}"

Different size password::

    password="{{ lookup('passwordstore', 'example/test create=true length=42')}}"

Create password and overwrite the password if it exists. As a bonus, this module includes the old password inside the pass file::

    password="{{ lookup('passwordstore', 'example/test create=true overwrite=true')}}"

Return the value for user in the KV pair user: username::

    password="{{ lookup('passwordstore', 'example/test subkey=user')}}"

Return the entire password file content::

    password="{{ lookup('passwordstore', 'example/test returnall=true')}}"

The location of the password-store directory can be specified in the following ways:
  - Default is ~/.password-store
  - Can be overruled by PASSWORD_STORE_DIR environment variable
  - Can be overruled by 'passwordstore: path/to/.password-store' ansible setting
  - Can be overruled by 'directory=path' argument in the lookup call

.. _csvfile_lookup:

The CSV File Lookup
```````````````````
.. versionadded:: 1.5

The ``csvfile`` lookup reads the contents of a file in CSV (comma-separated value)
format. The lookup looks for the row where the first column matches ``keyname``, and
returns the value in the second column, unless a different column is specified.

The example below shows the contents of a CSV file named elements.csv with information about the
periodic table of elements::

    Symbol,Atomic Number,Atomic Mass
    H,1,1.008
    He,2,4.0026
    Li,3,6.94
    Be,4,9.012
    B,5,10.81


We can use the ``csvfile`` plugin to look up the atomic number or atomic of Lithium by its symbol::

    - debug: msg="The atomic number of Lithium is {{ lookup('csvfile', 'Li file=elements.csv delimiter=,') }}"
    - debug: msg="The atomic mass of Lithium is {{ lookup('csvfile', 'Li file=elements.csv delimiter=, col=2') }}"


The ``csvfile`` lookup supports several arguments. The format for passing
arguments is::

    lookup('csvfile', 'key arg1=val1 arg2=val2 ...')

The first value in the argument is the ``key``, which must be an entry that
appears exactly once in column 0 (the first column, 0-indexed) of the table. All other arguments are optional.


==========   ============   =========================================================================================
Field        Default        Description
----------   ------------   -----------------------------------------------------------------------------------------
file         ansible.csv    Name of the file to load
col          1              The column to output, indexed by 0
delimiter    TAB            Delimiter used by CSV file. As a special case, tab can be specified as either TAB or \t.
default      empty string   Default return value if the key is not in the csv file
encoding     utf-8          Encoding (character set) of the used CSV file (added in version 2.1)
==========   ============   =========================================================================================

.. note:: The default delimiter is TAB, *not* comma.

.. _ini_lookup:

The INI File Lookup
```````````````````
.. versionadded:: 2.0

The ``ini`` lookup reads the contents of a file in INI format (key1=value1).
This plugin retrieve the value on the right side after the equal sign ('=') of
a given section ([section]). You can also read a property file which - in this
case - does not contain section.

Here's a simple example of an INI file with user/password configuration:

.. code-block:: ini

    [production]
    # My production information
    user=robert
    pass=somerandompassword

    [integration]
    # My integration information
    user=gertrude
    pass=anotherpassword


We can use the ``ini`` plugin to lookup user configuration::

    - debug: msg="User in integration is {{ lookup('ini', 'user section=integration file=users.ini') }}"
    - debug: msg="User in production  is {{ lookup('ini', 'user section=production  file=users.ini') }}"

Another example for this plugin is for looking for a value on java properties.
Here's a simple properties we'll take as an example:

.. code-block:: ini

    user.name=robert
    user.pass=somerandompassword

You can retrieve the ``user.name`` field with the following lookup::

    - debug: msg="user.name is {{ lookup('ini', 'user.name type=properties file=user.properties') }}"

The ``ini`` lookup supports several arguments like the csv plugin. The format for passing
arguments is::

    lookup('ini', 'key [type=<properties|ini>] [section=section] [file=file.ini] [re=true] [default=<defaultvalue>]')

The first value in the argument is the ``key``, which must be an entry that
appears exactly once on keys. All other arguments are optional.


==========   ============   =========================================================================================
Field        Default        Description
----------   ------------   -----------------------------------------------------------------------------------------
type         ini            Type of the file. Can be ini or properties (for java properties).
file         ansible.ini    Name of the file to load
section      global         Default section where to lookup for key.
re           False          The key is a regexp.
encoding     utf-8          Text encoding to use.
default      empty string   return value if the key is not in the ini file
==========   ============   =========================================================================================

.. note:: In java properties files, there's no need to specify a section.

.. _credstash_lookup:

The Credstash Lookup
````````````````````
.. versionadded:: 2.0

Credstash is a small utility for managing secrets using AWS's KMS and DynamoDB: https://github.com/fugue/credstash

First, you need to store your secrets with credstash:

.. code-block:: shell-session

    credstash put my-github-password secure123

    # my-github-password has been stored


Example usage::


    ---
    - name: "Test credstash lookup plugin -- get my github password"
      debug: msg="Credstash lookup! {{ lookup('credstash', 'my-github-password') }}"


You can specify regions or tables to fetch secrets from::


    ---
    - name: "Test credstash lookup plugin -- get my other password from us-west-1"
      debug: msg="Credstash lookup! {{ lookup('credstash', 'my-other-password', region='us-west-1') }}"


    - name: "Test credstash lookup plugin -- get the company's github password"
      debug: msg="Credstash lookup! {{ lookup('credstash', 'company-github-password', table='company-passwords') }}"


If you use the context feature when putting your secret, you can get it by passing a dictionary to the context option like this::

    ---
    - name: test
      hosts: localhost
      vars:
        context:
          app: my_app
          environment: production
      tasks:

      - name: "Test credstash lookup plugin -- get the password with a context passed as a variable"
        debug: msg="{{ lookup('credstash', 'some-password', context=context) }}"

      - name: "Test credstash lookup plugin -- get the password with a context defined here"
        debug: msg="{{ lookup('credstash', 'some-password', context=dict(app='my_app', environment='production')) }}"

If you're not using 2.0 yet, you can do something similar with the credstash tool and the pipe lookup (see below)::

    debug: msg="Poor man's credstash lookup! {{ lookup('pipe', 'credstash -r us-west-1 get my-other-password') }}"

.. _dns_lookup:

The DNS Lookup (dig)
````````````````````
.. versionadded:: 1.9.0

.. warning:: This lookup depends on the `dnspython <http://www.dnspython.org/>`_
             library.

The ``dig`` lookup runs queries against DNS servers to retrieve DNS records for
a specific name (*FQDN* - fully qualified domain name). It is possible to lookup any DNS record in this manner.

There is a couple of different syntaxes that can be used to specify what record
should be retrieved, and for which name. It is also possible to explicitly
specify the DNS server(s) to use for lookups.

In its simplest form, the ``dig`` lookup plugin can be used to retrieve an IPv4
address (DNS ``A`` record) associated with *FQDN*:

.. note:: If you need to obtain the ``AAAA`` record (IPv6 address), you must
          specify the record type explicitly. Syntax for specifying the record
          type is described below.

.. note:: The trailing dot in most of the examples listed is purely optional,
          but is specified for completeness/correctness sake.

::

      - debug: msg="The IPv4 address for example.com. is {{ lookup('dig', 'example.com.')}}"

In addition to (default) ``A`` record, it is also possible to specify a different
record type that should be queried. This can be done by either passing-in
additional parameter of format ``qtype=TYPE`` to the ``dig`` lookup, or by
appending ``/TYPE`` to the *FQDN* being queried. For example::

  - debug: msg="The TXT record for example.org. is {{ lookup('dig', 'example.org.', 'qtype=TXT') }}"
  - debug: msg="The TXT record for example.org. is {{ lookup('dig', 'example.org./TXT') }}"

If multiple values are associated with the requested record, the results will be
returned as a comma-separated list. In such cases you may want to pass option
``wantlist=True`` to the plugin, which will result in the record values being
returned as a list over which you can iterate later on::

  - debug: msg="One of the MX records for gmail.com. is {{ item }}"
    with_items: "{{ lookup('dig', 'gmail.com./MX', wantlist=True) }}"

In case of reverse DNS lookups (``PTR`` records), you can also use a convenience
syntax of format ``IP_ADDRESS/PTR``. The following three lines would produce the
same output::

  - debug: msg="Reverse DNS for 192.0.2.5 is {{ lookup('dig', '192.0.2.5/PTR') }}"
  - debug: msg="Reverse DNS for 192.0.2.5 is {{ lookup('dig', '5.2.0.192.in-addr.arpa./PTR') }}"
  - debug: msg="Reverse DNS for 192.0.2.5 is {{ lookup('dig', '5.2.0.192.in-addr.arpa.', 'qtype=PTR') }}"

By default, the lookup will rely on system-wide configured DNS servers for
performing the query. It is also possible to explicitly specify DNS servers to
query using the ``@DNS_SERVER_1,DNS_SERVER_2,...,DNS_SERVER_N`` notation. This
needs to be passed-in as an additional parameter to the lookup. For example::

  - debug: msg="Querying 198.51.100.23 for IPv4 address for example.com. produces {{ lookup('dig', 'example.com', '@198.51.100.23') }}"

In some cases the DNS records may hold a more complex data structure, or it may
be useful to obtain the results in a form of a dictionary for future
processing. The ``dig`` lookup supports parsing of a number of such records,
with the result being returned as a dictionary. This way it is possible to
easily access such nested data. This return format can be requested by
passing-in the ``flat=0`` option to the lookup. For example::

  - debug: msg="XMPP service for gmail.com. is available at {{ item.target }} on port {{ item.port }}"
    with_items: "{{ lookup('dig', '_xmpp-server._tcp.gmail.com./SRV', 'flat=0', wantlist=True) }}"

Take note that due to the way Ansible lookups work, you must pass the
``wantlist=True`` argument to the lookup, otherwise Ansible will report errors.

Currently the dictionary results are supported for the following records:

.. note:: *ALL* is not a record per-se, merely the listed fields are available
          for any record results you retrieve in the form of a dictionary.

==========   =============================================================================
Record       Fields
----------   -----------------------------------------------------------------------------
*ALL*        owner, ttl, type
A            address
AAAA         address
CNAME        target
DNAME        target
DLV          algorithm, digest_type, key_tag, digest
DNSKEY       flags, algorithm, protocol, key
DS           algorithm, digest_type, key_tag, digest
HINFO        cpu, os
LOC          latitude, longitude, altitude, size, horizontal_precision, vertical_precision
MX           preference, exchange
NAPTR        order, preference, flags, service, regexp, replacement
NS           target
NSEC3PARAM   algorithm, flags, iterations, salt
PTR          target
RP           mbox, txt
SOA          mname, rname, serial, refresh, retry, expire, minimum
SPF          strings
SRV          priority, weight, port, target
SSHFP        algorithm, fp_type, fingerprint
TLSA         usage, selector, mtype, cert
TXT          strings
==========   =============================================================================

.. _mongodb_lookup:

MongoDB Lookup
``````````````
.. versionadded:: 2.3

.. warning:: This lookup depends on the `pymongo 2.4+ <http://www.mongodb.org/>`_
             library.


The ``MongoDB`` lookup runs the *find()* command on a given *collection* on a given *MongoDB* server.

The result is a list of jsons, so slightly different from what PyMongo returns. In particular, *timestamps* are converted to epoch integers.

Currently, the following parameters are supported.

===========================  =========   =======   ====================   =======================================================================================================================================================================
Parameter                    Mandatory   Type      Default Value          Comment
---------------------------  ---------   -------   --------------------   -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
connection_string            no          string    mongodb://localhost/   Can be any valid MongoDB connection string, supporting authentication, replicasets, etc. More info at https://docs.mongodb.org/manual/reference/connection-string/
extra_connection_parameters  no          dict      {}                     Dictionary with extra parameters like ssl, ssl_keyfile, maxPoolSize etc... Check the full list here: https://api.mongodb.org/python/current/api/pymongo/mongo_client.html#pymongo.mongo_client.MongoClient
database                     yes         string                           Name of the database which the query will be made
collection                   yes         string                           Name of the collection which the query will be made
filter                       no          dict      [pymongo default]      Criteria of the output Example: { "hostname": "batman" }
projection                   no          dict      [pymongo default]      Fields you want returned. Example: { "pid": True    , "_id" : False , "hostname" : True }
skip                         no          integer   [pymongo default]      How many results should be skept
limit                        no          integer   [pymongo default]      How many results should be shown
sort                         no          list      [pymongo default]      Sorting rules. Please notice the constats are replaced by strings. [ [ "startTime" , "ASCENDING" ] , [ "age", "DESCENDING" ] ]
[any find() parameter]       no          [any]     [pymongo default]      Every parameter with exception to *connection_string*, *database* and *collection* are passed to pymongo directly.
===========================  =========   =======   ====================   =======================================================================================================================================================================

Please check https://api.mongodb.org/python/current/api/pymongo/collection.html?highlight=find#pymongo.collection.Collection.find for more detais.

Since there are too many parameters for this lookup method, below is a sample playbook which shows its usage and a nice way to feed the parameters:

.. code-block:: YAML+Jinja

    ---
    - hosts: all
      gather_facts: false

      vars:
        mongodb_parameters:
          #optional parameter, default = "mongodb://localhost/"
          # connection_string: "mongodb://localhost/"
          # extra_connection_parameters: { "ssl" : True , "ssl_certfile": /etc/self_signed_certificate.pem" }

          #mandatory parameters
          database: 'local'
          collection: "startup_log"

          #optional query  parameters
          #we accept any parameter from the normal mongodb query.
          # the official documentation is here
          # https://api.mongodb.org/python/current/api/pymongo/collection.html?highlight=find#pymongo.collection.Collection.find
          # filter:  { "hostname": "batman" }
          projection: { "pid": True    , "_id" : False , "hostname" : True }
          # skip: 0
          limit: 1
          # sort:  [ [ "startTime" , "ASCENDING" ] , [ "age", "DESCENDING" ] ]

      tasks:
        - debug: msg="Mongo has already started with the following PID [{{ item.pid }}]"
          with_mongodb: "{{mongodb_parameters}}"



Sample output:

.. code-block:: shell-session

    mdiez@batman:~/ansible$ ansible-playbook m.yml -i localhost.ini

    PLAY [all] *********************************************************************

    TASK [debug] *******************************************************************
    Sunday 20 March 2016  22:40:39 +0200 (0:00:00.023)       0:00:00.023 **********
    ok: [localhost] => (item={u'hostname': u'batman', u'pid': 60639L}) => {
        "item": {
            "hostname": "batman",
            "pid": 60639
        },
        "msg": "Mongo has already started with the following PID [60639]"
    }

    PLAY RECAP *********************************************************************
    localhost                  : ok=1    changed=0    unreachable=0    failed=0

    Sunday 20 March 2016  22:40:39 +0200 (0:00:00.067)       0:00:00.091 **********
    ===============================================================================
    debug ------------------------------------------------------------------- 0.07s
    mdiez@batman:~/ansible$


.. _more_lookups:

More Lookups
````````````

Various *lookup plugins* allow additional ways to iterate over data.  In :doc:`Loops <playbooks_loops>` you will learn
how to use them to walk over collections of numerous types.  However, they can also be used to pull in data
from remote sources, such as shell commands or even key value stores. This section will cover lookup plugins in this capacity.

Here are some examples::

    ---
    - hosts: all

      tasks:

         - debug: msg="{{ lookup('env','HOME') }} is an environment variable"

         - name: lines will iterate over each line from stdout of a command
           debug: msg="{{ item }} is a line from the result of this command"
           with_lines: cat /etc/motd

         - debug: msg="{{ lookup('pipe','date') }} is the raw result of running this command"

         - name: Always use quote filter to make sure your variables are safe to use with shell
           debug: msg="{{ lookup('pipe','getent ' + myuser|quote ) }}"

         - name: Quote variables with_lines also as it executes shell
           debug: msg="{{ item }} is a line from myfile"
           with_lines: "cat {{myfile|quote}}"

         - name: redis_kv lookup requires the Python redis package
           debug: msg="{{ lookup('redis_kv', 'redis://localhost:6379,somekey') }} is value in Redis for somekey"

         - name: dnstxt lookup requires the Python dnspython package
           debug: msg="{{ lookup('dnstxt', 'example.com') }} is a DNS TXT record for example.com"

         - debug: msg="{{ lookup('template', './some_template.j2') }} is a value from evaluation of this template"

         # Since 2.4, you can pass in variables during evaluation
         - debug: msg="{{ lookup('template', './some_template.j2', template_vars=dict(x=42)) }} is evaluated with x=42"

         - name: loading a json file from a template as a string
           debug: msg="{{ lookup('template', './some_json.json.j2', convert_data=False) }} is a value from evaluation of this template"


         - debug: msg="{{ lookup('etcd', 'foo') }} is a value from a locally running etcd"

         # shelvefile lookup retrieves a string value corresponding to a key inside a Python shelve file
         - debug: msg="{{ lookup('shelvefile', 'file=path_to_some_shelve_file.db key=key_to_retrieve') }}

         # The following lookups were added in 1.9
         # url lookup splits lines by default, an option to disable this was added in 2.4
         - debug: msg="{{item}}"
           with_url:
                - 'https://github.com/gremlin.keys'

         # outputs the cartesian product of the supplied lists
         - debug: msg="{{item}}"
           with_cartesian:
                - "{{list1}}"
                - "{{list2}}"
                - [1,2,3,4,5,6]

         - name: Added in 2.3 allows using the system's keyring
           debug: msg={{lookup('keyring','myservice myuser')}}


As an alternative, you can also assign lookup plugins to variables or use them elsewhere.
These macros are evaluated each time they are used in a task (or template)::

    vars:
      motd_value: "{{ lookup('file', '/etc/motd') }}"

    tasks:

      - debug: msg="motd value is {{ motd_value }}"

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_conditionals`
       Conditional statements in playbooks
   :doc:`playbooks_variables`
       All about variables
   :doc:`playbooks_loops`
       Looping in playbooks
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel



