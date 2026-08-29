# Acquire-and-Automate SMB Operator Playbook

Most agent businesses start with a workflow and look for customers.

There is another path:

> **Start with an existing customer base, recurring cash flow, and operating workflow—then improve the business with agents.**

This can mean buying a service business, taking an operating stake, forming a revenue-share partnership, or becoming the technology/operator layer behind an incumbent.

The thesis is not "buy labor and replace it with AI." The thesis is:

1. acquire or partner into durable demand,
2. map the actual workflow and exception structure,
3. automate only what production evidence supports,
4. improve throughput, margin, working capital, customer experience, and new-product velocity,
5. preserve the domain knowledge and relationships that made the business valuable in the first place.

This is an educational operating framework, not investment, legal, tax, financing, employment, or regulatory advice.

---

## 1. Choose the entry mode before choosing the target

Four common structures can expose an agent founder to the same workflow economics with very different capital requirements and risks.

| Mode | You control | Capital need | Good when | Main risk |
|---|---|---:|---|---|
| Build from scratch | product + delivery | low | distribution is accessible and workflow is already understood | slow customer acquisition |
| Revenue-share / managed-service partnership | one or more workflows | low-medium | incumbent has demand but weak automation capability | limited control over systems and change |
| Minority / operating partnership | technology + agreed operating levers | medium | owner wants growth or succession help without full sale | governance ambiguity |
| Acquisition / control investment | company + workflow + customer base | high | recurring economics and workflow are proven | overpaying for theoretical automation upside |

### Default founder rule

Do not acquire merely because acquisition is possible.

Prefer the **least capital-intensive structure that lets you test the value-creation thesis with real production evidence**.

A partnership that proves a 20-point gross-margin improvement is often more informative than a spreadsheet that assumes a 40-point improvement after acquisition.

---

## 2. Screen targets for agent-operability

Score each factor from 1–5.

| Factor | 1 | 5 |
|---|---|---|
| Recurring / repeat revenue | mostly one-off | highly recurring or repeat purchase |
| Workflow frequency | sporadic | daily, high-volume |
| Digital inputs | mostly physical/unstructured/offline | reliably digital and accessible |
| Process observability | undocumented | measured with timestamps, owners, outcomes |
| Labor intensity | little workflow labor | substantial repeatable labor |
| Exception rate | most cases bespoke | majority follows stable paths |
| Automation headroom | already optimized | obvious manual queues/handoffs |
| Data / contract rights | unclear/restricted | clearly usable for intended workflow |
| Customer concentration | one/few customers dominate | diversified |
| Switching / retention | low retention | sticky, embedded workflow |
| Integration tractability | fragmented inaccessible systems | accessible APIs/exports/automation surfaces |
| Domain risk | highly consequential / regulated | bounded operational work |
| Key-person dependency | founder knowledge is undocumented | knowledge distributed/documented |
| Margin visibility | weak job costing | contribution economics reconstructable |

**70 points max.**

Use score bands as a diligence aid, not a valuation model:

- **56–70:** strong candidate for deeper diligence,
- **45–55:** plausible, but identify the exact limiting factors,
- **below 45:** do not assume agents will repair a structurally weak business.

### Automatic rejection flags

Pause or reject the thesis when:

- customer retention depends mainly on one owner or rainmaker,
- critical workflows cannot be observed before the deal,
- customer contracts forbid or materially constrain the intended delivery changes,
- required data rights are unclear,
- automation economics depend on eliminating nearly all human review,
- service quality is highly bespoke but modeled as standardized,
- the acquisition only works under an untested future-margin assumption,
- one platform, vendor, employee, or customer can break the economics,
- the target has weak underlying demand and automation is being used to disguise it.

---

## 3. Build the AI value-creation map

Do not reduce the thesis to labor savings.

For each workflow, classify potential value into five buckets.

### A. Cost reduction

Examples:

- lower handling time,
- fewer manual reconciliations,
- lower rework,
- fewer duplicate touches,
- reduced external processing expense.

### B. Throughput expansion

Examples:

- more customers onboarded per operator,
- more cases processed per day,
- shorter backlog,
- more proposals submitted,
- faster month-end or reporting cycle.

### C. Revenue lift

Examples:

- faster lead follow-up,
- better renewal coverage,
- improved upsell detection,
- faster quote turnaround,
- fewer abandoned customer requests.

### D. Working-capital improvement

Examples:

- faster invoicing,
- lower days-sales-outstanding,
- quicker dispute resolution,
- better collections prioritization,
- reduced billing leakage.

### E. New agent-native products

Examples:

- always-on client reporting,
- paid monitoring,
- instant research or analysis add-ons,
- self-service customer workflows,
- API-accessible versions of an existing service.

### Portfolio rule

A resilient thesis usually has **at least two value buckets**.

A deal whose entire upside is "fewer employees" is fragile. A deal that can improve throughput, cash conversion, customer experience, and launch new services has more ways to win.

---

## 4. Diligence the workflow, not just the financial statements

Traditional diligence asks whether the historical business is real.

Agent-operability diligence also asks whether the **future workflow thesis is real**.

For every material workflow, reconstruct:

| Field | Question |
|---|---|
| Trigger | What starts the work? |
| Volume | How many cases per day/week/month? |
| Inputs | What data/documents/messages are required? |
| Systems | Which applications, inboxes, portals, spreadsheets, APIs? |
| Labor | Who touches it, for how long, at what cost? |
| Exceptions | What share cannot follow the standard path? |
| Authority | Which actions are reversible vs consequential? |
| Quality | How is correct completion judged today? |
| SLA | What latency/availability does the customer expect? |
| Rework | How often does work come back? |
| Dependencies | Which third parties can block completion? |
| Data rights | Can inputs be used for the intended processing? |
| Customer promise | What has actually been contracted? |
| Margin | Revenue and fully loaded cost per successful outcome? |

### Minimum evidence pack

Before underwriting automation upside, obtain enough evidence to estimate:

```text
monthly workflow volume
× current successful-completion rate
× current labor minutes per case
× current exception rate
× rework rate
× cost per completed outcome
```

Then compare the proposed agent workflow against that baseline using `docs/AGENT_WORKFLOW_ROI.md`.

Do not value hypothetical savings from a workflow you have not observed.

---

## 5. Preserve the operating knowledge before changing the work

Small service businesses often store critical operating knowledge in people, not systems.

Before aggressive automation:

1. identify the top domain experts,
2. record workflow walkthroughs,
3. collect representative normal and exception cases,
4. map escalation logic,
5. capture customer-specific constraints,
6. document judgment calls that cannot yet be safely automated,
7. define what quality failures look like,
8. identify knowledge that cannot be placed into an agent system for legal, privacy, contractual, or competitive reasons.

### Knowledge-retention metric

Track:

```text
critical workflow decisions with documented decision logic
----------------------------------------------------------
all recurring critical workflow decisions identified
```

Do not let key operators leave before the denominator is understood.

---

## 6. Run a pre-close or pre-commitment proof plan

Where access and transaction structure permit, identify two or three bounded workflows that can be tested without assuming full ownership or broad production authority.

Good proof candidates:

- frequent,
- measurable,
- reversible,
- digitally observable,
- low-regret if the test fails,
- economically meaningful.

### Proof ladder

```text
historical replay
-> shadow mode
-> human-approved production suggestions
-> bounded production subset
-> measured expansion
```

For each proof, define:

- baseline period,
- representative sample,
- target outcome,
- acceptance threshold,
- human-review requirement,
- cost per successful outcome,
- failure taxonomy,
- stop condition.

Do not convert a demo accuracy number into an acquisition underwriting assumption.

---

## 7. Build the acquisition-economics bridge

Keep **existing business value** separate from **agent-enabled upside**.

A useful bridge is:

```text
existing normalized operating profit
+ measured throughput contribution
+ measured revenue-lift contribution
+ measured working-capital benefit
+ measured cost reduction
+ contribution from validated new products
- incremental model/tool/data cost
- implementation and integration cost
- human review and exception handling
- additional support / reliability / compliance cost
- transition and retraining cost
= agent-enabled operating contribution
```

