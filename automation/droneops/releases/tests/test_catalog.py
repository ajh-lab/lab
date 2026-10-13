"""Real nginx/TLS checks; run on Linux with nginx and openssl installed."""
import json
import shutil
import ssl
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from automation.droneops.releases.catalog_config import render


class CatalogTests(unittest.TestCase):
    def test_rejects_configuration_injection(self):
        with self.assertRaises(ValueError):
            render(Path('/tmp/root;include evil'), Path('/tmp/tls'), Path('/tmp/run'), 'a' * 40)
        with self.assertRaises(ValueError):
            render(Path('/tmp/root'), Path('/tmp/tls'), Path('/tmp/run'), 'not-a-fingerprint')

    @unittest.skipUnless(shutil.which('nginx') and shutil.which('openssl'), 'Linux nginx integration')
    def test_real_mutual_tls_and_read_only_catalog(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root, tls, runtime = (base / name for name in ('www', 'tls', 'run'))
            for path in (root, tls, runtime):
                path.mkdir()
            (root / 'catalog.json').write_text('{"schema_version":1,"releases":[]}')

            def openssl(*args):
                return subprocess.run(['openssl', *args], cwd=tls, check=True, capture_output=True).stdout

            openssl('req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'ca.key',
                    '-out', 'ca.pem', '-days', '1', '-subj', '/CN=Test CA')
            for name in ('server', 'bs01', 'other'):
                openssl('req', '-newkey', 'rsa:2048', '-nodes', '-keyout', name + '.key',
                        '-out', name + '.csr', '-subj', '/CN=' + name)
                (tls / 'ext').write_text('subjectAltName=IP:127.0.0.1\nextendedKeyUsage=' +
                                        ('serverAuth' if name == 'server' else 'clientAuth'))
                openssl('x509', '-req', '-in', name + '.csr', '-CA', 'ca.pem', '-CAkey', 'ca.key',
                        '-CAcreateserial', '-days', '1', '-extfile', 'ext', '-out', name + '.pem')
            fingerprint = openssl('x509', '-in', 'bs01.pem', '-noout', '-fingerprint', '-sha1').decode().split('=')[1].strip().replace(':', '')
            shutil.copy(tls / 'ca.pem', tls / 'client-ca.pem')
            import socket
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            config = base / 'nginx.conf'
            config.write_text(render(root, tls, runtime, fingerprint, port=port, address='127.0.0.1'))
            process = subprocess.Popen(['nginx', '-c', str(config), '-g', 'daemon off;'], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            try:
                for _ in range(100):
                    if process.poll() is not None:
                        self.fail(process.stderr.read().decode())
                    try:
                        with socket.create_connection(('127.0.0.1', port), timeout=.1):
                            break
                    except OSError:
                        time.sleep(.05)
                def request(identity=None, method='GET', path='/releases/catalog.json'):
                    ctx = ssl.create_default_context(cafile=str(tls / 'ca.pem'))
                    if identity:
                        ctx.load_cert_chain(tls / (identity + '.pem'), tls / (identity + '.key'))
                    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ctx))
                    return opener.open(urllib.request.Request(f'https://127.0.0.1:{port}' + path, method=method), timeout=5)
                with request('bs01') as response:
                    self.assertEqual(json.load(response), {'schema_version': 1, 'releases': []})
                for identity, method, path in ((None, 'GET', '/releases/catalog.json'),
                                               ('other', 'GET', '/releases/catalog.json'),
                                               ('bs01', 'PUT', '/releases/catalog.json'),
                                               ('bs01', 'GET', '/server.key'),
                                               ('bs01', 'GET', '/releases/')):
                    with self.assertRaises((urllib.error.HTTPError, urllib.error.URLError, ssl.SSLError)):
                        request(identity, method, path)
            finally:
                process.terminate()
                process.wait(timeout=10)
                process.stderr.close()


if __name__ == '__main__':
    unittest.main()
