# Agent Insurance, Warranties, Guarantees & Risk Transfer

Autonomous agents create a new commercial problem: they can take useful actions at machine speed, but some of those actions can also create losses at machine speed.

A founder should not respond by promising perfection or by pushing every risk onto the customer. The better operating model is to **identify, bound, price, retain, reserve for, transfer, and evidence risk explicitly**.

This guide is educational and system-design focused. Insurance placement, policy interpretation, regulated insurance activity, indemnity drafting, and jurisdiction-specific legal advice should be handled with qualified insurance and legal professionals.

## 1. Start with the loss, not the policy

Before thinking about insurance products, define how the agent can create economic harm.

For each paid workflow, write down:

- the action the agent is allowed to take,
- the maximum economic authority attached to that action,
- the direct loss if the action is wrong,
- consequential loss that could follow,
- whether the action can be reversed,
- how quickly the failure can be detected,
- what evidence would prove what happened,
- who contractually bears the loss,
- what controls reduce probability or severity,
- and what residual risk remains after controls.

A useful risk record is:

```text
Risk event
+ probability
+ severity
+ detectability
+ reversibility
+ recovery cost
+ legal allocation
+ control effectiveness
= residual exposure
```

Do not treat all failures as equal. A bad draft is not the same as a mistaken refund, unauthorized payment, production deletion, compliance filing, or physical-world action.

## 2. Build an agent-loss taxonomy

At minimum, separate these categories.

### Model risk

Examples:

- hallucinated facts,
- incorrect classification,
- missed constraints,
- unsafe planning,
- brittle reasoning under edge cases.

### Tool and action risk

Examples:

- duplicate side effects,
- wrong API target,
- excessive permissions,
- unintended deletion,
- unauthorized transaction,
- irreversible external commitment.

### Data risk

Examples:

- stale information,
- wrong tenant data,
- provenance loss,
- permission leakage,
- licensed data used outside permitted scope.

### Counterparty risk

Examples:

- supplier non-performance,
- fraudulent agent identity,
- disputed delivery,
- payment reversal,
- marketplace manipulation.

### Operational risk

Examples:

- queue overload,
- failed retries,
- provider outage,
- incomplete handoff,
- missed deadline,
- broken rollback.

### Security risk

Examples:

- prompt injection,
- credential theft,
- malicious tool output,
- compromised dependency,
- privilege escalation.

### Financial risk

Examples:

- runaway spend,
- duplicate charge,
- incorrect refund,
- treasury concentration,
- FX or settlement mismatch.

### Regulatory and legal risk

Examples:

- prohibited automated decision,
- missing disclosure,
- unapproved regulated action,
- privacy violation,
- IP infringement,
- contractual breach.

A founder should map each material workflow to one or more categories before setting guarantees or liability terms.

## 3. Quantify expected loss per successful outcome

The core risk metric should be attached to the business unit that earns revenue.

A simple expected-loss model is:

```text
Expected loss per outcome
= sum(probability of event i × net severity of event i)
```

Net severity should include:

- customer reimbursement,
- remediation labor,
- replacement service cost,
- service credits,
- dispute cost,
- fraud loss,
- incident-response cost,
- and any uninsured retained loss.

For low-frequency, high-severity events, expected value alone is not enough. Track tail exposure too.

Useful measures include:

- maximum plausible loss per action,
- maximum loss per customer,
- maximum daily fleet exposure,
- 95th/99th percentile loss,
- correlated loss across shared models or providers,
- and cash required to survive a severe incident.

## 4. Separate frequency risk from severity risk

Frequent small errors and rare catastrophic errors require different controls.

### Frequency risk

Examples:

- small billing disputes,
- support SLA misses,
- minor incorrect outputs,
- low-value rework.

These may be handled with:

- pricing margin,
- service credits,
- operational reserves,
- automated remediation,
- and product-level quality improvement.

### Severity risk

Examples:

