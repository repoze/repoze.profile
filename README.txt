repoze.profile README
=====================

This package provides a WSGI middleware component which aggregates
profiling data across *all* requests to the WSGI application.

Installation
------------

Install using setuptools, e.g. (within a virtualenv)::

 $ bin/easy_install -d http://dist.repoze.org/ repoze.profile

Configuration
-------------

Wire the middleware into a pipeline in your Paste configuration::

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

The configuration options are as follows:

 - ``log_filename`` is the name of the file to which the accumulated
   profiler statistics are logged.

 - If ``discard_first_request`` to true (the default), then the
   middleware discards the statistics for the first request:  the
   rationale is that there are a bunch of lazy / "first time"
   initializations which distort measurement of the application's
   normal performance.

 - ``path`` is the URL path to the profiler UI.  It defaults to
   ``/__profile__``.

 - If ``flush_at_shutdown`` is true (the default), profiling data will
   be deleted when the middleware instance disappears (via its
   __del__).  If it's false, profiling data will persist across
   application restarts.

Once you have some profiling data, you can visit ``path`` in your
browser to see a user interface displaying profiling statistics.
