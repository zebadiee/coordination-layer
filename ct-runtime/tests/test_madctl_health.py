import pytest
from types import SimpleNamespace
from unittest.mock import patch

import mad_os.cli.madctl_stack as mcs


def _fake_run_factory(codes):
    it = iter(codes)
    def _fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=next(it))
    return _fake_run


def test_operator_hud_only_healthy(capsys):
    # OPERATOR: HUD required, Exo optional
    with patch('mad_os.cli.madctl_stack.resolve_mode', return_value='OPERATOR'):
        # order: exo_active, hud_active, exo_port, hud_port
        codes = [1, 0, 1, 0]
        with patch('mad_os.cli.madctl_stack.subprocess.run', side_effect=_fake_run_factory(codes)):
            mcs.cmd_health(None)
            captured = capsys.readouterr()
            assert "✅ MAD-OS is healthy" in captured.out


def test_full_missing_exo_unhealthy(capsys):
    # FULL: both HUD and Exo required
    with patch('mad_os.cli.madctl_stack.resolve_mode', return_value='FULL'):
        # simulate Exo missing, HUD present
        codes = [1, 0, 1, 0]  # exo_active (nonzero=inactive), hud_active (0=active), exo_port (inactive), hud_port (active)
        with patch('mad_os.cli.madctl_stack.subprocess.run', side_effect=_fake_run_factory(codes)):
            with pytest.raises(SystemExit) as exc:
                mcs.cmd_health(None)
            assert exc.value.code == 1
            captured = capsys.readouterr()
            assert "❌ MAD-OS health check failed" in captured.out
            assert "Exo service not active" in captured.out
