# Agent Intellectual Property, Model Licensing, and Data Rights

Agent businesses are built from layered rights: code, model weights, adapters, prompts, datasets, retrieval sources, customer inputs, generated outputs, branding, and human-created material. A technically working stack can still be commercially unusable if one layer lacks the rights required for the intended use.

This guide is operational guidance, not jurisdiction-specific legal advice. Copyright, contract/license, patent, trademark, database, publicity/digital-replica, confidentiality, and trade-secret rules differ and should not be collapsed into one generic “IP” answer.

## Core rule

**Publicly available is not the same as commercially usable.**

Before an agent business sells, redistributes, fine-tunes, or promises ownership of a deliverable, map the exact asset and exact use to current evidence.

```text
asset -> source/version -> rights evidence -> intended use -> conflicts -> review -> allowed action
```

If a material right is unknown, stale, disputed, incompatible, or contradicted by customer/provider terms, keep the record in `needs_review` or `blocked`.

## Canonical artifacts

- Playbook: `docs/AGENT_IP_DATA_RIGHTS.md`
- Schema: `schemas/ip-rights-record.schema.json`
- Safe starter: `templates/IP_RIGHTS_RECORD.json`
- Validator: `scripts/validate_ip_rights.py`

Validate a record:

```bash
python scripts/validate_ip_rights.py templates/IP_RIGHTS_RECORD.json
```

The starter intentionally assumes no verified commercial right.

## 1. Build the rights map

Inventory every material asset used to produce or deliver the paid outcome.

| Asset kind | Typical questions |
|---|---|
| Code | What license applies? Are dependencies compatible with distribution/SaaS use? |
| Model weights | Which exact model/version? Commercial use? Fine-tuning? Redistribution? Output terms? |
| Adapter / LoRA | Are upstream weights and training data compatible with the adapter's use? |
| Prompt | Who authored it? Does it contain confidential or customer material? |
| Dataset | What license/permission supports training, evaluation, or redistribution? |
| RAG/retrieval source | Is access equivalent to reuse? Are indexing, caching, quotation, or commercial uses permitted? |
| Customer input | Is the business authorized to process it for service delivery? For model improvement or training? |
| Generated output | What do provider terms say? What can the founder safely promise the customer? |
| Brand / domain | Who owns or controls the mark/domain? Any third-party brand or likeness risk? |
| Human-authored asset | Is there an assignment or license from founder, employee, or contractor? |

Do not infer rights from file access, an API response, a public URL, or a model being downloadable.

## 2. Separate rights dimensions

For every asset, track these independently:

- ownership/provenance status,
- commercial use,
- redistribution,
- derivative works/adaptation,
- training/fine-tuning/reuse,
- attribution requirements,
- customer-input status,
- terms/license version,
- effective and expiry dates,
- current evidence,
- unresolved conflicts.

One “licensed: yes” flag is too coarse. A model may be usable commercially but not redistributable. A dataset may allow research but not paid training. Customer data may be usable for the service but not for model improvement.

## 3. Model and provider terms

Treat model/provider terms as versioned dependencies.

For every production model/provider:

1. record the exact provider and model/version,
2. capture the terms/license identifier or version,
3. record when the evidence was observed,
4. determine the intended-use rights actually needed,
5. record attribution/pass-through obligations,
6. identify fallback providers/models,
7. monitor for material terms changes.

Model-distribution licensing is evolving quickly. In 2026, model-specific frameworks such as OpenMDW 1.1 and NVIDIA's Open Model Agreement illustrate why conventional software-license heuristics are not enough. The operational lesson is not that one license is “safe”; it is that founders should identify the exact terms governing the exact model materials and intended use.

### Terms-change procedure

When provider/model terms change:

```text
new terms detected
  -> mark old evidence superseded/stale
  -> identify affected models/products/customers
  -> compare commercial/redistribution/training/output rights
  -> stop incompatible new use
  -> route to fallback or owner/legal review
  -> update customer promises if necessary
  -> preserve old and new evidence references
```

