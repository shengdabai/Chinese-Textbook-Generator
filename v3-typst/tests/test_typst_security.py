"""Untrusted Markdown and CLI metadata must stay data in generated Typst."""
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import generate
from parsers.md_parser import MarkdownParser, NodeType
from renderers.typst_renderer import TypstRenderer


@pytest.mark.parametrize('kind', [NodeType.HEADING, NodeType.PARAGRAPH, NodeType.BLOCKQUOTE])
def test_directives_in_markdown_are_literal(kind):
    node = {'type': kind, 'level': 1, 'text': '#panic("injected") $ @missing ` * _ <x> //'}
    rendered = TypstRenderer().render([node])
    assert r'\#panic' in rendered
    for char in '$@`*_<>/':
        assert '\\' + char in rendered


def test_code_cannot_close_its_typst_fence():
    # Markdown only closes fences at the start of a line; Typst closes them inline too.
    markdown = '```text\nexample ``` #panic("injected") ```\n```\n'
    nodes = MarkdownParser().parse(markdown)
    rendered = TypstRenderer().render(nodes)
    assert rendered.startswith('#raw(')
    assert 'block: true' in rendered
    assert '\\"injected\\"' in rendered


def test_code_language_is_also_data():
    rendered = TypstRenderer().render([{
        'type': NodeType.CODE_BLOCK, 'lang': 'x\") #panic("injected")', 'code': 'print("ok")',
    }])
    assert 'lang: "x\\\") #panic(\\"injected\\")"' in rendered


def test_cli_metadata_is_quoted_and_default_output_stays_inside_output(monkeypatch, tmp_path):
    compile_mock = Mock(return_value=True)
    monkeypatch.setattr(generate, 'compile_typ', compile_mock)
    monkeypatch.setattr(generate, 'md_to_body', lambda *a, **k: 'Safe body')
    monkeypatch.setattr(generate, 'OUTPUT', tmp_path / 'output')
    md = tmp_path / 'lesson.md'
    md.write_text('Lesson', encoding='utf-8')
    payload = 'Title"\n#panic("injected")\n//'
    args = SimpleNamespace(md=str(md), number='1', title=payload, subtitle=payload, color=payload, out=None)
    generate.cmd_textbook(args)
    source, output = compile_mock.call_args.args
    assert '"\n#panic' not in source
    assert '#let book-title = "Title\\"\\u{a}#panic(\\"injected\\")\\u{a}//"' in source
    assert output.parent == generate.OUTPUT


def test_hsk_metadata_is_quoted(monkeypatch, tmp_path):
    md = tmp_path / 'lesson.md'
    md.write_text('Lesson', encoding='utf-8')
    monkeypatch.setattr(generate, 'md_files_for_hsk', lambda level: [md])
    monkeypatch.setattr(generate, 'V2_HSK_ROOT', tmp_path)
    monkeypatch.setattr(generate, 'md_to_body', lambda *a, **k: 'Safe body')
    source = generate.build_hsk_typ('1', 'Title"\n#panic("injected")')
    assert '"\n#panic' not in source


def test_compile_creates_output_directory_and_removes_tempfile(monkeypatch, tmp_path):
    templates = tmp_path / 'templates'
    templates.mkdir()
    monkeypatch.setattr(generate, 'TEMPLATES', templates)
    output = tmp_path / 'new' / 'book.pdf'

    def compile_stub(command, **kwargs):
        assert output.parent.is_dir()
        assert Path(command[2]).is_file()
        return SimpleNamespace(returncode=0, stderr='')

    monkeypatch.setattr(generate.subprocess, 'run', compile_stub)
    assert generate.compile_typ('Safe body', output)
    assert list(templates.iterdir()) == []


def test_hsk_source_root_is_anchored_to_script():
    assert generate.V2_HSK_ROOT == generate.BASE.parent / 'v2-weasyprint' / 'HSK备考'
