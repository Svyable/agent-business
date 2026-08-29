#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from scripts.validate_marketplace_listing import validate


def published_listing() -> dict:
    return {
        "schema_version": "1.0.0",
        "listing_id": "invoice-reconcile-storefront",
        "listing_version": "1.2.0",
        "updated_at": "2026-08-29T13:00:00Z",
        "status": "published",
        "provider": {
            "display_name": "Public Agent Co",
            "identity_ref": "https://public-agent.example/identity",
            "canonical_url": "https://public-agent.example/reconcile"
        },
        "capability": {
            "capability_id": "finance.reconcile-invoices",
            "name": "Reconcile invoices against purchase orders",
            "summary": "Matches invoices against purchase orders and returns a reconciliation report plus exception list without approving payment.",
            "categories": ["finance-operations"],
            "synonyms": ["invoice matching", "ap reconciliation"],
            "inputs": ["invoice", "purchase_order_records"],
            "outputs": ["reconciliation_report", "exception_list"],
            "human_review": "exceptions_only",
            "regions": ["US"],
            "protocols": [
                {
                    "id": "api-v1",
                    "protocol": "https_api",
                    "version": "1.0",
                    "endpoint": "https://public-agent.example/api/reconcile",
                    "evidence_ids": ["protocol-live"]
                }
            ]
        },
        "pricing": {
            "model": "usage",
            "currency": "USD",
            "headline": "$0.35 per invoice; $25 minimum",
            "minimum_commitment_minor": 2500,
            "variable_components": ["$0.35 per invoice"],
            "terms_url": "https://public-agent.example/terms"
        },
        "buyer_qualification": {
            "requires_authority_proof": true,
            "automatic_purchase_allowed": false,
            "acceptance_criteria_required": true,
            "max_autonomous_purchase_minor": 10000,
            "data_constraints": ["No payment credentials", "Buyer must be authorized to provide invoice data"]
        },
        "claims": [
            {
                "id": "claim-live-api",
                "statement": "The production reconciliation endpoint responded successfully to the current protocol probe.",
                "classification": "self_asserted",
                "marketplace_id": null,
                "evidence_ids": ["protocol-live"],
                "expires_at": "2026-09-29T13:00:00Z"
            },
            {
                "id": "claim-marketplace-badge",
                "statement": "The provider holds the Example Market verified-publisher badge under that marketplace's current process.",
                "classification": "platform_verified",
                "marketplace_id": "example-market",
                "evidence_ids": ["market-badge"],
                "expires_at": "2026-09-29T13:00:00Z"
            },
            {
                "id": "claim-editorial",
                "statement": "The badge should be treated as platform-scoped evidence, not universal proof of service quality.",
                "classification": "editorial_interpretation",
                "marketplace_id": null,
                "evidence_ids": [],
                "expires_at": null
            }
        ],
        "evidence": [
            {
                "id": "protocol-live",
                "type": "protocol_probe",
                "description": "Public canary for the production endpoint.",
                "public_url": "https://public-agent.example/status/reconcile",
                "observed_at": "2026-08-29T12:00:00Z",
                "expires_at": "2026-09-05T12:00:00Z",
                "status": "current",
                "marketplace_id": null
            },
            {
                "id": "market-badge",
                "type": "platform_verification",
                "description": "Example Market verified-publisher listing evidence.",
                "public_url": "https://market.example/listings/reconcile",
                "observed_at": "2026-08-29T12:30:00Z",
                "expires_at": "2026-09-29T12:30:00Z",
                "status": "current",
                "marketplace_id": "example-market"
            }
        ],
        "marketplaces": [
            {
                "marketplace_id": "example-market",
                "listing_url": "https://market.example/listings/reconcile",
                "external_listing_id": "listing-123",
                "state": "published",
                "projected_listing_version": "1.2.0",
                "synced_at": "2026-08-29T13:05:00Z",
                "badges": [
                    {
                        "name": "Verified publisher",
                        "scope": "Example Market publisher-control check only",
                        "evidence_ids": ["market-badge"]
                    }
                ]
            }
        ],
        "conversion": {
            "events": [
                "listing_discovered",
                "capability_inspected",
                "buyer_qualified",
                "quote_or_checkout_started",
                "paid_transaction",
                "successful_delivery",
                "repeat_purchase"
            ]
        },
        "privacy": {
            "public_disclosure_confirmed": True,
            "contains_secrets": False,
            "contains_private_customer_data": False,
            "contains_private_prompts": False,
            "contains_credentials": False
        }
    }


class MarketplaceListingValidationTests(unittest.TestCase):
    def test_valid_published_listing(self):
        validate(published_listing())

    def test_draft_requires_explicit_allow(self):
        record = published_listing()
        record["status"] = "draft"
        validate(copy.deepcopy(record), allow_draft=True)
        with self.assertRaises(SystemExit):
            validate(record)

    def test_published_protocol_requires_current_evidence(self):
        record = published_listing()
        record["evidence"][0]["status"] = "stale"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("published protocol", str(ctx.exception))

    def test_unknown_claim_evidence_is_rejected(self):
        record = published_listing()
        record["claims"][0]["evidence_ids"] = ["missing"]
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("unknown evidence", str(ctx.exception))

    def test_stale_marketplace_projection_is_rejected(self):
        record = published_listing()
        record["marketplaces"][0]["projected_listing_version"] = "1.1.0"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("stale projected_listing_version", str(ctx.exception))

    def test_marketplace_sync_before_canonical_update_is_rejected(self):
        record = published_listing()
        record["marketplaces"][0]["synced_at"] = "2026-08-29T12:59:00Z"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("synced before canonical updated_at", str(ctx.exception))

    def test_automatic_purchase_requires_authority_proof(self):
        record = published_listing()
        record["buyer_qualification"]["automatic_purchase_allowed"] = True
        record["buyer_qualification"]["requires_authority_proof"] = False
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("authority proof", str(ctx.exception))

    def test_automatic_purchase_requires_acceptance_criteria(self):
        record = published_listing()
        record["buyer_qualification"]["automatic_purchase_allowed"] = True
        record["buyer_qualification"]["acceptance_criteria_required"] = False
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("acceptance criteria", str(ctx.exception))

    def test_badge_evidence_must_be_platform_scoped(self):
        record = published_listing()
        record["evidence"][1]["marketplace_id"] = "other-market"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("not scoped", str(ctx.exception))

    def test_platform_verified_claim_requires_platform_evidence(self):
        record = published_listing()
        record["claims"][1]["evidence_ids"] = ["protocol-live"]
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("must be scoped", str(ctx.exception))

    def test_expired_claim_is_rejected(self):
        record = published_listing()
        record["claims"][0]["expires_at"] = "2026-08-28T13:00:00Z"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("expired", str(ctx.exception))

    def test_published_listing_cannot_have_undecided_pricing(self):
        record = published_listing()
        record["pricing"]["model"] = "undecided"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("undecided pricing", str(ctx.exception))

    def test_sensitive_field_is_rejected(self):
        record = published_listing()
        record["provider"]["api_key"] = "do-not-store-this"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("prohibited sensitive field", str(ctx.exception))

    def test_published_listing_requires_full_conversion_funnel(self):
        record = published_listing()
        record["conversion"]["events"].remove("successful_delivery")
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("successful_delivery", str(ctx.exception))

    def test_placeholder_text_cannot_be_evidence_reviewed(self):
        record = published_listing()
        record["status"] = "evidence_reviewed"
        record["provider"]["display_name"] = "Replace before publication"
        with self.assertRaises(SystemExit) as ctx:
            validate(record)
        self.assertIn("placeholder text", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