- large unauthorized transfers,
- broad data exposure,
- high-value irreversible purchases,
- regulated action errors,
- systemic agent-fleet compromise.

These require stronger tools:

- hard authority limits,
- human approval,
- separation of duties,
- contractual caps,
- dedicated reserves,
- escrow or holdbacks,
- and potentially third-party insurance.

Do not use a generous refund policy as a substitute for controlling catastrophic authority.

## 5. Create a retained-risk policy

Not every risk should be transferred.

A company can intentionally retain risk when:

- the loss is small and frequent,
- the company has enough data to estimate it,
- mitigation is cheaper than insurance,
- the company can absorb the loss without threatening runway,
- or transferring it creates too much friction.

Define explicit retained-risk limits:

```text
Per action retained limit
Per customer retained limit
Per day retained limit
Per incident retained limit
Aggregate monthly retained limit
Minimum cash reserve
```

When limits are exceeded, the system should automatically reduce authority, require approval, pause the workflow, or route the risk elsewhere.

## 6. Reserve for risk like a real operating cost

A guarantee is not free because claims have not happened yet.

Reserve expected losses alongside other delivery costs.

Example:

```text
Revenue per successful outcome        $100
Model/tool/data cost                   $18
Human review                            $7
Support and operations                  $5
Expected guarantee loss                 $3
Insurance / risk-transfer allocation    $2
Contribution before fixed cost         $65
```

If expected loss is omitted, a seemingly profitable agent business can become unprofitable the moment real claims arrive.

Reserve policy should connect directly to treasury and runway planning.

## 7. Use a risk ladder instead of one blanket promise

Commercial commitments can be layered.

From lowest to highest risk transfer:

1. best-effort service,
2. operational remediation,
3. service credit,
4. refund,
5. limited warranty,
6. performance guarantee,
7. outcome guarantee,
8. indemnity for defined harms,
9. third-party insurance-backed obligation.

Move upward only when the business can measure and price the exposure.

## 8. Design warranties around controllable facts

A warranty should promise something the company can actually verify.

Better warranty subjects:

- the service will execute within stated scope,
- specified controls are enabled,
- requests are processed within a time window,
- outputs are generated from designated sources,
- the system will not exceed a defined authority limit,
- the provider will remediate a documented failure under defined conditions.

Weaker warranty subjects:

- “the agent will always be correct,”
- “the customer will never lose money,”
- “the system is safe,”
- “the model cannot hallucinate.”

Promise measurable system behavior rather than impossible certainty.

## 9. Service credits are not the same as refunds

Define the distinction clearly.

### Service credit

A future-value remedy, often useful for availability or response-time misses.

### Refund

Returns some or all of the purchase price for a failed delivery.

### Re-performance

Repeats the workflow at no charge.

### Reimbursement

Pays for a defined direct loss caused by the service.

### Indemnity

Allocates responsibility for specified third-party claims or categories of harm.

### Insurance proceeds

Transfer some defined loss to an insurer subject to policy terms.

Each mechanism has different economic and legal consequences.

## 10. Build guarantees from a coverage function

A useful guarantee can be modeled explicitly.

```text
Covered event
+ eligibility conditions
+ exclusions
+ maximum payout
+ evidence requirement
+ claim window
+ investigation process
+ remediation option
+ payment timing
```

For example:

```text
Covered event: duplicate autonomous vendor payment
Eligibility: payment created through approved workflow
Exclusion: customer manually bypassed approval controls
Maximum payout: lower of verified direct loss or $10,000
Evidence: signed execution trace + settlement record
Claim window: 30 days
Remediation: recovery attempted before payout
```

This is dramatically safer than “we guarantee every transaction.”

## 11. Price risk into the offer

Risk-bearing should be visible in unit economics.

A pricing floor can include:

```text
Delivery cost
+ support cost
+ expected loss
+ reserve contribution
+ insurance premium allocation
+ capital charge
+ target contribution margin
= minimum sustainable price
```

Higher-risk authority should usually cost more.

