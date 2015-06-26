import httplib
import mimetypes
import urlparse
import uuid

def post_multipart(url, fields, files):
    parts = urlparse.urlparse(url)
    scheme = parts[0]
    host = parts[1]
    selector = parts[2]
    content_type, body = encode_multipart_formdata(fields, files)
    if scheme == 'http':
        h = httplib.HTTP(host)
    elif scheme == 'https':
        h = httplib.HTTPS(host)
    else:
        raise ValueError('unknown scheme: ' + scheme)
    h.putrequest('POST', selector)
    h.putheader('content-type', content_type)
    h.putheader('content-length', str(len(body)))
    h.endheaders()
    h.send(body)
    errcode, errmsg, headers = h.getreply()
    return h.file.read()


def encode_multipart_formdata(fields, files):
    def get_content_type(filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    LIMIT = '----------' + uuid.uuid4().hex
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + LIMIT)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + LIMIT)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + LIMIT + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % LIMIT
    return content_type, body
