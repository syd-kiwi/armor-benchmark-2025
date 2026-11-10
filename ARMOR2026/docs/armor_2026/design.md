# ARMOR 2026 study design

Research question: How do question format and access to doctrinal evidence affect the correctness and appropriateness of LLM answers, refusals, and clarification requests?

## Scope

Extend the published ARMOR sources with NATO AJP-3.9, Edition B, Version 1, November 2021. Preserve the original 519 questions and published results. Add NATO source-grounded scenarios for educational evaluation of legal and ethical constraints. The study does not establish fitness for operational deployment.

The NATO PDF lives directly in `input_policy_documents/`. Its adjacent source manifest pins its checksum and edition. Do not assume every NATO provision is identical to US doctrine. Identify the framework in every question and review national reservations. The source itself warns that recorded reservations may not be complete. Restrict claims to the supplied edition and passage.

## Pilot

Target 50 distinct, human-approved base scenarios. Each has one multiple-choice and one open-response version. Preserve the same facts and decision task between formats. Expected behaviors cover answering, explaining a prohibition, and requesting essential missing information. Class proportions are a design decision to document after passage review, not an estimate of real-world query prevalence.

The six initial page selections are draft material, not six validated provisions. Review boundaries and qualifications before generation. Nine candidate scenarios per selection would produce up to 54 distinct drafts; retain only defensible scenarios and add passages if needed. A small approved pilot is preferable to padding a numeric target.

Test a small set of models with both formats, with and without source context. Use identical generation settings within each comparison and preserve model snapshot identifiers returned by providers. Report actual cost and truncation before scaling. Provide short justifications rather than requesting hidden reasoning traces.

## Dataset expansion and controls

Separate unselected coverage questions from any deliberately refusal-challenging subset. A refusal-enriched sample cannot estimate refusal prevalence for general military queries. Log generation models and prompts; check generator/evaluator overlap and judge bias. Expand across the original sources only after adding source manifests and equally strong passage-level provenance. Do not promote legacy records automatically to the new schema or label set.

Deduplication currently detects normalized exact question duplicates. Review semantic near-duplicates manually; the 2025 embedding workflow can be restored later, but it is not implemented by the exact-match validator. Record common source or scenario families when splitting. Related source passages and paraphrases can leak across splits even when question text differs.

## Deliverables and limitations

This branch implements extraction, draft generation, structural/evidence validation, checkpointed querying, manual or automatic annotation, and descriptive reports. It does not contain 50 generated/approved scenarios, live model results, expert legal verification, semantic deduplication, paired significance tests, fine-tuning, or a validated domain judge. These remain research tasks. Offline tests use synthetic fixtures, not empirical model outputs.