Possible pricing dimensions:

- maximum transaction authority,
- workflow criticality,
- data sensitivity,
- reversibility,
- claim limit,
- response SLA,
- guaranteed outcome level,
- customer risk history,
- deployment controls.

This creates a natural link between stronger controls and lower price.

## 12. Offer risk tiers

Example structure:

| Tier | Agent authority | Human review | Commercial commitment |
|---|---|---|---|
| Observe | read-only | optional | best effort |
| Assist | drafts actions | approval required | remediation |
| Execute | low-value actions | sampled | service credits/refunds |
| Trusted | higher bounded authority | exception-based | limited warranty |
| Guaranteed | narrowly defined high-value workflow | risk-based | explicit outcome guarantee |

Avoid letting a customer buy more autonomy without also buying the controls needed to support it.

## 13. Use authority limits as underwriting inputs

Insurance and guarantees should care about what the agent can actually do.

Track:

- per-action monetary authority,
- cumulative daily authority,
- write/delete privileges,
- systems reachable,
- data classifications reachable,
- external commitment authority,
- ability to create new credentials,
- ability to delegate to other agents.

A $500 refund agent and a $5 million treasury agent should not have the same risk price.

## 14. Build an evidence packet for underwriters and enterprise buyers

A strong risk-evidence packet can include:

### System scope

- supported workflows,
- authority boundaries,
- deployment architecture,
- model/provider dependencies.

### Control evidence

- approval rules,
- deterministic policy gates,
- secret isolation,
- rate limits,
- kill switches,
- rollback design.

### Evaluation evidence

- task success rates,
- harmful action rates,
- prompt-injection evals,
- semantic regression evals,
- human-review results.

### Runtime evidence

- incident history,
- near misses,
- error rates,
- traces,
- recovery time,
- provider failure behavior.

### Financial evidence

- transaction limits,
- historical losses,
- reserve policy,
- concentration exposure,
- claim history.

### Governance evidence

- change management,
- permission reviews,
- reviewer separation of duties,
- incident response ownership.

The same evidence that makes an agent safer can make it easier to sell, insure, or guarantee.

## 15. Preserve claim-grade provenance

A claim or dispute should be reconstructable without relying on model memory.

Persist:

- customer instruction,
- policy and contract version,
- agent/model version,
- permissions at execution time,
- relevant retrieved sources,
- tool requests and responses,
- approvals,
- timestamps,
- resulting side effects,
- settlement records,
- remediation attempts.

Where appropriate, protect integrity with append-only logs, hashes, signatures, or equivalent controls.

Do not silently edit historical evidence after an incident.

## 16. Define the claims workflow before launch

A simple lifecycle:

```text
Notice -> Eligibility -> Evidence -> Investigation -> Recovery -> Decision -> Payment/Credit -> Root cause -> Control update
```

Define owners and deadlines for each stage.

Claims should feed back into:

- eval suites,
- model routing,
- permission limits,
- pricing,
- reserve assumptions,
- underwriting evidence,
- customer risk tiers.

A claim is operational training data, not only a support ticket.

## 17. Prevent guarantee fraud and moral hazard

Guarantees change behavior.

Potential abuse:

- customer intentionally creates a covered failure,
- buyer disables controls then claims a loss,
- supplier and buyer collude,
- repeated low-value claims exploit automatic payouts,
- fake identities create claim farms,
- a user takes larger risks because downside is transferred.

Controls can include:

- eligibility tied to approved workflow state,
- identity and reputation requirements,
- proof of actual settlement or loss,
- deductibles or co-insurance,
- rate limits,
- anomaly detection,
- claim concentration monitoring,
- manual review above thresholds.

The goal is not to make claims difficult. It is to keep the guarantee economically honest.

## 18. Watch correlated risk across the fleet

Agent failures are often not independent.

A single shared dependency can affect thousands of customers:

- model regression,
- tool-provider outage,
- compromised MCP server,
- faulty policy rollout,
- bad data source,
- cloud-region failure,
- prompt-injection campaign.

