repoze.profile README
=====================

This package provides a WSGI middleware component which aggregates
profiling data across *all* requests to the WSGI application.  It
provides a web GUI for viewing profiling data.

Installation
------------

Install using setuptools, e.g. (within a virtualenv)::

 $ easy_install repoze.profile

Configuration via Python
------------------------

Wire up the middleware in your application::

 from repoze.profile.profiler import AccumulatingProfileMiddleware
 middleware = AccumulatingProfileMiddleware(
                app,
                log_filename='/foo/bar.log',
                discard_first_request=True,
                flush_at_shutdown=True,
                path='/__profile__'
               )

The configuration options are as follows::

 - ``log_filename`` is the name of the file to which the accumulated
   profiler statistics are logged.

 - If ``discard_first_request`` to true (the default), then the
   middleware discards the statistics for the first request:  the
   rationale is that there are a bunch of lazy / "first time"
   initializations which distort measurement of the application's
   normal performance.

 - If ``flush_at_shutdown`` is true (the default), profiling data will
   be deleted when the middleware instance disappears (via its
   __del__).  If it's false, profiling data will not be deleted.

 - ``path`` is the URL path to the profiler UI.  It defaults to
   ``/__profile__``.

Once you have some profiling data, you can visit ``path`` in your
browser to see a user interface displaying profiling statistics
(e.g. ``http://localhost:8080/__profile__``).

Configuration via Paste
-----------------------

Wire the middleware into a pipeline in your Paste configuration, for
example::

 [filter:profile]
 use = egg:repoze.profile#profile
 log_filename = myapp.profile
 discard_first_request = true
 path = /__profile__
 flush_at_shutdown = true
 ...

 [pipeline:main]
 pipeline = egg:Paste#cgitb
            egg:Paste#httpexceptions
            profile
            myapp

Once you have some profiling data, you can visit ``path`` in your
browser to see a user interface displaying profiling statistics.

Reporting Bugs / Development Versions
-------------------------------------

Visit http://bugs.repoze.org to report bugs.  Visit
http://svn.repoze.org to download development or tagged versions.

