import sys
import types


def _ensure_module(name: str):
    if name in sys.modules:
        return sys.modules[name]
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


def pytest_sessionstart(session):
    # mock problematic dynamic imports to avoid circular import issues during tests
    pkg_base = "cryptnoxpro.command.user_keys.aws_kms"

    # Create mock for cryptnoxpro.command.helper.ui with minimal API used in code
    ui_mod = _ensure_module("cryptnoxpro.command.helper.ui")
    if not hasattr(ui_mod, "secret_with_exit"):
        def secret_with_exit(prompt: str, required: bool = True):
            return ""
        ui_mod.secret_with_exit = secret_with_exit
        ui_mod.input_with_exit = lambda *args, **kwargs: ""
        ui_mod.print_warning = lambda *args, **kwargs: None

    # Create mock aws_kms package and submodule to bypass heavy imports
    pkg = _ensure_module(pkg_base)
    sub = _ensure_module(pkg_base + ".aws_kms")

    class AwsKms:
        pass

    sub.AwsKms = AwsKms
    pkg.AwsKms = AwsKms
