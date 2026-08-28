# Agent AI Transparency, Disclosure, and Provenance

Customer-facing agents need an operating system for a question that identity, consent, and general compliance guidance do not answer by themselves: **what must a person or public audience be told about AI involvement, when must they be told, what provenance must travel with generated content, and what evidence proves the control actually operated?**

This guide is an operational evidence framework, not legal advice. Rules vary by jurisdiction, role, modality, audience, and use case. The safe default under unresolved material uncertainty is review, not silent non-disclosure.

## 1. Operating principles

1. **Classify the role before the obligation.** Provider/developer duties can differ from deployer/operator duties. Record the role and evidence for it instead of assuming one universal rule.
2. **Classify the surface.** Direct interaction, generated text, image, audio, video, deepfake, public-interest publication, emotion recognition, and biometric categorisation can trigger different transparency duties.
3. **Disclosure must precede the material interaction when required.** A footer shown after a user has already disclosed information or acted on an AI recommendation is not equivalent to first-interaction disclosure.
4. **Rendered evidence beats configured intent.** A template saying a disclosure should appear is not proof that it rendered in the actual channel, locale, accessibility path, or client.
5. **Provenance is a claim requiring evidence.** Do not claim watermarking, machine-readable marking, content credentials, detectability, accessibility, or human review unless the deployed mechanism has current evidence.
6. **Customer configuration cannot weaken mandatory controls.** Prompt text, branding settings, channel themes, or customer preferences must not be able to disable a required disclosure or provenance mechanism.
7. **Transparency never grants operating authority.** A valid disclosure record does not authorize publishing, messaging, profiling, biometric processing, sensitive-data use, or transactions.

## 2. Lifecycle

Use: `assessed -> disclosure_required | disclosure_not_required -> configured -> tested -> active -> changed -> suspended -> retired`.

- **assessed**: use case, audience, role, jurisdictions, and modalities are mapped; no production claim.
- **disclosure_required**: at least one applicable rule/policy requires a transparency control.
- **disclosure_not_required**: a supported ruleset decision concludes no disclosure is required for the scoped surface; this is not a universal exemption.
- **configured**: disclosure/provenance controls are configured but not yet proven on the actual channel.
- **tested**: representative channel, locale, accessibility, and provenance tests have current evidence.
- **active**: the current production configuration is covered by current ruleset and render/provenance evidence.
- **changed**: a material input changed and re-review is pending.
- **suspended**: a material uncertainty, failed disclosure, provenance failure, or policy change blocks a transparency claim.
- **retired**: the surface is no longer active.

## 3. Minimum assessment record

Track at least:

- business use case and product surface;
- audience and whether natural persons interact directly with the system;
- jurisdictions and governing ruleset references;
- provider/deployer/operator role with evidence;
- modalities produced or manipulated;
- whether the content is public-interest information, deepfake-like media, emotion recognition, or biometric categorisation;
- disclosure decision and rationale;
- disclosure surface, timing, wording reference, locale strategy, and accessibility path;
- provenance/marking method and evidence;
- human-review/editorial-control requirements and evidence;
- material-change triggers and review date;
- owner, incidents, metrics, and current evidence.

Never put private prompts, credentials, private customer data, unpublished legal advice, or raw regulated personal data into a public record.

## 4. Ruleset provenance

A transparency decision must cite a versioned or dated source. Record:

- jurisdiction;
- rule/policy identifier;
- source/reference;
- effective or retrieved date;
- next review date;
- provider/deployer applicability;
- the scoped conclusion.

Do not encode remembered law into software as if it were timeless. If the ruleset review date has passed, or a material policy change is detected, an `active` record should move to `changed` or `suspended` until reassessed.

### EU example

Article 50 transparency obligations under the EU AI Act apply from 2 August 2026. Current European Commission material highlights direct AI interactions, certain AI-generated/manipulated content, deepfakes, emotion recognition, biometric categorisation, and public-interest text without human review/editorial control. Treat this as a ruleset input, not a universal legal conclusion for every product.

## 5. Direct human interaction

