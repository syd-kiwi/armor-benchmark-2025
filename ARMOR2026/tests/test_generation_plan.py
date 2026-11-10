"""Offline checks only. Fixtures are synthetic, not generated benchmark questions."""
from collections import Counter
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('generation', ROOT / 'scripts/generate_mcqs_multi_llm.py')
generation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generation)


def source():
    return {'Document': 'synthetic', 'Category': 'Test', 'Text': 'A required fact must be known.',
            'provenance': {'Snippet_ID': 'TEST', 'National_Reservation': 'Synthetic reservation'}}


def fixture(behavior='answer'):
    return {'question': 'Synthetic test fixture?', 'option_A': 'First option', 'option_B': 'Second option',
            'option_C': 'Third option', 'correct_option': 'B', 'expected_behavior': behavior,
            'supporting_evidence': 'A required fact must be known.', 'reference_answer': 'Synthetic explanation',
            'reservation_handling': 'Synthetic context only', 'decisive_facts': ['Synthetic fact'],
            'missing_facts': ['Unresolved synthetic fact'] if behavior == 'clarify' else []}


class PlanTests(unittest.TestCase):
    def test_exact_provider_and_behavior_quotas(self):
        tasks = generation.plan_tasks([source()], 50, 2026)
        providers = Counter()
        for task in tasks:
            providers[task['provider']] += len(task['behaviors'])
        self.assertEqual(providers, {'gpt': 17, 'gemini': 17, 'claude': 16})
        self.assertEqual(Counter(b for t in tasks for b in t['behaviors']),
                         {'answer': 17, 'reject_conduct': 17, 'clarify': 16})
        self.assertEqual(sum(t['family_kind'] == 'matched_triple' for t in tasks), 15)
        self.assertEqual(len(tasks), 20)
        for n in [3, 4, 5, 49, 51, 100]:
            self.assertEqual(sum(len(t['behaviors']) for t in generation.plan_tasks([source()], n, 1)), n)

    def test_source_hash_join_and_reservation_in_prompt(self):
        rows = generation.load_snippets(ROOT / 'data/nato/nato_doctrine_snippets.csv',
                                        ROOT / 'data/nato/nato_snippet_provenance.csv')
        self.assertEqual(len(rows), 30)
        reserved = next(x for x in rows if x['provenance']['National_Reservation'])
        task = generation.plan_tasks([reserved], 3, 1)[0]
        self.assertIn(reserved['provenance']['National_Reservation'], generation.build_prompt(task))

    def test_plan_only_cannot_call_clients_or_write_questions(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'never_created.jsonl'
            with patch.dict(os.environ, {}, clear=True), patch.object(generation, 'make_clients') as clients:
                with patch('sys.argv', ['generator', '--env_file', str(Path(tmp)/'missing.env'),
                                        '--output_questions', str(output)]):
                    with contextlib.redirect_stdout(io.StringIO()):
                        generation.main()
                clients.assert_not_called()
            self.assertFalse(output.exists())
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_run_with_missing_configuration_never_calls_clients(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {}, clear=True), patch.object(generation, 'make_clients') as clients:
                with patch('sys.argv', ['generator', '--run', '--env_file', str(Path(tmp)/'missing.env')]):
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit):
                            generation.main()
                clients.assert_not_called()


