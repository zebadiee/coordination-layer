import tempfile
import os
from tools.atlas import write_topology as wt


def test_append_topology(tmp_path):
    vault = str(tmp_path / "vault")
    os.makedirs(vault, exist_ok=True)
    wt.append_topology(vault, "hermes", "initial lock")
    path = os.path.join(vault, "SYSTEM", "topology.md")
    assert os.path.exists(path)
    txt = open(path).read()
    assert "initial lock" in txt
