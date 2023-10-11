Introducing Pymend to your project
==================================

.. NOTE::

    This guide is incomplete. Contributions are welcomed and would be deeply
    appreciated!


Avoiding ruining git blame
--------------------------

A long-standing argument against moving to automated code modifiers like *PyMend* is
that the migration will clutter up the output of :code:`git blame`. This was a valid argument,
but since Git version 2.23, Git natively supports
`ignoring revisions in blame <https://git-scm.com/docs/git-blame#Documentation/git-blame.txt---ignore-revltrevgt>`__
with the :code:`--ignore-rev` option. You can also pass a file listing the revisions to ignore
using the :code:`--ignore-revs-file` option. The changes made by the revision will be ignored
when assigning blame. Lines modified by an ignored revision will be blamed on the
previous revision that modified those lines.

So when running *PyMend* over your project to fix docstrings, reformat everything and commit
the changes (preferably in one massive commit). Then put the full 40 characters commit
identifier(s) into a file.

.. code-block:: text

    # Run PyMend
    5b4ab991dede475d393e9d69ec388fd6bd949699

Afterwards, you can pass that file to :code:`git blame` and see clean and meaningful blame
information.

.. code-block:: console

    $ git blame important.py --ignore-revs-file .git-blame-ignore-revs
    7a1ae265 (John Smith 2019-04-15 15:55:13 -0400 1) def very_important_function(text, file):
    abdfd8b0 (Alice Doe  2019-09-23 11:39:32 -0400 2)     text = text.lstrip()
    7a1ae265 (John Smith 2019-04-15 15:55:13 -0400 3)     with open(file, "r+") as f:
    7a1ae265 (John Smith 2019-04-15 15:55:13 -0400 4)         f.write(formatted)


You can even configure :code:`git` to automatically ignore revisions listed in a file on every
call to :code:`git blame`.

.. code-block:: console

    $ git config blame.ignoreRevsFile .git-blame-ignore-revs


**The one caveat is that some online Git-repositories like GitLab do not yet support
ignoring revisions using their native blame UI.** So blame information will be cluttered
with a reformatting commit on those platforms. (If you'd like this feature, there's an
open issue for `GitLab <https://gitlab.com/gitlab-org/gitlab/-/issues/31423>`__).
`GitHub supports .git-blame-ignore-revs <https://docs.github.com/en/repositories/working-with-files/using-files/viewing-a-file#ignore-commits-in-the-blame-view>`__
by default in blame views however.
