# Agent Fraud, Abuse, Chargebacks & Economic Integrity

Autonomous businesses can move money, discounts, inventory, reputation, referrals, supplier awards, refunds, and marketplace rank at machine speed. That makes **economic integrity** a first-class operating system, not a checkout feature.

The objective is not zero fraud. The objective is to keep expected loss, false-positive cost, review cost, and customer friction inside explicit bounds while preserving legitimate conversion.

```text
Intent -> Identity -> Authority -> Risk -> Decision -> Execution -> Evidence -> Settlement -> Feedback
```

Every material economic action should pass deterministic controls before a model-generated recommendation can become a real-world side effect.

## 1. Threat model the economic actions, not just the accounts

Start with the actions that can create or transfer value:

| Surface | Typical abuse | Primary control |
|---|---|---|
| Purchase | stolen credentials, unauthorized delegated spend | identity + authority + spend mandate |
| Payout | account takeover, payout rerouting | destination binding + step-up + hold |
| Refund | refund loops, refund-before-delivery, collusion | delivery evidence + velocity + approval tier |
| Credit | promotional abuse, duplicate compensation | eligibility + idempotency + lifetime caps |
| Referral | Sybil farms, self-referral, attribution hijack | graph linkage + beneficiary checks + delayed payout |
| Marketplace | wash trading, fake reviews, ranking manipulation | counterparty graph + verified outcomes + concentration limits |
| Procurement | collusive bidding, fake suppliers, bid steering | supplier identity + sealed criteria + separation of duties |
| Subscription | trial cycling, entitlement sharing | account linkage + entitlement policy + device/session signals |
| Withdrawal | mule accounts, rapid cash-out | source-of-funds evidence + velocity + settlement delay |
| Promotion | coupon stacking, synthetic identities | deterministic eligibility + campaign budget guardrails |

Do not create one opaque “fraud score” and treat it as sufficient. Different actions have different loss modes and different tolerances for friction.

## 2. Build a canonical economic action envelope

The repository includes:

- `schemas/economic-action-policy.schema.json`
- `templates/ECONOMIC_ACTION_POLICY.json`
- `scripts/validate_economic_integrity.py`

Use one policy record per action class or risk tier. The record should bind:

- the action being authorized,
- maximum monetary exposure,
- currency and settlement mode,
- identity requirements,
- authority requirements,
- deterministic velocity limits,
- risk thresholds,
- step-up and human-review requirements,
- payout/refund/withdrawal delays,
- evidence requirements,
- reserve treatment,
- and incident escalation.

The policy is an **execution control**, not a prompt. Store and enforce it outside model-visible free-form memory.

## 3. Separate risk signals by domain

A useful risk decision decomposes signals so operators can understand why an action was allowed, challenged, held, or denied.

### Identity risk

Examples:

- identity verification status,
- workload or agent identity attestation,
- account age,
- identity-document confidence,
- synthetic-identity indicators,
- beneficiary ownership evidence.

### Authority risk

Examples:

- valid delegated authority envelope,
- action scope,
- spend ceiling,
- beneficiary restrictions,
- geographic restrictions,
- expiry,
- revocation status,
- delegation-chain integrity.

Identity answers **who**. Authority answers **what this identity is allowed to do now**.

### Payment risk

Examples:

- credential provenance,
- tokenization status,
- payment-instrument age,
- prior dispute rate,
- card/account verification,
- settlement reversibility.

### Session and device risk

Examples:

- abrupt environment change,
- impossible travel,
- automation anomalies,
- compromised browser/session indicators,
- repeated account switching,
- high-risk network infrastructure.

Do not treat “looks like a bot” as automatically malicious. Legitimate agents are expected to automate. Score consistency, authorization, and economic behavior instead.

### Reputation risk

Examples:

- verified successful outcomes,
- dispute history,
- refund history,
- counterparty diversity,
- evidence freshness,
- reputation-source independence.

### Velocity risk

Examples:

- transactions per minute/hour/day,
- spend per rolling window,
- refunds per buyer/seller pair,
- new beneficiaries per day,
- referral rewards per identity cluster,
- withdrawals shortly after credits or sales.

### Counterparty and graph risk

Examples:

- shared payout destination,
- shared funding source,
- repeated buyer/seller pairs,
- dense referral rings,
- common infrastructure,
- circular trading patterns,
- concentration around one beneficiary.

### Behavioral risk

Examples:

- sudden strategy change,
- unusual order mix,
- repeated boundary testing,
- attempts just below approval thresholds,
- high cancellation/retry loops,
- anomalous negotiation behavior.

## 4. Use deterministic decision bands

Models can summarize evidence and recommend review, but high-risk economic side effects should resolve through deterministic bands.

A practical decision ladder:

```text
ALLOW
  low risk + inside authority + inside velocity limits

ALLOW_WITH_MONITORING
  moderate risk + reversible action + bounded exposure

STEP_UP
  missing confidence that can be resolved with stronger verification

HOLD
  action is plausible but needs delayed settlement or evidence

HUMAN_REVIEW
  material exposure, conflicting evidence, or policy exception

DENY
  invalid authority, prohibited action, replay, known abuse, or hard limit breach
```

The policy must define which band applies at each threshold. Avoid prompts such as “use good judgment for large refunds.”

## 5. Put hard limits around irreversible actions

At minimum, bound:

- single-transaction spend,
- aggregate daily spend,
- payouts to new destinations,
- refund amount and refund frequency,
- promotional credits,
- marketplace withdrawals,
- supplier prepayments,
- discount percentage,
- service credits,
- and manual override authority.

For irreversible or difficult-to-recover value transfers, require stronger evidence than for reversible actions.

## 6. Account takeover and credential compromise

Account takeover becomes more dangerous when a compromised agent can act continuously.

Controls should include:

1. short-lived credentials,
2. audience binding,
3. authority checks at action time,
4. destination-change cooling periods,
5. step-up verification for payout/bank changes,
6. revocation propagation,
7. anomaly detection on action patterns,
8. kill switches that stop economic execution independently of model state.

A valid session token is not sufficient evidence for a high-value payout.

## 7. Synthetic identity and Sybil abuse

Autonomous markets make identity creation cheap. Defend against one operator appearing as many independent actors.

Use layered evidence:

- verified beneficiary ownership,
- payment-instrument uniqueness,
- device/infrastructure linkage,
- account-creation bursts,
- shared contact or tax identity where legally appropriate,
- behavioral similarity,
- repeated trading/referral clusters,
- reputation earned from independent counterparties.

Do not rely on any one linkage signal as proof. Graph evidence is probabilistic and can create false positives.

## 8. Referral and promotion abuse

Referral programs are especially vulnerable to machine-speed farming.

Deterministic controls:

- prohibit self-referral where intended,
- delay rewards until the referred outcome is verified,
- cap rewards per beneficiary and identity cluster,
- block reward cycling through refunds,
- use unique attribution events,
- require net-positive contribution margin before payout,
- claw back rewards for reversed transactions,
- separately monitor organic and incentivized cohorts.

Measure fraud loss **and** legitimate customer loss from over-aggressive blocking.

## 9. Marketplace wash trading and reputation manipulation

A marketplace can look liquid while economically empty.

Detect:

- repeated reciprocal trades,
- circular transaction graphs,
- counterparties sharing beneficiaries,
- unusually concentrated review pairs,
- high GMV with low net cash movement,
- fast cancellation/rebook loops,
- identical delivery artifacts,
- reputation growth disconnected from independent buyer diversity.

Rank verified successful outcomes higher than raw transaction count. Reputation should decay or recertify when evidence becomes stale.

## 10. Procurement collusion and bid manipulation

Autonomous procurement can scale both efficiency and collusion risk.

Controls:

- define award criteria before bids are observed,
- separate bidder identity verification from ranking,
- retain versioned bid evidence,
- detect common ownership or payout destinations,
- monitor repeated winner/runner-up patterns,
- compare bids to external cost/reference bands,
- require human review for material single-source exceptions,
- preserve supplier substitution and challenge rights.

Do not let a purchasing agent rewrite its award criteria after seeing bids.

## 11. Refund and credit integrity

Refunds and credits are customer-success tools and attack surfaces.

Require a canonical refund decision to reference:

- original order/contract,
- payment/settlement record,
- delivery or acceptance evidence,
- refund reason,
- prior refunds/credits,
- current authority,
- applicable guarantee or policy version.

Example bands:

| Exposure | Default handling |
|---|---|
| low, first occurrence, verified failure | automatic |
| moderate, repeated customer issue | monitored or step-up |
| high, new payout destination, disputed evidence | hold + review |
| invalid contract/authority or replay | deny |

Never issue both a refund and equivalent service credit unless policy explicitly allows stacking.

## 12. Chargebacks and dispute evidence

Design for disputes before the first transaction.

Maintain an evidence bundle containing:

- buyer/seller identities,
- delegated authority reference,
- service contract/order version,
- pricing version,
- delivery receipt,
- acceptance status,
- communication evidence where legally appropriate,
- refund/credit history,
- settlement identifier,
- risk-decision version.

Keep evidence immutable or tamper-evident where feasible. Do not place sensitive payment credentials in dispute artifacts.

Track:

```text
chargeback_rate
fraud_chargeback_rate
win_rate
loss_amount
representment_cost
false_positive_declines
```

The decision to fight a dispute should consider expected recovery minus evidence/review cost.

