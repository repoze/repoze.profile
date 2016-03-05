import unittest
import sys

from repoze.profile.compat import BytesIO
from repoze.profile.compat import bytes_
from repoze.profile.compat import StringIO
from repoze.profile.compat import text_

class TestProfileMiddleware(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from repoze.profile.profiler import ProfileMiddleware
        return ProfileMiddleware(*arg, **kw)

    def _makeRequest(self, extra_environ):
        environ = self._makeEnviron(extra_environ)
        from repoze.profile.profiler import MiniRequest
        return MiniRequest(environ)

    def _makeEnviron(self, kw):
        environ = {}
        environ['wsgi.url_scheme'] = 'http'
        environ['CONTENT_TYPE'] = 'text/html'
        environ['QUERY_STRING'] = ''
        environ['SERVER_NAME'] = 'localhost'
        environ['SERVER_PORT'] = '80'
        environ['REQUEST_METHOD'] = 'POST'
        environ['PATH_INFO'] = '/'
        environ.update(kw)
        return environ

    def test_index_post(self):
        fields = [
            ('fulldirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        environ = {
            'wsgi.input':BytesIO(body),
            'CONTENT_TYPE':content_type,
            'CONTENT_LENGTH':len(body),
            'REQUEST_METHOD':'POST',
            }
        middleware = self._makeOne(None)
        request = self._makeRequest(environ)
        html = middleware.index(request)
        self.assertFalse(html.find('There is not yet any profiling data') == -1)

    def test_index_get(self):
        environ = {
             'REQUEST_METHOD':'GET',
             'wsgi.input':'',
             }
        request = self._makeRequest(environ)
        middleware = self._makeOne(None)
        html = middleware.index(request)
        self.assertFalse(html.find('There is not yet any profiling data') == -1)

    def test_index_clear(self):
        import os
        import tempfile
        fields = [
            ('fulldirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ('clear', 'submit'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        environ = {
            'wsgi.input':BytesIO(body),
            'CONTENT_TYPE':content_type,
            'CONTENT_LENGTH':len(body),
            'REQUEST_METHOD':'POST',
             }

        middleware = self._makeOne(None)
        f = tempfile.mktemp()
        f = open(f, 'w')
        f.write('x')
        f.close()
        middleware.log_filename = f.name
        request = self._makeRequest(environ)
        html = middleware.index(request)
        self.assertFalse(html.find('There is not yet any profiling data') == -1)
        self.assertFalse(os.path.exists(f.name))

    def test_index_get_withdata(self):
        request = self._makeRequest({
             'REQUEST_METHOD':'GET',
             'wsgi.input':'',
             })
        middleware = self._makeOne(None)
        output = BytesIO(bytes_('hello!'))
        html = middleware.index(request, output)
        self.assertTrue('Profiling information is generated' in html)

    def test_index_post_withdata_fulldirs(self):
        fields = [
            ('fulldirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        request = self._makeRequest(
            {'wsgi.input':BytesIO(body),
             'CONTENT_TYPE':content_type,
             'CONTENT_LENGTH':len(body),
             })

        middleware = self._makeOne(None)
        request.environ['PATH_INFO'] = middleware.path
        output = BytesIO(bytes_('hello!'))
        html = middleware.index(request, output)
        self.assertTrue('Profiling information is generated' in html)

    def test_index_withstats(self):
        import os
        import tempfile
        fields = [
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'stats'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        request = self._makeRequest(
            {'wsgi.input':BytesIO(body),
            'CONTENT_TYPE':content_type,
             'CONTENT_LENGTH':len(body),
             })

        middleware = self._makeOne(None)
        stats = DummyStats()
        middleware.Stats = stats
        f = tempfile.mktemp()
        f = open(f, 'w')
        f.write('x')
        f.close()
        middleware.log_filename = f.name
        request.environ['PATH_INFO'] = middleware.path
        middleware.index(request)
        self.assertEqual(stats.stripped, True)
        self.assertNotEqual(stats.stream, True)
        self.assertEqual(stats.printlimit, 500)
        self.assertEqual(stats.sortspec, 'cumulative')
        os.remove(f.name)

    def test_index_withstats_and_filename(self):
        import os
        import tempfile
        fields = [
            ('sort', 'stats'),
            ('limit', '500'),
            ('mode', 'fake'),
            ('filename', 'fred'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        request = self._makeRequest(
            {'wsgi.input':BytesIO(body),
            'CONTENT_TYPE':content_type,
             'CONTENT_LENGTH':len(body),
             })

        middleware = self._makeOne(None)
        stats = DummyStats()
        middleware.Stats = stats
        f = tempfile.mktemp()
        f = open(f, 'w')
        f.write('x')
        f.close()
        middleware.log_filename = f.name
        request.environ['PATH_INFO'] = middleware.path
        middleware.index(request)
        self.assertEqual(stats.stripped, True)
        self.assertNotEqual(stats.stream, True)
        self.assertEqual(stats.printlimit, 500)
        self.assertEqual(stats.filename, 'fred')
        self.assertEqual(stats.sortspec, 'stats')
        os.remove(f.name)

    def test_app_iter_is_not_closed(self):
        middleware = self._makeOne(app)
        def start_response(status, headers, exc_info=None):
            pass
        environ = self._makeEnviron({})
        iterable = middleware(environ, start_response)
        self.assertEqual(iterable.closed, False)

    def test_app_iter_as_generator_is_consumed_when_unwind_true(self):
        _consumed = []
        def start_response(status, headers, exc_info=None):
            pass
        def _app(status, headers, exc_info=None):
            start_response('200 OK', (), exc_info)
            yield 'one'
            _consumed.append('OK')
        middleware = self._makeOne(_app, unwind=True)
        environ = self._makeEnviron({})
        middleware(environ, start_response)
        self.assertTrue(_consumed)

    def test_app_iter_as_generator_is_not_consumed_when_unwind_false(self):
        _consumed = []
        def start_response(status, headers, exc_info=None): # pragma: no cover
            pass
        def _app(status, headers, exc_info=None): # pragma: no cover
            start_response('200 OK', (), exc_info)
            yield 'one'
            _consumed.append('OK')
        middleware = self._makeOne(_app, unwind=False)
        environ = self._makeEnviron({})
        middleware(environ, start_response)
        self.assertFalse(_consumed)

    def test_call_withpath(self):
        fields = [
            ('fulldirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        environ = self._makeEnviron(
            {'wsgi.input':BytesIO(body),
            'CONTENT_TYPE':content_type,
             'CONTENT_LENGTH':len(body),
             })

        middleware = self._makeOne(None)
        environ['PATH_INFO'] = middleware.path
        statuses = []
        headerses = []
        def start_response(status, headers):
            statuses.append(status)
            headerses.append(headers)
        iterable = middleware(environ, start_response)
        html = text_(iterable[0])
        self.assertFalse(html.find('There is not yet any profiling data') == -1)
        self.assertEqual(statuses[0], '200 OK')
        self.assertEqual(headerses[0][0],
                         ('content-type', 'text/html; charset="UTF-8"'))
        self.assertEqual(headerses[0][1], ('content-length', str(len(html))))

    def test_call_discard_first_request(self):
        import os
        import tempfile
        fields = [
            ('fulldirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        environ = self._makeEnviron(
            {'wsgi.input':BytesIO(body),
            'CONTENT_TYPE':content_type,
             'CONTENT_LENGTH':len(body),
             })
        log_filename = tempfile.mktemp()
        middleware = self._makeOne(app, log_filename=log_filename)
        self.assertTrue(middleware.first_request)
        statuses = []
        headerses = []
        def start_response(status, headers, exc_info=None):
            statuses.append(status)
            headerses.append(headers)
        middleware(environ, start_response)
        self.assertEqual(statuses[0], '200 OK')
        self.assertFalse(middleware.first_request)
        self.assertFalse(os.path.exists(log_filename))
        middleware(environ, start_response)
        self.assertTrue(os.path.exists(log_filename))
        os.remove(log_filename)

    def test_call_keep_first_request(self):
        import os
        import tempfile
        fields = [
            ('fulldirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        environ = self._makeEnviron(
            {'wsgi.input':BytesIO(body),
            'CONTENT_TYPE':content_type,
             'CONTENT_LENGTH':len(body),
             })
        log_filename = tempfile.mktemp()
        middleware = self._makeOne(app, discard_first_request=False,
                                   log_filename=log_filename)
        self.assertFalse(middleware.first_request)
        statuses = []
        headerses = []
        def start_response(status, headers, exc_info=None):
            statuses.append(status)
            headerses.append(headers)
        middleware(environ, start_response)
        self.assertEqual(statuses[0], '200 OK')
        self.assertFalse(middleware.first_request)
        self.assertTrue(os.path.exists(log_filename))
        os.remove(log_filename)

    def test_call_with_cachegrind(self):
        from repoze.profile.profiler import HAS_PP2CT
        if not HAS_PP2CT: # pragma: no cover
            return
        import os
        import tempfile
        fields = [
            ('fulldirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        environ = self._makeEnviron(
            {'wsgi.input':BytesIO(body),
            'CONTENT_TYPE':content_type,
             'CONTENT_LENGTH':len(body),
             })
        log_filename = tempfile.mktemp()
        cachegrind_filename = tempfile.mktemp()
        middleware = self._makeOne(app, discard_first_request=False,
                                   log_filename=log_filename,
                                   cachegrind_filename=cachegrind_filename)
        self.assertFalse(middleware.first_request)
        statuses = []
        headerses = []
        def start_response(status, headers, exc_info=None):
            statuses.append(status)
            headerses.append(headers)
        middleware(environ, start_response)
        self.assertEqual(statuses[0], '200 OK')
        self.assertFalse(middleware.first_request)
        self.assertTrue(os.path.exists(log_filename))
        os.remove(log_filename)
        self.assertTrue(os.path.exists(cachegrind_filename))
        os.remove(cachegrind_filename)

    def test_flush_at_shutdown(self):
        import os
        import tempfile
        fields = [
            ('fulldirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        log_filename = tempfile.mktemp()
        middleware = self._makeOne(app, flush_at_shutdown=True,
                                   log_filename=log_filename)
        f = open(log_filename, 'w')
        f.write('')
        f.close()
        # We can't do the following:
        # del middleware
        # because it won't get called right away under PyPy.
        middleware.__del__()
        self.assertFalse(os.path.exists(log_filename))
        
    def test_keep_at_shutdown(self):
        import os
        import tempfile
        fields = [
            ('fulldirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        log_filename = tempfile.mktemp()
        middleware = self._makeOne(app, flush_at_shutdown=False,
                                   log_filename=log_filename)
        f = open(log_filename, 'w')
        f.write('')
        f.close()
        del middleware
        self.assertTrue(os.path.exists(log_filename))
        os.remove(log_filename)

class TestMakeProfileMiddleware(unittest.TestCase):
    def _callFUT(self, *arg, **kw):
        from repoze.profile.profiler import make_profile_middleware
        return make_profile_middleware(*arg, **kw)

    def test_it(self):
        mw = self._callFUT(app,
                           {},
                           log_filename='/tmp/log',
                           cachegrind_filename='/tmp/cachegrind',
                           discard_first_request='true',
                           flush_at_shutdown='false',
                           path='/__profile__')
        self.assertEqual(mw.app, app)
        self.assertEqual(mw.log_filename, '/tmp/log')
        self.assertEqual(mw.cachegrind_filename, '/tmp/cachegrind')
        self.assertEqual(mw.first_request, True)
        self.assertEqual(mw.flush_at_shutdown, False)
        self.assertEqual(mw.path, '/__profile__')

class TestMiniRequest(unittest.TestCase):
    def _makeOne(self, environ):
        from repoze.profile.profiler import MiniRequest
        return MiniRequest(environ)
    
    def test_get_url_no_qs(self):
        environ = {'wsgi.url_scheme': 'http',
                   'SERVER_NAME': 'example.com',
                   'SERVER_PORT': '80',
                   'SCRIPT_NAME': '/script',
                   'PATH_INFO': '/path/info',
                  }
        req = self._makeOne(environ)
        self.assertEqual(req.get_url(), 'http://example.com/script/path/info')

    def test_get_url_w_qs(self):
        environ = {'wsgi.url_scheme': 'http',
                   'SERVER_NAME': 'example.com',
                   'SERVER_PORT': '80',
                   'SCRIPT_NAME': '/script',
                   'PATH_INFO': '/path/info',
                   'QUERY_STRING': 'foo=bar&baz=bam'
                  }
        req = self._makeOne(environ)
        self.assertEqual(req.get_url(),
                         'http://example.com/script/path/info?foo=bar&baz=bam')

    def test_get_url_w_httphost_withport(self):
        environ = {'wsgi.url_scheme': 'http',
                   'SERVER_NAME': 'example.com',
                   'SERVER_PORT': '80',
                   'SCRIPT_NAME': '/script',
                   'PATH_INFO': '/path/info',
                   'HTTP_HOST': 'localhost:8080'
                  }
        req = self._makeOne(environ)
        self.assertEqual(req.get_url(),
                         'http://localhost:8080/script/path/info')
    
    def test_get_url_w_httphost_noport(self):
        environ = {'wsgi.url_scheme': 'http',
                   'SERVER_NAME': 'example.com',
                   'SERVER_PORT': '80',
                   'SCRIPT_NAME': '/script',
                   'PATH_INFO': '/path/info',
                   'HTTP_HOST': 'localhost'
                  }
        req = self._makeOne(environ)
        self.assertEqual(req.get_url(),
                         'http://localhost/script/path/info')

    def test_get_url_https(self):
        environ = {'wsgi.url_scheme': 'https',
                   'SERVER_NAME': 'example.com',
                   'SERVER_PORT': '443',
                   'SCRIPT_NAME': '/script',
                   'PATH_INFO': '/path/info',
                  }
        req = self._makeOne(environ)
        self.assertEqual(req.get_url(),
                         'https://example.com/script/path/info')
    
    def test_get_url_https_withport(self):
        environ = {'wsgi.url_scheme': 'https',
                   'SERVER_NAME': 'example.com',
                   'SERVER_PORT': '553',
                   'SCRIPT_NAME': '/script',
                   'PATH_INFO': '/path/info',
                  }
        req = self._makeOne(environ)
        self.assertEqual(req.get_url(),
                         'https://example.com:553/script/path/info')

class TestProfileDecorator(unittest.TestCase):

    def test_w_lines_eq_zero(self):
        from repoze.profile.decorator import profile
        @profile('test function', lines=0)
        def do_nothing():
            pass
        out = StringIO()
        old_out = sys.stdout
        sys.stdout = out
        do_nothing()
        assert 'test function' in out.getvalue()
        assert 'Ordered by: cumulative time' in out.getvalue()
        sys.stdout = old_out

    def test_it(self):
        from repoze.profile.decorator import profile
        @profile('test function')
        def do_nothing():
            pass
        out = StringIO()
        old_out = sys.stdout
        sys.stdout = out
        do_nothing()
        assert 'test function' in out.getvalue()
        assert 'Ordered by: cumulative time' in out.getvalue()
        sys.stdout = old_out
        
    def test_sort_columns(self):
        from repoze.profile.decorator import profile
        @profile('test sort columns', sort_columns=('time',))
        def do_nothing():
            pass
        out = StringIO()
        old_out = sys.stdout
        sys.stdout = out
        do_nothing()
        assert 'test sort columns' in out.getvalue()
        assert 'Ordered by: internal time' in out.getvalue()
        sys.stdout = old_out
        
    def test_limit_lines(self):
        from repoze.profile.decorator import profile
        @profile('test limit lines', lines=1)
        def do_nothing():
            pass
        out = StringIO()
        old_out = sys.stdout
        sys.stdout = out
        do_nothing()
        assert 'test limit lines' in out.getvalue()
        assert '1 due to restriction' in out.getvalue()
        sys.stdout = old_out
        
def app(environ, start_response, exc_info=None):
    start_response('200 OK', (), exc_info)
    return closeable([''])

class closeable(list):
    closed = False
    def close(self): self.closed = True

def encode_multipart_formdata(fields):
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = bytes_(CRLF.join(L))
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

class DummyStats:
    stripped = False
    stream = True
    log_filename = None
    def __call__(self, log_filename):
        self.log_filename = log_filename
        return self

    def strip_dirs(self):
        self.stripped = True

    def print_stats(self, limit):
        self.printlimit = limit

    def print_fake(self, filename, limit):
        self.printlimit = limit
        self.filename = filename

    def sort_stats(self, sort):
        self.sortspec = sort
        