When disclosure is required for a chatbot, voice agent, embedded assistant, or other direct interaction:

- render the disclosure before or at the first material interaction;
- do not hide it behind a settings page or later footer;
- cover non-visual paths for voice and assistive technology;
- test representative clients, locales, and reconnect/session-reset behavior;
- record evidence that the disclosure actually rendered;
- prevent prompts or customer themes from suppressing it.

Useful metrics: first-interaction disclosure coverage, render failure rate, accessibility failure rate, locale fallback rate, and time to remediate missing disclosure.

## 6. Generated and manipulated content

Separate human-visible disclosure from machine-readable provenance. Depending on the governing ruleset and content type, one or both may be required.

Track:

- modality: text/image/audio/video/multimodal;
- generation vs material manipulation;
- provenance mechanism and version;
- whether the mark survives supported export/transcode paths;
- whether downstream systems strip or rewrite marks;
- visible label behavior;
- evidence from actual generated outputs.

A metadata field configured in the generator is not enough if the marketplace, export pipeline, CDN, editor, or transcoder removes it.

## 7. Human review and editorial responsibility

A string such as `reviewer: Alice` is not evidence of meaningful review. If a rule or policy relies on human review/editorial responsibility, preserve evidence of:

- reviewer/editor role and authority;
- review scope;
- timestamp;
- artifact/version reviewed;
- disposition or changes requested;
- publication link/reference;
- whether automation could bypass the gate.

If human review is the basis for an exception, missing review evidence fails closed.

## 8. Channel patterns

| Channel | Primary controls |
|---|---|
| Web/app chat | first-interaction disclosure, accessible label, session-reset test |
| Voice | spoken disclosure, timing before material exchange, transcript/telephony evidence |
| Email/SMS/DM | sender identity, AI involvement disclosure where required, immutable footer/header controls |
| Social/public post | visible disclosure where required, provenance mark, publication-review evidence |
| Generated image/audio/video | machine-readable provenance plus visible disclosure where required; export-survival tests |
| Marketplace listing | listing-level AI disclosure, generated-media provenance, seller/deployer responsibility |
| Embedded agent | host integration contract preventing disclosure suppression |
| API-mediated experience | provider/deployer responsibility split and contract requiring downstream disclosure where applicable |

## 9. Material change triggers

Re-review when any of these change materially:

- model/provider or system role;
- modality;
- audience or jurisdiction;
- deployment channel;
- direct-interaction behavior;
- disclosure wording, timing, locale, or accessibility implementation;
- provenance/marking technology;
- human-review workflow;
- public-interest or regulated use classification;
- governing law, regulator guidance, platform policy, or standard.

## 10. Observability and incidents

Monitor at minimum:

- disclosure render success;
- first-interaction coverage;
- provenance-mark coverage and export survival;
- accessibility failures;
- required reviewer completion;
- published/exported content without required marks;
- policy/ruleset staleness;
- time to suspend/remediate a failed control.

Treat missing disclosure, misleading AI identity presentation, provenance stripping, incorrect jurisdiction/role classification, or publication without required review as incident candidates. Link consequential cases into the repository's incident-response and audit-evidence systems.

## 11. Failure modes to test

A production transparency system should reject or escalate at least:

- required AI identity disclosure omitted from direct interaction;
- disclosure rendered only after material interaction;
- stale ruleset evidence;
- provider/deployer role unresolved;
- prompt/customer configuration disables a required control;
- disclosure inaccessible on a supported path;
- synthetic media exported without required provenance;
- provenance claimed without current evidence;
- nominal human reviewer without review evidence;
- public-interest publication relying on an unsupported review exception;
- active status after a material policy or product change;
- privacy-sensitive or secret material embedded in the portable record.

## 12. Repository contract

Use `templates/AI_TRANSPARENCY_RECORD.json` as the zero-authority starter, validate with:

```bash
python scripts/validate_ai_transparency.py templates/AI_TRANSPARENCY_RECORD.json
```

The starter is intentionally non-active. Populate real evidence and ruleset provenance before advancing lifecycle state.