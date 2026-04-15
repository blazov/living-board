"""Tests for the runner startup credentials banner.

The banner emits a one-line ``[credentials] present=... absent=...`` log at
process start so operators can see at a glance which credentials are wired
up. Secret values are never printed — only variable names.
"""

from __future__ import annotations

import runner.agent as agent_module
from runner.agent import CREDENTIAL_ENV_VARS, emit_credentials_banner


def _reset_guard() -> None:
    agent_module._credentials_banner_emitted = False


def test_banner_splits_present_and_absent():
    _reset_guard()
    env = {
        "AGENTMAIL_API_KEY": "sk-am-xxxxxxxx",
        "CLAUDE_API_KEY": "sk-ant-xxxxxxxx",
    }
    captured: list[str] = []
    line = emit_credentials_banner(env=env, emit=captured.append)

    assert line is not None
    assert captured == [line]
    assert line.startswith("[credentials] present=")
    assert "present=AGENTMAIL_API_KEY,CLAUDE_API_KEY" in line
    # Absent set = all seven minus the two present, in declared order.
    expected_absent = [n for n in CREDENTIAL_ENV_VARS if n not in env]
    assert f"absent={','.join(expected_absent)}" in line
    # No values ever printed.
    assert "sk-am-xxxxxxxx" not in line
    assert "sk-ant-xxxxxxxx" not in line


def test_banner_emits_once_per_process():
    _reset_guard()
    calls: list[str] = []
    first = emit_credentials_banner(env={}, emit=calls.append)
    second = emit_credentials_banner(env={"CLAUDE_API_KEY": "x"}, emit=calls.append)

    assert first is not None
    assert second is None, "second call must be a no-op (emit-once guard)"
    assert len(calls) == 1, "emit callback must fire exactly once per process"


def test_banner_all_absent_when_env_empty():
    _reset_guard()
    captured: list[str] = []
    line = emit_credentials_banner(env={}, emit=captured.append)
    assert line is not None
    assert "present=(none)" in line
    assert f"absent={','.join(CREDENTIAL_ENV_VARS)}" in line


def test_banner_all_present():
    _reset_guard()
    env = {name: "value" for name in CREDENTIAL_ENV_VARS}
    captured: list[str] = []
    line = emit_credentials_banner(env=env, emit=captured.append)
    assert line is not None
    assert f"present={','.join(CREDENTIAL_ENV_VARS)}" in line
    assert "absent=(none)" in line


def test_banner_empty_string_counts_as_absent():
    """An env var set to '' is treated as absent — consistent with how shells
    export empty credentials and with truthy checks elsewhere in the runner."""
    _reset_guard()
    env = {"CLAUDE_API_KEY": ""}
    captured: list[str] = []
    line = emit_credentials_banner(env=env, emit=captured.append)
    assert line is not None
    assert "present=(none)" in line
    assert "CLAUDE_API_KEY" in line.split("absent=", 1)[1]


def test_force_flag_bypasses_guard():
    _reset_guard()
    emit_credentials_banner(env={}, emit=lambda _l: None)
    calls: list[str] = []
    second = emit_credentials_banner(env={}, emit=calls.append, force=True)
    assert second is not None
    assert len(calls) == 1


if __name__ == "__main__":
    # Tiny ad-hoc harness so the tests are runnable without pytest.
    import traceback

    tests = [fn for name, fn in globals().items()
             if name.startswith("test_") and callable(fn)]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError:
            failed += 1
            print(f"FAIL  {fn.__name__}")
            traceback.print_exc()
    if failed:
        raise SystemExit(f"{failed} test(s) failed")
    print(f"\n{len(tests)} passed")
