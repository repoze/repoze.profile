""" Middleware that profiles all requests, accumulating timings.

o Insprired by the paste.debug.profile version, which profiles single requests.
"""

import cgi
import os
import pstats
import string
import sys
import threading

from repoze.profile.compat import bytes_
from repoze.profile.compat import parse_qs
from repoze.profile.compat import profile
from repoze.profile.compat import StringIO
from repoze.profile.compat import url_quote

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3

HAS_PP2CT = True
try: # pragma: no cover
    import pyprof2calltree # pragma: no cover
except ImportError: # pragma: no cover
    HAS_PP2CT = False # pragma: no cover

_HERE = os.path.abspath(os.path.dirname(__file__))

DEFAULT_PROFILE_LOG = 'wsgi.prof'

PROFILE_EXEC_EAGER = """
# unwind the iterator; it may call start_response, do lots of work, etc
app_iter = self.app(environ, start_response)
app_iter_ = list(app_iter)
if hasattr(app_iter, 'close'):
    app_iter.close()
"""

PROFILE_EXEC_LAZY = """
# don't unwind the iterator (dont consume resources)
app_iter_ = self.app(environ, start_response)
"""

class ProfileMiddleware(object):
    Stats = pstats.Stats

    def __init__(self, app,
                 global_conf=None,
                 log_filename=DEFAULT_PROFILE_LOG,
                 cachegrind_filename=None,
                 discard_first_request=True,
                 flush_at_shutdown = True,
                 path='/__profile__',
                 unwind=False,
                ):
        self.exists = os.path.exists # for __del__
        self.remove = os.remove # for __del__
        self.app = app
        self.profiler = profile.Profile()
        self.log_filename = log_filename
        self.cachegrind_filename = cachegrind_filename
        self.first_request = discard_first_request
        self.lock = threading.Lock()
        self.flush_at_shutdown = flush_at_shutdown
        self.path = path
        self.unwind = unwind

    def index(self, request, output=None): # output=None D/I for testing
        querydata = request.get_params()
        fulldirs = int(querydata.get('fulldirs', 0))
        sort = querydata.get('sort', 'time')
        clear = querydata.get('clear', None)
        filename = querydata.get('filename', '').strip()
        limit = int(querydata.get('limit', 100))
        mode = querydata.get('mode', 'stats')
        if output is None:
            output = StringIO()
        url = request.get_url()
        log_exists = os.path.exists(self.log_filename)

        if clear and log_exists:
            os.remove(self.log_filename)
            self.profiler = profile.Profile()
            log_exists = False

        if log_exists:
            stats = self.Stats(self.log_filename) # D/I
            if not fulldirs:
                stats.strip_dirs()
            stats.sort_stats(sort)
            if hasattr(stats, 'stream'):
                # python 2.5
                stats.stream = output
            try:
                orig_stdout = sys.stdout # python 2.4
                sys.stdout = output
                print_fn = getattr(stats, 'print_%s' % mode)
                if filename:
                    print_fn(filename, limit)
                else:
                    print_fn(limit)
            finally:
                sys.stdout = orig_stdout

        profiledata = output.getvalue()
        description = empty_description
        action = url
        formelements = ''
        filename = filename or ''
        if profiledata:
            description = """
            Profiling information is generated using the standard Python 
            profiler. To learn how to interpret the profiler statistics, 
            see the <a
            href="http://www.python.org/doc/current/lib/module-profile.html">
            Python profiler documentation</a>."""
            sort_repl = '<option value="%s">' % sort
            sort_selected = '<option value="%s" selected>' % sort
            sort = sort_tmpl.replace(sort_repl, sort_selected)
            limit_repl = '<option value="%s">' % limit
            limit_selected = '<option value="%s" selected>' % limit
            limit = limit_tmpl.replace(limit_repl, limit_selected)
            mode_repl = '<option value="%s">' % mode
            mode_selected = '<option value="%s" selected>' % mode
            mode = mode_tmpl.replace(mode_repl, mode_selected)
            fulldirs_checked = '/>'
            fulldirs_repl = '/>'
            if fulldirs:
                fulldirs_checked = 'checked/>'
            fulldirs = fulldirs_tmpl.replace(fulldirs_repl, fulldirs_checked)
            filename_repl = 'value=""'
            filename_selected = 'value="%s"' % filename
            filename = filename_tmpl.replace(filename_repl, filename_selected)
            fulldirs_repl
            formelements = string.Template(formelements_tmpl)
            formelements = formelements.substitute(
                {'description':description,
                 'action':action,
                 'sort':sort,
                 'limit':limit,
                 'fulldirs':fulldirs,
                 'mode':mode,
                 'filename':filename,
                 }
                )
        index = string.Template(index_tmpl)
        index = index.substitute(
            {'formelements':formelements,
             'action':action,
             'description':description,
             'profiledata':profiledata, 
             }
            )
        return index

    def __del__(self):
        if self.flush_at_shutdown and self.exists(self.log_filename):
            self.remove(self.log_filename)

    def __call__(self, environ, start_response):
        request = MiniRequest(environ)

        if request.path_info == self.path:
            # we're being asked to render the profile view
            self.lock.acquire()
            try:
                text = self.index(request)
            finally:
                self.lock.release()
            start_response('200 OK', [
                ('content-type', 'text/html; charset="UTF-8"'),
                ('content-length', str(len(text)))])
            return [bytes_(text)]

        self.lock.acquire()
        try:
            _locals = locals()
            code = self.unwind and PROFILE_EXEC_EAGER or PROFILE_EXEC_LAZY
            self.profiler.runctx(code, globals(), _locals)

            if self.first_request: # discard to avoid timing warm-up
                self.profiler = profile.Profile()
                self.first_request = False
            else:
                self.profiler.dump_stats(self.log_filename)
                if HAS_PP2CT and self.cachegrind_filename is not None:
                    stats = pstats.Stats(self.profiler)
                    conv = pyprof2calltree.CalltreeConverter(stats)
                    with open(self.cachegrind_filename, 'w') as grind:
                        conv.output(grind)
            app_iter = _locals['app_iter_']
            return app_iter
        finally:
            self.lock.release()

