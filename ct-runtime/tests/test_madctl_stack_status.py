from types import SimpleNamespace
from mad_os.cli import madctl_stack as mcs


def test_stack_status_includes_exo_health(capsys):
    args = SimpleNamespace(json=False)
    mcs.cmd_stack_status(args)
    cap = capsys.readouterr()
    out = cap.out
    assert "EXO" in out
    assert "8000" in out
    assert "HEALTHY" in out or "LISTENING" in out
    assert "HUD" in out
