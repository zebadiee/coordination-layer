import json
import os
import urllib.request
from typing import Tuple

CONTRACT_PATH = os.path.join(os.path.dirname(__file__), '..', 'contracts', 'exo.json')
CONTRACT_PATH = os.path.normpath(CONTRACT_PATH)


def load_contract() -> dict:
    here = os.path.dirname(__file__)
    p = os.path.join(here, '..', 'contracts', 'exo.json')
    p = os.path.normpath(p)
    with open(p, 'r') as fh:
        return json.load(fh)


def get_health(host: str = 'localhost', port: int = 8000, path: str = '/health', timeout: int = 2) -> Tuple[int, bytes]:
    url = f'http://{host}:{port}{path}'
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
        return r.getcode(), body


def is_healthy(host: str = 'localhost', port: int = 8000, path: str = '/health', timeout: int = 2) -> bool:
    try:
        code, _ = get_health(host, port, path, timeout=timeout)
        return code == 200
    except Exception:
        return False


if __name__ == '__main__':
    c = load_contract()
    print('Contract:', c)
    healthy = is_healthy(c.get('host', 'localhost'), c.get('port', 8000), c.get('health', '/health'))
    print('Healthy:', healthy)
