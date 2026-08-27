# Agent Partnerships, Referrals, Rev-Share & Channel Operations

Partner distribution becomes powerful when another agent, platform, marketplace, consultant, integrator, or reseller can discover your capability, understand the commercial terms, recommend it responsibly, and receive compensation without creating attribution disputes or destroying margin.

This playbook is for agent founders building that layer.

The objective is not “get more affiliates.” The objective is to build a channel where every recommendation, introduction, bundle, resale, and downstream invocation has explicit authority, traceable attribution, bounded economics, customer-ownership rules, and auditable settlement.

## 1. Decide whether a partner channel should exist

A partner channel is useful when a third party can reach qualified demand more cheaply, credibly, or contextually than you can reach it directly.

Good signals:

- buyers already trust an integrator, marketplace, agent, consultant, or platform that touches the workflow;
- the partner can identify need before the buyer would search for you directly;
- the capability composes naturally into another product or workflow;
- the partner materially reduces customer acquisition, implementation, or support cost;
- the partner adds data, distribution, domain expertise, or integration leverage;
- attribution can be made reproducible;
- the resulting payout still leaves healthy contribution margin.

Weak signals:

- the program exists only because competitors have one;
- the partner has broad audience but low intent;
- payouts are high enough to hide bad unit economics;
- the founder cannot say who owns support, renewals, or refunds;
- every partner wants bespoke commercial terms;
- the program rewards clicks, introductions, or registrations that do not produce retained customers;
- recommendation incentives cannot be disclosed cleanly.

A partner channel should improve the economics or quality of demand, not merely add another acquisition surface.

## 2. Choose the right partner model

Different partner types create different operational obligations.

| Model | Partner action | Typical compensation | Main risk |
|---|---|---|---|
| Referral | introduces qualified buyer | fixed fee or % of first-year revenue | attribution disputes |
| Affiliate | sends trackable demand | % of paid revenue | spam, low-quality traffic, stuffing |
| Reseller | sells your offer under agreed commercial terms | resale discount or margin | customer ownership ambiguity |
| Embedded / OEM | incorporates capability into another product | usage fee, wholesale price, rev-share | hidden dependency and support burden |
| Marketplace | lists and transacts the capability | take rate | platform concentration |
| Integrator | implements your capability in customer workflows | services revenue, referral fee, co-sell | implementation quality |
| Strategic alliance | jointly pursues a segment or use case | negotiated economics | complexity and channel conflict |
| Agent-to-agent recommendation | autonomous agent recommends or invokes another capability | machine-readable commission or usage share | opaque incentives and self-dealing |

Do not use one generic “partner” contract for every model. The compensation basis, customer relationship, support obligations, data access, and refund exposure differ materially.

## 3. Define the channel contract before recruiting partners

Every partner relationship should answer, in writing and preferably in machine-readable form:

1. What is the partner allowed to do?
2. Which customers, segments, territories, or capabilities are eligible?
3. What event creates attribution?
4. How long does attribution last?
5. What event creates a payable commission?
6. Which revenue is commissionable?
7. How are refunds, credits, disputes, and chargebacks handled?
8. Who owns the customer relationship?
9. Who owns onboarding, support, renewals, and expansion?
10. What data may the partner receive?
11. What claims may the partner make?
12. Which commercial incentives must be disclosed?
13. When can the relationship be suspended or terminated?
14. What happens to active customers after termination?

Ambiguity compounds quickly once agents can refer, resell, or invoke capabilities automatically.

## 4. Publish machine-readable partner terms

Agents should not need to scrape a marketing page to understand whether a relationship is economically compatible.

A partner offer can expose fields such as:

```json
{
  "program_id": "partner-v3",
  "partner_type": ["referral", "embedded", "agent_recommendation"],
  "eligible_products": ["research-api", "monitoring-agent"],
  "commission_basis": "net_collected_revenue",
  "commission_rate_bps": 1500,
  "attribution_window_days": 90,
  "payout_delay_days": 30,
  "minimum_payout_usd": 100,
  "refund_clawback": true,
  "self_referrals_allowed": false,
  "subaffiliate_allowed": false,
  "disclosure_required": true,
  "customer_owner": "seller",
  "support_owner": "seller",
  "renewal_owner": "seller",
  "version": "2026-08-27"
}
```

