"""Hermes version-gate arithmetic for the 0.22.x compatibility port.

Implements SPEC-hermes-0.22-compat.md §6.1 unit tests:

* UT-1 — ``hermes_version_supported()`` in ``health.py`` returns the expected
  result for every boundary / representative version of the widened range.
* UT-2 — ``adapter.py``'s copy of the same gate mirrors ``health.py``'s for
  every case (detects drift between the two constant copies).
* UT-3 — ``CERTIFIED_HERMES_VERSION`` parses to a triple inside the new range
  in both modules.

The plugin modules use package-relative imports (``from . import serve``), so
the bundle is imported as a package: the directory containing this test's
``__init__.py``-bearing parent is placed on ``sys.path`` and the bundle is
imported under its own directory name. No installed package is required.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

# The bundle root is the directory that holds ``__init__.py`` (one level above
# ``tests/``). Its PARENT must be importable so the bundle resolves as a package.
_BUNDLE_ROOT = Path(__file__).resolve().parents[1]
if str(_BUNDLE_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(_BUNDLE_ROOT.parent))

health = importlib.import_module(f"{_BUNDLE_ROOT.name}.health")
adapter = importlib.import_module(f"{_BUNDLE_ROOT.name}.adapter")


# SPEC §6.1 UT-1 case matrix: (input, expected admission).
UT1_CASES = (
    ("0.21.0", False),             # below min
    ("0.21.1", True),              # min inclusive
    ("0.21.5", True),              # old baseline
    ("0.22.0", True),              # newly admitted
    ("0.22.5", True),              # port target
    ("0.22.7", True),              # latest patch
    ("0.23.0", False),             # max exclusive
    ("0.23.0.dev0", False),        # dev cycle
    ("0.22.5+12.gabc1234", True),  # git describe suffix
    ("0.0.0", False),              # placeholder
    ("", False),                   # empty
    (None, False),                 # unparseable
)

# SPEC §6.3 regression-gate inputs.
RG_REFUSED = ("0.20.0", "0.20.5", "0.20.99", "0.23.0", "0.23.0.dev0", "0.23.99")


def test_ut1_health_version_range():
    """UT-1: health.py gate admits exactly the widened >=0.21.1,<0.23.0 range."""
    for raw, expected in UT1_CASES:
        assert health.hermes_version_supported(raw) is expected, (raw, expected)


def test_ut2_adapter_mirrors_health():
    """UT-2: adapter.py's gate returns identical results to health.py's."""
    for raw, expected in UT1_CASES:
        actual = adapter.hermes_version_supported(raw)
        assert actual is expected, (raw, expected, actual)
        assert actual == health.hermes_version_supported(raw), raw


def test_ut3_certified_constants_in_range():
    """UT-3: CERTIFIED_HERMES_VERSION parses inside the supported range."""
    for module in (adapter, health):
        parsed = module.parse_version(module.CERTIFIED_HERMES_VERSION)
        assert parsed is not None, module.__name__
        assert (
            module.SUPPORTED_HERMES_MIN
            <= parsed
            < module.SUPPORTED_HERMES_MAX_EXCLUSIVE
        ), (module.__name__, parsed)


def test_rg1_old_baseline_still_admitted():
    """RG-1: a 0.21.5 host is still admitted."""
    assert health.hermes_version_supported("0.21.5") is True


def test_rg2_pre_floor_refused():
    """RG-2: pre-0.21.1 hosts are refused."""
    for raw in ("0.20.0", "0.20.5", "0.20.99"):
        assert health.hermes_version_supported(raw) is False, raw


def test_rg3_future_major_refused():
    """RG-3: 0.23.0+ hosts are refused (no silent admission of a future major)."""
    for raw in ("0.23.0", "0.23.0.dev0", "0.23.99"):
        assert health.hermes_version_supported(raw) is False, raw


def test_rg_refused_matrix_matches_health_and_adapter():
    """Cross-check the refused set against both module copies."""
    for raw in RG_REFUSED:
        assert health.hermes_version_supported(raw) is False, raw
        assert adapter.hermes_version_supported(raw) is False, raw


if __name__ == "__main__":  # standalone: python tests/test_hermes_version_gate.py
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print(f"PASS {name}")
    print("ALL PASS")
