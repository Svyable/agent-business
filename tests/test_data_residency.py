import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("validate_data_residency",ROOT/"scripts"/"validate_data_residency.py")
MOD=importlib.util.module_from_spec(SPEC); assert SPEC.loader is not None; SPEC.loader.exec_module(MOD)
STARTER=json.loads((ROOT/"templates"/"DATA_RESIDENCY_RECORD.json").read_text())

def evidence(eid,etype="config",status="current"):
    return {"id":eid,"type":etype,"status":status,"observed_at":"2026-08-28T21:45:00Z","reference":f"https://example.com/{eid}"}

def active_record():
    r=copy.deepcopy(STARTER); r["status"]="active"; r["tenant_scope"]={"tenant_id":"tenant-eu","constrained":True}
    r["requirements"]=[{"id":"eu","allowed_geographies":["eu-west","eu-central"],"evidence_ids":["req"]}]
    r["data_paths"]=[{"id":"inference","data_class":"prompt-response","material":True,"storage_region":"eu-west","processing_region":"eu-west","routing_mode":"regional","telemetry_region":"eu-west","control_plane_region":"eu-west","backup_regions":["eu-central"],"failover_regions":["eu-central"],"provider":"example-provider","subprocessor_location":"eu-west","support_admin_geography":"eu-west","requirement_id":"eu","evidence_ids":["path"]}]
    r["failover"]={"compliant":True,"tested":True,"evidence_ids":["dr"]}; r["authority"]={"can_activate":True,"evidence_ids":["auth"]}
    r["evidence"]=[evidence("req","contract"),evidence("path"),evidence("dr","drill"),evidence("auth","authority")]
    return r

class ResidencyValidationTests(unittest.TestCase):
    def assertFails(self,r,text):
        with self.assertRaises(SystemExit) as cm: MOD.validate(r)
        self.assertIn(text,str(cm.exception))
    def test_starter_safe(self): MOD.validate(copy.deepcopy(STARTER))
    def test_active_happy_path(self): MOD.validate(active_record())
    def test_global_endpoint_rejected_for_constrained_tenant(self):
        r=active_record(); r["data_paths"][0]["routing_mode"]="global"; self.assertFails(r,"cannot use global endpoint")
    def test_unknown_processing_region_rejected(self):
        r=active_record(); r["data_paths"][0]["processing_region"]="unknown"; self.assertFails(r,"unknown processing_region")
    def test_unknown_telemetry_region_rejected(self):
        r=active_record(); r["data_paths"][0]["telemetry_region"]="unknown"; self.assertFails(r,"unknown telemetry_region")
    def test_disallowed_backup_region_rejected(self):
        r=active_record(); r["data_paths"][0]["backup_regions"]=["us-east"]; self.assertFails(r,"disallowed geography")
    def test_disallowed_failover_region_rejected(self):
        r=active_record(); r["data_paths"][0]["failover_regions"]=["us-east"]; self.assertFails(r,"disallowed geography")
    def test_provider_location_must_be_known(self):
        r=active_record(); r["data_paths"][0]["subprocessor_location"]="unknown"; self.assertFails(r,"unknown subprocessor_location")
    def test_tested_status_requires_drill(self):
        r=active_record(); r["status"]="tested"; r["failover"]["tested"]=False; self.assertFails(r,"compliant tested failover")
    def test_material_change_invalidates_active(self):
        r=active_record(); r["change_control"]={"material_change_detected":True,"re_review_required":True}; self.assertFails(r,"active status invalid")
    def test_change_requires_rereview(self):
        r=copy.deepcopy(STARTER); r["change_control"]={"material_change_detected":True,"re_review_required":False}; self.assertFails(r,"must trigger re-review")
    def test_active_requires_authority(self):
        r=active_record(); r["authority"]={"can_activate":False,"evidence_ids":[]}; self.assertFails(r,"activation authority")
    def test_stale_path_evidence_rejected(self):
        r=active_record(); next(x for x in r["evidence"] if x["id"]=="path")["status"]="stale"; self.assertFails(r,"requires current evidence")
    def test_unknown_requirement_rejected(self):
        r=active_record(); r["data_paths"][0]["requirement_id"]="missing"; self.assertFails(r,"unknown requirement")
    def test_secret_like_field_rejected(self):
        r=copy.deepcopy(STARTER); r["api_key"]="redacted"; self.assertFails(r,"prohibited sensitive field")
    def test_retired_drops_activation_authority(self):
        r=copy.deepcopy(STARTER); r["status"]="retired"; r["authority"]["can_activate"]=True; self.assertFails(r,"cannot retain activation authority")

if __name__=="__main__": unittest.main()
