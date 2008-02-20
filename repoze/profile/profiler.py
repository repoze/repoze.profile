""" Middleware that profiles all requests, accumulating timings.

o Insprired by the paste.debug.profile version, which profiles single requests.
"""
import os
import profile
import pstats
import sys
import StringIO
import threading

from paste.request import parse_formvars
from paste.request import construct_url

import meld3

_HERE = os.path.abspath(os.path.dirname(__file__))

DEFAULT_PROFILE_LOG = 'wsgi.prof'

class AccumulatingProfileMiddleware(object):

    def __init__(self, app,
                 global_conf=None,
                 log_filename=DEFAULT_PROFILE_LOG,
                 discard_first_request=True,
                 flush_at_shutdown = True,
                 path='/__profile__',
                ):
        self.app = app
        self.profiler = profile.Profile()
        self.log_filename = log_filename
        self.first_request = discard_first_request
        self.lock = threading.Lock()
        self.flush_at_shutdown = flush_at_shutdown
        self.path = path
        self.template = os.path.join(_HERE, 'profiler.html')
        self.meldroot = meld3.parse_xml(self.template)

    def index(self, environ):
        root = self.meldroot.clone()
        querydata = parse_formvars(environ)
        full_dirs = int(querydata.get('full_dirs', 0))
        sort = querydata.get('sort', 'time')
        clear = querydata.get('clear', None)
        limit = int(querydata.get('limit', 100))
        mode = querydata.get('mode', 'stats')
        output = StringIO.StringIO()
        url = construct_url(environ)
        log_exists = os.path.exists(self.log_filename)

        if clear and log_exists:
            os.remove(self.log_filename)
            log_exists = False

        if log_exists:
            stats = pstats.Stats(self.log_filename)
            if not full_dirs:
                stats.strip_dirs()
            stats.sort_stats(sort)
            if hasattr(stats, 'stream'):
                # python 2.5
                stats.stream = output
            try:
                orig_stdout = sys.stdout # python 2.4
                sys.stdout = output
                print_fn = getattr(stats, 'print_%s' % mode)
                print_fn(limit)
            finally:
                sys.stdout = orig_stdout

        data = output.getvalue()

        form = root.findmeld('form')
        form.attributes(action=url)
        if data:
            description = root.findmeld('description')
            description.content("""
            Profiling information is generated using the standard Python 
            profiler. To learn how to interpret the profiler statistics, 
            see the <a
            href="http://www.python.org/doc/current/lib/module-profile.html">
            Python profiler documentation</a>.""", structure=True)
            formelements = root.findmeld('formelements')

            if full_dirs:
                formelements.fillmeldhtmlform(sort=sort,
                                              limit=str(limit),
                                              full_dirs=True,
                                              mode=mode)
            else:
                formelements.fillmeldhtmlform(sort=sort,
                                              limit=str(limit),
                                              mode=mode)

            profiledata = root.findmeld('profiledata')
            profiledata.content(data)
        else:
            formelements = root.findmeld('formelements')
            formelements.content('')
        return root.write_xhtmlstring()

    def __del__(self):
        if self.flush_at_shutdown and os.path.exists(self.log_filename):
            os.remove(self.log_filename)

    def __call__(self, environ, start_response):
        catch_response = []
        body = []

        path_info = environ.get('PATH_INFO')

        if path_info == self.path:
            # we're being asked to render the profile view
            body = self.index(environ)
            start_response('200 OK', [('content-type', 'text/html'),
                                      ('content-length', str(len(body)))])
            return [body]

        def replace_start_response(status, headers, exc_info=None):
            catch_response.extend([status, headers])
            start_response(status, headers, exc_info)
            return body.append

        def run_app():
            app_iter = self.app(environ, replace_start_response)
            try:
                body.extend(app_iter)
            finally:
                if hasattr(app_iter, 'close'):
                    app_iter.close()

        self.lock.acquire()
        try:
            self.profiler.runctx('run_app()', globals(), locals())

            if self.first_request: # discard to avoid timing warm-up
                self.profiler = profile.Profile()
                self.first_request = False
            else:
                self.profiler.dump_stats(self.log_filename)

            body = ''.join(body)
            return [body]
        finally:
            self.lock.release()

def make_profile_middleware(app,
                            global_conf,
                            log_filename=DEFAULT_PROFILE_LOG,
                            discard_first_request=True,
                            path='/__profile__',
                            flush_at_shutdown='true',
                           ):
    """Wrap the application in a component that will profile each
    request, appending data from each request to an aggregate
    file.

    Nota bene
    ---------

    o This middleware serializes all requests (i.e., removing concurrency).

    o The Python profiler is seriously SLOW (maybe an order of magnitude!).

    o Ergo, NEVER USE THIS MIDDLEWARE IN PRODUCTION.
    """
    if flush_at_shutdown.lower().startswith('t'):
        flush_at_shutdown = 1
    else:
        flush_at_shutdown = 0
        
    return AccumulatingProfileMiddleware(
                app,
                log_filename=log_filename,
                discard_first_request=discard_first_request,
                flush_at_shutdown=int(flush_at_shutdown),
                path=path,
               )
