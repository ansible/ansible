.. _network_dev_guide:

**************************
Developing network modules
**************************

.. contents::
   :local:

.. _developing_modules_network:

Network connection plugins
==========================

Each network connection plugin has a set of implementation plugins which provide a specific implementation of that connection for a particular set of devices.

Public methods of these plugins may be called on the connection proxy object from the module just as connection methods can.

.. _developing_plugins_httpapi:

Developing HttpApi plugins
--------------------------

:ref:`HttpApi plugins <httpapi_plugins>` serve as adapters for various HTTP(S) APIs for use with the ``httpapi`` connection plugin. They should implement a minimal set of convenience methods tailored to the API you are attempting to use.

Specifically, there are a few methods that the ``httpapi`` connection plugin expects to exist.

Making requests
^^^^^^^^^^^^^^^

The ``httpapi`` connection plugin has a ``send()`` method, but an HttpApi plugin needs a ``send_request(self, data, **message_kwargs)`` method as a higher-level wrapper to ``send()``. This method should prepare requests by adding fixed values like common headers or URL root paths, and may do more complex work such as turning data into formatted payloads, or determining which path or method to request. It may then also unpack responses to be more easily consumed by the caller.

Authenticating
^^^^^^^^^^^^^^

By default, all requests will authenticate with HTTP Basic authentication. If a request can return some kind of token to stand in place of HTTP Basic, the ``update_auth(self, response, response_text)`` method should be implemented to inspect responses for such tokens. If the token is meant to be included with the headers of each request, it is sufficient to return a dictionary which will be merged with the computed headers for each request. The default implementation of this method does exactly this for cookies. If the token is used in another way, say in a query string, you should instead save that token to an instance variable, where the ``send_request()`` method (above) can add it to each request

If instead an explicit login endpoint needs to be requested to receive an authentication token, the ``login(self, username, password)`` method can be implemented to call that endpoint. If implemented, this method will be called once before requesting any other resources of the server. By default, it will also be attempted once when a HTTP 401 is returned from a request.

Similarly, ``logout(self)`` can be implemented to call an endpoint to invalidate and/or release the current token, if such an endpoint exists. This will be automatically called when the connection is closed (and, by extension, when reset).

Error handling
^^^^^^^^^^^^^^

The ``handle_httperror(self, exception)`` method can deal with status codes returned by the server. The return value indicates how the plugin will continue with the request:

* A value of ``true`` means that the request can be retried. This my be used to indicate a transient error, or one that has been resolved. For example, the default implementation will try to call ``login()`` when presented with a 401, and return ``true`` if successful.

* A value of ``false`` means that the plugin is unable to recover from this response. The status code will be returned to the calling module as an exception. Any other value will be taken as a nonfatal response from the request. This may be useful if the server returns error messages in the body of the response. Returning the original exception is usually sufficient in this case, as HTTPError objects have the same interface as a successful response.

For example HttpApi plugins, see the `source code for the httpapi plugins <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/httpapi>`_ included with Ansible Core.
