import json
import os


def test_exo_contract_exists_and_fields():
    p = os.path.join(os.path.dirname(__file__), '..', 'mad_os', 'contracts', 'exo.json')
    p = os.path.normpath(p)
    with open(p, 'r') as fh:
        j = json.load(fh)

    assert j.get('service') == 'exo'
    assert j.get('port') == 8000
    assert j.get('health') == '/health'
    assert 'llm_proxy' in j.get('capabilities', [])