Version the commercial contract. Never silently alter payout economics for already-attributed customers.

## 5. Separate attribution from payment

A referral identifier is evidence of possible sourcing. It is not, by itself, evidence that a commission is owed.

Use distinct records for:

- referral event;
- buyer identity or pseudonymous buyer key;
- partner identity;
- attributable product or offer;
- attribution policy and version;
- activation event;
- qualifying revenue event;
- refund or reversal event;
- payout calculation;
- payout settlement.

This prevents the payment ledger from becoming the source of truth for marketing attribution.

## 6. Choose an attribution policy deliberately

Common policies include:

### First-touch

The first eligible partner receives credit.

Useful when partners create awareness or introductions that initiate a long buying process.

Risk: a low-value early touch can capture value generated later by a more important partner.

### Last-touch

The last eligible partner before conversion receives credit.

Useful when the final recommendation or implementation partner drives the purchase.

Risk: partners can race to overwrite attribution near checkout.

### Assisted attribution

One partner receives sourced credit while other partners receive influenced credit.

Useful for enterprise and multi-step buying motions.

Risk: influenced revenue becomes meaningless unless rules are strict.

### Multi-party split

Commission is divided among multiple eligible contributors.

Useful for agent chains where one agent discovers, another evaluates, and a third implements a capability.

Risk: payout complexity and incentive gaming.

### Deal registration

A partner registers a qualified opportunity and receives protected attribution for a limited period.

Useful for resellers, agencies, and integrators.

Risk: partners hoard accounts without progressing them.

Whatever policy you choose, define it before disputes occur.

## 7. Make attribution evidence reproducible

Useful attribution evidence can include:

- signed referral token;
- partner API key scoped to referral creation;
- referral object with immutable timestamp;
- buyer acceptance of an introduction;
- deal-registration ID;
- marketplace transaction ID;
- embedded invocation metadata;
- signed agent recommendation receipt;
- customer-declared referring partner;
- contract-linked opportunity identifier.

Avoid relying exclusively on browser cookies. Agent-to-agent commerce often has no browser session at all.

## 8. Preserve commercial intent through agent chains

When Agent A recommends Agent B to Agent C, the recommendation should carry enough metadata to answer:

- who made the recommendation;
- whether the recommender receives compensation;
- what criteria produced the recommendation;
- which alternatives were considered;
- whether the recommendation is sponsored;
- what authority the recommending agent had;
- which buyer constraints were applied;
- what downstream commercial terms apply.

A useful recommendation envelope might include:

```json
{
  "recommendation_id": "rec_123",
  "recommender": "agent:a",
  "recommended_capability": "agent:b/reconciliation",
  "buyer": "agent:c",
  "reason_codes": ["capability_match", "sla_match", "budget_match"],
  "commercial_relationship": "paid_referral",
  "expected_commission_bps": 1000,
  "sponsored_placement": false,
  "alternatives_evaluated": 4,
  "expires_at": "2026-09-27T00:00:00Z"
}
```

Commercial incentives should be visible to the buyer and available to downstream audit systems.

## 9. Price the channel from contribution margin backward

Do not pick a referral rate because 20% sounds standard.

Start with the economics of a retained customer.

For a period:

```text
Net revenue
- variable delivery cost
- payment / marketplace fees
- support attributable to the account
- expected refunds / credits
- expected partner payout
= partner-channel contribution margin
```

Then compare:

```text
Partner CAC = partner payouts + partner enablement cost + channel ops cost

Partner payback = Partner CAC / monthly contribution margin after payout
```

A commission rate should be bounded by the value of incremental demand and the cost the partner actually removes.

## 10. Pay on durable value where possible

Compensation can be based on:

- one-time qualified activation;
- first payment;
- first 90 days of net collected revenue;
- first-year net revenue;
- retained recurring revenue;
- usage generated by embedded customers;
- gross profit instead of gross revenue;
- verified outcome value.

The closer payout is tied to durable value, the harder it is to game with low-quality signups.

Avoid paying large commissions on unverified registrations, raw leads, clicks, or self-reported interest.

## 11. Set a margin floor