Do not silently continue under remembered terms.

## 4. Open source and open weights

“Open” can describe access, not necessarily the legal rights required by the business.

Before commercial use, check:

- exact license/version,
- whether weights, code, data, docs, and adapters share the same terms,
- commercial-use limitations,
- acceptable-use restrictions,
- attribution/notice obligations,
- redistribution conditions,
- derivative/fine-tuning conditions,
- patent or trademark clauses,
- output provisions,
- sublicensing/pass-through obligations.

If a model distribution contains components under different licenses, track them as separate assets rather than assuming the top-level license covers everything.

## 5. Training, fine-tuning, and data rights

A training or fine-tuning pipeline needs a data-rights map, not just a data pipeline.

For each dataset/source, record:

- source and provenance,
- purpose of collection/access,
- allowed use,
- commercial status,
- training/reuse permission,
- redistribution permission,
- applicable opt-out or rightsholder controls where relevant,
- retention/caching rules,
- current evidence.

### Customer data

Default to the narrowest use authorized by the customer relationship.

Do not infer permission to train or improve a model merely because customer data can be processed to deliver the service.

Separate:

```text
service delivery
quality assurance
analytics
model evaluation
fine-tuning
general model improvement
cross-customer learning
```

A contract may permit one and prohibit another.

## 6. RAG and retrieval sources

Retrieval creates its own rights questions.

Access to a webpage, API, database, document collection, or customer corpus does not automatically establish permission to:

- copy it into a persistent index,
- cache it indefinitely,
- reproduce substantial portions,
- train on it,
- redistribute it,
- expose it to another customer,
- create a commercial derivative dataset.

Record source-level rights and avoid storing restricted source text in public evidence records. Use metadata/references instead.

## 7. Input confidentiality and trade secrets

Customer prompts, documents, source code, credentials, internal plans, and proprietary datasets may carry contractual or trade-secret obligations even when copyright is not the main issue.

Before sending sensitive input to a model/provider, verify:

- authorized purpose,
- provider retention/training terms,
- subprocessor exposure,
- residency constraints when relevant,
- confidentiality obligations,
- deletion/retention controls,
- whether the customer authorized that provider class.

Never copy private customer or provider agreement text into the public repository's IP-rights record. Reference a controlled internal record.

## 8. Generated outputs and customer promises

Avoid promising more than the evidence supports.

Separate three questions:

1. What rights does the provider claim or disclaim in outputs?
2. What rights, if any, can the founder assert in the generated deliverable?
3. What rights can the founder safely grant or assign to the customer?

These are not equivalent.

A provider saying it does not claim ownership does not by itself prove that a generated output is copyrightable, non-infringing, or exclusively ownable by the founder/customer.

For important customer deliverables, review:

- provider output terms,
- source/retrieval provenance,
- human authorship/editorial contribution where relevant,
- similarity/infringement risk appropriate to the product,
- customer ownership/license language,
- indemnity/warranty boundaries.

## 9. Customer contract checklist

Before signing a customer IP clause, compare it to the upstream stack.

Check:

- who owns pre-existing IP,
- customer input rights,
- deliverable ownership or license,
- rights in improvements/feedback,
- training/model-improvement permissions,
- provider pass-through restrictions,
- attribution obligations,
- confidentiality/trade-secret treatment,
- infringement warranties,
- indemnity scope,
- exclusions for customer-supplied material,
- post-termination rights.

If the customer asks for ownership or warranties the upstream provider terms do not support, block the promise rather than hoping the conflict never matters.

## 10. Founder, employee, and contractor IP

Company ownership should be evidenced, not assumed.

For important company-created assets, link the IP record to controlled evidence for:

- founder assignment,
- employee invention/assignment terms,
- contractor work-product assignment/license,
- third-party code/content notices,
- pre-existing IP exclusions.

Do not store signatures, government IDs, private employment terms, or full agreements in the public repository record.

## 11. Brand, trademark, likeness, and synthetic media

Brand rights and generated-media rights may require separate review.

Escalate when an agent business:

