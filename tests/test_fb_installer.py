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


LSBLK_SAMPLE = '''{
  "blockdevices": [
    {"name":"sda","size":"20G","type":"disk","children":[
      {"name":"sda1","size":"512M","type":"part"},
      {"name":"sda2","size":"19.5G","type":"part"}
    ]}
  ]
}'''


def test_parse_lsblk_returns_partitions():
    mod = load_mod()
    parts = mod.parse_lsblk(LSBLK_SAMPLE)
    paths = [p["path"] for p in parts]
    assert "/dev/sda1" in paths
    assert "/dev/sda2" in paths
    assert "/dev/sda" not in paths


def test_parse_lsblk_includes_size():
    mod = load_mod()
    parts = mod.parse_lsblk(LSBLK_SAMPLE)
    sda1 = next(p for p in parts if p["path"] == "/dev/sda1")
    assert sda1["size"] == "512M"


def test_parse_rsync_progress_extracts_percent():
    mod = load_mod()
    line = "    1,234,567  45%   12.3MB/s    0:00:10"
    assert mod.parse_rsync_progress(line) == 45


def test_parse_rsync_progress_none_when_absent():
    mod = load_mod()
    assert mod.parse_rsync_progress("sending incremental file list") is None


def test_step_percent_weights():
    mod = load_mod()
    assert mod.step_percent(0, 0) == 0
    assert mod.step_percent(2, 50) == 35
    assert mod.step_percent(8, 100) == 100


def test_initial_state_shape():
    mod = load_mod()
    st = mod.new_state()
    assert st["percent"] == 0
    assert st["done"] is False
    assert st["error"] is None
    assert st["step"] == ""


def test_install_steps_match_weights():
    mod = load_mod()
    assert len(mod.INSTALL_STEPS) == len(mod.STEP_WEIGHTS)


def test_validate_install_cfg():
    mod = load_mod()
    ok = {"root_part": "/dev/sda2", "hostname": "fruit",
          "username": "kev", "password": "x"}
    assert mod.validate_install_cfg(ok) is None
    assert mod.validate_install_cfg({**ok, "hostname": "Bad Host"})
    assert mod.validate_install_cfg({**ok, "username": "1bad"})
    assert mod.validate_install_cfg({**ok, "password": ""})
    assert mod.validate_install_cfg({**ok, "root_part": ""})