class ModelOptionTests(unittest.TestCase):
    def test_cli_overrides_environment_and_preserves_unspecified_models(self):
        with patch.dict(os.environ, {'OPENAI_MODEL': 'env-gpt', 'GEMINI_MODEL': 'env-gemini',
                                     'ANTHROPIC_MODEL': 'env-claude'}, clear=True):
            self.assertEqual(generation.configured_models({'gemini': ' cli-gemini '}),
                             {'gpt': 'env-gpt', 'gemini': 'cli-gemini', 'claude': 'env-claude'})
            self.assertEqual(generation.configured_models({'gemini': ''})['gemini'], '')

    def test_all_cli_model_ids_work_without_model_environment_variables(self):
        env = {'OPENAI_API_KEY': 'fake', 'GEMINI_API_KEY': 'fake', 'ANTHROPIC_API_KEY': 'fake'}
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, env, clear=True):
            with patch.object(generation, 'execute') as execute:
                with patch('sys.argv', ['generator', '--run', '--env_file', str(Path(tmp)/'absent'),
                                        '--gpt-model', 'cli-gpt', '--gemini_model', 'cli-gemini',
                                        '--claude-model', 'cli-claude']):
                    with contextlib.redirect_stdout(io.StringIO()):
                        generation.main()
                execute.assert_called_once()
                self.assertEqual(execute.call_args.args[1],
                                 {'gpt': 'cli-gpt', 'gemini': 'cli-gemini', 'claude': 'cli-claude'})

    def test_model_override_preview_is_offline(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            with patch.object(generation, 'execute') as execute, patch.object(generation, 'make_clients') as clients:
                with patch('sys.argv', ['generator', '--env_file', str(Path(tmp)/'absent'),
                                        '--gemini-model', 'preview-gemini']):
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        generation.main()
                self.assertIn('gemini: model preview-gemini', output.getvalue())
                execute.assert_not_called()
                clients.assert_not_called()


class ValidationTests(unittest.TestCase):
    def task(self, behavior='answer'):
        return {'behaviors': [behavior], 'source': source()}

    def test_valid_fixture_and_exact_evidence_rejection(self):
        self.assertEqual(len(generation.parse_questions(json.dumps({'questions': [fixture()]}), self.task())), 1)
        bad = fixture(); bad['supporting_evidence'] = 'Invented rule'
        with self.assertRaises(ValueError):
            generation.parse_questions(json.dumps({'questions': [bad]}), self.task())

    def test_count_behavior_duplicates_and_missing_facts_rejected(self):
        for changed in [dict(option_B='First option'), dict(expected_behavior='reject_conduct'),
                        dict(correct_option='D'), dict(decisive_facts=[])]:
            bad = fixture() | changed
            with self.assertRaises(ValueError):
                generation.parse_questions(json.dumps({'questions': [bad]}), self.task())
        with self.assertRaises(ValueError):
            generation.parse_questions(json.dumps({'questions': []}), self.task())
        with self.assertRaises(ValueError):
            generation.parse_questions(json.dumps({'questions': [fixture()]}), self.task(), ['synthetic test fixture?'])
        bad = fixture('clarify'); bad['missing_facts'] = []
        with self.assertRaises(ValueError):
            generation.parse_questions(json.dumps({'questions': [bad]}), self.task('clarify'))


class AdapterTests(unittest.TestCase):
    def test_provider_calls_with_mock_clients_only(self):
        gpt = Mock()
        gpt.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(finish_reason='stop', message=SimpleNamespace(content='{}', refusal=None))],
            model='mock-gpt', id='mock-id', usage=None)
        gemini = Mock()
        gemini.models.generate_content.return_value = SimpleNamespace(
            candidates=[SimpleNamespace(finish_reason='STOP')], text='{}', model_version='mock-gemini',
            response_id='mock-id', usage_metadata=None)
        claude = Mock()
        claude.messages.create.return_value = SimpleNamespace(stop_reason='end_turn',
            content=[SimpleNamespace(type='text', text='{}')], model='mock-claude', id='mock-id',
            usage=SimpleNamespace(model_dump=lambda: {}))
        for provider, client in [('gpt', gpt), ('gemini', gemini), ('claude', claude)]:
            self.assertEqual(generation.call_llm(client, provider, 'mock-model', 'synthetic prompt', 500)['text'], '{}')
        self.assertEqual(gpt.chat.completions.create.call_args.kwargs['max_completion_tokens'], 500)
        self.assertEqual(gemini.models.generate_content.call_args.kwargs['config']['response_mime_type'], 'application/json')
        self.assertEqual(claude.messages.create.call_args.kwargs['max_tokens'], 500)


