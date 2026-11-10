"""Isolate Gemini without calling GPT/Claude or touching their checkpoints.

Default: plan only. --probe --run makes one tiny diagnostic request.
--run generates only Gemini's 17-question share of the 50-question plan.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import sys

from generate_mcqs_multi_llm import (
    ROOT, append, build_prompt, call_llm, load_snippets, normal, parse_questions,
    plan_tasks, read_jsonl, records_for, sha, timestamp,
)


def safe_error(exc):
    """Keep useful status/message, remove credentials and URLs before logging."""
    code = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
    message = getattr(exc, 'message', None) or str(exc)
    if not isinstance(message, str):
        message = type(exc).__name__
    for name in ('GEMINI_API_KEY', 'GOOGLE_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY'):
        value = os.environ.get(name)
        if value:
            message = message.replace(value, '[REDACTED]')
    message = re.sub(r'AIza[\w-]+', '[REDACTED]', message)
    message = re.sub(r'https?://\S+', '[URL omitted]', message)
    message = re.sub(r'(?i)(?:bearer\s+|(?:api[_-]?key|authorization)\s*[:=]\s*)[^\s,;]+', '[REDACTED]', message)
    return {'error_type': type(exc).__name__, 'http_status': code if isinstance(code, (int, str)) else None,
            'message': ' '.join(message.split())[:600]}


def make_client():
    from google import genai
    from google.genai import types
    return genai.Client(api_key=os.environ['GEMINI_API_KEY'], http_options=types.HttpOptions(
        timeout=120000, retry_options=types.HttpRetryOptions(attempts=1)))


def generate(client, tasks, model, args):
    output = args.output
    raw = output.with_suffix(output.suffix + '.raw.jsonl')
    manifest_path = output.with_suffix(output.suffix + '.manifest.json')
    manifest = {'format': 'gemini-only-v1', 'model': model, 'max_tokens': args.max_tokens,
                'tasks_sha256': sha(json.dumps(tasks, sort_keys=True, ensure_ascii=False)),
                'prompt_sha256': sha('\n'.join(build_prompt(t) for t in tasks))}
    if output.exists():
        raise ValueError('Gemini-only output already exists; use a new --output_questions path')
    if args.resume:
        if not manifest_path.exists() or json.loads(manifest_path.read_text(encoding='utf-8')) != manifest:
            raise ValueError('Resume needs the same Gemini-only model, plan, prompts, and token budget. A different model needs a new --output_questions path. Original three-provider checkpoints are separate.')
    elif manifest_path.exists() or raw.exists():
        raise ValueError('Gemini-only run files exist; add --resume or use a new output path')
    output.parent.mkdir(parents=True, exist_ok=True)
    if not args.resume:
        with manifest_path.open('x', encoding='utf-8') as handle:
            json.dump(manifest, handle, indent=2)
    history = read_jsonl(raw) if raw.exists() else []
    successful = {}
    task_by_id = {t['task_id']: t for t in tasks}
    all_records = []
    # Reserve all saved stems before generating missing tasks.
    for entry in history:
        if entry.get('status') != 'ok':
            continue
        task_id = entry['task_id']
        if task_id in successful or task_id not in task_by_id:
            raise ValueError('Duplicate or unknown saved task')
        items = parse_questions(entry['response']['text'], task_by_id[task_id],
                                [normal(x['question']).casefold() for x in all_records])
        records = entry['records']
        if len(records) != len(items) or any(r['generator_model'] != 'gemini' for r in records):
            raise ValueError('Invalid saved Gemini records')
        successful[task_id] = entry
        all_records.extend(records)
    completed_now = 0
    for task in tasks:
        if task['task_id'] in successful:
            continue
        if args.max_new_tasks is not None and completed_now >= args.max_new_tasks:
            break
        response = None
        try:
            response = call_llm(client, 'gemini', model, build_prompt(task), args.max_tokens)
            items = parse_questions(response['text'], task,
                                    [normal(x['question']).casefold() for x in all_records])
            records = records_for(items, task, response)
            entry = {'task_id': task['task_id'], 'status': 'ok', 'response': response, 'records': records}
            append(raw, entry)
            successful[task['task_id']] = entry
            all_records.extend(records)
            completed_now += 1
            print(f"Gemini saved {task['task_id']}: {len(all_records)}/17 draft questions")
        except Exception as exc:
            details = safe_error(exc)
            append(raw, {'task_id': task['task_id'], 'status': 'failed', **details,
                         'response': response, 'timestamp': timestamp()})
            raise RuntimeError(f"Gemini {task['task_id']}: {json.dumps(details)}. GPT/Claude were not called. Successful Gemini tasks are saved; --resume retries only remaining Gemini tasks.") from None
    expected = sum(len(t['behaviors']) for t in tasks)
    if len(successful) != len(tasks):
        print(f"Paused after {completed_now} new tasks. Saved {len(all_records)}/{expected} Gemini drafts in {raw}. Use --run --resume to continue, without --max_new_tasks to complete the remainder.")
        return
    if len(all_records) != expected:
        raise ValueError('Gemini question count mismatch')
    with output.open('x', encoding='utf-8') as handle:
        for task in tasks:
            for record in successful[task['task_id']]['records']:
                handle.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f'Saved {expected} Gemini-only DRAFT questions to {output}. Existing GPT files are unchanged.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--probe', action='store_true', help='One tiny API test; no benchmark question generation')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--max_new_tasks', type=int, help='Stop after this many successful new generation tasks')
    parser.add_argument('--max_tokens', type=int, default=8192)
    parser.add_argument('--env_file', type=Path, default=ROOT / '.env')
    parser.add_argument('--model', help='Override GEMINI_MODEL without changing .env')
    parser.add_argument('--output_questions', dest='output', type=Path,
                        default=ROOT / 'results/armor_2026/runs/nato_gemini_only.jsonl')
    args = parser.parse_args()
    try:
        if args.max_tokens < 1 or (args.max_new_tasks is not None and args.max_new_tasks < 1):
            raise ValueError('Token budget and task limit must be positive')
        if args.probe and args.resume:
            raise ValueError('A probe has no checkpoint to resume')
        if args.env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(args.env_file, override=False)
        model = args.model or os.environ.get('GEMINI_MODEL', '').strip()
        key = os.environ.get('GEMINI_API_KEY', '').strip()
        print(f'Gemini only: model {model or "NOT SET"}; key {"set" if key else "NOT SET"}')
        tasks = []
        if not args.probe:
            rows = load_snippets(ROOT / 'data/nato/nato_doctrine_snippets.csv',
                                 ROOT / 'data/nato/nato_snippet_provenance.csv')
            tasks = [t for t in plan_tasks(rows, 50, 2026) if t['provider'] == 'gemini']
            print('Plan: 17 Gemini questions; GPT and Claude excluded. Behaviors:',
                  dict(Counter(b for t in tasks for b in t['behaviors'])))
        if not args.run:
            print('Preview only. No API calls or output files created. Add --run when ready.')
            return
        if not key or key.startswith('YOUR_') or not model or model.startswith('YOUR_'):
            raise ValueError('Set a real GEMINI_API_KEY and GEMINI_MODEL (or --model)')
        client = make_client()
        try:
            if args.probe:
                # Small diagnostic only: no doctrine and no saved run files.
                response = client.models.generate_content(model=model,
                    contents='Reply with exactly OK.', config={'max_output_tokens': 512})
                text = response.text or ''
                reasons = [str(c.finish_reason) for c in (response.candidates or [])]
                print('Probe HTTP request returned. Finish reasons:', reasons)
                print('Probe returned OK:', text.strip() == 'OK')
                print('Probe checks basic access only; it does not validate the full generation prompt.')
            else:
                generate(client, tasks, model, args)
        finally:
            client.close()
    except (ValueError, RuntimeError, ImportError, OSError) as exc:
        parser.exit(1, 'Error: ' + json.dumps(safe_error(exc)) + '\n')
    except Exception as exc:
        parser.exit(1, 'Gemini API error: ' + json.dumps(safe_error(exc)) + '\n')


if __name__ == '__main__':
    main()