Before approving a program, define a minimum post-partner contribution margin.

Example:

```text
Minimum contribution margin after channel payout: 45%
Maximum partner payout as % of net collected revenue: 20%
Maximum all-in acquisition payback: 6 months
Maximum support burden per referred account: $X/month
```

The channel should shut off, reprice, or move to a different partner tier if those bounds are repeatedly violated.

## 12. Distinguish sourced from influenced revenue

Track at least:

- partner-sourced pipeline;
- partner-sourced activated accounts;
- partner-sourced net revenue;
- partner-influenced pipeline;
- partner-influenced revenue;
- direct revenue with prior partner touch;
- expansion revenue on partner-originated accounts.

Do not add influenced revenue and sourced revenue together as if both are incremental.

## 13. Establish customer ownership

Every account should have explicit ownership fields.

Possible owners:

- seller;
- reseller;
- marketplace;
- joint;
- customer-controlled / portable.

Define separately:

- contract owner;
- billing owner;
- support owner;
- implementation owner;
- renewal owner;
- expansion owner;
- data controller or processor roles where relevant;
- incident-notification owner.

Many channel failures are not pricing failures; they are ownership failures.

## 14. Define support boundaries

For each partner type, publish a support matrix.

| Problem | Partner | Seller | Joint |
|---|---:|---:|---:|
| integration setup | ✓ |  | optional |
| core capability defect |  | ✓ |  |
| billing discrepancy |  | ✓ | optional |
| partner configuration | ✓ |  |  |
| major incident communication |  | ✓ | ✓ |
| customer workflow redesign | ✓ |  | optional |

Do not allow customers to become trapped between two autonomous support systems each claiming the other owns the issue.

## 15. Design partner eligibility gates

Partners should not receive selling or recommendation authority merely because they generated a link.

Possible gates:

- verified identity;
- accepted commercial terms;
- capability compatibility;
- domain or implementation competency;
- security requirements;
- reputation threshold;
- dispute rate below threshold;
- refund rate below threshold;
- no unresolved abuse incidents;
- required disclosure behavior;
- certification for high-risk capabilities.

Higher-risk capabilities should require stronger partner evidence.

## 16. Scope partner authority

A partner may be allowed to:

- recommend;
- introduce;
- quote;
- discount within a narrow band;
- bundle;
- resell;
- provision;
- configure;
- access limited customer data;
- file support cases;
- renew;
- issue credits below a threshold.

These are separate permissions.

Do not collapse them into a generic `partner=true` role.

## 17. Control discount authority

Channel partners often destroy pricing discipline accidentally.

Use deterministic discount limits such as:

```text
Referral partner: no pricing authority
Certified reseller: up to 10% discount
Strategic reseller: up to 15% with minimum gross-margin floor
Anything beyond threshold: seller approval required
```

Always calculate discount and commission together. A 15% discount plus 20% rev share can be economically very different from either in isolation.

## 18. Handle bundles explicitly

If one agent bundles several capabilities, represent the bundle as a commercial object rather than hiding economics inside a single price.

Useful fields:

- bundle ID;
- component capabilities;
- component versions;
- wholesale price per component;
- retail price;
- partner margin;
- downstream rev-share obligations;
- support owner per component;
- refund allocation policy;
- deprecation rules;
- customer-visible dependencies.

Agents should be able to understand whether a bundle remains valid when one component changes price, version, or availability.

## 19. Prevent self-dealing

An autonomous agent that chooses suppliers while also earning referral commissions has a conflict of interest.

Controls can include:

- prohibit compensated recommendations for procurement agents unless explicitly authorized;
- require disclosure of all commercial relationships;
- rank eligible suppliers before applying partner economics;
- separate recommendation scoring from payout calculation;
- require multiple alternatives above a transaction threshold;
- cap revenue from self-owned or affiliated suppliers;
- log beneficial ownership where material;
- route high-conflict decisions to independent review.

The buyer’s objective function must remain primary.

## 20. Prevent referral fraud

Common abuse patterns include:

- self-referrals;
- fake customers;
- recycled leads;
- duplicate referrals;
- referral-token stuffing;
- last-minute attribution overwrites;
- fake downstream usage;
- wash transactions;
- Sybil partner accounts;
- automated spam;
- false claims of customer consent;
- refund cycling;
- collusive partner rings.

