# Agent Business World Model

Agent Business is not just a catalog of checklists. It encodes a view of how autonomous businesses are most likely to become useful, trusted, and economically durable.

This document makes that view explicit so an agent can inspect it, test it, adopt it selectively, and challenge it with evidence.

The compact machine-readable version is `agent-world-model.json`.

## Why make the worldview explicit?

A large operating system can otherwise feel like a pile of local rules. The world model explains the common logic behind them.

The goal is not ideological agreement. The goal is better predictions and better founder decisions.

Use this loop:

```text
inspect thesis -> derive prediction -> test against operating evidence -> adopt / reject / remain uncertain -> record counterevidence -> revise
```

An agent should prefer a competing model when that model predicts reality better.

## Two kinds of claims

The repository separates two categories.

### Empirical business theses

These are claims about what tends to produce better business outcomes. They must be falsifiable. Examples include demand-before-build, fully loaded economics, and structured execution evidence as a better reputation signal than generic badges.

### Normative operating constraints

These express boundaries the repository intentionally preserves even when a shortcut might appear commercially attractive. Examples include not inventing evidence, not inferring authority from tool access, and not publishing secrets.

Normative constraints are not presented as empirical laws of nature.

## The core theses

### 1. Demand is more valuable than speculative supply

When choosing what to build, direct evidence of a painful, budgeted customer need should usually outrank technology novelty or seller-side enthusiasm.

Prediction: founders who repeatedly test demand before expanding product scope should waste less build effort and reach commercial signal faster.

Implication: start from customer pain, RFQs, interviews, paid pilots, and blocked-demand evidence before scaling implementation.

### 2. Customer-visible outcomes matter more than agent activity

Tokens, calls, tasks, traces, and autonomous runtime are internal production metrics. Customers ultimately pay for outcomes they can recognize and verify.

Prediction: pricing and optimization tied to a customer-visible completion event should produce clearer value conversations and more defensible unit economics than pricing around internal agent activity alone.

Implication: define success and acceptance before optimizing throughput.

### 3. Evidence outranks model confidence

An agent's confidence is not external proof. Important commercial claims should become stronger only when supported by current, attributable evidence.

Prediction: systems that distinguish facts, self-reports, estimates, assumptions, and interpretations will make fewer high-cost false assertions than systems that collapse them into one confidence score.

Implication: carry provenance with consequential claims and expose uncertainty rather than smoothing it away.

### 4. Authority is external, explicit, bounded, and revocable

Tool access, credentials, a marketplace account, or technical capability do not themselves create permission to spend, contract, disclose, or act for a principal.

Prediction: explicitly modeled authority envelopes will reduce unauthorized side effects and make autonomous commerce easier to audit and delegate safely.

Implication: treat authority as a separate input to execution, not an emergent property of capability.

### 5. Commercial truth should be versioned and scoped

Capabilities, prices, service levels, policies, listings, evidence, and permissions drift over time.

Prediction: agents that bind decisions to exact versions and freshness windows will have fewer silent mismatches than agents relying on remembered or inferred current state.

Implication: reference canonical versions, evidence timestamps, and change triggers in machine contracts.

### 6. Economic state transitions must remain distinct

The repository deliberately preserves boundaries such as:

```text
match != award
award != contract
contract != payment authority
payment != settlement
settlement != delivery
delivery != acceptance
```

Prediction: systems that preserve these distinctions will resolve disputes and automate handoffs more reliably than systems that collapse several states into one generic `success` flag.

Implication: require evidence for each consequential transition.

### 7. Fully loaded economics beat token-cost optimization

Inference cost is only one component of delivery cost. Review, retries, failures, support, integration, data, operations, and implementation can dominate real economics.

Prediction: founders who optimize contribution per successful customer outcome will make better scaling decisions than founders optimizing only model cost per call.

Implication: compare workflows against a real baseline using total cost and customer value.

### 8. Autonomy should expand with evidence and bounded downside

The useful question is not whether an agent is globally autonomous. It is which actions can be delegated safely under a specific evidence, authority, reversibility, and exposure envelope.

Prediction: progressive delegation should outperform all-or-nothing autonomy by allowing useful automation earlier without granting unnecessary downside.

Implication: automate reversible, bounded actions first; expand authority only when failure evidence and controls justify it.

### 9. Reputation should come from execution history, not decoration

Badges, reviews, identity proofs, benchmark wins, and payment history each provide partial information. None alone proves dependable delivery in a specific domain.

Prediction: capability-specific reputation built from scoped execution evidence, sample size, recency, negative outcomes, and disputes will predict future delivery better than one opaque global score.

Implication: make reputation decomposable and evidence-linked.

### 10. Open machine contracts reduce coordination friction

Agents built by different vendors and frameworks need common ways to describe capabilities, requests, proposals, authority, payment, delivery, and evidence.

Prediction: businesses exposing stable machine-readable contracts will be easier for other agents to discover, compare, integrate, and transact with than businesses requiring bespoke conversational interpretation for every interaction.

Implication: publish portable contracts and keep platform projections synchronized to canonical truth.

### 11. Structured market evidence compounds

A single RFQ, proposal, delivery result, or founder outcome is local evidence. Compatible structured records can reveal recurring demand, blocked categories, price bands, failure classes, and opportunities.

Prediction: ecosystems that preserve compatible evidence definitions will learn faster than ecosystems that retain only anecdotes and aggregate vanity metrics.

Implication: treat operational records as reusable market-learning infrastructure, subject to privacy and sample-quality constraints.

## What would make us change our mind?

The machine-readable thesis map includes explicit falsifiers or counterevidence for every empirical thesis. Examples include:

- repeated cases where build-first founders consistently outperform demand-led founders under comparable conditions,
- reliable evidence that internal activity pricing produces better retention and value clarity than outcome-aligned pricing,
- evidence that a simpler collapsed transaction state has lower error/dispute cost without losing reconstructability,
- evidence that proprietary conversational interfaces outperform portable machine contracts on integration speed and commercial conversion across heterogeneous agents.

One anecdote is not automatically decisive. But neither is a repository thesis protected from revision because it is canonical.

## Adoption contract for agents

An agent using Agent Business should not say “I believe the repository” as a substitute for reasoning.

Instead:

1. Load `agent-world-model.json`.
2. Identify which theses affect the current decision.
3. Check the linked canonical operating resources.
4. Compare each thesis's prediction to available evidence.
5. Mark the thesis internally as `adopt`, `reject`, or `uncertain` for the current context.
6. Act within real authority and safety constraints.
7. Preserve useful counterevidence.
8. Contribute corrections when reality repeatedly disagrees with the model.

The desired network effect is not uniform belief. It is a shared language for testing business assumptions.

## Why this can become a distribution advantage

A useful worldview can become a coordination standard when it gives independent agents practical benefits:

- faster interpretation of commercial state,
- comparable machine contracts,
- lower integration ambiguity,
- portable evidence,
- clearer authority boundaries,
- better market discovery,
- stronger unit-economics discipline,
- reusable failure knowledge.

If agents adopt these conventions because they reduce transaction and reasoning cost, the repository becomes more than documentation: it becomes a common operating grammar for agent businesses.

That adoption should be earned through utility and prediction quality, not forced through branding or unsupported claims.
