Heartfelt Hooks
===============

git pre-commit hooks that work with http://pre-commit.com/

Hooks available
---------------

``check-whitespace``

Checks for filenames that contain whitespace.

* ``README.txt``: good
* ``READ ME.txt``: bad

``check-mixed-case``

Checks for filenames that contain a mixture of upper and lowercase.

* ``README.txt``: good
* ``ReadMe.txt``: bad

``check-snake-case``

Checks that filenames are either snake-case or sausage-case but never a mixture.

* ``read-me-first.txt``: good
* ``read-me_first.txt``: bad

``check-heading-levels``

Check for consitency of heading levels in a notebook. This means that heading
levels do not increase by more than one and do not drop lower than the first
heading level in the notebook.

Good:

.. code-block:: markdown

  # Heading 1

  ## Heading 1.1
  ### Heading 1.1.1

  # Heading 2

Bad (heading 1.1.1 indents two levels from heading 1):

.. code-block:: markdown

  # Heading 1

  ### Heading 1.1.1

  # Heading 2

Also bad (heading 2 dedents below the anchor heading 1):

.. code-block:: markdown

  ## Heading 1

  ### Heading 1.1

  # Heading 2


``insert-toc``

Inserts a table of contents into a notebook based on its headings.

``hide-solution-cells``

Hides the solution cells of a notebook by changing the cell type to *markdown*
and putting within a ``<details>`` *html* tag.
