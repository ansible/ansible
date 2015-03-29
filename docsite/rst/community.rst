Community Information & Contributing
````````````````````````````````````

Ansible is an open-source project designed to bring together administrators and developers of all
kinds to collaborate on building IT automation solutions that work well for them.

Should you wish to get more involved -- whether just asking a question, helping other users,
introducing new people to Ansible, or helping with the software or documentation -- we welcome your
contributions to the project.

.. contents:: Topics

Ansible Users
=============

I've Got A Question
-------------------

We're happy to help!

Ansible questions are best asked on the `Ansible Google Group Mailing List
<http://groups.google.com/group/ansible-project>`_. This is a high-traffic list for answering
questions and sharing tips and tricks. Anyone can join, and email delivery is optional if you just
want to read the group online.  To cut down on spam, your first post is moderated, though posts are
approved quickly.

When asking a question, please be sure to include any relevant commands you ran, its output, the
version of Ansible, and additional detail that may assist in solving the question. Where needed,
link to Gists or GitHub repositories to show examples rather than sending attachments to the list.

We recommend using Google search to see if a topic has been answered recently, but note that
comments found in older threads may be outdated, depending on the topic.

Before you post, be sure you are running the latest stable version of Ansible.  You can check this
by comparing the output of 'ansible --version' with the version indicated on `PyPI
<https://pypi.python.org/pypi/ansible>`_.

Alternatively, you can also join our IRC channel: #ansible on irc.freenode.net.  It's a very high
traffic channel as well, but if you don't get an answer you like, please stop by our mailing list
which is more likely to attract the attention of core developers (as it is asynchronous).


I'd Like To Keep Up With Release Announcements
----------------------------------------------

Release announcements are posted to ansible-project, though if you don't want to keep up with the
very active list, you can join the `Ansible Announce Mailing List
<http://groups.google.com/group/ansible-announce>`_.

This is a low-traffic read-only list where we'll share release announcements and occasionally links
to major Ansible Events around the world.


I'd Like To Help Share and Promote Ansible
------------------------------------------

You can help share Ansible with others by telling friends and colleagues, writing a blog post, or
presenting at user groups (like DevOps groups or your local LUG). You are also welcome to share
slides on Speaker Deck -- sign up for a free account and tag it "Ansible". On Twitter, you can also
share things with #ansible and may also wish to `follow us <https://twitter.com/ansible>`_.


I'd Like To Help Ansible Move Faster
------------------------------------

If you're a developer, one of the most valuable things you can do is look at the `GitHub issues
list <http://github.com/ansible/ansible/issues>`_ and help fix bugs.  We almost always prioritize
bug fixing over feature development, so clearing bugs out of the way is one of the best things you
can do.

If you're not a developer, helping test pull requests for bug fixes and features is still immensely
valuable.  You can do this by checking out ansible, making a test branch off the main one, merging
a GitHub issue, testing, and then commenting on that particular issue on GitHub.


I'd Like To Report A Bug
------------------------

Ansible practices responsible disclosure; if this is a security-related bug, email
`security@ansible.com <mailto:security@ansible.com>`_ instead of filing a ticket or posting to the
Google Group and you will receive a prompt response.

Bugs related to the core language should be reported to `github.com/ansible/ansible
<http://github.com/ansible/ansible>`_ after signing up for a free GitHub account.  Before reporting
a bug, please use the bug/issue search to see if the issue has already been reported.

Module-related bugs, however, belong in either the `ansible-modules-core
<github.com/ansible/ansible-modules-core>`_ or `ansible-modules-extras
<github.com/ansible/ansible-modules-extras>`_ repositories based on the classification of the
module.  This is listed on the bottom of the docs page for any module.

When filing a bug report, please use the `issue template
<https://github.com/ansible/ansible/raw/devel/ISSUE_TEMPLATE.md>`_ to provide all relevant
information, regardless of what repository you are filing a ticket against. Knowing your Ansible
version, the exact commands you are running, and what you expect to happen saves time and helps us
resolve everyone's issues more quickly. If you are not sure if something is a bug yet, you are
welcome to ask about it on the mailing list or IRC first.

For multiple-file content, we encourage use of `Gist <https://gist.github.com>`_.  Online pastebin
content can expire, and it's nice to have something more permanent referenced in a ticket.

Do not use the issue tracker for "how do I do this" type questions. These are better suited for IRC
or the mailing list instead, where things are likely to be more of a discussion.