## 13. Reserves, holds, and settlement delays

Expected fraud loss belongs in unit economics.

A simple framework:

```text
expected_fraud_loss
  = transaction_volume
  × fraud_probability
  × loss_given_fraud
```

Then include:

```text
risk_adjusted_contribution_margin
  = gross_margin
  - expected_fraud_loss
  - dispute_cost
  - review_cost
  - verification_cost
  - reserve_cost
```

Use reserves or settlement holds when losses may emerge after value leaves the system.

Reserve policy may depend on:

- seller tenure,
- dispute rate,
- product/service reversibility,
- delivery latency,
- transaction concentration,
- counterparty diversity,
- verified identity strength,
- abrupt volume changes.

Avoid indefinite holds without clear policy and escalation paths.

## 14. Risk scoring without black-box governance

A model or ML system can contribute a risk signal, but operators need interpretable action policy.

Recommended structure:

```text
risk_features -> domain scores -> deterministic policy -> action decision
```

Example domain scores:

```json
{
  "identity": 0.08,
  "authority": 0.00,
  "payment": 0.12,
  "velocity": 0.42,
  "counterparty": 0.61,
  "behavior": 0.18
}
```

Do not collapse everything into one score if different domains trigger different remediation. High authority risk should usually deny or step-up even if the overall weighted score looks low.

## 15. Step-up verification

Step-up should answer a specific uncertainty.

Examples:

- re-authenticate the principal,
- verify a new payout destination,
- require buyer confirmation above a spend threshold,
- request additional supplier ownership evidence,
- require a second approver,
- hold settlement until delivery evidence arrives.

Do not add generic friction if it does not reduce the risk that triggered the challenge.

## 16. Human review as a scarce control resource

Review queues should be risk-weighted.

Prioritize by:

```text
expected_loss_avoided - review_cost - customer_delay_cost
```

Reviewers need a compact evidence packet, not raw logs.

Include:

- proposed action,
- exposure,
- policy band,
- triggered rules,
- relevant domain scores,
- authority evidence,
- counterparty history,
- decision deadline,
- safe alternatives.

Track reviewer disagreement and rubber-stamping.

## 17. Feedback loops and labels

Fraud systems fail when labels are delayed, contaminated, or ambiguous.

Separate outcomes such as:

- confirmed fraud,
- suspected fraud,
- policy abuse,
- account takeover,
- customer dispute,
- merchant/service failure,
- friendly fraud,
- false positive,
- unresolved.

Do not train future risk models on “chargeback = fraud.” Many disputes reflect service or policy failures.

## 18. False-positive economics

Every prevention rule has a conversion cost.

Track:

```text
blocked_legitimate_value
step_up_abandonment_rate
review_delay_cost
false_positive_rate
fraud_loss_prevented
net_risk_value
```

A rule that prevents $10,000 of fraud but blocks $50,000 of good contribution margin is not successful.

## 19. Observability and SLOs

Core metrics:

### Loss

- gross fraud loss,
- net fraud loss after recoveries,
- fraud basis points of volume,
- chargeback rate,
- refund abuse rate,
- promotion/referral abuse cost.

### Control quality

- approval rate,
- challenge rate,
- review rate,
- false-positive rate,
- false-negative rate where measurable,
- time to risk decision,
- time to revoke compromised authority.

### Market integrity

- buyer/seller concentration,
- independent counterparty diversity,
- wash-trade indicators,
- reputation concentration,
- collusion alerts,
- linked-account clusters.

### Operations

- review queue depth,
- review SLA breaches,
- evidence completeness,
- policy-version drift,
- reserve coverage.

## 20. Incident response

Economic incidents need a money-first containment sequence.

```text
1. stop or narrow economic authority
2. freeze affected payouts/withdrawals where legally permitted
3. revoke compromised credentials
4. preserve evidence
5. identify linked accounts/counterparties
6. bound maximum exposure
7. notify payment/marketplace partners as required
8. remediate affected customers
9. update rules/models
10. run post-incident loss attribution
```

Do not destroy suspicious accounts or evidence before legal, dispute, and recovery needs are considered.

## 21. Failure-mode evals

Run economic-integrity evals before increasing autonomous spend or payout limits.

### Eval 1 — Replayed purchase

Replay a previously successful transaction request with the same idempotency key.

**Pass:** no duplicate charge or entitlement.

### Eval 2 — Compromised credential

Use a valid credential outside its intended audience or authority scope.

**Pass:** action is denied despite credential validity.

### Eval 3 — Threshold probing

Submit repeated actions just below review limits.

**Pass:** rolling velocity/aggregate exposure triggers control.

### Eval 4 — Refund loop

Purchase, consume value, refund, then repeat across linked accounts.

**Pass:** linkage and lifetime policy stop scalable extraction.

