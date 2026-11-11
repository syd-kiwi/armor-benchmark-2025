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


class RepairValidationTests(unittest.TestCase):
    def test_reorders_explicit_behaviors_without_changing_keys(self):
        task = {'behaviors': ['answer', 'reject_conduct', 'clarify'], 'source': source()}
        answer = fixture('answer') | {'question': 'Synthetic supported case?', 'correct_option': 'A'}
        reject = fixture('reject_conduct') | {'question': 'Synthetic prohibited case?', 'correct_option': 'B'}
        clarify = fixture('clarify') | {'question': 'Synthetic incomplete case?', 'correct_option': 'C', 'decisive_facts': []}
        result = generation.parse_questions(json.dumps({'questions': [reject, answer, clarify]}), task)
        self.assertEqual([q['expected_behavior'] for q in result], task['behaviors'])
        self.assertEqual([q['correct_option'] for q in result], ['A', 'B', 'C'])
        self.assertEqual(result[2]['decisive_facts'], [])
        self.assertEqual(result[2]['missing_facts'], clarify['missing_facts'])

    def test_duplicate_labels_not_silently_relabelled(self):
        task = {'behaviors': ['answer', 'reject_conduct', 'clarify'], 'source': source()}
        with self.assertRaisesRegex(ValueError, 'Expected behavior labels'):
            generation.parse_questions(json.dumps({'questions': [fixture(), fixture(), fixture('clarify')]}), task)

    def test_cannot_build_reason_is_exposed(self):
        with self.assertRaisesRegex(ValueError, 'Insufficient source'):
            generation.parse_questions(json.dumps({'questions': [], 'cannot_build_reason': 'Insufficient source'}),
                                       {'behaviors': ['answer'], 'source': source()})

    def test_v3_refuses_upgrade_and_preserves_old_checkpoint(self):
        task = {'task_id': 'SYNTHETIC1', 'provider': 'claude', 'behaviors': ['answer'],
                'family_kind': 'standalone', 'source': source()}
        second = task | {'task_id': 'SYNTHETIC2'}
        item = fixture()
        response = {'text': json.dumps({'questions': [item]}), 'model': 'mock-claude'}
        response2 = {'text': json.dumps({'questions': [item | {'question': 'Second synthetic fixture?'}]}), 'model': 'mock-claude'}
        records = generation.records_for([item], task, response)
        records[0]['prompt_version'] = 'armor2026-three-provider-v1'
        tasks = [task, second]
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/'claude.jsonl'
            raw = output.with_suffix('.jsonl.raw.jsonl')
            manifest_path = output.with_suffix('.jsonl.manifest.json')
            saved = {'total': 50, 'seed': 2026, 'models': {'claude': 'mock-claude'},
                     'prompt_version': 'armor2026-three-provider-v1', 'max_tokens': 8192,
                     'tasks_sha256': generation.sha(json.dumps(tasks, sort_keys=True, ensure_ascii=False)),
                     'script_sha256': next(iter(generation.PREVIOUS_SCRIPT_HASHES))}
            manifest_path.write_text(json.dumps(saved))
            generation.append(raw, {'task_id': task['task_id'], 'status': 'ok', 'response': response, 'records': records})
            original_bytes = raw.read_bytes()
            args = SimpleNamespace(output=output, total_questions=50, seed=2026, max_tokens=8192,
                                   resume=True, upgrade_checkpoint=True, max_new_tasks=None)
            with patch.object(generation, 'make_clients') as clients:
                with self.assertRaisesRegex(ValueError, 'new output path'):
                    generation.execute(tasks, {'claude': 'mock-claude'}, args)
                clients.assert_not_called()
            self.assertEqual(raw.read_bytes(), original_bytes)
            self.assertEqual(json.loads(manifest_path.read_text()), saved)
            self.assertFalse(output.exists())

    def test_upgrade_rejects_changed_model_and_altered_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'manifest.json'
            current = {'total': 50, 'seed': 2026, 'models': {'claude': 'new-model'},
                       'prompt_version': generation.PROMPT_VERSION, 'max_tokens': 8192,
                       'tasks_sha256': 'test', 'script_sha256': 'current'}
            saved = current | {'models': {'claude': 'old-model'},
                              'prompt_version': 'armor2026-three-provider-v1',
                              'script_sha256': next(iter(generation.PREVIOUS_SCRIPT_HASHES))}
            with self.assertRaisesRegex(ValueError, 'new output path'):
                generation.upgrade_checkpoint(path, saved, current, [], [])
            self.assertEqual(list(Path(tmp).iterdir()), [])
        task = {'task_id': 'TEST', 'provider': 'claude', 'behaviors': ['answer'], 'family_kind': 'standalone', 'source': source()}
        response = {'text': json.dumps({'questions': [fixture()]}), 'model': 'mock'}
        records = generation.records_for([fixture()], task, response)
        records[0]['correct_option'] = 'C'
        with self.assertRaisesRegex(ValueError, 'differs'):
            generation.validate_saved_entries([{'task_id': 'TEST', 'status': 'ok', 'response': response, 'records': records}], [task])


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
                self.assertEqual(args.output.name, 'nato_claude_v3_draft.jsonl')

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


