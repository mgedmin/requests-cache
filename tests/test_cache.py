#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
import time
import json
from collections import defaultdict

import requests

import requests_cache


class CacheTestCase(unittest.TestCase):

    def setUp(self):
        requests_cache.configure()
        requests_cache.clear()

    def test_speedup_and_undo_redo_patch(self):
        delay = 1
        def long_request():
            t = time.time()
            for i in range(5):
                r = requests.get('http://httpbin.org/delay/%s' % delay)
            delta = time.time() - t
            self.assertLess(delta, delay * 3)
        long_request()
        requests_cache.undo_patch()
        t = time.time()
        r = requests.get('http://httpbin.org/delay/%s' % delay)
        delta = time.time() - t
        self.assertGreaterEqual(delta, delay)
        requests_cache.redo_patch()
        long_request()


    def test_expire_cache(self):
        delay = 1
        url = 'http://httpbin.org/delay/%s' % delay
        requests_cache.configure(expire_after=0.001)
        t = time.time()
        r = requests.get(url)
        delta = time.time() - t
        self.assertGreaterEqual(delta, delay)
        t = time.time()
        r = requests.get(url)
        delta = time.time() - t
        self.assertGreaterEqual(delta, delay)

    def test_just_for_coverage(self):
        # str method and keys
        s = str(requests_cache.get_cache())
        url = 'http://httpbin.org/redirect/3'
        r = requests.get(url)
        # delete keys
        requests_cache.get_cache().del_cached_url(url)
        requests_cache.get_cache().del_cached_url('http://httpbin.org/redirect/3')
        url_map = requests_cache.get_cache().url_map
        with self.assertRaises(KeyError):
            del url_map['123']

        # update
        url_map['http://ya.ru/'] = 'htpp://??.ru'
        url_map['http://ya.ru/'] = 'htpp://ya.ru'


    def test_unregistered_backend(self):
        with self.assertRaises(ValueError):
            requests_cache.configure(backend='nonexistent')


    def test_async_compatibility(self):
        from requests import async
        n = 3
        def long_running():
            t = time.time()
            rs = [async.get('http://httpbin.org/delay/%s' % i) for i in range(n + 1)]
            async.map(rs)
            return time.time() - t
        # cache it
        delta = long_running()
        self.assertGreaterEqual(delta, n)
        # fast from cache
        delta = 0
        for i in range(n):
            delta += long_running()
        self.assertLessEqual(delta, 1)

    def test_hooks(self):
        state = defaultdict(int)
        for hook in ('response', 'post_request'):

            def hook_func(r):
                state[hook] += 1
                return r
            n = 5
            for i in range(n):
                r = requests.get('http://httpbin.org/get', hooks={hook: hook_func})
            self.assertEqual(state[hook], n)

    def test_post(self):
        url = 'http://httpbin.org/post'
        r1 = json.loads(requests.post(url, data={'test1': 'test1'}).content)
        r2 = json.loads(requests.post(url, data={'test2': 'test2'}).content)
        self.assertIn('test2', r2['form'])
        self.assert_(not requests_cache.has_url(url))



    # TODO: https test

if __name__ == '__main__':
    unittest.main()