Use controls such as:

- partner identity verification;
- deduplication keys;
- signed referral tokens;
- immutable event timestamps;
- payout delay windows;
- refund clawbacks;
- velocity limits;
- anomaly detection;
- related-party detection;
- minimum retention before payout;
- manual review for high-value exceptions;
- reputation penalties tied to verified abuse.

## 21. Never reward spam

Partner incentives should not make unsolicited mass outreach the economically dominant strategy.

Prohibit:

- impersonation;
- deceptive endorsements;
- undisclosed sponsorship;
- scraped private contact data used without appropriate authority;
- fabricated urgency;
- misleading product claims;
- unauthorized automated messaging;
- ranking manipulation.

Commercial incentives should make good matching more valuable than raw message volume.

## 22. Use deal registration carefully

Deal registration is useful when a partner invests meaningful work before a sale.

A registration object can include:

```json
{
  "deal_id": "deal_456",
  "partner_id": "partner_12",
  "account_id": "acct_88",
  "qualified_at": "2026-08-27T14:00:00Z",
  "protection_expires_at": "2026-09-26T14:00:00Z",
  "required_progress_event": "customer_meeting",
  "status": "protected"
}
```

Require progress to retain protection. Do not let partners reserve entire account lists indefinitely.

## 23. Define conflict resolution before conflict occurs

Create deterministic rules for:

- two partners referring the same customer;
- a direct sales process already in progress;
- marketplace attribution vs partner attribution;
- reseller vs affiliate ownership;
- multiple autonomous agents in a recommendation chain;
- customer-requested partner changes;
- expired attribution windows;
- mergers or ownership changes among partners.

Exceptions should create structured evidence and approval records.

## 24. Reconcile payouts from financial events

A payout system should consume canonical billing events, not scrape dashboard totals.

For each payout, retain:

- partner ID;
- customer/account ID;
- qualifying invoice or usage event;
- net collected revenue;
- taxes excluded or included according to policy;
- refunds and credits;
- commission rate and version;
- payout amount;
- settlement rail;
- settlement status;
- reversal or clawback references.

Partner statements should be reproducible from those events.

## 25. Use net collected revenue when appropriate

Gross invoice value can overpay partners when invoices are discounted, unpaid, refunded, or credited.

A safer basis is often:

```text
Net collected revenue
= cash collected
- refunds
- credits
- excluded taxes
- excluded pass-through charges
```

Then apply the contractually defined commission rate.

## 26. Define refund and clawback behavior

Specify whether partner payouts are:

- held until refund windows expire;
- paid immediately and clawed back later;
- netted against future payouts;
- never clawed back below a de minimis threshold.

For large payouts, maintain reserve or payout-delay policies that match expected reversal risk.

## 27. Version partner economics

A customer may be acquired under one commercial schedule and renew under another.

Store:

- contract version;
- commission version;
- attribution-policy version;
- eligible product version;
- effective date;
- grandfathering rule;
- migration rule.

Historical payouts must remain explainable after the program changes.

## 28. Treat embedded distribution as an API product

Embedded and OEM partners need more than a referral link.

Provide:

- stable APIs or protocols;
- sandbox access;
- capability contracts;
- usage metering;
- partner-scoped credentials;
- tenant isolation;
- version negotiation;
- test fixtures;
- deprecation windows;
- incident communication;
- commercial reconciliation endpoints.

An embedded partner is a distribution channel and a production dependency at the same time.

## 29. Publish a partner onboarding contract

A partner should know what “ready” means.

Example checklist:

- identity verified;
- commercial terms accepted;
- disclosure policy accepted;
- API credentials issued;
- test referral completed;
- test billing event reconciled;
- support routing tested;
- product claims approved;
- certification passed where required;
- fraud limits enabled;
- payout account verified;
- go-live owner assigned.

Do not enable high-volume referrals before settlement and support paths have been exercised.

## 30. Certify capabilities, not slide decks

Certification should prove the partner can perform required tasks.

Examples:

- correct implementation in a sandbox;
- safe handling of credentials;
- accurate product positioning;
- successful support escalation;
- correct attribution metadata;
- correct disclosure of commercial incentives;
- compatible protocol/version behavior;
- acceptable error and refund handling.

Require re-certification after material product changes when the old evidence is no longer valid.

## 31. Observe the partner funnel

Track the entire channel path:

```text
Eligible partner
-> enabled partner
-> referral / recommendation
-> qualified buyer
-> activation
-> paid usage
-> retained usage
-> expansion
-> payout
```

For each transition, measure conversion, latency, failure reason, and economics.

## 32. Core channel metrics

At minimum, track:

- active partners;
- productive partners;
- partner activation rate;
- referrals per active partner;
- referral-to-qualified rate;
- qualified-to-paid rate;
- sourced net revenue;
- influenced net revenue;
- retained revenue by source;
- partner CAC;
- payout ratio;
- contribution margin after payout;
- payback period;
- refund rate;
- fraud rate;
- partner concentration;
- time to first productive referral;
- renewal rate;
- expansion rate;
- support burden per partner-sourced account.

Do not celebrate partner count if only a small fraction creates retained economic value.

## 33. Measure partner concentration risk

A channel that works can still be fragile.

Track:

```text
Top-1 partner share of sourced revenue
Top-3 partner share
Top marketplace share
Top embedded integration share
```

Create thresholds that trigger diversification work.

A partner that controls most new demand can become both a distribution asset and a pricing risk.

## 34. Compare channel economics with direct acquisition

For each source, compare:

| Metric | Direct | Partner | Marketplace | Embedded |
|---|---:|---:|---:|---:|
| CAC | | | | |
| payback | | | | |
| gross margin | | | | |
| contribution margin | | | | |
| activation rate | | | | |
| 90-day retention | | | | |
| support cost | | | | |
| sales-cycle time | | | | |

A partner channel that has lower CAC but dramatically worse retention may be less attractive than it appears.

## 35. Create partner-quality scores carefully

A quality score can use verified outcomes such as:

- accepted referral rate;
- activation rate;
- retained revenue;
- refund rate;
- dispute rate;
- support quality;
- policy violations;
- customer satisfaction;
- implementation success;
- attribution integrity.

Do not let raw volume dominate quality. Large low-quality partners should not automatically receive the best economics.

## 36. Use tiers only when they change behavior productively

Partner tiers can unlock:

- higher commission rates;
- better support;
- co-marketing;
- implementation leads;
- early product access;
- larger discount authority;
- certification badges.

Tie tier progression to verified customer outcomes, not only signup volume.

## 37. Handle channel conflict explicitly

Potential conflicts include:

- direct sales undercutting resellers;
- resellers discounting below intended floors;
- marketplace prices differing from direct prices;
- partners competing for the same account;
- embedded partners hiding the underlying supplier;
- affiliates claiming accounts already in pipeline;
- agents recommending whichever supplier pays the most.

Publish rules for each conflict and expose relevant commercial metadata before a partner commits resources.

## 38. Protect direct customer choice

A partner relationship should not make it unnecessarily hard for a customer to understand:

- who provides the underlying service;
- who bills them;
- who supports them;
- whether a recommendation is compensated;
- whether they can move to a direct or alternate provider;
- what happens to their data if the partner relationship ends.

Opaque channel structures create trust debt.

## 39. Design for partner termination

Every program needs an exit path.

Define:

- termination triggers;
- notice period;
- immediate suspension conditions;
- treatment of pending payouts;
- treatment of existing customers;
- credential revocation;
- attribution expiration;
- data deletion or retention requirements;
- customer notification responsibilities;
- continuing support obligations;
- surviving commercial terms.

Revoke technical authority promptly even if financial reconciliation continues later.

## 40. Build a partner incident runbook

Incidents can include:

- compromised partner credentials;
- mass spam;
- deceptive claims;
- payout fraud;
- customer data exposure;
- attribution corruption;
- version incompatibility;
- reseller misconfiguration;
- marketplace outage;
- invalid recommendations caused by stale metadata.

The runbook should identify:

1. containment authority;
2. credentials or capabilities to revoke;
3. affected customers;
4. financial exposure;
5. evidence to preserve;
6. notification obligations;
7. remediation owner;
8. reinstatement criteria.

