import time

from mad_os.adapters import exo_adapter as ea


def test_exo_is_healthy_real_stub():
    # The Exo stub should be running on 8000
    # retry a few times in case of timing
    for _ in range(3):
        if ea.is_healthy(port=8000):
            break
        time.sleep(0.2)
    assert ea.is_healthy(port=8000)


def test_exo_unreachable_returns_false():
    # Port 59999 is very likely unused
    assert ea.is_healthy(port=59999) is False
