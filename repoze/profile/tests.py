import unittest

class TestProfileMiddleware(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from repoze.profile.profiler import AccumulatingProfileMiddleware
        return AccumulatingProfileMiddleware(*arg, **kw)
        

    def _makeEnviron(self, kw):
        environ = {}
        environ['wsgi.url_scheme'] = 'http'
        environ['CONTENT_TYPE'] = 'text/html'
        environ['QUERY_STRING'] = ''
        environ['SERVER_NAME'] = 'localhost'
        environ['SERVER_PORT'] = '80'
        environ['REQUEST_METHOD'] = 'POST'
        environ.update(kw)
        return environ

    def test_index_post(self):
        from StringIO import StringIO
        fields = [
            ('full_dirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        environ = self._makeEnviron(
            {'wsgi.input':StringIO(body),
             'CONTENT_TYPE':content_type,
             'CONTENT_LENGTH':len(body),
             'REQUEST_METHOD':'POST',
             })
        middleware = self._makeOne(None)
        html = middleware.index(environ)
        self.failIf(html.find('There is not yet any profiling data') == -1)

    def test_index_get(self):
        environ = self._makeEnviron({
             'REQUEST_METHOD':'GET',
             'wsgi.input':'',
             })
        middleware = self._makeOne(None)
        html = middleware.index(environ)
        self.failIf(html.find('There is not yet any profiling data') == -1)

    def test_index_clear(self):
        from StringIO import StringIO
        fields = [
            ('full_dirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ('clear', 'submit'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        environ = self._makeEnviron(
            {'wsgi.input':StringIO(body),
            'CONTENT_TYPE':content_type,
             'CONTENT_LENGTH':len(body),
             'REQUEST_METHOD':'POST',
             })

        middleware = self._makeOne(None)
        import tempfile
        f = tempfile.mktemp()
        open(f, 'w').write('x')
        middleware.log_filename = f
        html = middleware.index(environ)
        self.failIf(html.find('There is not yet any profiling data') == -1)
        import os
        self.failIf(os.path.exists(f))

    def test_call_withpath(self):
        from StringIO import StringIO
        fields = [
            ('full_dirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        environ = self._makeEnviron(
            {'wsgi.input':StringIO(body),
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
        html = iterable[0]
        self.failIf(html.find('There is not yet any profiling data') == -1)
        self.assertEqual(statuses[0], '200 OK')
        self.assertEqual(headerses[0][0], ('content-type', 'text/html'))
        self.assertEqual(headerses[0][1], ('content-length', str(len(html))))

    def test_call_discard_first_request(self):
        from StringIO import StringIO
        fields = [
            ('full_dirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        environ = self._makeEnviron(
            {'wsgi.input':StringIO(body),
            'CONTENT_TYPE':content_type,
             'CONTENT_LENGTH':len(body),
             })
        import tempfile
        log_filename = tempfile.mktemp()
        middleware = self._makeOne(app, log_filename=log_filename)
        self.failUnless(middleware.first_request)
        statuses = []
        headerses = []
        def start_response(status, headers, exc_info=None):
            statuses.append(status)
            headerses.append(headers)
        iterable = middleware(environ, start_response)
        self.assertEqual(statuses[0], '200 OK')
        self.failIf(middleware.first_request)
        import os
        self.failIf(os.path.exists(log_filename))
        another = middleware(environ, start_response)
        self.failUnless(os.path.exists(log_filename))
        os.remove(log_filename)

    def test_call_keep_first_request(self):
        from StringIO import StringIO
        fields = [
            ('full_dirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        environ = self._makeEnviron(
            {'wsgi.input':StringIO(body),
            'CONTENT_TYPE':content_type,
             'CONTENT_LENGTH':len(body),
             })
        import tempfile
        log_filename = tempfile.mktemp()
        middleware = self._makeOne(app, discard_first_request=False,
                                   log_filename=log_filename)
        self.failIf(middleware.first_request)
        statuses = []
        headerses = []
        def start_response(status, headers, exc_info=None):
            statuses.append(status)
            headerses.append(headers)
        iterable = middleware(environ, start_response)
        self.assertEqual(statuses[0], '200 OK')
        self.failIf(middleware.first_request)
        import os
        self.failUnless(os.path.exists(log_filename))
        os.remove(log_filename)

    def test_flush_at_shutdown(self):
        from StringIO import StringIO
        fields = [
            ('full_dirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        environ = self._makeEnviron(
            {'wsgi.input':StringIO(body),
            'CONTENT_TYPE':content_type,
             'CONTENT_LENGTH':len(body),
             })
        import tempfile
        log_filename = tempfile.mktemp()
        middleware = self._makeOne(app, flush_at_shutdown=True,
                                   log_filename=log_filename)
        f = open(log_filename, 'w')
        f.write('')
        del middleware
        import os
        self.failIf(os.path.exists(log_filename))
        
    def test_keep_at_shutdown(self):
        from StringIO import StringIO
        fields = [
            ('full_dirs', '1'),
            ('sort', 'cumulative'),
            ('limit', '500'),
            ('mode', 'callers'),
            ]
        content_type, body = encode_multipart_formdata(fields)
        environ = self._makeEnviron(
            {'wsgi.input':StringIO(body),
            'CONTENT_TYPE':content_type,
             'CONTENT_LENGTH':len(body),
             })
        import tempfile
        log_filename = tempfile.mktemp()
        middleware = self._makeOne(app, flush_at_shutdown=False,
                                   log_filename=log_filename)
        f = open(log_filename, 'w')
        f.write('')
        del middleware
        import os
        self.failUnless(os.path.exists(log_filename))
        os.remove(log_filename)
        
def app(environ, start_response, exc_info=None):
    start_response('200 OK', (), exc_info)
    return ['']

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
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

