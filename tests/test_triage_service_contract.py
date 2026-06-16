from pathlib import Path
import json


def test_triage_service_exposes_assessment_rest_contract() -> None:
    controller = Path(
        "backend/triage-service/src/main/kotlin/com/example/healthcare/triage/controller/TriageAssessmentController.kt"
    ).read_text(encoding="utf-8")
    request = Path(
        "backend/triage-service/src/main/kotlin/com/example/healthcare/triage/model/TriageAssessmentRequest.kt"
    ).read_text(encoding="utf-8")
    response = Path(
        "backend/triage-service/src/main/kotlin/com/example/healthcare/triage/model/TriageAssessmentResponse.kt"
    ).read_text(encoding="utf-8")

    assert '@RequestMapping("/api/triage")' in controller
    assert '@PostMapping("/assess")' in controller
    assert "caseText: String" in request
    assert "urgencyLevel: String" in response
    assert "recommendedDepartment: String" in response
    assert "redFlags: List<String>" in response


def test_triage_service_uses_same_public_decisions_as_python_triage_agent() -> None:
    triage_service = Path(
        "backend/triage-service/src/main/kotlin/com/example/healthcare/triage/service/TriageAssessmentService.kt"
    ).read_text(encoding="utf-8")
    python_triage = Path("app/agents/triage.py").read_text(encoding="utf-8")
    policy = json.loads(Path("config/clinical-policy.json").read_text(encoding="utf-8"))

    assert '"high"' in triage_service
    assert '"standard"' in triage_service
    assert '"emergency"' in triage_service
    assert '"general_medicine"' in triage_service
    assert "urgency_level" in python_triage
    assert "ClinicalPolicy.load()" in triage_service
    assert "policy.urgentTerms" in triage_service
    for term in ["chest discomfort", "confusion", "shortness of breath"]:
        assert term in policy["urgentTerms"]


def test_triage_service_documents_negated_red_flag_handling() -> None:
    triage_service = Path(
        "backend/triage-service/src/main/kotlin/com/example/healthcare/triage/service/TriageAssessmentService.kt"
    ).read_text(encoding="utf-8")
    python_rules = Path("app/agents/rules.py").read_text(encoding="utf-8")
    policy = json.loads(Path("config/clinical-policy.json").read_text(encoding="utf-8"))

    assert "isNegatedClinicalMention" in triage_service
    assert "no chest pain, confusion or severe shortness of breath" in triage_service
    assert "denies" in policy["negationCues"]["english"]
    assert "negationCues" in triage_service
    assert "app.policies.clinical_policy" in python_rules
