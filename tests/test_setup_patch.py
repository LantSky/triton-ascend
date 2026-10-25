import ast
from pathlib import Path


def _load_ascend_arg_helper():
    source_path = Path(__file__).parents[1] / "third_party" / "ascend" / "build" / "setup_patch.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_get_ascend_proton_cmake_args"
    )
    namespace = {"os": __import__("os"), "Path": Path}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source_path), "exec"), namespace)
    return namespace[function.name]


def test_ascend_include_dir_is_opt_in_and_falls_back_to_toolkit_home(tmp_path, monkeypatch):
    toolkit_include = tmp_path / "runtime" / "include"
    (toolkit_include / "acl").mkdir(parents=True)
    (toolkit_include / "acl" / "acl.h").write_text("/* test */")
    monkeypatch.setenv("ASCEND_INCLUDE_DIR", str(tmp_path / "missing"))
    monkeypatch.setenv("ASCEND_TOOLKIT_HOME", str(tmp_path))
    monkeypatch.delenv("ASCEND_HOME_PATH", raising=False)

    assert _load_ascend_arg_helper()() == [
        "-DPROTON_ENABLE_NPU=ON",
        f"-DASCEND_INCLUDE_DIR={toolkit_include}",
    ]


def test_ascend_proton_args_are_empty_without_a_valid_cann_include(monkeypatch):
    monkeypatch.setenv("ASCEND_INCLUDE_DIR", "")
    monkeypatch.setenv("ASCEND_HOME_PATH", "")
    monkeypatch.setenv("ASCEND_TOOLKIT_HOME", "")

    assert _load_ascend_arg_helper()() == []
