Community Information & Contributing
````````````````````````````````````

Ansible is an open source project designed to bring together administrators and developers of all kinds to collaborate on building
IT automation solutions that work well for them.   

Should you wish to get more involved -- whether in terms of just asking a question, helping other users, introducing new people to Ansible, or helping with the software or documentation, we welcome your contributions to the project.

.. contents:: Topics

Ansible Users
=============

I've Got A Question
-------------------

We're happy to help!

Ansible questions are best asked on the `Ansible Google Group Mailing List <http://groups.google.com/group/ansible-project>`_.  

This is a very large high-traffic list for answering questions and sharing tips
and tricks. Anyone can join, and email delivery is optional if you just want to read the group online.  To cut down on spam, your first post is moderated, though posts are approved quickly.

Please be sure to share any relevant commands you ran, output, and detail, indicate the version of Ansible you are using when asking a question.

Where needed, link to gists or GitHub repos to show examples, rather than sending attachments to the list.

We recommend using Google search to see if a topic has been answered recently, but comments found in older threads may no longer apply, depending on the topic.

Before you post, be sure you are running the latest stable version of Ansible.  You can check this by comparing the output of ``ansible --version`` with the version indicated on `PyPi <https://pypi.python.org/pypi/ansible>`_.

Alternatively, you can also join our IRC channel - ``#ansible`` on irc.freenode.net.  It's a very high traffic channel as well, so if you don't get an answer you like, please stop by our mailing list, which is more likely
to get the attention of core developers since it's asynchronous.

I'd Like To Keep Up With Release Announcements
----------------------------------------------

Release announcements are posted to ansible-project, though if you don't want to keep up with the very active list, you can join the `Ansible Announce Mailing List <http://groups.google.com/group/ansible-announce>`_.

This is a low-traffic read-only list, where we'll share release announcements and occasionally links to major Ansible Events around the world.

I'd Like To Help Share and Promote Ansible
------------------------------------------

You can help share Ansible with others by telling friends and colleagues, writing a blog post, 
or presenting at user groups (like DevOps groups or the local LUG).  

You are also welcome to share slides on speakerdeck, sign up for a free account and tag it “Ansible”. On Twitter, 
you can also share things with #ansible and may wish to `follow us <https://twitter.com/ansible>`_.

I'd Like To Help Ansible Move Faster
------------------------------------

If you're a developer, one of the most valuable things you can do is look at the GitHub issues list and help fix bugs.  We almost always prioritize bug fixing over
feature development, so clearing bugs out of the way is one of the best things you can do.

If you're not a developer, helping test pull requests for bug fixes and features is still immensely valuable.  You can do this by checking out ansible, making a test
branch off the main one, merging a GitHub issue, testing, and then commenting on that particular issue on GitHub.

I'd Like To Report A Bug
------------------------------------

Ansible practices responsible disclosure - if this is a security related bug, email `security@ansible.com <mailto:security@ansible.com>`_ instead of filing a ticket or posting to the Google Group and you will receive a prompt response.

Ansible bugs should be reported to `github.com/ansible/ansible <https://github.com/ansible/ansible>`_ after
signing up for a free GitHub account.  Before reporting a bug, please use the bug/issue search
to see if the issue has already been reported.
This is listed on the bottom of the docs page for any module.

Knowing your ansible version and the exact commands you are running, and what you expect, saves time and helps us help everyone with their issues
more quickly.

Do not use the issue tracker for "how do I do this" type questions.  These are great candidates
for IRC or the mailing list instead where things are likely to be more of a discussion.

To be respectful of reviewers' time and allow us to help everyone efficiently, please 
provide minimal well-reduced and well-commented examples versus sharing your entire production
playbook.  Include playbook snippets and output where possible.  

When sharing YAML in playbooks, formatting can be preserved by using `code blocks <https://help.github.com/articles/creating-and-highlighting-code-blocks/>`_.

For multiple-file content, we encourage use of gist.github.com.  Online pastebin content can expire, so it's nice to have things around for a longer term if they
are referenced in a ticket.

