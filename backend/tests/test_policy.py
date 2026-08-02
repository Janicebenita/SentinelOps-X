import pytest
from backend.app.tools.patch_tools import PatchPolicyError, inspect_patch
from backend.app.tools.sandbox import LocalSandbox, validate_command

def test_safe_patch():
    assert inspect_patch("-x\n+y", ["demo_app/app/main.py", "demo_app/tests/test_regression.py"], True)["within_policy"]

def test_protected_patch():
    with pytest.raises(PatchPolicyError):
        inspect_patch("+x", ["sandbox/Dockerfile"], True)

def test_command_allowlist():
    validate_command(["pytest", "-q"])
    with pytest.raises(ValueError):
        validate_command(["curl", "example.com"])
    with pytest.raises(ValueError):
        validate_command(["pytest", "-q;whoami"])

def test_local_sandbox_rejects_non_predefined_command(tmp_path):
    with pytest.raises(ValueError, match="predefined pytest"):
        LocalSandbox().run(["python", "-c", "print(1)"], str(tmp_path))

def test_local_sandbox_runs_predefined_pytest_in_copy(tmp_path):
    test_dir = tmp_path / "demo_app" / "tests"
    test_dir.mkdir(parents=True)
    test_file = test_dir / "test_regression_checkout.py"
    test_file.write_text("def test_isolated():\n    assert True\n", encoding="utf-8")
    result = LocalSandbox().run(
        ["pytest", "-q", "demo_app/tests/test_regression_checkout.py"], str(tmp_path)
    )
    assert result.exit_code == 0
    assert "1 passed" in result.stdout