class ProviderSelectionTests(unittest.TestCase):
    def test_claude_selection_needs_only_claude_settings(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'fake'}, clear=True):
            with patch.object(generation, 'execute') as execute:
                with patch('sys.argv', ['generator', '--provider', 'claude', '--model', 'mock-claude',
                                        '--run', '--env_file', str(Path(tmp)/'absent')]):
                    with contextlib.redirect_stdout(io.StringIO()):
                        generation.main()
                tasks, models, args = execute.call_args.args
                self.assertEqual({t['provider'] for t in tasks}, {'claude'})
                self.assertEqual(sum(len(t['behaviors']) for t in tasks), 16)
                self.assertEqual(models, {'claude': 'mock-claude'})
                self.assertEqual(args.output.name, 'nato_claude_draft.jsonl')

    def test_probe_only_selected_provider_and_no_files(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'fake'}, clear=True):
            client = Mock()
            with patch.object(generation, 'make_clients', return_value={'claude': client}) as factory:
                with patch.object(generation, 'call_llm', return_value={'text': '{"ok":true}'}) as call:
                    with patch('sys.argv', ['generator', '--provider', 'claude', '--model', 'mock-claude',
                                            '--probe', '--run', '--env_file', str(Path(tmp)/'absent')]):
                        with contextlib.redirect_stdout(io.StringIO()):
                            generation.main()
                    factory.assert_called_once_with(('claude',))
                    call.assert_called_once()
                    self.assertEqual(call.call_args.args[1], 'claude')
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_all_provider_probe_is_rejected_before_client_creation(self):
        with patch.object(generation, 'make_clients') as clients:
            with patch('sys.argv', ['generator', '--probe', '--run']):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        generation.main()
            clients.assert_not_called()

    def test_sanitized_status_without_key(self):
        err = RuntimeError('HTTP 503: secret-key https://example.org/?key=private')
        err.code = 503
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'secret-key'}):
            details = generation.safe_error(err)
        self.assertEqual(details['http_status'], 503)
        self.assertNotIn('secret-key', details['message'])
        self.assertNotIn('private', details['message'])

    def test_provider_only_pause_and_resume_does_not_touch_gpt(self):
        row = source()
        task = {'task_id': 'SYNTHETIC1', 'provider': 'claude', 'behaviors': ['answer'],
                'family_kind': 'standalone', 'source': row}
        other = task | {'task_id': 'SYNTHETIC2'}
        item = fixture() | {'supporting_evidence': row['Text']}
        first = {'text': json.dumps({'questions': [item]}), 'model': 'mock-claude'}
        second = {'text': json.dumps({'questions': [item | {'question': 'Second synthetic fixture?'}]}), 'model': 'mock-claude'}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gpt = root/'gpt.raw.jsonl'; gpt.write_text('UNCHANGED')
            args = SimpleNamespace(output=root/'claude.jsonl', total_questions=50, seed=2026,
                                   max_tokens=8192, resume=False, max_new_tasks=1)
            with patch.object(generation, 'make_clients', return_value={'claude': Mock()}) as clients:
                with patch.object(generation, 'call_llm', return_value=first) as call:
                    with contextlib.redirect_stdout(io.StringIO()):
                        generation.execute([task, other], {'claude': 'mock-claude'}, args)
                    call.assert_called_once()
                clients.assert_called_once_with(('claude',))
            self.assertFalse(args.output.exists())
            args.resume = True; args.max_new_tasks = None
            with patch.object(generation, 'make_clients', return_value={'claude': Mock()}):
                with patch.object(generation, 'call_llm', return_value=second) as call:
                    with contextlib.redirect_stdout(io.StringIO()):
                        generation.execute([task, other], {'claude': 'mock-claude'}, args)
                    call.assert_called_once()
            self.assertEqual(len(generation.read_jsonl(args.output)), 2)
            self.assertEqual(gpt.read_text(), 'UNCHANGED')


if __name__ == '__main__':
    unittest.main()