def boolean(s):
    if s == True:
        return True # pragma: no cover
    s = s.lower()
    if ( s.startswith('t') or s.startswith('y') or
         s.startswith('1') or s.startswith('on') ):
        return True
    return False

empty_description = """
        There is not yet any profiling data to report.
        <input type="submit" name="refresh" value="Refresh"/>
"""

sort_tmpl = """
              <select name="sort">
                <option value="time">time</option>
                <option value="cumulative">cumulative</option>
                <option value="calls">calls</option>
                <option value="pcalls">pcalls</option>
                <option value="name">name</option>
                <option value="file">file</option>
                <option value="module">module</option>
                <option value="line">line</option>
                <option value="nfl">nfl</option>
                <option value="stdname">stdname</option>
              </select>
"""

limit_tmpl = """
              <select name="limit">
                <option value="100">100</option>
                <option value="200">200</option>
                <option value="300">300</option>
                <option value="400">400</option>
                <option value="500">500</option>
              </select>
"""

fulldirs_tmpl = """
              <input type="checkbox" name="fulldirs" value="1"/>
"""

mode_tmpl = """
              <select name="mode">
                <option value="stats">stats</option>
                <option value="callees">callees</option>
                <option value="callers">callers</option>
              </select>
"""

filename_tmpl = """
              <input type="text" name="filename"
              value="" placeholder="filename part" />
"""

formelements_tmpl = """
      <div>
        <table>
          <tr>
            <td>
              <strong>Sort</strong>:
               ${sort}
            </td>
            <td>
              <strong>Limit</strong>:
               ${limit}
            </td>
            <td>
              <strong>Full Dirs</strong>:
              ${fulldirs}
            </td>
            <td>
              <strong>Mode</strong>:
              ${mode}
            </td>
            <td>
              <strong>Filter</strong>:
              ${filename}
            </td>
            <td>
              <input type="submit" name="submit" value="Update"/>
            </td>
            <td>
              <input type="submit" name="clear" value="Clear"/>
            </td>
          </tr>
        </table>
      </div>
"""

index_tmpl = """
<html>
  <head>
    <title>repoze.profile results</title>
  </head>
  <body>
    
    <form action="${action}" method="POST">

      <div class="form-text">
        ${description}
      </div>

      ${formelements}
    
    </form>
    <pre>
       ${profiledata}
    </pre>
  </body>
</html>
"""

PATH_SAFE = '/:@&+$,'

class MiniRequest(object):
    def __init__(self, environ):
        self.environ = environ
        self.path_info = environ['PATH_INFO']

    def get_url(self):
        e = self.environ
        url = e['wsgi.url_scheme'] + '://'
        if e.get('HTTP_HOST'):
            host = e['HTTP_HOST']
            if ':' in host:
                host, port = host.split(':', 1)
            else:
                port = None
        else:
            host = e['SERVER_NAME']
            port = e['SERVER_PORT']
        if self.environ['wsgi.url_scheme'] == 'https':
            if port == '443':
                port = None
        elif self.environ['wsgi.url_scheme'] == 'http':
            if port == '80':
                port = None
        url += host
        if port:
            url += ':%s' % port
        url += url_quote(
            self.environ.get('SCRIPT_NAME', ''), PATH_SAFE)
        url += url_quote(
            self.environ.get('PATH_INFO', ''), PATH_SAFE)

        if self.environ.get('QUERY_STRING'):
            url += '?' + self.environ['QUERY_STRING']
        return url

    def get_params(self):
        params = {}
        fs = cgi.FieldStorage(
            fp=self.environ['wsgi.input'],
            environ=self.environ,
            keep_blank_values=True)
        for field in fs.list or ():
            name = field.name
            value = field.value
            params[name] = value
        get_params = parse_qs(self.environ.get('QUERY_STRING', ''),
                              keep_blank_values=True,
                              strict_parsing=False)
        params.update(get_params)
        return params

AccumulatingProfileMiddleware = ProfileMiddleware # bw compat

def make_profile_middleware(app,
                            global_conf,
                            log_filename=DEFAULT_PROFILE_LOG,
                            cachegrind_filename=None,
                            discard_first_request='true',
                            path='/__profile__',
                            flush_at_shutdown='true',
                            unwind='false',
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
    flush_at_shutdown = boolean(flush_at_shutdown)
    discard_first_request = boolean(discard_first_request)
    unwind = boolean(unwind)
        
    return ProfileMiddleware(
        app,
        log_filename=log_filename,
        cachegrind_filename=cachegrind_filename,
        discard_first_request=discard_first_request,
        flush_at_shutdown=flush_at_shutdown,
        path=path,
        unwind=unwind,
        )
