import importlib.util
import pathlib

SPEC_PATH = pathlib.Path(__file__).parent.parent / "airootfs/usr/local/bin/fb-installer.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("fb_installer", SPEC_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_step_weights_sum_to_100():
    mod = load_mod()
    assert sum(mod.STEP_WEIGHTS) == 100


def test_validate_name_accepts_simple():
    mod = load_mod()
    assert mod.validate_name("kev") is True
    assert mod.validate_name("fruit_bang") is True
    assert mod.validate_name("test-host") is True


def test_validate_name_rejects_bad():
    mod = load_mod()
    assert mod.validate_name("") is False
    assert mod.validate_name("1host") is False
    assert mod.validate_name("Has Space") is False
    assert mod.validate_name("UPPER") is False
    assert mod.validate_name("inject;rm") is False
    assert mod.validate_name("a" * 33) is False
