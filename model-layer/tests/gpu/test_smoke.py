import subprocess


def test_cpu_smoke():
    # Use small size to be fast in unit tests
    import model_layer.tools.gpu.smoke_test as st
    code = st.cpu_smoke(1024)
    assert isinstance(code, int)
    assert 0 <= code < 256
