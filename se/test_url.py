# Copyright 2022-2023 Laurent Defert
#
#  This file is part of SOSSE.
#
# SOSSE is free software: you can redistribute it and/or modify it under the terms of the GNU Affero
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# SOSSE is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along with SOSSE.
# If not, see <https://www.gnu.org/licenses/>.

from django.test import TestCase

from .url import absolutize_url, urlparse, url_beautify, norm_url_path
from .utils import reverse_no_escape


class UrlTest(TestCase):
    def test_url_parse_no_scheme(self):
        url = urlparse('://127.0.0.1/')
        self.assertEqual(url.scheme, '')
        self.assertEqual(url.netloc, '127.0.0.1')
        self.assertEqual(url.path, '/')

        url = urlparse('//127.0.0.1/')
        self.assertEqual(url.scheme, '')
        self.assertEqual(url.netloc, '127.0.0.1')
        self.assertEqual(url.path, '/')

    def test_url_parse_no_slash(self):
        url = urlparse('http:netloc')
        self.assertEqual(url.scheme, 'http')
        self.assertEqual(url.netloc, 'netloc')
        self.assertEqual(url.path, '/')

    def test_url_parse_params(self):
        url = urlparse('a;p')
        self.assertEqual(url.scheme, '')
        self.assertEqual(url.netloc, '')
        self.assertEqual(url.path, 'a')
        self.assertEqual(url.params, 'p')

        url = urlparse(';p')
        self.assertEqual(url.scheme, '')
        self.assertEqual(url.netloc, '')
        self.assertEqual(url.path, '')
        self.assertEqual(url.params, 'p')

    def test_absolutize(self):
        self.assertEqual(absolutize_url('http://127.0.0.1/', 'http://127.0.0.2/', True, True), 'http://127.0.0.2/')
        self.assertEqual(absolutize_url('http://127.0.0.1/', 'page.html', True, True), 'http://127.0.0.1/page.html')
        self.assertEqual(absolutize_url('http://127.0.0.1/dir1/', '/page.html', True, True), 'http://127.0.0.1/page.html')
        self.assertEqual(absolutize_url('http://127.0.0.1/dir1/dir2/', '../page.html', True, True), 'http://127.0.0.1/dir1/page.html')

    def test_no_scheme(self):
        self.assertEqual(absolutize_url('http://127.0.0.1/', '//127.0.0.2/', True, True), 'http://127.0.0.2/')
        self.assertEqual(absolutize_url('https://127.0.0.1/', '//127.0.0.2/', True, True), 'https://127.0.0.2/')

    def test_no_scheme_broken(self):
        self.assertEqual(absolutize_url('http://127.0.0.1/', '///127.0.0.2/', True, True), 'http://127.0.0.2/')
        self.assertEqual(absolutize_url('http://127.0.0.1/', '////127.0.0.2/', True, True), 'http://127.0.0.2/')
        self.assertEqual(absolutize_url('https://127.0.0.1/', '///127.0.0.2/', True, True), 'https://127.0.0.2/')
        self.assertEqual(absolutize_url('https://127.0.0.1/', '////127.0.0.2/', True, True), 'https://127.0.0.2/')

    def test_rel(self):
        self.assertEqual(absolutize_url('http://127.0.0.1/', './page.html', True, True), 'http://127.0.0.1/page.html')
        self.assertEqual(absolutize_url('https://127.0.0.1/index.html', './page.html', True, True), 'https://127.0.0.1/page.html')

    def test_query(self):
        self.assertEqual(absolutize_url('http://127.0.0.1/index.html?f=1', './page.html?g=3', True, True), 'http://127.0.0.1/page.html?g=3')

    def test_reverse_no_escape(self):
        self.assertEqual(reverse_no_escape('www', ['a']), '/www/a')
        self.assertEqual(reverse_no_escape('www', ['%20']), '/www/%20')
        self.assertEqual(reverse_no_escape('www', ['?a=b']), '/www/?a=b')

    def test_norm_url_path(self):
        for url, expected in (('/b/c', '/b/c'),
                              ('/b/c/', '/b/c/'),
                              ('/b/c/.', '/b/c/'),
                              ('/b/c/./', '/b/c/'),
                              ('/b/c/..', '/b/'),
                              ('/b/c/../', '/b/'),
                              ('/b/c/../g', '/b/g'),
                              ('/b/c/../..', '/'),
                              ('/b/c/../../', '/'),
                              ('/b/c/../../g', '/g')):
            self.assertEqual(norm_url_path(url), expected, 'non normed url %s' % url)

    def test_zzz_rfc3986_5_4_1_normal_examples(self):
        # https://datatracker.ietf.org/doc/html/rfc3986#section-5.4
        base_url = 'http://a/b/c/d;p?q'

        for link, expected in (('http:h', 'http://h/'),  # modified to folllow sosse's conventions
                               ('g', 'http://a/b/c/g'),
                               ('./g', 'http://a/b/c/g'),
                               ('g/', 'http://a/b/c/g/'),
                               ('/g', 'http://a/g'),

                               # trailing '/' was added to the result compared to the rfc,
                               # because that's a convention in sosse to put the trailing '/'
                               # on all http://domain urls
                               ('//g', 'http://g/'),

                               ('?y', 'http://a/b/c/d;p?y'),
                               ('g?y', 'http://a/b/c/g?y'),
                               ('#s', 'http://a/b/c/d;p?q#s'),
                               ('g#s', 'http://a/b/c/g#s'),
                               ('g?y#s', 'http://a/b/c/g?y#s'),
                               (';x', 'http://a/b/c/;x'),
                               ('g;x', 'http://a/b/c/g;x'),
                               ('g;x?y#s', 'http://a/b/c/g;x?y#s'),
                               ('', 'http://a/b/c/d;p?q'),
                               ('.', 'http://a/b/c/'),
                               ('./', 'http://a/b/c/'),
                               ('..', 'http://a/b/'),
                               ('../', 'http://a/b/'),
                               ('../g', 'http://a/b/g'),
                               ('../..', 'http://a/'),
                               ('../../', 'http://a/'),
                               ('../../g', 'http://a/g')):
            self.assertEqual(absolutize_url(base_url, link, True, True), expected, 'link: %s' % link)

    def test_zzz_rfc3986_5_4_2_abnormal_examples(self):
        # https://datatracker.ietf.org/doc/html/rfc3986#section-5.4
        base_url = 'http://a/b/c/d;p?q'

        for link, expected in (('../../../g', 'http://a/g'),
                               ('../../../../g', 'http://a/g'),
                               ('/./g', 'http://a/g'),
                               ('/../g', 'http://a/g'),
                               ('g.', 'http://a/b/c/g.'),
                               ('.g', 'http://a/b/c/.g'),
                               ('g..', 'http://a/b/c/g..'),
                               ('..g', 'http://a/b/c/..g'),
                               ('./../g', 'http://a/b/g'),
                               ('./g/.', 'http://a/b/c/g/'),
                               ('g/./h', 'http://a/b/c/g/h'),
                               ('g/../h', 'http://a/b/c/h'),

                               # ; and = is quoted in the result compared to the rfc,
                               # because it's part of the path (same below)
                               ('g;x=1/./y', 'http://a/b/c/g%3Bx%3D1/y'),

                               ('g;x=1/../y', 'http://a/b/c/y'),
                               ('./../g', 'http://a/b/g'),
                               ('./g/.', 'http://a/b/c/g/'),
                               ('g/./h', 'http://a/b/c/g/h'),
                               ('g/../h', 'http://a/b/c/h'),
                               ('g;x=1/./y', 'http://a/b/c/g%3Bx%3D1/y'),
                               ('g;x=1/../y', 'http://a/b/c/y'),
                               ('g?y/./x', 'http://a/b/c/g?y%2F.%2Fx'),
                               ('g?y/../x', 'http://a/b/c/g?y%2F..%2Fx'),
                               ('g#s/./x', 'http://a/b/c/g#s/./x'),
                               ('g#s/../x', 'http://a/b/c/g#s/../x')):
            self.assertEqual(absolutize_url(base_url, link, True, True), expected, 'link: %s' % link)


class UrlBeautifyTest(TestCase):
    def test_beautify(self):
        URLS = (
            ('http://xn--z7x.com/', 'http://猫.com/'),
            ('http://test.com/%E7%8C%AB', 'http://test.com/猫'),
        )

        for a, b in URLS:
            self.assertEqual(url_beautify(a), b)