Track concentration by:

- model provider,
- tool provider,
- region,
- workflow type,
- customer vertical,
- shared prompt/policy version,
- external counterparty.

Risk that looks small per customer can become existential when correlated.

## 19. Stress-test tail scenarios

At least quarterly, simulate scenarios such as:

- a model update increases bad financial actions 10x,
- a shared credential is compromised,
- a payment retry bug duplicates 5% of transactions,
- the largest supplier fails during peak demand,
- a customer account is hijacked,
- a high-authority agent is prompt-injected,
- a regulator or enterprise buyer requires immediate suspension,
- an insurer disputes coverage after a major incident.

For each scenario ask:

- how is it detected,
- what stops propagation,
- what is the maximum loss before containment,
- how much cash is needed,
- what contractual obligations trigger,
- what evidence exists,
- and whether the company survives.

## 20. Use risk-adjusted margin

Gross margin alone can reward unsafe growth.

Track:

```text
Risk-adjusted contribution
= revenue
- delivery cost
- human review
- expected loss
- reserve contribution
- insurance / guarantee cost
- incident remediation
```

Then compare cohorts by:

- customer type,
- workflow,
- authority tier,
- model/provider,
- geography,
- guarantee level.

A high-revenue customer with extreme retained downside may be a worse customer than a smaller, well-controlled one.

## 21. Core metrics

Useful metrics include:

### Exposure

- authority dollars outstanding,
- maximum loss per action,
- maximum loss per customer,
- aggregate daily exposure,
- dependency concentration.

### Loss

- expected loss per successful outcome,
- claim frequency,
- claim severity,
- near-miss frequency,
- recovery rate,
- fraud rate.

### Reserves

- reserve coverage ratio,
- claims paid / reserves,
- reserve drawdown after incidents,
- months of runway after modeled tail loss.

### Guarantees

- guarantee attach rate,
- guarantee cost per outcome,
- payout ratio,
- margin by guarantee tier.

### Operations

- time to detect loss,
- time to contain,
- time to claim decision,
- time to recovery,
- evidence completeness rate.

## 22. Build a risk-adjusted customer score

A simple customer risk score can incorporate:

- authority requested,
- transaction size,
- workflow reversibility,
- data sensitivity,
- integration complexity,
- historical incidents,
- control adoption,
- fraud signals,
- concentration contribution.

Use the score to set:

- approval requirements,
- guarantee limits,
- pricing,
- reserve contribution,
- support level,
- deployment eligibility.

Do not use opaque automated risk scoring for regulated insurance or credit decisions without appropriate legal/regulatory review.

## 23. Decide when third-party insurance may help

Potential reasons to explore insurance with a qualified broker or insurer:

- enterprise contracts require specified coverage,
- a severe loss exceeds the company’s risk appetite,
- a class of losses is measurable and insurable,
- customers value an external balance sheet behind the promise,
- insurance improves procurement eligibility,
- concentrated tail risk cannot be self-funded safely.

But insurance does not replace:

- secure architecture,
- authority limits,
- incident response,
- good contracts,
- reserves,
- accurate disclosures.

A policy can fail to respond because of terms, exclusions, limits, retention, timing, or facts. Treat coverage as one layer, not the only layer.

## 24. Separate product guarantees from regulated insurance activity

Founders can easily cross boundaries unintentionally.

A product warranty, refund promise, service credit, contractual indemnity, insurance policy, risk pool, guarantee marketplace, and surety arrangement may be treated very differently under law and regulation.

Before marketing a risk-transfer product:

- identify the legal structure,
- identify who bears risk,
- identify whether risk is pooled,
- identify whether premium-like consideration is collected,
- identify licensing requirements,
- identify required disclosures,
- and obtain qualified advice.

Do not call something “insurance” merely because it compensates loss.

## 25. Agent-to-agent risk transfer

