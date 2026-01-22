import sys

# Ensure the HUD package path is importable
sys.path.insert(0, '/home/zebadiee/ai-token-exo-bridge')

from src import spiral_codex_hud as hud


def test_hud_module_has_functions():
    assert hasattr(hud, 'get_exo_status_from_stack')
    assert hasattr(hud, 'render_hud')
    assert callable(hud.get_exo_status_from_stack)
    assert callable(hud.render_hud)