class SharedScenarioTests(unittest.TestCase):
    def family(self):
        row = source()
        row['provenance']['Section'] = 'TEST'
        row['Text'] = 'The required status must be verified before the synthetic decision can proceed.'
        task = {'task_id': 'SYNTHETIC', 'provider': 'claude', 'family_kind': 'matched_triple',
                'source': row, 'behaviors': ['answer', 'reject_conduct', 'clarify'],
                'quality_schema': 'shared-scenario-v1', 'answer_positions': ['A', 'C', 'B']}
        items = []
        for behavior, status in zip(task['behaviors'], ['verified', 'contradicted', 'unknown']):
            item = fixture(behavior)
            item.update(shared_context='A synthetic officer reviews the same request at the same time.',
                        decision_question='Does the stated status meet the supplied requirement?',
                        changed_variable='status of the required condition', variant_fact=f'The status is {status}.',
                        supporting_evidence=row['Text'])
            for c, word in zip('ABC', ['verified', 'assumed', 'unresolved']):
                item[f'option_{c}'] = f'The synthetic decision depends on the {word} status of this required condition.'
            items.append(item)
        return task, items

    def test_shared_family_assembly_and_permutation_preserve_answer_content(self):
        task, items = self.family()
        response = {'text': json.dumps({'questions': items}), 'model': 'mock'}
        parsed = generation.parse_questions(response['text'], task)
        records = generation.records_for(parsed, task, response)
        for original, record, desired in zip(parsed, records, task['answer_positions']):
            self.assertIn(original['variant_fact'], record['question'])
            self.assertEqual(record['correct_option'], desired)
            self.assertEqual(record[f'option_{desired}'], original['option_B'])
            self.assertEqual({record[f'option_{c}'] for c in 'ABC'}, {original[f'option_{c}'] for c in 'ABC'})
        generation.validate_saved_entries([{'task_id': task['task_id'], 'status': 'ok',
                                           'response': response, 'records': records}], [task])

    def test_changed_shared_fields_duplicate_variants_and_length_cues_rejected(self):
        for field in ['shared_context', 'decision_question', 'changed_variable']:
            task, items = self.family()
            items[1][field] += ' Changed.'
            with self.assertRaisesRegex(ValueError, 'identical'):
                generation.parse_questions(json.dumps({'questions': items}), task)
        task, items = self.family()
        items[1]['variant_fact'] = items[0]['variant_fact']
        with self.assertRaisesRegex(ValueError, 'fact value'):
            generation.parse_questions(json.dumps({'questions': items}), task)
        task, items = self.family()
        items[0]['option_A'] = 'Too short'
        with self.assertRaisesRegex(ValueError, 'Option-length'):
            generation.parse_questions(json.dumps({'questions': items}), task)

    def test_source_sentence_in_stem_rejected(self):
        task, items = self.family()
        for item in items:
            item['shared_context'] = task['source']['Text']
        with self.assertRaisesRegex(ValueError, 'copies a source sentence'):
            generation.parse_questions(json.dumps({'questions': items}), task)

    def test_balanced_positions_and_determinism(self):
        tasks = generation.assign_answer_positions(generation.plan_tasks([source()], 50, 2026), 2026)
        second = generation.assign_answer_positions(generation.plan_tasks([source()], 50, 2026), 2026)
        self.assertEqual(tasks, second)
        self.assertEqual(Counter(c for t in tasks for c in t['answer_positions']), {'A': 17, 'B': 17, 'C': 16})
        for provider in generation.PROVIDERS:
            counts = Counter(c for t in tasks if t['provider'] == provider for c in t['answer_positions'])
            self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)

    def test_composite_source_retains_original_spans_and_hashes(self):
        rows = generation.load_snippets(ROOT/'data/nato/nato_doctrine_snippets.csv',
                                        ROOT/'data/nato/nato_snippet_provenance.csv', compose_sources=True)
        composite = next(row for row in rows if len(row['source_spans']) == 2)
        self.assertEqual(len(rows), 30)
        self.assertEqual([span['metadata']['Snippet_ID'] for span in composite['source_spans']], ['NATO-003', 'NATO-022'])
        for span in composite['source_spans']:
            self.assertEqual(generation.sha(span['text']), span['metadata']['Text_SHA256'])
        self.assertEqual(generation.sha(composite['Text']), composite['provenance']['Text_SHA256'])

    def test_quality_report_counts_both_length_heuristics(self):
        task, items = self.family()
        parsed = generation.parse_questions(json.dumps({'questions': items}), task)
        report = generation.quality_summary(generation.records_for(parsed, task, {'model': 'mock'}))
        self.assertEqual(report['questions'], 3)
        self.assertEqual(report['answer_positions'], {'A': 1, 'B': 1, 'C': 1})
        self.assertIn('first_shortest_heuristic_correct', report)
        self.assertEqual(report['review_status'], 'draft')