If you are not sure if something is a bug yet, you are welcome to ask about something on 
the mailing list or IRC first.  

As we are a very high volume project, if you determine that 
you do have a bug, please be sure to open the issue yourself to ensure we have a record of
it. Don’t rely on someone else in the community to file the bug report for you.

It may take some time to get to your report, see our information about priority flags below.

I'd Like To Help With Documentation
-----------------------------------

Ansible documentation is a community project too!  

If you would like to help with the 
documentation, whether correcting a typo or improving a section, or maybe even 
documenting a new feature, submit a GitHub pull request to  the code that
lives in the ``docsite/rst`` subdirectory of the project for most pages, and there is an "Edit on GitHub"
link up on those.

Module documentation is generated from a ``DOCUMENTATION`` structure embedded in the source code of each module, which is in `/lib/ansible/modules/ <https://github.com/ansible/ansible/tree/devel/lib/ansible/modules/>`_.

For more information on module documentation see `How to document modules <http://docs.ansible.com/ansible/dev_guide/developing_modules_documenting.html>`_.

Aside from modules, the main docs are in restructured text
format.  

If you aren’t comfortable with restructured text, you can also open a ticket on 
GitHub about any errors you spot or sections you would like to see added. For more information
on creating pull requests, please refer to the
`GitHub help guide <https://help.github.com/articles/using-pull-requests>`_.

For Current and Prospective Developers
=======================================

I'd Like To Learn How To Develop on Ansible
-------------------------------------------

If you're new to Ansible and would like to figure out how to work on things, stop by the ansible-devel mailing list
and say hi, and we can hook you up.

A great way to get started would be reading over some of the development documentation on the module site, and then
finding a bug to fix or small feature to add.

Modules are some of the easiest places to get started.

Contributing Code (Features or Bugfixes)
----------------------------------------

The Ansible project keeps its source on GitHub at `github.com/ansible/ansible <https://github.com/ansible/ansible>`_.

The project takes contributions through `github pull requests <https://help.github.com/articles/using-pull-requests>`_.

It is usually a good idea to join the ansible-devel list to discuss any large features prior to submission,
and this especially helps in avoiding duplicate work or efforts where we decide, upon seeing a pull request
for the first time, that revisions are needed. (This is not usually needed for module development, but can be nice for large changes).

Note that we do keep Ansible to a particular aesthetic, so if you are unclear about whether a feature
is a good fit or not, having the discussion on the development list is often a lot easier than having
to modify a pull request later.

New module developers should read through `developing modules <http://docs.ansible.com/ansible/dev_guide/developing_modules.html>`_.

For more information about testing see `testing <http://docs.ansible.com/ansible/dev_guide/testing.html>`_.

In order to keep the history clean and better audit incoming code, we will require resubmission of pull requests that
contain merge commits.  Use ``git pull --rebase`` (rather than ``git pull``) and ``git rebase`` (rather than ``git merge``). Also be sure to use topic
branches to keep your additions on different branches, such that they won't pick up stray commits later.

If you make a mistake you do not need to close your PR. Instead, create a clean branch locally and then push to GitHub
with ``--force`` to overwrite the existing branch (permissible in this case as no one else should be using that
branch as reference). Code comments won't be lost, they just won't be attached to the existing branch.

We’ll then review your contributions and engage with you about questions and  so on.

Because we have a very large and active community it may take awhile to get your contributions
in!  See the notes about priorities in a later section for understanding our work queue.
Be patient, your request might not get merged right away, we also try to keep the devel branch more
or less usable so we like to examine Pull requests carefully, which takes time.

Patches should always be made against the ``devel`` branch.

Keep in mind that small and focused requests are easier to examine and accept, having example cases
also help us understand the utility of a bug fix or a new feature.

Contributions can be for new features like modules, or to fix bugs you or others have found. If you
are interested in writing new modules to be included in the core Ansible distribution, please refer
to the `module development documentation <http://docs.ansible.com/developing_modules.html>`_.

