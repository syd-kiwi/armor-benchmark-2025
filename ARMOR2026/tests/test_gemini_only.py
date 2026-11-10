"""Synthetic fixtures and mock clients only; no provider requests."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import generate_gemini_only as gemini


def fixture(task):
    behavior = task['behaviors'][0]
    return {'question': 'Synthetic fixture?', 'option_A': 'One', 'option_B': 'Two', 'option_C': 'Three',
            'correct_option': 'A', 'expected_behavior': behavior, 'supporting_evidence': 'Synthetic rule.',
            'reference_answer': 'Synthetic explanation', 'reservation_handling': 'Synthetic context',
            'decisive_facts': ['Synthetic fact'], 'missing_facts': ['Unknown fact'] if behavior == 'clarify' else []}


class GeminiTests(unittest.TestCase):
    def test_diagnostics_redact_key_and_keep_status(self):
        err = RuntimeError('Service unavailable; secret-key-value https://example.org/?key=hidden')
        err.code = 503
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'secret-key-value'}):
            details = gemini.safe_error(err)
        self.assertEqual(details['http_status'], 503)
        self.assertNotIn('secret-key-value', details['message'])
        self.assertNotIn('hidden', details['message'])

    def test_preview_does_not_create_client(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(gemini, 'make_client') as client:
            with patch('sys.argv', ['script', '--env_file', str(Path(tmp)/'absent')]):
                with contextlib.redirect_stdout(io.StringIO()):
                    gemini.main()
            client.assert_not_called()

    def test_probe_only_calls_gemini_and_creates_no_run_files(self):
        client = Mock()
        client.models.generate_content.return_value = SimpleNamespace(text='OK', candidates=[])
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {'GEMINI_API_KEY': 'fake', 'GEMINI_MODEL': 'mock'}):
                with patch.object(gemini, 'make_client', return_value=client):
                    with patch('sys.argv', ['script', '--probe', '--run', '--env_file', str(Path(tmp)/'absent'),
                                            '--output_questions', str(Path(tmp)/'never.jsonl')]):
                        with contextlib.redirect_stdout(io.StringIO()):
                            gemini.main()
            client.models.generate_content.assert_called_once()
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_resume_preserves_completed_tasks_and_other_files(self):
        task = {'task_id': 'SYNTHETIC', 'provider': 'gemini', 'behaviors': ['clarify'],
                'family_kind': 'standalone', 'source': {'Document': 'synthetic', 'Category': 'test',
                    'Text': 'Synthetic rule.', 'provenance': {'Snippet_ID': 'TEST'}}}
        response = {'text': json.dumps({'questions': [fixture(task)]}), 'model': 'mock'}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            saved_gpt = root/'gpt.raw.jsonl'; saved_gpt.write_text('DO NOT CHANGE')
            args = SimpleNamespace(output=root/'gemini.jsonl', max_tokens=8192, resume=False, max_new_tasks=1)
            # Include two tasks to exercise pause and resume, using distinct stems.
            other = task | {'task_id': 'SYNTHETIC2'}
            response2 = {'text': json.dumps({'questions': [fixture(other) | {'question': 'Other synthetic fixture?'}]}), 'model': 'mock'}
            with patch.object(gemini, 'call_llm', return_value=response) as call:
                with contextlib.redirect_stdout(io.StringIO()):
                    gemini.generate(Mock(), [task, other], 'mock', args)
                self.assertEqual(call.call_count, 1)
            self.assertFalse(args.output.exists())
            args.resume = True; args.max_new_tasks = None
            with patch.object(gemini, 'call_llm', return_value=response2) as call:
                with contextlib.redirect_stdout(io.StringIO()):
                    gemini.generate(Mock(), [task, other], 'mock', args)
                self.assertEqual(call.call_count, 1)
            self.assertEqual(len(gemini.read_jsonl(args.output)), 2)
            self.assertEqual(saved_gpt.read_text(), 'DO NOT CHANGE')
            self.assertEqual({r['generator_model'] for r in gemini.read_jsonl(args.output)}, {'gemini'})

    def test_no_automatic_retry_and_failure_status_checkpointed(self):
        task = {'task_id': 'SYNTHETIC', 'provider': 'gemini', 'behaviors': ['answer'],
                'family_kind': 'standalone', 'source': {'Document': 'synthetic', 'Category': 'test',
                    'Text': 'Synthetic rule.', 'provenance': {'Snippet_ID': 'TEST'}}}
        with tempfile.TemporaryDirectory() as tmp:
            args = SimpleNamespace(output=Path(tmp)/'out.jsonl', max_tokens=8192, resume=False, max_new_tasks=None)
            error = RuntimeError('Temporary service failure'); error.code = 500
            with patch.object(gemini, 'call_llm', side_effect=error) as call:
                with self.assertRaisesRegex(RuntimeError, '500'):
                    gemini.generate(Mock(), [task], 'mock', args)
                call.assert_called_once()
            entry = gemini.read_jsonl(args.output.with_suffix('.jsonl.raw.jsonl'))[0]
            self.assertEqual(entry['http_status'], 500)
            self.assertFalse(args.output.exists())


if __name__ == '__main__':
    unittest.main()