Machine commerce creates a future pattern where one agent may refuse to transact unless another agent provides machine-verifiable assurance.

A machine-readable assurance object could include:

```json
{
  "provider": "example-agent",
  "capability": "invoice-payment",
  "max_authority": 5000,
  "guarantee": {
    "covered_event": "duplicate_payment",
    "limit": 5000,
    "claim_window_days": 30
  },
  "evidence": {
    "eval_version": "2026-08",
    "incident_rate_90d": 0.0008,
    "audit_log": true
  }
}
```

Possible future transaction logic:

```text
Discover capability
-> verify identity
-> inspect authority
-> inspect reputation
-> inspect assurance
-> compare expected value
-> transact
-> preserve evidence
```

This turns risk into part of market matching rather than a post-incident surprise.

## 26. Business opportunities

Risk transfer itself can become agent infrastructure.

Potential businesses include:

### Agent underwriting data

Normalize execution traces, controls, incidents, and authority into risk evidence for insurers and enterprise buyers.

### Guarantee infrastructure

APIs for attaching bounded commercial guarantees to agent outcomes.

### Embedded risk transfer

Let agent marketplaces or payment rails offer optional risk protection at transaction time through properly regulated partners.

### Claims automation

Evidence collection, eligibility checks, recovery workflows, and claims reconciliation for agent-caused incidents.

### Agent risk scoring

Independent scoring based on authority, control maturity, incident history, evals, and dependency concentration.

### Warranty operations

Infrastructure for product warranties, refunds, service credits, payout limits, and reserve accounting.

### Risk marketplaces

Platforms that connect well-instrumented agent workloads with insurers, reinsurers, guarantors, or other regulated risk-capital providers.

### Control-to-price optimization

Systems that show founders which security, eval, authority, or runtime improvements reduce expected loss enough to justify their cost.

## 27. A founder launch checklist

Before offering a material guarantee:

- [ ] List material failure modes.
- [ ] Quantify maximum authority per action.
- [ ] Estimate expected loss per successful outcome.
- [ ] Model a plausible tail-loss scenario.
- [ ] Define retained-risk limits.
- [ ] Set a reserve floor.
- [ ] Define exactly what is covered.
- [ ] Define exclusions and eligibility conditions.
- [ ] Set a payout or liability limit.
- [ ] Preserve claim-grade execution evidence.
- [ ] Define claim notice and investigation workflow.
- [ ] Add fraud and moral-hazard controls.
- [ ] Track correlated dependency exposure.
- [ ] Include risk cost in unit economics.
- [ ] Confirm guarantees do not exceed the company’s ability to pay.
- [ ] Get qualified legal/insurance advice where required.

## 28. Minimum viable risk-transfer operating system

A small agent business does not need an actuarial department on day one.

Start with:

1. a risk register for paid workflows,
2. deterministic authority limits,
3. an expected-loss estimate,
4. a simple reserve account or reserve policy,
5. bounded refund/warranty terms,
6. complete execution logs,
7. a claims and incident workflow,
8. monthly risk-adjusted margin review.

Add insurance, sophisticated models, risk tiers, and embedded guarantees only after exposure justifies the complexity.

## 29. Anti-patterns

Avoid:

- unlimited guarantees,
- vague “AI is insured” marketing,
- treating insurance as a substitute for controls,
- hiding exclusions from autonomous buyers,
- letting the agent decide its own claim eligibility,
- mixing mutable model memory with claim evidence,
- pricing without expected-loss attribution,
- assuming failures are independent across customers,
- offering high authority without higher controls,
- creating a pooled risk product without regulatory review,
- optimizing claim denial rate instead of legitimate-loss resolution.

## 30. Operating principle

**Trust becomes commercially durable when downside is bounded as explicitly as upside is sold.**

The strongest agent businesses will not promise that autonomous systems never fail. They will know what can fail, limit what a failure can cost, preserve evidence, price the residual risk, compensate customers predictably when defined failures occur, and transfer only the risks that make economic sense to transfer.