Ansible's aesthetic encourages simple, readable code and consistent,
conservatively extending, backwards-compatible improvements. When contributing code to Ansible, 
please observe the following guidelines:

- Code developed for Ansible needs to support Python2-2.6 or higher and Python3-3.5 or higher.
- Use a 4-space indent, not  tabs.
- We do not enforce 80 column lines; up to 160 columns are acceptable.
- We do not accept 'style only' pull requests unless the code is nearly unreadable.
- We are "PEP8ish", but not strictly compliant, see :doc:`testing_pep8` for more information.

You can also contribute by testing and revising other requests, especially if it is one you are interested
in using. Please keep your comments clear and to the point, courteous and constructive, tickets are not a
good place to start discussions (ansible-devel and IRC exist for this).

Tip: To easily run from a checkout, source ``./hacking/env-setup`` and that's it -- no install
required.  You're now live! For more information see `hacking/README.md <https://github.com/ansible/ansible/blob/devel/hacking/README.md>`_.

Other Topics
============

Ansible Staff
-------------

Ansible, Inc is a company supporting Ansible and building additional solutions based on
Ansible.  We also do services and support for those that are interested. We also offer an
enterprise web front end to Ansible (see Tower below).

Our most important task however is enabling all the great things that happen in the Ansible
community, including organizing software releases of Ansible.  For more information about
any of these things, contact info@ansible.com

On IRC, you can find us as jimi_c, abadger1999, Tybstar, bcoca, and others.   On the mailing list,
we post with an @ansible.com address.

Mailing List Information
------------------------

Ansible has several mailing lists.  Your first post to the mailing list will be
moderated (to reduce spam), so please allow a day or less for your first post.

`Ansible Project List <https://groups.google.com/forum/#!forum/ansible-project>`_ is for sharing Ansible Tips,
answering questions, and general user discussion.

`Ansible Development List <https://groups.google.com/forum/#!forum/ansible-devel>`_ is for learning how to develop on Ansible,
asking about prospective feature design, or discussions about extending ansible or features in progress.

`Ansible Announce list <https://groups.google.com/forum/#!forum/ansible-announce>`_ is a read-only list that shares information
about new releases of Ansible, and also rare infrequent event information, such as announcements about an AnsibleFest coming up,
which is our official conference series.

`Ansible Lockdown List <https://groups.google.com/forum/#!forum/ansible-lockdown>`_ is for all things related to Ansible Lockdown projects, including DISA STIG automation and CIS Benchmarks.

To subscribe to a group from a non-google account, you can send an email to the subscription address requesting the subscription. For example: ansible-devel+subscribe@googlegroups.com

IRC Meetings
------------

The Ansible community holds regular IRC meetings on various topics, and anyone who is interested is invited to 
participate. For more information about Ansible meetings, consult the `meeting schedule and agenda page <https://github.com/ansible/community/blob/master/meetings/README.md>`_.

Release Numbering
-----------------

Releases ending in ".0" are major releases and this is where all new features land.  Releases ending
in another integer, like "0.X.1" and "0.X.2" are dot releases, and these are only going to contain
bugfixes.

Typically we don't do dot releases for minor bugfixes (reserving these for larger items),
but may occasionally decide to cut dot releases containing a large number of smaller fixes if it's still a fairly long time before
the next release comes out.

Releases are also given code names based on Van Halen songs, that no one really uses.

Tower Support Questions
-----------------------

Ansible `Tower <https://ansible.com/tower>`_ is a UI, Server, and REST endpoint for Ansible, produced by Ansible, Inc.

If you have a question about Tower, visit `Red Hat support <https://access.redhat.com/products/ansible-tower-red-hat/>`_ rather than using the IRC
channel or the general project mailing list.

IRC Channel
-----------

Ansible has several IRC channels on Freenode (irc.freenode.net):

