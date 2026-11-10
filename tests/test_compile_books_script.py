"""The batch compiler must fail when a book is missing or compilation fails."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / 'compile_books_51_70.sh'
FIRST_BOOK = 'Book51_JobHunter'
PDF_NAME = 'ZTurns_Book51_JobHunter.pdf'


class CompileBooksScriptTest(unittest.TestCase):
    def run_compiler(self, *, source=True, exit_code=0, stale_pdf=False):
        work = Path(self.enterContext(tempfile.TemporaryDirectory()))
        script = work / SCRIPT.name
        shutil.copyfile(SCRIPT, script)
        book = work / 'output' / FIRST_BOOK
        book.mkdir(parents=True)
        if source:
            (book / 'lesson with spaces.md').write_text('# Lesson\n', encoding='utf-8')
        if stale_pdf:
            (book / PDF_NAME).write_bytes(b'old PDF')
        venv = work / 'venv'
        (venv / 'bin').mkdir(parents=True)
        python = venv / 'bin' / 'python3'
        python.write_text(f'#!/bin/bash\necho "compiler ran"\nexit {exit_code}\n', encoding='utf-8')
        python.chmod(0o700)
        return subprocess.run(
            ['bash', str(script)], cwd=work,
            env={**os.environ, 'VIRTUAL_ENV': str(venv)},
            capture_output=True, text=True, timeout=10,
        )

    def test_missing_source_is_failure(self):
        result = self.run_compiler(source=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('no MD file', result.stdout)
        self.assertNotIn('All done', result.stdout)

    def test_compiler_failure_is_not_hidden_by_tail_or_stale_pdf(self):
        result = self.run_compiler(exit_code=7, stale_pdf=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('compiler ran', result.stdout)
        self.assertIn('Book51 FAILED (exit 7)', result.stdout)
        self.assertNotIn('All done', result.stdout)
        self.assertNotIn('Book51 done', result.stdout)

    def test_success_without_pdf_is_failure(self):
        result = self.run_compiler()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Book51 FAILED', result.stdout)
        self.assertNotIn('All done', result.stdout)

    def test_one_failure_does_not_stop_the_batch(self):
        result = self.run_compiler(source=False)
        self.assertIn('Book52', result.stdout)
        self.assertIn('book(s) failed', result.stdout)


if __name__ == '__main__':
    unittest.main()
