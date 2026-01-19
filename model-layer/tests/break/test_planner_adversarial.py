import pytest
from model_layer.planner.planner import build_execution_plan


def adapters(n):
    return [{"adapter_id": f"a{i}", "capabilities": {}} for i in range(n)]


def test_reject_fanout_zero():
    with pytest.raises(ValueError):
        build_execution_plan("hi", adapters(3), strategy="fanout", fanout=0)


def test_fanout_one_degenerates_to_single():
    p = build_execution_plan("hi", adapters(3), strategy="fanout", fanout=1, seed=1)
    assert len(p["nodes"]) == 1


def test_fanout_upper_bound_enforced():
    with pytest.raises(ValueError):
        build_execution_plan("hi", adapters(3), strategy="fanout", fanout=1000000)


def test_mixed_conflicting_strategies_rejected():
    # in our planner API, passing quorum with fanout but strategy fanout is conflicting
    with pytest.raises(ValueError):
        build_execution_plan("hi", adapters(3), strategy="fanout", fanout=2, quorum=3)


def test_impossible_quorum_rejected():
    with pytest.raises(ValueError):
        build_execution_plan("hi", adapters(2), strategy="verify", quorum=3)


def test_seed_edge_cases():
    p0 = build_execution_plan("hi", adapters(5), strategy="fanout", fanout=3, seed=0)
    p1 = build_execution_plan("hi", adapters(5), strategy="fanout", fanout=3, seed=2**31-1)
    p2 = build_execution_plan("hi", adapters(5), strategy="fanout", fanout=3, seed=0)
    assert p0["nodes"] == p2["nodes"]
    assert p0 != p1
