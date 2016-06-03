``repoze.profile`` Changelog
============================

2.2 (2016-06-03)
----------------

- Add decorator for profiling individual functions.

- Add support for Python 3.5.

- Drop support for Python 2.6 and Python 3.2.

2.1 (2015-05-28)
----------------

- Add support for testing on Travis-CI.

- Add support for Python 3.4.

2.0 (2013-04-08)
----------------

- No changes since 2.0b1.

2.0b1 (2013-01-30)
------------------

- Add support for building docs / exercising doctest snippets under ``tox``.

- Add ``setup.py docs`` alias (installs Sphinx).

- Note support for PyPy.

- Add support for Python 3.3.

- Drop support for Python 2.4 / 2.5.

1.4 (2012-03-29)
----------------

- This release is the last which will maintain support for Python 2.4 /
  Python 2.5.

- Added an ``unwind`` configuration option.  If ``unwind`` is True, the
  iterable returned by the downstream application will be consumed and turned
  into a list during profiling.  This allows you to profile applications
  which return generators or other iterables that do "real work".

- Applications which return generators that do "real work" will now need to
  supply the ``unwind`` flag to configuration to see that work in profile
  output.

1.3 (2011-09-30)
----------------

- Added an option to filter profile output by filename.  Thanks to Shish
  for the patch.

- Put a lock around "index" method in order to prevent exceptions when trying
  to view profile data as it's being generated.  Closes
  http://bugs.repoze.org/issue168.

- Removed these dependencies: ``meld3``, ``paste``.

- A new ``paste.filter_app_factory`` entry point has been added named
  ``main`` which points to the profiler.  This allows for the simplified
  spelling ``egg:repoze.profile`` in paste.ini files when referring to the
  profile middleware (instead of the older, more verbose
  ``egg:repoze.profile#profiler``.  The older alias continues to work as
  well.

- The new canonical import location for the profiling middleware is
  ``repoze.profile.ProfileMiddleware``.  Older imports continue to work.

- Remove ez_setup.py.

- Python 3.2 compatibility.

1.2 (2010-11-25)
----------------

- Converted documentation to Sphinx.

- Ensure we consume generators returned by the wrapped application.
  Fixes http://bugs.repoze.org/issue169 

1.1 (2009-10-06)
----------------

- 100% test coverage.

- Get rid of spurious measurements of testing scaffolding in profile
  output (show no calls that are inside r.profile itself).

1.0 (2009-06-04)
----------------

- Relax the pinned requirement on elementtree < 1.2.7.

0.9 (2009-05-10)
----------------

- Made the `pyprof2calltree` dependency conditional on the Python version.
  This package depends on Python >= 2.5.

0.8 (2009-02-25)
----------------

- Added optional support for directly writing out the profiling data in the
  KCacheGrind format.

- Avoid a dependency on `elementtree` when used with Python 2.5 and later.
  In those Python versions we used the built-in xml.etree support.

0.7 (2009-02-08)
----------------

- ``discard_first_request = true`` did not work!

- Added tests for ``discard_first_request`` and ``flush_at_shutdown``.

- Converted CHANGES.txt to ReST.

- Bump ez_setup.py version.

0.6 (2008-08-21)
----------------

- ``discard_first_request = false`` did not work.

- Clearing the profile data from the user interface did not properly
   discard profiler state.

0.5 (2008-06-11)
----------------

- Initial PyPI release.

0.4 (2008-05-07)
----------------

- Remove dependency-link to http://dist.repoze.org to prevent
  easy_install from adding that to its search path.

- Incorporated a patch from Alec Flett <alecf@metaweb.com> to uses
  ``cProfile``, if available, rather than pure Python ``profile``.

- Bump ez_setup.py version.

0.3 (2008-02-20)
----------------

- Added compatibility with Python 2.5.

- Made setup.py depend explicitly on ElementTree 1.2.6: meld needs it
  but meld isn't a setuptools package.

0.2 (2008-02-20)
----------------

- Added a browser UI.

- Added a knob to control discard at shutdown.

0.1 (2008-02-08)
----------------

- Initial release.
