Ansible Community  Information
==============================

The purpose of the Ansible community is to  unite developers, system administrators, operations, and 
IT managers to share and build great automation solutions.  This document contains all sorts of 
information about how to contribute and interact with Ansible.  Welcome!

Ways to Interact
================

There are a lot of ways to join and  be a part  of the  Ansible community, such as:

Sharing Ansible with Others
---------------------------

You can help share Ansible with others by telling friends and colleagues, writing a blog post, 
or presenting at user groups (like DevOps groups or the local LUG or BUG).  You are also 
welcome to share slides on speakerdeck, sign up for a free account and tag it “Ansible”. On Twitter, 
you can also share things with #ansible and may wish 
to follow [@Ansible](https://twitter.com/ansible).

Sharing Content and Tips
------------------------

Join the [Ansible project mailing list](https://groups.google.com/forum/#!forum/ansible-project) and you 
can share playbooks you may have written and other interesting implementation stories. Put your Ansible 
content up on places like github  to share with others.

Sharing A Feature Idea
----------------------

Ideas are very welcome and the best place to share them is the [Ansible project mailing list](https://groups.google.com/forum/#!forum/ansible-project) ([Subscribe](https://groups.google.com/forum/#!forum/ansible-project/join)) or #ansible on irc.freenode.net.

While you can file a feature request on GitHub, pull requests are a much better way to get your feature added than submitting a feature request.  Open source is all about itch scratching, and it's less likely that someone else will have the same itches as yourself.  We keep code reasonably simple on purpose so it's easy to dive in and make additions, but be sure to read the "Contributing Code" section below too -- as it doesn't hurt to have a discussion about a feature first -- we're inclined to have preferences about how incoming features might be implemented, and that can save confusion later.

Helping with Documentation
--------------------------

Ansible documentation is a community project too!  If you would like to help with the 
documentation, whether correcting a typo or improving a section, or maybe even 
documenting a new feature, submit a github pull request to  the code that
lives in the “docsite/rst” subdirectory of the project.   Docs are in restructured text
format.  If you aren’t comfortable with restructured text, you can also open a ticket on 
github about any errors you spot or sections you would like to see added. For more information
on creating pull requests, please refer to the
[github help guide](https://help.github.com/articles/using-pull-requests).


Contributing Code (Features or Bugfixes)
----------------------------------------

The Ansible project keeps it’s source on github at 
[github.com/ansible/ansible](http://github.com/ansible/ansible) 
and takes contributions through
[github pull requests](https://help.github.com/articles/using-pull-requests).

It is usually a good idea to join the ansible-devel list to discuss any large features prior to submission, and this especially helps in avoiding duplicate work or efforts where we decide, upon seeing a pull request for the first time, that revisions are needed.  (This is not usually needed for module development)

Note that we do keep Ansible to a particular aesthetic, so if you are unclear about whether a feature
is a good fit or not, having the discussion on the development list is often a lot easier than having
to modify a pull request later.

When submitting patches, be sure to run the unit tests first “make tests” and always use 
“git rebase” vs “git merge” (aliasing git pull to git pull --rebase is a great idea) to 
avoid merge commits in your submissions.  There are also integration tests that can be run in the "tests/integration" directory.  

In order to keep the history clean and better audit incoming code, we will require resubmission of pull requests that contain merge commits.  Use "git pull --rebase" vs "git pull" and "git rebase" vs "git merge". Also be sure to use topic branches to keep your additions on different branches, such that they won't pick up stray commits later.

We’ll then review your contributions and engage with you about questions and  so on.  

As we have a very large and active community, so it may take awhile to get your contributions 
in!  See the notes about priorities in a later section for understanding our work queue.

Patches should be made against the 'devel' branch.

Contributions can be for new features like modules, or to fix bugs you or others have found. If you 
are interested in writing new modules to be included in the core Ansible distribution, please refer 
to the [Module Developers documentation on our website](http://docs.ansible.com/developing_modules.html).

Ansible's aesthetic encourages simple, readable code and consistent, conservatively extending, 
backwards-compatible improvements.  Code developed for Ansible needs to support Python 2.6+, 
while code in modules must run under Python 2.4 or higher.  Please also use a 4-space indent
and no tabs.

Tip: To easily run from a checkout, source "./hacking/env-setup" and that's it -- no install
required.  You're now live!


Reporting A Bug
---------------

Ansible practices responsible disclosure - if this is a security related bug, email security@ansible.com instead of filing a ticket or posting to the Google Group and you will receive a prompt response.

Bugs should be reported to [github.com/ansible/ansible](http://github.com/ansible/ansible) after 
signing up for a free github account.  Before reporting a bug, please use the bug/issue search 
to see if the issue has already been reported.  

When filing a bug, please use the [issue template](https://raw2.github.com/ansible/ansible/devel/examples/issues/ISSUE_TEMPLATE.md) to provide all relevant information.

Do not use the issue tracker for "how do I do this" type questions.  These are great candidates
for IRC or the mailing list instead where things are likely to be more of a discussion.

To be respectful of reviewers time and allow us to help everyone efficiently, please 
provide minimal well-reduced and well-commented examples versus sharing your entire production
playbook.  Include playbook snippets and output where possible.  

Content in the GitHub bug tracker can be indented four spaces to preserve formatting.  
For multiple-file content, we encourage use of gist.github.com.  Online pastebin content can expire.

If you are not sure if something is a bug yet, you are welcome to ask about something on 
the mailing list or IRC first.  As we are a very high volume project, if you determine that 
you do have a bug, please be sure to open the issue yourself to ensure we have a record of
it. Don’t rely on someone else in the community to file the bug report for you.

It may take some time to get to your report, see "A Note About Priorities" below.

A Note About Priorities
=======================

Ansible was one of the top 5 projects with the most OSS contributors on GitHub in 2013, and well over
600 people have added code to the project.  As a result, we have a LOT of incoming activity to process.

In the interest of transparency, we're telling you how we do this.

In our bug tracker you'll notice some labels - P1, P2, P3, P4, and P5.  These are our internal
priority orders that we use to sort tickets.  

With some exceptions for easy merges (like documentation typos for instance), 
we're going to spend most of our time working on P1 and P2 items first, including pull requests.  
These usually relate to important
bugs or features affecting large segments of the userbase.  So if you see something categorized
"P3 or P4", and it's not appearing to get a lot of immediate attention, this is why.

These labels don't really have definition - they are a simple ordering.  However something
affecting a major module (yum, apt, etc) is likely to be prioritized higher than a module
affecting a smaller number of users.

Since we place a strong emphasis on testing and code review, it may take a few months for a minor feature to get merged.

Don't worry though -- we'll also take periodic sweeps through the lower priority queues and give
them some attention as well, particularly in the area of new module changes.  So it doesn't neccessarily
mean that we'll be exhausting all of the higher-priority queues before getting to your ticket.

Release Numbering
=================

Releases ending in ".0" are major releases and this is where all new features land.  Releases ending
in another integer, like "0.X.1" and "0.X.2" are dot releases, and these are only going to contain
bugfixes.  Typically we don't do dot releases for minor releases, but may occasionally decide to cut
dot releases containing a large number of smaller fixes if it's still a fairly long time before
the next release comes out.

Online Resources
================

Documentation
-------------

The main ansible documentation can be found at [docs.ansible.com](http://docs.ansible.com). 
As mentioned above this is an open source project, so we accept contributions to the documentation. 
You can also find some best practices examples that we recommend reading at 
[ansible-examples](http://github.com/ansible/ansible-examples).

Mailing lists
-------------

Ansible has several mailing lists.  Your first post to the mailing list will be 
moderated (to reduce spam), so please allow a day or less for your first post.

[ansible-announce](https://groups.google.com/forum/#!forum/ansible-announce) is for release 
announcements and major news.  It is a low traffic read-only list and you should only get a few 
emails a month.

[ansible-project](https://groups.google.com/forum/#!forum/ansible-project) is the main list, and is 
used for sharing cool projects you may have built, talking about Ansible ideas, and for users to ask 
questions or to help other users.

[ansible-devel](https://groups.google.com/forum/#!forum/ansible-devel) is a technical list for 
developers working on Ansible and Ansible modules.  Join here to discuss how to build modules, 
prospective feature implementations, or technical challenges.

To subscribe to a group from a non-google account, you can email the subscription address, for 
example ansible-devel+subscribe@googlegroups.com.

IRC
---

Ansible has a general purpose IRC channel available at #ansible on irc.freenode.net.
Use this channel for all types of conversations, including sharing tips, coordinating 
development work, or getting help from other users.

Miscellaneous Information
=========================

Staff
-----

Ansible, Inc is a company supporting Ansible and building additional solutions based on 
Ansible.  We also do services and support for those that are interested.   Our most 
important task however is enabling all the great things that happen in the Ansible 
community, including organizing software releases of Ansible.  For more information about
any of these things, contact info@ansible.com

On IRC, you can find us as mdehaan, jimi_c, Tybstar, and others.   On the mailing list, 
we post with an @ansible.com address.

Community Code of Conduct
-------------------------

Ansible’s community welcomes users of all types, backgrounds, and skill levels. Please 
treat others as you expect to be treated, keep discussions positive, and avoid discrimination, profanity, allegations of Cthulhu worship, or engaging in controversial debates (except vi vs emacs is cool).  

Posts to mailing lists  should remain focused around Ansible and IT automation.   Abuse of these community guidelines will not be tolerated and may result in banning from community resources.

Contributors License Agreement
------------------------------

By contributing you agree that these contributions are your own (or approved by your employer) 
and you grant a full, complete, irrevocable
copyright license to all users and developers of the project, present and future, pursuant 
to the license of the project.



