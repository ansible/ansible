
.. _search_hints:

Writing documentation so search can find it
-------------------------------------------

One of the keys to writing good documentation is to make it findable. Readers use a combination of internal site search and external search engines such as Google or duckduckgo.

To ensure Ansible documentation is findable, you should:

#. Use headings that clearly reflect what you are documenting.
#. Use numbered lists for procedures or high-level steps where possible.
#. Avoid linking to github blobs where possible.


Using clear headings in documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We all use simple English when we want to find something. For example, the title of this page could have been any one of the following:

* Search optimization
* Findable documentation
* Writing for findability

What we are really trying to describe is - how do I write documentation so search engines can find my content? That simple phrase is what drove the title of this section. When you are creating your headings for documentation, spend some time to think about what you would type in a search box to find it, or more importantly, how someone less familiar with Ansible would try to find that information. Your heading should be the answer to that question.

One word of caution - you do want to limit the size of your headings. A full heading such as `How do I write documentation so search engines can find my content?` is too long. Search engines would truncate anything over 50 - 60 characters. Long headings would also wrap on smaller devices such as a smart phone.

Using numbered lists for `zero position` snippets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Google can optimize the search results by adding a `feature snippet <https://support.google.com/websearch/answer/9351707>`_ at the top of the search results. This snippet provides a small window into the documentation on that first search result that adds more detail than the rest of the search results, and can occasionally answer the reader's questions right there, or at least verify that the linked page is what the reader is looking for.

Google returns the feature snippet in the form of numbered steps. Where possible, you should add a numbered list near the top of your documentation page, where appropriate. The steps can be the exact procedure a reader would follow, or could be a high level introduction to the documentation topic, such as the numbered list at the top of this page.

Problems with github blobs on search results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Search engines do not typically return github blobs in search results, at least not in higher ranked positions. While it is possible and sometimes necessary to link to github blobs from documentation, the better approach would be to copy that information into an .rst page in Ansible documentation.

Other search hints
^^^^^^^^^^^^^^^^^^

While it may not be possible to adapt your documentation to all search optimizations, keep the following in mind as you write your documentation:

* **Search engines don't parse beyond the `#` in an html page.** So for example, all the subheadings on this page are appended to the main page URL. As such, when I search for 'Using number lists for zero position snippets', the search result would be a link to the top of this page, not a link directly to the subheading I searched for. Using :ref:`local TOCs <local_toc>` helps alleviate this problem as the reader can scan for the header at top of the page and click to the section they are looking for. For critical documentation, consider creating a new page that can be a direct search result page.

* **Make your first few sentences clearly describe your page topic.** Search engines return not just the URL, but a short description of the information at the URL. For Ansible documentation, we do not have description metadata embedded on each page. Instead, the search engines return the first couple of sentences (140 characters) on the page. That makes your first sentence or two very important to the reader who is searching for something in Ansible.
