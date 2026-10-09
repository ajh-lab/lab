"""Render the read-only, one-device release catalog nginx configuration."""
import argparse
import re
from pathlib import Path, PurePosixPath


def render(root: Path, tls: Path, runtime: Path, client_fingerprint: str,
           *, port: int = 8443, address: str = '192.168.1.48') -> str:
    paths = [str(path).replace('\\', '/') for path in (root, tls, runtime)]
    if any(not PurePosixPath(path).is_absolute() or not re.fullmatch(r'/[A-Za-z0-9/_.-]+', path)
           or '..' in PurePosixPath(path).parts for path in paths):
        raise ValueError('safe absolute paths are required')
    if not re.fullmatch(r'[a-fA-F0-9]{40}', client_fingerprint):
        raise ValueError('the approved client certificate fingerprint is required')
    if type(port) is not int or not 1024 <= port <= 65535 or address not in {'192.168.1.48', '127.0.0.1'}:
        raise ValueError('invalid listen endpoint')
    root_path, tls_path, run_path = paths
    return f'''worker_processes 1;
pid {run_path}/nginx.pid;
error_log stderr warn;
events {{ worker_connections 64; }}
http {{
    access_log off;
    server_tokens off;
    client_body_temp_path {run_path}/body;
    proxy_temp_path {run_path}/proxy;
    fastcgi_temp_path {run_path}/fastcgi;
    uwsgi_temp_path {run_path}/uwsgi;
    scgi_temp_path {run_path}/scgi;
    map $ssl_client_fingerprint $approved_device {{
        default 0;
        "{client_fingerprint.lower()}" 1;
    }}
    server {{
        listen {address}:{port} ssl;
        server_name releases.droneops.home.arpa;
        ssl_certificate {tls_path}/server.pem;
        ssl_certificate_key {tls_path}/server.key;
        ssl_client_certificate {tls_path}/client-ca.pem;
        ssl_verify_client on;
        ssl_verify_depth 1;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_session_tickets off;
        client_max_body_size 1k;
        client_body_timeout 10s;
        send_timeout 60s;
        keepalive_timeout 10s;
        if ($approved_device = 0) {{ return 403; }}
        location /releases/ {{
            alias {root_path}/;
            autoindex off;
            limit_except GET {{ deny all; }}
            add_header Cache-Control "no-store" always;
            add_header X-Content-Type-Options nosniff always;
        }}
        location / {{ return 404; }}
    }}
}}
'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-fingerprint', required=True)
    args = parser.parse_args()
    print(render(Path('/srv/droneops/releases'), Path('/etc/droneops/catalog/tls'),
                 Path('/run/droneops-release-catalog'), args.client_fingerprint))