- adopts a name/logo close to another brand,
- uses customer or third-party trademarks in marketing,
- generates realistic depictions of identifiable people,
- clones voice/likeness,
- creates endorsements or testimonials,
- produces synthetic media subject to disclosure requirements.

As of August 2, 2026, EU AI Act Article 50 transparency obligations apply to specified AI-generated/manipulated content and interactive AI contexts. Treat disclosure obligations as an operating requirement distinct from ownership rights.

## 12. Evidence states

Use evidence status explicitly:

- `current` — reviewed and applicable to the asset/version/use,
- `stale` — needs refresh,
- `disputed` — conflict exists,
- `superseded` — replaced by newer terms/evidence,
- `draft` — not yet reliable.

A `commercial_ready` record must rely on current evidence for material assets and customer/output terms.

## 13. Commercial-readiness gate

Before `status = commercial_ready`, require:

- all material assets have resolved rights status,
- commercial rights support the intended paid use,
- redistribution rights support anything actually redistributed,
- training rights support any training/fine-tuning activity,
- required attribution has an implementation reference,
- current evidence supports each material asset,
- model/provider terms version is recorded for licensed/permissioned assets,
- customer input rights are resolved,
- provider pass-through terms were reviewed,
- output-rights claims are resolved,
- no rights conflicts remain,
- required owner/legal review is complete,
- the public record contains no private contract/customer/restricted-source content.

Run:

```bash
python scripts/validate_ip_rights.py <record>
```

Passing the validator means the repository's semantic gates are satisfied. It does not constitute a legal opinion.

## 14. Failure-mode evals

Test at least these scenarios:

1. **Noncommercial model in paid service** — commercial readiness must fail.
2. **Unknown model terms** — downloadable model must not be treated as commercially cleared.
3. **Redistribution mismatch** — shipping weights/adapters while redistribution is prohibited must fail.
4. **Customer data reused for training** — unknown/prohibited training permission must fail.
5. **Missing attribution** — attribution-required asset without an implementation reference must fail.
6. **Stale provider terms** — stale evidence must not support commercial readiness.
7. **Unlicensed RAG source** — unresolved retrieval-source rights remain blocked/review-required.
8. **Unsupported ownership promise** — customer deliverable cannot promise ownership while output rights remain unknown.
9. **Provider/customer conflict** — incompatible pass-through and customer clauses block readiness.
10. **Expired permission** — expired asset permission cannot remain production-ready.
11. **Leaked private agreement** — raw contract text must be rejected from portable/public records.
12. **Restricted dataset copied into record** — public artifact must contain metadata/reference only.
13. **Terms change after launch** — affected asset becomes stale/superseded and triggers impact review.
14. **Synthetic likeness use** — route separately to publicity/digital-replica and transparency review.

## 15. Operating metrics

Useful metrics include:

- percent of production assets with current rights evidence,
- number of unresolved commercial-right blockers,
- days since provider/model terms refresh,
- assets with unknown training/reuse permissions,
- customer contracts with unresolved upstream pass-through conflicts,
- time from terms change to impact determination,
- percentage of generated deliverables requiring human/IP review,
- rights-related product stoppages or incidents.

These are operational metrics, not legal-compliance guarantees.

## 16. Agent-native opportunities

The rights layer itself creates business opportunities:

- model-license inventory and compatibility agents,
- provider-terms change monitoring,
- customer/upstream IP-clause conflict detection,
- dataset/RAG provenance systems,
- attribution obligation automation,
- rights-aware model routing,
- training-data permission ledgers,
- diligence-ready IP evidence rooms,
- generated-output provenance and review workflows.

A durable advantage is not simply knowing more license names. It is maintaining a current, inspectable chain from each business asset to the rights needed for the exact commercial action.

## Final rule

Do not ask, “Is this AI asset open?”

Ask:

> **For this exact asset/version, do we have current evidence that permits this exact commercial use, and do our customer promises remain inside those upstream rights?**

If the answer is not evidenced, the safe operational state is not ready.