- ``#ansible`` - For general use questions and support.
- ``#ansible-devel`` - For discussions on developer topics and code related to features/bugs.
- ``#ansible-aws`` - For discussions on Amazon Web Services.
- ``#ansible-container`` - For discussions on Ansible Container.
- ``#ansible-vmware`` - For discussions on Ansible & VMware.
- ``#ansible-windows`` - For discussions on Ansible & Windows.
- ``#ansible-meeting`` - For public community meetings. We will generally announce these on one or more of the above mailing lists. See the `meeting schedule and agenda page <https://github.com/ansible/community/blob/master/meetings/README.md>`_
- ``#ansible-notices`` - Mostly bot output from things like Github, etc.

Notes on Priority Flags
-----------------------

Ansible was one of the top 5 projects with the most OSS contributors on GitHub in 2013, and has over 1400 contributors
to the project to date, not to mention a very large user community that has downloaded the application well over a million
times. As a result, we have a LOT of incoming activity to process.

In the interest of transparency, we're telling you how we sort incoming requests.

In our bug tracker you'll notice some labels - P1 and P2.  These are the internal
priority orders that we use to sort tickets.

With some exceptions for easy merges (like documentation typos for instance),
we're going to spend most of our time working on P1 and P2 items first, including pull requests.
These usually relate to important bugs or features affecting large segments of the userbase.  If you see something categorized without P1 or P2, and it's not appearing to get a lot of immediate attention, this is why.

These labels don't really have a definition - they are a simple ordering.  However something
affecting a major module (yum, apt, etc) is likely to be prioritized higher than a module
affecting a smaller number of users.

Since we place a strong emphasis on testing and code review, it may take a few months for a minor feature to get merged. This doesn't mean that we'll be exhausting all of the higher-priority queues before getting to your ticket; we will also take periodic sweeps through the lower priority queues and give them some attention as well, particularly in the area of new module changes. 


Every bit of effort helps - if you're wishing to expedite the inclusion of a P3 feature pull request for instance, the best thing you can do is help close P2 bug reports.

Community Code of Conduct
=========================

Every community can be strengthened by a diverse variety of viewpoints, insights,
opinions, skillsets, and skill levels. However, with diversity comes the potential for
disagreement and miscommunication. The purpose of this Code of Conduct is to ensure that
disagreements and differences of opinion are conducted respectfully and on their own
merits, without personal attacks or other behavior that might create an unsafe or
unwelcoming environment.

These policies are not designed to be a comprehensive set of Things You Cannot Do. We ask
that you treat your fellow community members with respect and courtesy, and in general,
Don't Be A Jerk. This Code of Conduct is meant to be followed in spirit as much as in
letter and is not exhaustive.

All Ansible events and participants therein are governed by this Code of Conduct and
anti-harassment policy. We expect organizers to enforce these guidelines throughout all events,
and we expect attendees, speakers, sponsors, and volunteers to help ensure a safe
environment for our whole community. Specifically, this Code of Conduct covers
participation in all Ansible-related forums and mailing lists, code and documentation
contributions, public IRC channels, private correspondence, and public meetings.

Ansible community members are...

**Considerate**

Contributions of every kind have far-ranging consequences. Just as your work depends on
the work of others, decisions you make surrounding your contributions to the Ansible
community will affect your fellow community members. You are strongly encouraged to take
those consequences into account while making decisions.

**Patient**

Asynchronous communication can come with its own frustrations, even in the most responsive
of communities. Please remember that our community is largely built on volunteered time,
and that questions, contributions, and requests for support may take some time to receive
a response. Repeated "bumps" or "reminders" in rapid succession are not good displays of
patience. Additionally, it is considered poor manners to ping a specific person with
general questions. Pose your question to the community as a whole, and wait patiently for
a response.

**Respectful**

Every community inevitably has disagreements, but remember that it is
possible to disagree respectfully and courteously. Disagreements are never an excuse for
rudeness, hostility, threatening behavior, abuse (verbal or physical), or personal attacks.

**Kind**

