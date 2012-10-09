.. _ohai:

ohai
``````````````````````````````

.. versionadded:: 0.6

Similar to the ``facter`` module, this runs the *ohai* discovery program (http://wiki.opscode.com/display/chef/Ohai) on the remote host and returns JSON inventory data. *Ohai* data is a bit more verbose and nested than *facter*. 


.. raw:: html

    <p>Retrieve <em>ohai</em> data from all Web servers and store in one-file per host</p>    <p><pre>
    ansible webservers -m ohai --tree=/tmp/ohaidata
    </pre></p>
    <br/>

