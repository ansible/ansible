
.. _developing_modules_network:
.. _developing_plugins_network:

**************************
Network connection plugins
**************************

Each network connection plugin has a set of its own plugins which provide a specification of the
connection for a particular set of devices. The specific plugin used is selected at runtime based
on the value of the ``ansible_network_os`` variable assigned to the host. This variable should be
set to the same value as the name of the plugin to be loaed. Thus, ``ansible_network_os=nxos``
will try to load a plugin in a file named ``nxos.py``, so it is important to name the plugin in a
way that will be sensible to users.

Public methods of these plugins may be called from a module or module_utils with the connection
proxy object just as other connection methods can. The following is a very simple example of using
such a call in a module_utils file so it may be shared with other modules.

.. code-block:: python

  from ansible.module_utils.connection import Connection

  def get_config(module):
      # module is your AnsibleModule instance.
      connection = Connection(module._socket_path)

      # You can now call any method (that doesn't start with '_') of the connection
      # plugin or its platform-specific plugin
      return connection.get_config()

.. contents::
   :local:

.. _developing_plugins_httpapi:

Developing httpapi plugins
==========================

:ref:`httpapi plugins <httpapi_plugins>` serve as adapters for various HTTP(S) APIs for use with the ``httpapi`` connection plugin. They should implement a minimal set of convenience methods tailored to the API you are attempting to use.

Specifically, there are a few methods that the ``httpapi`` connection plugin expects to exist.

Making requests
---------------

The ``httpapi`` connection plugin has a ``send()`` method, but an httpapi plugin needs a ``send_request(self, data, **message_kwargs)`` method as a higher-level wrapper to ``send()``. This method should prepare requests by adding fixed values like common headers or URL root paths. This method may do more complex work such as turning data into formatted payloads, or determining which path or method to request. It may then also unpack responses to be more easily consumed by the caller.

.. code-block:: python

   from ansible.module_utils.six.moves.urllib.error import HTTPError

   def send_request(self, data, path, method='POST'):
       # Fixed headers for requests
       headers = {'Content-Type': 'application/json'}
       try:
           response, response_content = self.connection.send(path, data, method=method, headers=headers)
       except HTTPError as exc:
           return exc.code, exc.read()

       # handle_response (defined separately) will take the format returned by the device
       # and transform it into something more suitable for use by modules.
       # This may be JSON text to Python dictionaries, for example.
       return handle_response(response_content)

Authenticating
--------------

By default, all requests will authenticate with HTTP Basic authentication. If a request can return some kind of token to stand in place of HTTP Basic, the ``update_auth(self, response, response_text)`` method should be implemented to inspect responses for such tokens. If the token is meant to be included with the headers of each request, it is sufficient to return a dictionary which will be merged with the computed headers for each request. The default implementation of this method does exactly this for cookies. If the token is used in another way, say in a query string, you should instead save that token to an instance variable, where the ``send_request()`` method (above) can add it to each request

.. code-block:: python

   def update_auth(self, response, response_text):
       cookie = response.info().get('Set-Cookie')
       if cookie:
           return {'Cookie': cookie}

       return None

If instead an explicit login endpoint needs to be requested to receive an authentication token, the ``login(self, username, password)`` method can be implemented to call that endpoint. If implemented, this method will be called once before requesting any other resources of the server. By default, it will also be attempted once when a HTTP 401 is returned from a request.

.. code-block:: python

   def login(self, username, password):
       login_path = '/my/login/path'
       data = {'user': username, 'password': password}

       response = self.send_request(data, path=login_path)
       try:
           # This is still sent as an HTTP header, so we can set our connection's _auth
           # variable manually. If the token is returned to the device in another way,
           # you will have to keep track of it another way and make sure that it is sent
           # with the rest of the request from send_request()
           self.connection._auth = {'X-api-token': response['token']}
       except KeyError:
           raise AnsibleAuthenticationFailure(message="Failed to acquire login token.")

Similarly, ``logout(self)`` can be implemented to call an endpoint to invalidate and/or release the current token, if such an endpoint exists. This will be automatically called when the connection is closed (and, by extension, when reset).

.. code-block:: python

   def logout(self):
       logout_path = '/my/logout/path'
       self.send_request(None, path=logout_path)

       # Clean up tokens
       self.connection._auth = None

Error handling
--------------

The ``handle_httperror(self, exception)`` method can deal with status codes returned by the server. The return value indicates how the plugin will continue with the request:

* A value of ``true`` means that the request can be retried. This my be used to indicate a transient error, or one that has been resolved. For example, the default implementation will try to call ``login()`` when presented with a 401, and return ``true`` if successful.

* A value of ``false`` means that the plugin is unable to recover from this response. The status code will be returned to the calling module as an exception. Any other value will be taken as a nonfatal response from the request. This may be useful if the server returns error messages in the body of the response. Returning the original exception is usually sufficient in this case, as HTTPError objects have the same interface as a successful response.

For example httpapi plugins, see the `source code for the httpapi plugins <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/httpapi>`_ included with Ansible Core.