Everyone should feel welcome in the Ansible community, regardless of their background.
Please be courteous, respectful and polite to fellow community members. Do not make or
post offensive comments related to skill level, gender, gender identity or expression,
sexual orientation, disability, physical appearance, body size, race, or religion.
Sexualized images or imagery, real or implied violence, intimidation, oppression,
stalking, sustained disruption of activities, publishing the personal information of
others without explicit permission to do so, unwanted physical contact, and unwelcome
sexual attention are all strictly prohibited.  Additionally, you are encouraged not to
make assumptions about the background or identity of your fellow community members.

**Inquisitive**

The only stupid question is the one that does not get asked. We
encourage our users to ask early and ask often. Rather than asking whether you can ask a
question (the answer is always yes!), instead, simply ask your question. You are
encouraged to provide as many specifics as possible. Code snippets in the form of Gists or
other paste site links are almost always needed in order to get the most helpful answers.
Refrain from pasting multiple lines of code directly into the IRC channels - instead use
gist.github.com or another paste site to provide code snippets.

**Helpful**

The Ansible community is committed to being a welcoming environment for all users,
regardless of skill level. We were all beginners once upon a time, and our community
cannot grow without an environment where new users feel safe and comfortable asking questions.
It can become frustrating to answer the same questions repeatedly; however, community
members are expected to remain courteous and helpful to all users equally, regardless of
skill or knowledge level. Avoid providing responses that prioritize snideness and snark over
useful information. At the same time, everyone is expected to read the provided
documentation thoroughly. We are happy to answer questions, provide strategic guidance,
and suggest effective workflows, but we are not here to do your job for you.

Anti-harassment policy
----------------------
Harassment includes (but is not limited to) all of the following behaviors:

- Offensive comments related to gender (including gender expression and identity), age, sexual orientation, disability, physical appearance, body size, race, and religion
- Derogatory terminology including words commonly known to be slurs
- Posting sexualized images or imagery in public spaces
- Deliberate intimidation
- Stalking
- Posting others' personal information without explicit permission
- Sustained disruption of talks or other events
- Inappropriate physical contact
- Unwelcome sexual attention

Participants asked to stop any harassing behavior are expected to comply immediately.
Sponsors are also subject to the anti-harassment policy. In particular, sponsors should
not use sexualized images, activities, or other material. Meetup organizing staff and
other volunteer organizers should not use sexualized attire or otherwise create a
sexualized environment at community events.

In addition to the behaviors outlined above, continuing to behave a certain way after you
have been asked to stop also constitutes harassment, even if that behavior is not
specifically outlined in this policy. It is considerate and respectful to stop doing
something after you have been asked to stop, and all community members are expected to
comply with such requests immediately.

Policy violations
-----------------
Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by
contacting greg@ansible.com, to any channel operator in the community IRC
channels, or to the local organizers of an event. Meetup organizers are encouraged to
prominently display points of contact for reporting unacceptable behavior at local events.

If a participant engages in harassing behavior, the meetup organizers may take any action
they deem appropriate. These actions may include but are not limited to warning the
offender, expelling the offender from the event, and barring the offender from future
community events.

Organizers will be happy to help participants contact security or local law enforcement,
provide escorts to an alternate location, or otherwise assist those experiencing
harassment to feel safe for the duration of the meetup. We value the safety and well-being
of our community members and want everyone to feel welcome at our events, both online and
offline.

We expect all participants, organizers, speakers, and attendees to follow these policies at
all of our event venues and event-related social events.

The Ansible Community Code of Conduct is licensed under the Creative Commons
Attribution-Share Alike 3.0 license. Our Code of Conduct was adapted from Codes of Conduct
of other open source projects, including:

* Contributor Covenant
* Elastic
* The Fedora Project
* OpenStack
* Puppet Labs
* Ubuntu

Contributors License Agreement
==============================

By contributing you agree that these contributions are your own (or approved by your employer) and you grant a full, complete, irrevocable
copyright license to all users and developers of the project, present and future, pursuant to the license of the project.