### Do not capitalize unproven savings as if already achieved

Track three columns:

| Value source | Current / observed | Proven in pilot | Underwriting hypothesis |
|---|---:|---:|---:|
| Labor efficiency |  |  |  |
| Throughput |  |  |  |
| Revenue lift |  |  |  |
| Working capital |  |  |  |
| New products |  |  |  |

The distinction prevents a plausible automation story from silently becoming the purchase price.

### Payback view

For incremental transformation spend:

```text
payback months = implementation investment / monthly incremental contribution
```

For an acquisition, do **not** pretend this simple equation replaces a proper transaction/financing valuation. Use it only to isolate the transformation layer from the base-business economics.

---

## 8. First 100 days: instrument before optimizing

### Days 0–30 — Observe and stabilize

Priorities:

- retain critical operators,
- validate customer/service commitments,
- instrument workflow volumes and outcomes,
- establish baseline cost and quality,
- map access and data rights,
- identify unstable processes,
- stop undocumented automation already causing risk,
- choose 2–3 high-confidence workflows.

Output:

> a measured operating baseline, not a transformation announcement.

### Days 31–60 — Shadow and assist

Priorities:

- replay historical cases,
- run agents in shadow mode,
- compare recommendations to real outcomes,
- create exception taxonomies,
- estimate review capacity,
- remove obvious non-AI bottlenecks,
- retrain operators for review/escalation roles,
- test customer-visible quality before customer-visible autonomy.

Output:

> evidence of where agents help, fail, and create review load.

### Days 61–100 — Bounded production

Priorities:

- activate only proven workflow slices,
- impose exposure caps,
- preserve rollback,
- monitor defect escape and rework,
- measure cost per successful outcome,
- compare actual contribution against thesis,
- communicate material customer changes,
- decide which workflows expand, pause, or revert.

Output:

> measured production contribution, not theoretical automation percentage.

---

## 9. Redesign the workforce around judgment, not just headcount

Agent-enabled operating leverage can change staffing needs, but the first operational question should be:

> Where does scarce human judgment create the most value after routine work is automated?

Track:

- review minutes per successful outcome,
- exception volume per operator,
- escalation resolution time,
- domain-expert utilization,
- retraining/redeployment rate,
- knowledge-loss incidents,
- quality after staffing changes.

Potential role shifts:

```text
processor -> exception resolver
coordinator -> workflow operator
manager -> quality / capacity manager
subject-matter expert -> policy + escalation owner
analyst -> customer-facing advisor
```

A model that requires hidden human review is not automated simply because the customer cannot see the humans.

---

## 10. Three target archetypes

These are research directions, not recommendations to transact.

### Archetype A — Bookkeeping / accounting operations

Potential workflow map:

- document intake,
- categorization suggestions,
- reconciliations,
- close checklists,
- anomaly review,
- client information requests,
- recurring reporting.

Why potentially attractive:

- recurring workflows,
- high document/data volume,
- measurable cycle time,
- strong opportunity for throughput and client-service expansion.

What can break the thesis:

- poor source data,
- fragmented client systems,
- professional judgment treated as routine processing,
- privacy/security obligations,
- seasonal capacity incorrectly modeled as steady state.

First proof metric:

```text
review-adjusted minutes per correctly completed reconciliation
```

### Archetype B — Property-management back office

Potential workflow map:

- maintenance intake and routing,
- vendor coordination,
- resident communications,
- invoice/document handling,
- lease/admin workflow support,
- owner reporting.

Why potentially attractive:

- repetitive coordination work,
- many handoffs,
- response speed matters,
- recurring customer relationships.

What can break the thesis:

- emergency/safety cases mixed with routine cases,
- poor vendor-system integration,
- local/regulatory differences,
- automation degrading resident trust.

First proof metric:

```text
median time from routine request intake to correctly routed next action
```

### Archetype C — B2B administrative / compliance services

Potential workflow map:

- evidence collection,
- recurring customer requests,
- document completeness checks,
- deadline tracking,
- status reporting,
- bounded research and preparation.

Why potentially attractive:

- repeatable recurring work,
- costly coordination,
- strong retention when embedded,
- possible managed-outcome pricing.

What can break the thesis:

- regulated interpretation hidden inside "administrative" work,
- unclear customer-data rights,
- stale rules,
- inaccurate output carrying disproportionate downside.

First proof metric:

```text
cost and elapsed time per correctly completed bounded administrative outcome
```

---

## 11. Buy vs partner vs build decision

Score each dimension 1–5 for the opportunity.

| Dimension | Favors build | Favors partner | Favors acquire |
|---|---|---|---|
| Customer acquisition | cheap | incumbent has access | distribution is scarce/valuable |
| Workflow knowledge | already known | shared knowledge needed | embedded tacit knowledge matters |
| Capital | scarce | moderate | available and justified |
| Integration control | not important | negotiable | deep control required |
| Brand / licenses | unnecessary | can leverage partner | difficult to recreate |
| Speed to revenue | can sell quickly | partner accelerates | acquired book is valuable |
| Automation proof | strong already | needs live test | proven + business itself attractive |

### Simple decision heuristic

**Build** when customer access and domain knowledge are cheap.

**Partner** when workflow access is the scarce asset but full ownership is unnecessary.

**Acquire** only when the base business is attractive enough that you would still respect owning it if the automation upside arrives slower than expected.

---

## 12. The transformation scorecard

At minimum, review monthly:

### Customer

- retention / churn,
- SLA attainment,
- complaint rate,
- customer-visible defect rate,
- time to first response / completion.

### Workflow

- volume,
- successful completion rate,
- straight-through automation rate,
- human-review rate,
- exception rate,
- rework rate,
- defect escape rate.

### Economics

- revenue per successful outcome,
- fully loaded cost per successful outcome,
- gross contribution,
- implementation spend,
- incremental contribution versus baseline,
- working-capital changes.

### People

- review load,
- overtime / capacity stress,
- redeployment / retraining,
- key-person concentration,
- knowledge capture progress.

### Technology

- model/tool cost,
- integration failure rate,
- dependency outages,
- rollback count,
- agent-caused incident count.

A rising automation percentage with falling retention is not success.

---

## 13. Failure modes worth rehearsing

1. **Automation-premium overpayment** — price assumes savings not yet demonstrated.
2. **Key-person evaporation** — critical operators leave before tacit workflow knowledge is captured.
3. **Customer-trust break** — delivery changes without adequate communication or quality proof.
4. **Rights assumption** — acquired data/contracts do not permit the intended AI use.
5. **Hidden review factory** — agent output shifts work into invisible human QA rather than removing it.
6. **Exception blindness** — the easy 70% is automated while the costly 30% grows.
7. **System-fragmentation drag** — integration work consumes the expected savings.
8. **Quality arbitrage** — faster/cheaper work damages the feature customers actually paid for.
9. **Revenue thesis ignored** — team focuses only on cost reduction and misses throughput/new-product upside.
10. **Premature workforce cuts** — capacity is removed before production behavior and seasonality are understood.
11. **One-model dependency** — economics fail when provider cost, latency, availability, or capability changes.
12. **Weak underlying business** — automation improves unit cost but cannot repair poor demand or retention.

---

## 14. Founder operating sequence

Use this sequence to avoid underwriting the story before proving the work:

```text
screen the business
-> choose build / partner / acquire path
-> reconstruct workflow economics
-> verify data + contract + system access
-> preserve tacit operating knowledge
-> select bounded proof workflows
-> establish historical baseline
-> shadow / replay
-> measure review-adjusted production economics
-> activate bounded production
-> compare actual contribution with thesis
-> expand only proven workflow slices
-> launch revenue / new-product plays after service quality is stable
```

The best acquire-and-automate opportunity is not the business with the most employees.

It is the business where **durable demand + observable repetitive workflows + usable data + strong customer relationships + bounded agent leverage** combine to create measurable enterprise value.