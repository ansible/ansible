galaxy-metadata
===============

* Validates the required keys (namespace, name, version, readme, authors) for the collection galaxy.yml metadata file.
* If the required keys aren’t present or if the required and other keys contain ``null`` value in the galaxy.yml file then this sanity test will throw an error.
