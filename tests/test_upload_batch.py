import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('upload_batch', Path(__file__).resolve().parents[1] / 'plugins/aip/skills/aip/scripts/upload_batch.py')
upload = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(upload)

class UploadTests(unittest.TestCase):
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
                conn.getresponse.side_effect = RuntimeError('secret=private')
                result = upload.upload(job)
                self.assertFalse(result['ok']); self.assertNotIn('private', str(result))
                cls.side_effect = RuntimeError('secret=private')
                self.assertEqual(upload.upload(job)['error'], 'upload_failed')

if __name__ == '__main__':
    unittest.main()