To be respectful of reviewers time and allow us to help everyone efficiently, please provide
minimal well-reduced and well-commented examples rather than sharing your entire production
playbook.  Include playbook snippets and output where possible. When sharing YAML in playbooks,
formatting can be preserved by using `code blocks
<https://help.github.com/articles/github-flavored-markdown#fenced-code-blocks>`_.

As we are a very high volume project, if you determine that you do have a bug, please be sure to
open the issue yourself to ensure we have a record of it. Don’t rely on someone else in the
community to file the bug report for you.

It may take some time to get to your report -- see our information about priority flags below.


I'd Like To Help With Documentation
-----------------------------------

Ansible documentation is a community project too!

If you would like to help with docmentation, whether correcting a typo, improving a section, or
maybe even documenting a new feature, submit a GitHub pull request. For most of the documentation
pages, the corresponding code lives in the 'docsite/rst' subdirectory of the project. When accessed
from GitHub, there is an 'Edit on GitHub' link on these pages for convenience.

Module documentation is generated from a DOCUMENTATION structure embedded in the source code of
each module, which is in either the ansible-modules-core or ansible-modules-extra repositories on
GitHub, depending on the module. Information about this is always listed on the bottom of the web
documentation for each module.

Aside from modules, the main documentation is written in the reStructuredText format. If you aren’t
comfortable with reStructuredText, you can also open a ticket on GitHub about any errors you spot
or sections you would like to see added. For more information on creating pull requests, please
refer to the `GitHub help guide <https://help.github.com/articles/using-pull-requests>`_ on the
subject.



For Current and Prospective Developers
=======================================

I'd Like To Learn How To Develop on Ansible
-------------------------------------------

If you're new to Ansible and would like to figure out how to work on things, stop by the
ansible-devel mailing list and say hi, and we can hook you up.

A great way to get started would be by reading over some of the development documentation on the
module site and then finding a bug to fix or a small feature to add. Modules are some of the
easiest places to get started.


Contributing Code (Features or Bug Fixes)
-----------------------------------------

The Ansible project keeps its source on GitHub in various different locations. The core application
is located at `github.com/ansible/ansible <http://github.com/ansible/ansible>`_, and two
sub-repositories (ansible/ansible-modules-core and ansible/ansible-modules-extras) exist for
module-related items. If you need to know if a module is in 'core' or 'extras', consult the web
documentation page for that module.

The project accepts contributions through `GitHub pull requests <https://help.github.com/articles/using-pull-requests>`_.

It is usually a good idea to join the ansible-devel list to discuss any large features prior to
submission. This especially helps in avoiding duplicate work or efforts where we decide, upon
seeing a pull request for the first time, that revisions are needed. (This is not usually needed
for module development, but can be useful for large changes). Note that we do keep Ansible to a
particular aesthetic, so if you are unclear about whether a feature is a good fit or not, having
the discussion on the development list is often a lot easier than having to modify a pull request
later.

When submitting patches, be sure to run the unit tests first using "make tests". There are also
integration tests that can be run from the "test/integration" directory.

Always use "git rebase" rather than "git merge" to avoid merge commits in your submissions
(aliasing "git pull" to "git pull --rebase" is a great idea). This is required in order to keep the
commit history of the project clean and to better audit incoming code. Also, be sure to use topic
branches to keep your additions on different branches so that they won't pick up stray commits
later. Following the submission of your pull request, we will review your contributions and inquire
further if necessary.

As we have a very large and active community, it may take a while to merge your contributions in!
See the notes about priorities in a later section for a more comprehensive understanding our work
queue.

Patches should be made against the 'devel' branch.

Contributions can be for new features like modules, or to fix bugs you or others have found. If you
are interested in writing new modules to be included in the core Ansible distribution, please refer
to the `module development documentation <http://docs.ansible.com/developing_modules.html>`_.

Ansible's aesthetic encourages simple, readable code and consistent, conservatively-extending,
backwards-compatible improvements.  Code developed for Ansible needs to support Python 2.6+
while code in modules must run under Python 2.4 or higher.  Please use a 4-space soft indentation
(no tabs).

Tip: To easily run from a checkout, source "./hacking/env-setup" and that's it -- no installation
required. You're now live!



Other Topics
============

Ansible Staff
-------------

