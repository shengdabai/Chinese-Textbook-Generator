"""create_kdp_series_b01_b10's helpers must work when the module is imported, not only via main()."""
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import create_kdp_series_b01_b10 as kdp_module

V3 = Path(__file__).resolve().parent.parent
MD = "# 第一章\n\n| 汉字 | Pinyin | English |\n|---|---|---|\n| 学 | xué | learn |\n"


@pytest.fixture
def kdp(monkeypatch):
    # The script's paths are relative to the directory it is run from; point them at this checkout.
    monkeypatch.setattr(kdp_module, "V3_DIR", V3)
    monkeypatch.setattr(kdp_module, "TEMPLATE_PATH", V3 / "templates" / "textbook.typ")
    yield kdp_module
    kdp_module._pipeline.cache_clear()
    kdp_module._kdp_template.cache_clear()


def test_md_to_body_without_main(kdp, tmp_path):
    md = tmp_path / "book.md"
    md.write_text(MD, encoding="utf-8")
    body = kdp.md_to_body(md)
    assert "= 第一章" in body
    assert "#vocab-table((" in body
    assert "[learn]" in body


def test_build_typst_source_without_main(kdp, tmp_path):
    md = tmp_path / "book.md"
    md.write_text(MD, encoding="utf-8")
    src = kdp.build_typst_source(kdp.SERIES_META[0], md)
    assert f'#let book-title = "{kdp.SERIES_META[0].title}"' in src
    assert "width: 6in" in src  # the KDP trim-size template, not the A4 one
    assert "[learn]" in src


def test_template_contact_is_configurable_data(kdp):
    template = (V3 / "templates" / "textbook.typ").read_text(encoding="utf-8")
    for source in (template, kdp.build_template()):
        assert 'sys.inputs.at("contact-email", default: "contact@example.com")' in source
        assert '#link("mailto:" + contact-email, contact-email)' in source
    assert "For permissions or bulk licensing, contact:" in kdp.build_template()


def test_contact_sources_only_contain_neutral_email_defaults():
    for path in (V3 / "templates" / "textbook.typ", Path(kdp_module.__file__)):
        emails = re.findall(r'[\w.+-]+@(?:[\w-]+\.)+[A-Za-z]{2,}', path.read_text(encoding="utf-8"))
        assert set(emails) <= {"contact@example.com"}


@pytest.mark.parametrize(
    ("explicit", "environment", "expected"),
    [
        (None, None, "contact@example.com"),
        (None, "publisher@example.org", "publisher@example.org"),
        ("rights@example.net", "publisher@example.org", "rights@example.net"),
        ('x\") #panic("injected") @example.org', None, 'x\") #panic("injected") @example.org'),
    ],
)
def test_compile_contact_is_one_data_argument(kdp, monkeypatch, tmp_path, explicit, environment, expected):
    if environment is None:
        monkeypatch.delenv("TEXTBOOK_CONTACT_EMAIL", raising=False)
    else:
        monkeypatch.setenv("TEXTBOOK_CONTACT_EMAIL", environment)
    templates = tmp_path / "templates"
    templates.mkdir()
    monkeypatch.setattr(kdp, "V3_DIR", tmp_path)
    run = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(kdp.subprocess, "run", run)

    kdp.compile_typ("Safe body", tmp_path / "output" / "book.pdf", contact_email=explicit)

    command = run.call_args.args[0]
    assert command[-2:] == ["--input", f"contact-email={expected}"]
    assert not run.call_args.kwargs.get("shell", False)
    assert list(templates.iterdir()) == []


def test_main_passes_cli_contact_to_compiler(kdp, monkeypatch, tmp_path):
    monkeypatch.setattr(kdp, "TARGET_ROOT", tmp_path / "series")
    monkeypatch.setattr(kdp, "SERIES_META", kdp.SERIES_META[:1])
    monkeypatch.setattr(kdp, "build_book_md", lambda *args: MD)
    compile_mock = Mock()
    monkeypatch.setattr(kdp, "compile_typ", compile_mock)

    kdp.main(["--contact-email", "rights@example.net"])

    assert compile_mock.call_args.kwargs == {"contact_email": "rights@example.net"}
