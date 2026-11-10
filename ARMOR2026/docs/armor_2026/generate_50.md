# Prepare 50 NATO questions with three providers

This is a preparation workflow. No live generation was run when this script was added.

The script adapts the original `generate_mcqs_multi_llm.py` recovered from commit `e072c0d086a3fe2561f69686e6953b4d0c9181de`. The old count was per category and provider; `--total_questions 50` now means 50 questions across the entire input.

| Provider | Questions |
| --- | ---: |
| GPT | 17 |
| Gemini | 17 |
| Claude | 16 |
| Total | 50 |

Fifty is not divisible by three. Each provider generates five matched scenario triples (45 questions total), then GPT and Gemini each contribute two standalone questions and Claude contributes one. The expected-behavior plan is 17 answers, 17 rejections of prohibited conduct, and 16 clarification/conditional-answer items. The five standalone items should not be used as matched triples in RQ2 analyses. Matched-family quality and the answer key still require independent human review.

## Windows Command Prompt setup

From the `armor-benchmark-2025` checkout:

```bat
git switch armor-2026
git pull --ff-only
cd ARMOR2026
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements-generation.txt
copy .env.example .env
notepad .env
```

Fill in your three API keys and three exact model IDs in `.env`, then save and close it. Model IDs are deliberately configurable rather than tied to historical model names. Use a model supported by the corresponding endpoint and your account. The script uses OpenAI Chat Completions, Google Gen AI GenerateContent, and Anthropic Messages. It does not list models or test credentials during planning. Editing `.env` updates credentials without editing Python; existing shell variables take precedence.

- [OpenAI API keys](https://platform.openai.com/api-keys)
- [Google AI Studio API keys](https://aistudio.google.com/apikey)
- [Claude API console](https://platform.claude.com/)

Gemini now uses `google-genai`, not the old `google-generativeai` SDK. Provider imports and client creation are delayed until an explicit live run, and only selected providers are initialized. No credentials are printed or stored in the run manifest.

## Preview the plan without generating anything

### Choose model IDs on the command line

You can override any or all model IDs without changing `.env`. The options are `--gpt-model`, `--gemini-model`, and `--claude-model` (underscore spellings are also accepted). IDs not supplied on the command line keep their environment or `.env` settings. Keys still come from environment variables or `.env`.

From the repository root in PowerShell, preview your chosen IDs:

```powershell
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --total_questions 50 --gpt-model YOUR_OPENAI_MODEL_ID --gemini-model YOUR_GEMINI_MODEL_ID --claude-model YOUR_CLAUDE_MODEL_ID
```

Replace those three placeholders with the exact provider IDs you want. Without `--run`, this command makes no API calls. Adding `--run` generates the planned 17 GPT, 17 Gemini, and 16 Claude questions using those IDs. These flags choose IDs within the three supported providers; they do not add providers or change allocation.

The effective IDs are saved in the run manifest. A different model ID still requires a new output path rather than resuming an incompatible checkpoint. Updates to the script change the script hash checked by older manifests; this version does not migrate or modify those checkpoints. Keep earlier saved results. To work on Gemini without repeating GPT, use the same script with `--provider gemini --model` (see [provider selection](provider_selection.md)):

```powershell
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --provider gemini --model YOUR_GEMINI_MODEL_ID --probe --run
```

That sends one small paid diagnostic request and does not generate benchmark questions. Run it without `--run` for a preview only.

```bat
python scripts\generate_mcqs_multi_llm.py --total_questions 50
```

This prints allocation and configuration status only; no questions, run files, or API requests are created. It works without API SDKs/keys if no `.env` exists. Reading an existing `.env` requires `python-dotenv`.

## Generate later, when you are ready

```bat
python scripts\generate_mcqs_multi_llm.py --total_questions 50 --run
```

This is the paid command for all three providers. The default output is `results/armor_2026/runs/nato_50_draft.jsonl`, with a manifest and raw checkpoint beside it. No such question file is included in this commit. With default settings there are 20 generation tasks/API requests: 15 requests for three related questions and five requests for one question. SDK retries are disabled. Do not run two processes against the same output path.

Every response must match the requested count, three-option schema, expected behavior, exact evidence quotation, and fact metadata. Duplicate stems are rejected. These are structural checks; they cannot establish legal correctness, independent item quality, or whether a model obeyed a national reservation.

If any request fails, generation stops and the final 50-question file is not written. Completed tasks remain in the raw checkpoint. After resolving the problem, retry the same configuration with:

```bat
python scripts\generate_mcqs_multi_llm.py --total_questions 50 --run --resume
```

Resume skips saved successful tasks and retries failed/incomplete tasks, which can incur charges. After a crash between a provider response and checkpoint write, that task may be called again. Changed source data, script, model IDs, seed, or token settings require a new `--output_questions` path. Increase `--max_tokens` with a new output path if a selected reasoning model exhausts the output budget. API access and live model compatibility have not been verified.

Generated records preserve the provider, exact model ID, source passage, section/pages, source hash, national-reservation notes, family ID, requested behavior, and draft review status. They use the historical flat MCQ fields but are not directly accepted by the separate `python -m armor2026 validate` paired-format schema. Convert and review them before using that evaluation pipeline. No multi-model agreement or human approval is implied by using three generators.

## Offline checks

```bat
python -m unittest discover -s tests -p test_generation_plan.py -v
```

Tests use synthetic fixtures and mocked API responses only. They do not generate a benchmark dataset or call providers.

## Select one provider

Use `--provider claude`, `--provider gemini`, or `--provider gpt` to run only that provider. With the default total plan of 50, these select 16, 17, or 17 questions respectively; the total is not reallocated. Omit the flag or use `--provider all` for all 50. A selected provider needs only its own key and model ID. Its default output uses a separate name, such as `nato_claude_draft.jsonl`. See [provider commands and probes](provider_selection.md).
