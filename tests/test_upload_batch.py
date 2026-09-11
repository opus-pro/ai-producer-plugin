import base64
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

SPEC = importlib.util.spec_from_file_location('upload_batch', Path(__file__).resolve().parents[1] / 'plugins/aip/skills/aip/scripts/upload_batch.py')
upload = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(upload)

class UploadTests(unittest.TestCase):
    def setUp(self):
        # Keep the developer's own proxy settings out of the default expectations.
        for name, value in (('getproxies', {}), ('proxy_bypass', False)):
            patcher = patch.object(upload, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_paths_and_https(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / 'x.html').write_text('ok')
            row = {'path': 'x.html', 'upload_url': 'https://example.test/upload?secret=value', 'headers': {'Content-Type': 'text/html'}}
            self.assertEqual(len(upload.prepare(root, [row])), 1)
            for changes in [{'path': 3}, {'path': '../outside'}, {'upload_url': 'http://example.test/x'}, {'headers': {'x': 3}}, {'upload_url': 'https://example.test:bad/x'}]:
                with self.assertRaises(ValueError):
                    upload.prepare(root, [dict(row, **changes)])

    def test_service_paths_map_to_local_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / 'index.html').write_text('ok')
            row = {'path': 'render-engine/index.html', 'upload_url': 'https://example.test/upload'}
            job = upload.prepare(root, [row])[0]
            self.assertEqual(job[0], 'index.html')
            self.assertEqual(job[1], root / 'index.html')
            with self.assertRaises(ValueError):
                upload.prepare(root, [dict(row, path='render-engine/../outside')])

    def test_upload_and_error_are_sanitized(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); (root / 'x').write_bytes(b'abc')
            job = upload.prepare(root, [{'path':'x','upload_url':'https://example.test/x?secret=private'}])[0]
            with patch.object(upload.http.client, 'HTTPSConnection') as cls:
                conn = cls.return_value; conn.getresponse.return_value.status = 200
                self.assertTrue(upload.upload(job)['ok'])
                conn.send.assert_called_once_with(b'abc')
                conn.set_tunnel.assert_not_called()
                cls.assert_called_once_with('example.test', None, timeout=upload.TIMEOUT_SECONDS)
                conn.getresponse.side_effect = RuntimeError('secret=private')
                result = upload.upload(job)
                self.assertFalse(result['ok']); self.assertNotIn('private', str(result))
                cls.side_effect = RuntimeError('secret=private')
                self.assertEqual(upload.upload(job)['error'], 'upload_failed')

    def test_proxy_is_resolved_from_host_configuration(self):
        url = urlsplit('https://example.test/x')
        for setting, expected in [('http://proxy.test:3128', ('proxy.test', 3128, {})),
                                  ('proxy.test', ('proxy.test', upload.DEFAULT_PROXY_PORT, {}))]:
            with patch.object(upload, 'getproxies', return_value={'https': setting}):
                self.assertEqual(upload.proxy_for(url), expected)
        with patch.object(upload, 'getproxies', return_value={'https': 'http://user:p%40ss@proxy.test:3128'}):
            _, _, headers = upload.proxy_for(url)
            self.assertEqual(base64.b64decode(headers['Proxy-Authorization'].split()[1]).decode(), 'user:p@ss')
        self.assertIsNone(upload.proxy_for(url))
        with patch.object(upload, 'getproxies', return_value={'https': 'http://proxy.test:3128'}):
            with patch.object(upload, 'proxy_bypass', return_value=True):
                self.assertIsNone(upload.proxy_for(url))
            with patch.object(upload, 'getproxies', return_value={'https': 'http://:3128'}):
                with self.assertRaises(ValueError):
                    upload.proxy_for(url)

    def test_upload_tunnels_through_the_proxy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); (root / 'x').write_bytes(b'abc')
            with patch.object(upload, 'getproxies', return_value={'https': 'http://proxy.test:3128'}):
                job = upload.prepare(root, [{'path': 'x', 'upload_url': 'https://example.test/x?secret=private'}])[0]
            with patch.object(upload.http.client, 'HTTPSConnection') as cls:
                conn = cls.return_value; conn.getresponse.return_value.status = 200
                self.assertTrue(upload.upload(job)['ok'])
                cls.assert_called_once_with('proxy.test', 3128, timeout=upload.TIMEOUT_SECONDS)
                # The tunnel carries the origin host, so the signed PUT stays end-to-end TLS.
                conn.set_tunnel.assert_called_once_with('example.test', None, {})

if __name__ == '__main__':
    unittest.main()
