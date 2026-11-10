# NATO AJP-3.9 doctrine snippets for ARMOR 2026

This is a curated initial extraction of 30 source passages, not an exhaustive extraction or an independently adjudicated legal dataset. It contains no generated benchmark questions or assigned answer/reject/clarify labels.

## Source and acknowledgment

NATO Standardization Office, *Allied Joint Doctrine for Joint Targeting*, AJP-3.9, Edition B, Version 1, November 2021. NATO is acknowledged as the source of the reproduced passages, as required by paragraph 3 of the publication's letter of promulgation. Copyright NATO/OTAN.

- [Official publication page](https://www.gov.uk/government/publications/allied-joint-doctrine-for-joint-targeting-ajp-39a)
- [Source PDF](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1033306/AJP-3.9_EDB_V1_E.pdf)
- Source PDF SHA-256: `cbc1d451bd17030f53c92edb99591ddaffdc6e044d386eb57ebd2a08f46efb50`
- Extracted November 10, 2026.

## Files

`nato_doctrine_snippets.csv` retains the original three-column format:

| Column | Meaning |
| --- | --- |
| Document | Stable source identifier for this edition |
| Category | Proposed ARMOR category mapping |
| Text | Extracted source passage with whitespace normalized |

`nato_snippet_provenance.csv` records the physical CSV row (header is row 1), stable snippet ID, text hash, section, printed page, one-based PDF page, context, national-reservation flags, and source URL. Join it to the snippet CSV using the SHA-256 of the UTF-8 Text value; CSV_Row also identifies the original ordering. Row numbers cease to be reliable after reordering. Snippet IDs are assigned in this extraction and do not imply official NATO paragraph identifiers.

Both CSV files use UTF-8 with a BOM for Excel compatibility. Quoted commas and line handling were checked by a CSV write/read round trip. Each extracted segment was matched against whitespace-normalized source-page text; no rule wording was generated. Page breaks, running headers, and intervening footnotes are omitted when joining a paragraph across pages. Superscript footnote markers inside selected passages remain as extracted digits; their relevant context is recorded in the provenance file. Source grammar and terminal list punctuation are preserved.

## Coverage and category review

The selection emphasizes legal constraints, civilian protection, proportionality, verification, legal advice, accountability, national caveats, and cyberspace legal boundaries. It is intentionally selective. Category labels are proposed mappings, not evidence that this source covers every original ARMOR category. Reconcile them with the authoritative category vocabulary in the existing pipeline before merging datasets.

## National reservations and context

AJP-3.9 includes a record of national reservations. A source provision must not be presented as universally accepted by all NATO members.

- NATO-017 extracts section 1.6.2(c). U.S. reservation 3 (printed VI, PDF page 10) disputes language in that paragraph concerning distinction and direct participation in hostilities. Footnote 38 is separately extracted as NATO-019. Footnote 37 provides additional civilian-protection policy context on printed page 1-24.
- NATO-020 extracts selected sentences from section 1.7(a). U.S. reservation 4 (printed VI, PDF page 10) explicitly rejects its presumption concerning civilian objects in cases of doubt. The antecedent of "these entities" is dual-use entities.
- The record also contains broader U.S. reservations concerning terminology and variances from national doctrine, as well as other nations' reservations. The row-level flags identify directly relevant reservations noticed during this extraction; they are not an exhaustive national applicability assessment.
- NATO-030 is footnote 28 from the discussion of Phase 4; retain that context rather than treating the wording as a new standalone rule.

Review the entire applicable source paragraph, footnotes, reservations, and national context before creating a reference answer. Keep the provenance available to the question-generation step; the three-column CSV alone does not convey every qualifier. Questions using disputed provisions should explicitly name the supplied AJP provision and specify any national perspective. Do not infer unconditional engagement permission from source definitions or from the absence of a prohibition in an excerpt.

## Next use

Select suitable snippets for the pilot, then construct scenario variants whose decisive facts justify answering, rejecting proposed conduct, or requesting clarification/answering conditionally. Assign expected behavior at the scenario level, not solely from the snippet category. Not every passage supports all three variants. Independent review of the category mappings, source applicability, and reference answers remains to be completed.