Ansible, Inc is a company supporting Ansible and building additional solutions based on
Ansible.  We also provide services and support for those that are interested.

Our most important task, however, is enabling all the great things that happen in the Ansible
community, including organizing software releases of Ansible.  For more information about
any of these things, contact info@ansible.com.

On IRC, you can find us as mdehaan, jimi_c, abadger1999, Tybstar, and others. On the mailing list,
we post with an @ansible.com address.


Mailing List Information
------------------------

Ansible has several mailing lists.  Your first post to the mailing list will be
moderated (to reduce spam), so please allow a day or less for your first post.

`Ansible Project List <https://groups.google.com/forum/#!forum/ansible-project>`_ is for sharing
Ansible Tips, answering questions, and general user discussion.

`Ansible Development List <https://groups.google.com/forum/#!forum/ansible-devel>`_ is for learning
how to develop on Ansible, asking about prospective feature design, or discussions about extending
ansible or features in progress.

`Ansible Announce list <https://groups.google.com/forum/#!forum/ansible-announce>`_ is a read-only
list that shares information about new releases of Ansible, and also rare infrequent event
information, such as announcements about an AnsibleFest coming up, which is our official conference
series.

To subscribe to a group from a non-Google account, you can email the corresponding subscription
address (for example, ansible-devel+subscribe@googlegroups.com).


Release Numbering
-----------------

Releases ending in ".0" are major releases and this is where all new features land.  Releases ending
in another integer, like "0.X.1" and "0.X.2" are dot releases, and these are only going to contain
bugfixes.

Typically, we don't do dot releases for minor bugfixes (reserving these for larger items), but we
may occasionally decide to cut dot releases containing a large number of smaller fixes if it will
be a sizable amount of time before the next release comes out.

Releases are given codenames based on Van Halen songs, that no one really uses.


Tower Support Questions
-----------------------

Ansible `Tower <http://ansible.com/tower>`_ is a UI, Server, and REST endpoint for Ansible,
produced by Ansible, Inc.

If you have a question about tower, email `support@ansible.com <mailto:support@ansible.com>`_
rather than using the IRC
channel or the general project mailing list.


IRC Channel
-----------

Ansible has an IRC channel #ansible on irc.freenode.net.


Notes on Priority Flags
-----------------------

Ansible was one of the top 5 projects with the most OSS contributors on GitHub in 2013, and has
over 800 contributors
to the project to date, not to mention a very large user community that has downloaded the
application well over a million
times. As a result, we have a `lot` of incoming activity to process. In the interest of
transparency, we're telling you how we sort incoming requests.

In our bug tracker you'll notice some labels - P1, P2, P3, P4, and P5. These are our internal
priority orders that we use to sort tickets.

With some exceptions for easy merges (like documentation typos for instance), we're going to spend
most of our time working on P1 and P2 items first, including pull requests. These usually relate to
important bugs or features affecting large segments of the userbase. Hence, if you see something
categorized "P3" or "P4" and it's not appearing to get a lot of immediate attention, this is why.

These labels don't really have a formal definition -- they are simply an ordering. However,
something affecting a major module (yum, apt, etc) is likely to be prioritized higher than a module
affecting a smaller number of users.

Since we place a strong emphasis on testing and code review, it may take a few months for a minor
feature to get merged.

Don't worry though -- we'll also take periodic sweeps through the lower priority queues and give
them some attention as well, particularly in the area of new module changes, so it doesn't
necessarily mean that we'll be exhausting all of the higher-priority queues before getting to your
ticket.

Every bit of effort helps; if you're wishing to expedite the inclusion of a P3 feature pull request
for instance, the best thing you can do
is help close P2 bug reports.

Community Code of Conduct
-------------------------

Ansible’s community welcomes users of all types, backgrounds, and skill levels. Please treat others
as you expect to be treated, keep discussions positive, and avoid discrimination of all kinds,
profanity, allegations of Cthulhu worship, or engaging in controversial debates (excluding, of
course, vi vs emacs).

These expectations apply to both community events and online interactions.

Posts to mailing lists should remain focused around Ansible and IT automation. Abuse of these
community guidelines will not be tolerated and may result in being banned from community resources.


Contributors License Agreement
------------------------------

By contributing, you agree that these contributions are your own (or approved by your employer) and
you grant a full, complete, irrevocable copyright license to all users and developers of the
project, present and future, pursuant to the license of the project.
