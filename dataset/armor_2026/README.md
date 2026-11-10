# ARMOR 2026 dataset development

`passages.jsonl` contains six **draft page selections**, extracted from the exact PDF recorded in `input_policy_documents/AJP-3.9_EDB_V1_E.source.json`. They are NOT approved source spans or generated benchmark questions. The full pages provide context and can contain adjoining provisions, headers, footnotes, and page breaks.

Before generation, a reviewer must trim each `text` to a complete, relevant provision, verify it against the PDF, preserve necessary qualifications, check national reservations, and set `review_status` to `approved` with a named `reviewer`. PDF page numbers are one-based file positions, not printed page labels. Passage records keep the original PDF hash after text trimming because it identifies the source file, not the edited passage.

Generate into a new `candidates.jsonl` file. Inspect and edit both versions of every scenario, then save approved pairs in `reviewed.jsonl`. A candidate never becomes approved solely because structural validation passes. Keep both versions of each scenario in the same split. If adding paraphrases or missing-information variants, reuse the family-level split assignment and record a parent family ID; the current validator checks `scenario_id`, so reviewers must also check cross-family relationships.

The initial goal is 50 distinct approved NATO scenarios (100 prompt variants), covering answerable questions, proposed prohibited conduct, and missing essential facts. This is a target, not an existing dataset or guaranteed class balance. Do not force unsupported question types from a passage.

The published 2025 dataset remains at `dataset/questions_final_519.jsonl`. It uses its original schema; it is not silently converted to reviewed 2026 ground truth.
