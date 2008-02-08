""" Middleware that profiles all requests, accumulating timings.

o Insprired by the paste.debug.profile version, which profiles single requests.
"""
import profile
import threading

DEFAULT_PROFILE_LOG = 'wsgi.prof'

class AccumulatingProfileMiddleware(object):

    def __init__(self, app,
                 global_conf=None,
                 log_filename=DEFAULT_PROFILE_LOG,
                 discard_first_request=True,
                ):
        self.app = app
        self.profiler = profile.Profile()
        self.log_filename = log_filename
        self.first_request = discard_first_request
        self.lock = threading.Lock()

    def __call__(self, environ, start_response):
        catch_response = []
        body = []

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
    return AccumulatingProfileMiddleware(
                app,
                log_filename=log_filename,
                discard_first_request=discard_first_request
               )