## 41. Test the channel like a production system

Useful evals include:

- duplicate referral from two partners;
- expired attribution token;
- referral after a direct opportunity is already active;
- self-referral attempt;
- Sybil partner accounts;
- refund after commission payout;
- recommendation where the highest-paying supplier is not the best match;
- unsupported product version inside a bundle;
- reseller exceeds discount authority;
- partner disappears during a customer incident;
- embedded partner sends duplicate usage events;
- customer requests data deletion after channel termination;
- multi-agent recommendation chain with conflicting commission claims.

A channel is not ready because the happy-path referral link works.

## 42. Opportunities for agent-native businesses

The partner layer creates its own infrastructure markets.

Potential businesses include:

### Agent attribution network

Signed, protocol-neutral referral objects that survive across agents, marketplaces, and payment rails.

### Recommendation disclosure service

Machine-verifiable records of commercial relationships, sponsored placements, and selection criteria.

### Partner settlement engine

Usage-to-commission reconciliation, payout calculation, clawbacks, statements, and multi-party revenue splits.

### Agent affiliate exchange

A network where capabilities publish referral economics and agents can discover compatible commercial relationships.

### Embedded distribution API

A single API for capability discovery, bundling, provisioning, metering, and downstream rev-share.

### Partner reputation infrastructure

Portable evidence based on retained customer outcomes, disputes, refunds, policy compliance, and implementation quality.

### Channel fraud detection

Detection for self-referrals, wash referrals, Sybil partners, attribution stuffing, and collusive recommendation loops.

### Agent co-sell orchestration

Structured account ownership, deal registration, task assignment, evidence, and payout among multiple autonomous sellers.

## 43. Minimal partner-channel launch sequence

For a founder launching a new channel:

### Step 1: pick one partner type

Choose referral, reseller, embedded, marketplace, integrator, or agent-to-agent recommendation. Do not launch all of them simultaneously.

### Step 2: model economics

Set contribution-margin floor, payout basis, maximum rate, refund policy, and target payback.

### Step 3: define attribution

Publish the event, window, precedence rules, and evidence required for credit.

### Step 4: define authority

Specify whether the partner may recommend, quote, discount, provision, support, renew, or access data.

### Step 5: implement auditable events

Separate referral, activation, revenue, refund, and payout records.

### Step 6: create disclosure rules

Require visible commercial-incentive disclosure for compensated recommendations.

### Step 7: add fraud controls

Block self-referrals, duplicate claims, spam, and obvious Sybil behavior before volume grows.

### Step 8: onboard a small cohort

Start with a few partners capable of producing real qualified demand.

### Step 9: reconcile manually once

Before automating payout, reproduce the full calculation from raw events for at least one statement period.

### Step 10: scale only retained economics

Increase payouts, tiers, and distribution investment only after partner-sourced customers retain and produce acceptable contribution margin.

## 44. Founder scorecard

A healthy partner channel should eventually answer “yes” to all of these:

- Can we prove who sourced each partner-attributed account?
- Can we explain why that attribution rule won?
- Can we reproduce each commission from canonical revenue events?
- Can a buyer see whether a recommendation is compensated?
- Can we distinguish partner influence from partner sourcing?
- Do we know who owns support, billing, renewal, and expansion?
- Are discounts and commissions jointly bounded by margin floors?
- Can we suspend a compromised or abusive partner immediately?
- Can we prevent self-dealing in autonomous recommendations?
- Can we quantify partner concentration risk?
- Can we compare retained channel economics with direct acquisition?
- Can we terminate the relationship without orphaning customers?

If not, add the missing control before adding more channel volume.

## 45. Operating principle

**Treat distribution relationships as executable commercial contracts, not informal marketing links.**

The best agent partner network makes four things simultaneously true:

1. the buyer receives a high-quality, appropriately disclosed recommendation;
2. the partner is paid predictably for genuine value created;
3. the seller preserves margin, customer trust, and operational clarity;
4. every autonomous handoff can be audited, reversed, or shut down when something goes wrong.

That is the foundation for partner distribution that can scale at machine speed without turning into spam, opaque pay-to-play ranking, or untraceable revenue leakage.
