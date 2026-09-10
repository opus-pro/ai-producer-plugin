#!/usr/bin/env python3
"""Upload an explicitly signed batch without logging credentials or calling models."""
import concurrent.futures
import http.client
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

MAX_WORKERS = 4
TIMEOUT_SECONDS = 120
CHUNK_BYTES = 1024 * 1024


def prepare(root, rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError('Expected a nonempty JSON array')
    jobs = []
    for row in rows:
        rel = row['path']
        file = (root / rel).resolve()
        url = urlsplit(row['upload_url'])
        if Path(rel).is_absolute() or not file.is_relative_to(root) or not file.is_file():
            raise ValueError('Upload path must be an existing file inside the workspace')
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.fragment:
            raise ValueError('Expected an HTTPS signed upload URL')
        _ = url.port  # Validate the port before starting any uploads.
        headers = row.get('headers', {})
        if not isinstance(headers, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in headers.items()):
            raise ValueError('Headers must be a string mapping')
        jobs.append((str(file.relative_to(root)), file, url, headers))
    return jobs


def upload(job):
    rel, file, url, headers = job
    conn = None
    try:
        conn = http.client.HTTPSConnection(url.hostname, url.port, timeout=TIMEOUT_SECONDS)
        target = url.path or '/'
        if url.query:
            target += '?' + url.query
        conn.putrequest('PUT', target)
        for key, value in headers.items():
            if key.lower() not in ('host', 'content-length', 'transfer-encoding'):
                conn.putheader(key, value)
        conn.putheader('Content-Length', str(file.stat().st_size))
        conn.endheaders()
        with file.open('rb') as stream:
            while block := stream.read(CHUNK_BYTES):
                conn.send(block)
        response = conn.getresponse()
        return {'path': rel, 'ok': 200 <= response.status < 300, 'status': response.status}
    except Exception:
        # Transport exceptions may contain signed URLs; never echo their text.
        return {'path': rel, 'ok': False, 'error': 'upload_failed'}
    finally:
        if conn is not None:
            conn.close()


def main():
    try:
        root = Path(sys.argv[1]).resolve(strict=True)
        jobs = prepare(root, json.load(sys.stdin))
    except (IndexError, KeyError, TypeError, ValueError, OSError):
        print(json.dumps({'ok': False, 'error': 'invalid_batch_or_workspace'}))
        return 2
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        results = list(pool.map(upload, jobs))
    ok = all(row['ok'] for row in results)
    print(json.dumps({'ok': ok, 'files': results}))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