### Eval 5 — Sybil referral ring

Create multiple identities sharing beneficiaries/infrastructure and refer them to one another.

**Pass:** rewards are held or denied pending independent evidence.

### Eval 6 — Wash trading

Generate reciprocal marketplace trades to inflate reputation.

**Pass:** rank/reputation does not materially improve from self-linked trade.

### Eval 7 — Collusive bids

Submit supplier bids from commonly controlled entities with coordinated pricing.

**Pass:** ownership/linkage evidence triggers review and award criteria remain immutable.

### Eval 8 — Payout destination swap

Change payout destination immediately before a large withdrawal.

**Pass:** cooling period or step-up prevents immediate cash-out.

### Eval 9 — Fake delivery

Provide malformed or duplicated delivery evidence.

**Pass:** acceptance, payout, and billing remain blocked.

### Eval 10 — Friendly-fraud dispute

Submit a dispute where delivery and acceptance evidence exist.

**Pass:** evidence bundle is reconstructable without exposing secrets.

### Eval 11 — Risk-model degradation

Inject a risk-model outage or stale score.

**Pass:** system falls back to deterministic conservative policy rather than silently allowing.

### Eval 12 — Review overload

Flood the review queue with borderline actions.

**Pass:** high-exposure cases retain priority and economic execution does not fail open.

## 22. Policy rollout

Treat fraud-policy changes like production releases.

Use:

1. shadow evaluation,
2. historical replay,
3. segmented rollout,
4. false-positive guardrails,
5. rollback criteria,
6. policy-version logging.

Never silently change thresholds that alter material customer or seller outcomes without traceability.

## 23. Cross-border and legal considerations

Fraud, identity, payments, credit, sanctions, privacy, and consumer-protection requirements vary by jurisdiction and business model.

Before collecting or acting on identity/device/network signals:

- establish a lawful basis,
- minimize data,
- document retention,
- control access,
- evaluate discrimination/fairness risk,
- provide required customer notices and dispute rights,
- confirm whether holds, reserves, or delayed payouts are contractually and legally permitted.

This guide is an operating framework, not legal advice.

## 24. Business opportunities

Agent-native economic integrity creates businesses beyond conventional fraud APIs:

### Agent transaction risk API

Score action-specific risk with explicit identity, authority, velocity, and counterparty dimensions.

### Economic policy engine

Compile machine-readable authority and risk policy into deterministic allow/challenge/hold/review/deny decisions.

### Agent graph intelligence

Detect Sybil clusters, shared beneficiaries, wash trading, and collusive agent behavior across marketplaces.

### Dispute evidence automation

Assemble contract, authority, delivery, acceptance, and settlement evidence into claim-grade bundles.

### Agent marketplace trust network

Provide portable, evidence-backed reputation and economic abuse signals with freshness and provenance.

### Revenue assurance + fraud convergence

Unify duplicate charging, refund abuse, promotion leakage, and settlement anomalies into one financial-control layer.

### Autonomous procurement integrity

Detect supplier ownership linkage, collusion, bid steering, and anomalous awards.

## 25. Minimum production checklist

Before an autonomous business lets an agent move meaningful value:

- [ ] list every economic action and maximum exposure
- [ ] bind each action to current identity and authority
- [ ] define hard spend/refund/payout/credit limits
- [ ] define rolling velocity limits
- [ ] define step-up and review thresholds
- [ ] define settlement holds and reserve policy
- [ ] create dispute-grade evidence references
- [ ] measure false positives and conversion loss
- [ ] run coordinated multi-agent abuse evals
- [ ] test credential compromise and replay
- [ ] test risk-system failure behavior
- [ ] provide independent kill switches
- [ ] version every material policy change

## 26. Reference signals

The agent-commerce environment is moving toward explicit identity, authorization, controls, and machine-speed settlement. Useful current references include:

- Experian Agent Trust (April 30, 2026): human-to-agent binding, agent registry, and real-time transaction risk — https://www.experianplc.com/newsroom/press-releases/2026/experian-announces-agent-trust-to-power-trusted-ai-driven-commer
- Mastercard Agent Pay for Machines (June 10, 2026): permissioned, orchestrated machine-speed payments with credentialing and controls — https://www.mastercard.com/us/en/news-and-trends/press/2026/june/mastercard-launches-agent-pay-for-machines.html
- Akamai 2026 commerce research: agent hijacking, synthetic identity, signal masking, and the need to distinguish legitimate agent traffic from malicious automation — https://www.akamai.com/newsroom/press-release/akamai-research-commerce-becomes-the-epenter-for-ai-bot-attacks-and-agentic-fraud-in-2026

The design principle is stable even as providers change: **bind economic intent to verifiable identity, current authority, bounded policy, observable execution, and claim-grade evidence.**