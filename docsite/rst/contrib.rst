Ansible Resources
=================

User contributed playbooks, modules, and articles. This is a small
curated list, but growing. Everyone is encouraged to add to this
document, just send in a github pull request to docsite/rst/contrib.rst!

Ansible Modules
```````````````

Ansible modules are a way of adding new client-side logic to ansible.
They can be written in any language.

-  `Official "core" ansible modules <http://ansible.cc/docs/modules.html>`_ - various
-  `mercurial <https://github.com/bradobro/ansible-module-mercurial>`_ - bradobro
-  `zypper (bash module example) <https://github.com/jpmens/ansible-zypp>`_ - jp\_mens
-  `homebrew <https://gist.github.com/3170079>`_ - swehack
-  `additional provisioning-related modules <https://github.com/ansible-provisioning>`_ - jhoekx and dagwieers
-  `dynamic dns updates <https://github.com/jpmens/ansible-m-dnsupdate>`_ - jp\_mens
-  `RabbitMQ <https://github.com/elventear/ansible-rabbitmq>`_ - elventear

Python modules using 0.6 and later can and should use the common "AnsibleModule"
class to dramatically reduce the amount of boilerplate code required.
Not all modules above yet take advantage of this feature. See the
official documentation for more details.

Selected Playbooks
``````````````````

`Playbooks <http://ansible.cc/docs/playbooks.html>`_ are Ansible's
configuration management language. It should be easy to write your own
from scratch for most applications, but it's always helpful to look at
what others have done for reference.

-  `Hadoop <https://github.com/jkleint/ansible-hadoop>`_ - jkleint
-  `LAMP <https://github.com/fourkitchens/server-playbooks>`_ - `Four Kitchens <http://fourkitchens.com>`_
-  `LEMP <https://github.com/francisbesset/ansible-playbooks>`_ - francisbesset
-  `Ganglia (demo) <https://github.com/mpdehaan/ansible-examples>`_ - mpdehaan
-  `Nginx <http://www.capsunlock.net/2012/04/ansible-nginx-playbook.html>`_ - cocoy
-  `OpenStack <http://github.com/lorin/openstack-ansible>`_ - lorin
-  `Systems Configuration <https://github.com/cegeddin/ansible-contrib>`_ - cegeddin
-  `Fedora Infrastructure <http://infrastructure.fedoraproject.org/cgit/ansible.git/tree/>`_ - `Fedora <http://fedoraproject.org>`_

Callbacks and Plugins
`````````````````````

The Ansible project has a whole repo devoted to extending ansible with
new connection types, logging/event callbacks, and inventory data
storage. Talk to Cobbler and EC2, tweak the way things are logged, or
even add sound effects.

-  `Ansible-Plugins <https://github.com/ansible/ansible/tree/devel/plugins>`_

Scripts And Misc
````````````````

Ansible isn't just a program, it's also an API. Here's some examples of
some clever integrations with the "Runner" and also Playbook APIs, and
integrations with other interesting pieces of software.

-  `Ansible Vagrant plugin <https://github.com/dsander/vagrant-ansible>`_ - dsander
-  `Ansible+Vagrant Tutorial <https://github.com/mattupstate/vagrant-ansible-tutorial>`_ - mattupstate -
-  `virt-install <http://fedorapeople.org/cgit/skvidal/public_git/scripts.git/tree/ansible/start-prov-boot.py>`_ - skvidal
-  `rebooting hosts <http://fedorapeople.org/cgit/skvidal/public_git/scripts.git/tree/ansible/host-reboot>`_ - skvidal
-  `uptime (API demo) <https://github.com/ansible/ansible/blob/devel/examples/scripts/uptime.py>`_ - mpdehaan
-  `vim snippet generator <https://github.com/bleader/ansible_snippet_generator>`_ - bleader

Blogs & Articles
````````````````

-  `HighScalability.com <http://highscalability.com/blog/2012/4/18/ansible-a-simple-model-driven-configuration-management-and-c.html>`_ - mpdehaan
-  `ColoAndCloud.com interview <http://www.coloandcloud.com/editorial/an-interview-with-ansible-author-michael-dehaan/>`_ - mpdehaan
-  `dzone <http://server.dzone.com/articles/ansible-cm-deployment-and-ad>`_ - Mitch Pronschinske
-  `Configuration Management With Ansible <http://jpmens.net/2012/06/06/configuration-management-with-ansible/>`_ - jp\_mens
-  `Shell Scripts As Ansible Modules <http://jpmens.net/2012/07/05/shell-scripts-as-ansible-modules/>`_ - jp\_mens
-  `Ansible Facts <http://jpmens.net/2012/07/15/ansible-it-s-a-fact/>`_ - jp\_mens
-  `Infrastructure as Data <http://www.capsunlock.net/2012/04/ansible-infrastructure-as-data-not-infrastructure-as-code.html>`_ - cocoy
-  `Ansible Pull Mode <http://www.capsunlock.net/2012/05/using-ansible-pull-and-user-data-to-setup-ec2-or-openstack-servers.html>`_ - cocoy
-  `Exploring Configuration Management With Ansible <http://palominodb.com/blog/2012/08/01/exploring-configuration-management-ansible>`_ - Palamino DB
-  `You Should Consider Using SSH Based Configuration Management <http://www.lshift.net/blog/2012/07/30/you-should-consider-using-ssh-based-configuration-management>`_ - LShift Ltd
-  `Deploying Flask/uWSGI, Nginx, and Supervisorctl <http://mattupstate.github.com/python/devops/2012/08/07/flask-wsgi-application-deployment-with-ubuntu-ansible-nginx-supervisor-and-uwsgi.html>`_ - mattupstate
-  `Infracoders Presentation <http://www.danielhall.me/2012/10/ansible-talk-infra-coders/>`_ - Daniel Hall
-  `Ansible - an introduction <https://speakerdeck.com/jpmens/ansible-an-introduction>`_ - jp\_mens

Disclaimer
``````````

Modules and playbooks here may not be using the latest in Ansible
features. When in doubt to the features of a particular version of
Ansbile, always consult `ansible.cc <http://ansible.cc>`_ and in
particular see `Best Practices <http://ansible.cc/docs/bestpractices.html>`_ for some tips
and tricks that may be useful.

Ansible is (C) 2012, `Michael DeHaan <http://twitter.com/laserllama>`_
and others and is available under the GPLv3 license. Content here is as
specified by individual contributors.
