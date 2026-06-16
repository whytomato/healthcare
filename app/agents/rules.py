from app.policies.clinical_policy import (
    SPECIALTY_RECOMMENDATIONS,
    URGENT_TERMS,
    VITAL_RISK_TERMS,
    assess_patient_encounter,
    matched_terms,
    select_specialties,
)
from app.policies.workflow_state import selected_specialties
