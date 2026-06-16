from __future__ import annotations

import json
from pathlib import Path


def test_clinical_policy_assesses_red_flags_and_specialties_from_shared_config() -> None:
    from app.policies.clinical_policy import assess_patient_encounter

    outpatient = assess_patient_encounter(
        "A 34-year-old has cough and low-grade fever, with no chest pain, "
        "confusion or severe shortness of breath."
    )
    emergency = assess_patient_encounter("患者出现胸痛、呼吸困难和意识模糊。")

    assert outpatient.urgency_level == "standard"
    assert outpatient.recommended_department == "general_medicine"
    assert outpatient.red_flags == []
    assert "respiratory" in outpatient.selected_specialties
    assert "cardiology" not in outpatient.selected_specialties
    assert "neurology" not in outpatient.selected_specialties

    assert emergency.urgency_level == "high"
    assert emergency.recommended_department == "emergency"
    assert {"胸痛", "呼吸困难", "意识模糊"}.issubset(set(emergency.red_flags))
    assert {"cardiology", "neurology"}.issubset(set(emergency.selected_specialties))


def test_triage_service_and_python_agents_depend_on_same_clinical_policy_file() -> None:
    policy_path = Path("config/clinical-policy.json")
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    triage_service = Path(
        "backend/triage-service/src/main/kotlin/com/example/healthcare/triage/service/TriageAssessmentService.kt"
    ).read_text(encoding="utf-8")
    python_rules = Path("app/agents/rules.py").read_text(encoding="utf-8")

    assert policy["urgentTerms"]
    assert policy["specialtyTerms"]["respiratory"]
    assert "config/clinical-policy.json" in triage_service
    assert "app.policies.clinical_policy" in python_rules
