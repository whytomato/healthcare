from __future__ import annotations

from typing import Any

from app.tools.care_coordination import CareCoordinationTool


def ready_tool_result(
    tool: str,
    summary: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "tool": tool,
        "status": "ready",
        "summary": summary,
        "payload": payload or {},
    }


def skipped_tool_result(
    tool: str,
    reason: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "tool": tool,
        "status": "skipped",
        "summary": reason,
        "payload": payload or {},
    }


class GuidelineLookupTool:
    name = "guideline_lookup"

    def run(self, case_text: str, red_flags: list[str]) -> dict[str, Any]:
        if not red_flags:
            return skipped_tool_result(
                self.name,
                "No acute red flags; guideline lookup is optional for this demo encounter.",
                {"redFlags": red_flags},
            )
        return ready_tool_result(
            self.name,
            "Demo guideline lookup recommends urgent assessment for current red flags.",
            {"redFlags": red_flags, "guideline": "urgent_current_encounter_safety"},
        )


class LabOrderTool:
    name = "lab_order"

    def run(self, orders: list[str], priority: str) -> dict[str, Any]:
        lab_orders = [
            item
            for item in orders
            if item in {"CBC", "CRP", "troponin", "blood culture", "pathogen testing"}
        ]
        if not lab_orders:
            return skipped_tool_result(
                self.name,
                "No lab orders selected by diagnostic ordering agent.",
                {"orders": []},
            )
        return ready_tool_result(
            self.name,
            f"Created {len(lab_orders)} demo lab orders.",
            {"orders": lab_orders, "priority": priority},
        )


class LabResultFetchTool:
    name = "lab_result_fetch"

    def run(self, orders: list[str]) -> dict[str, Any]:
        lab_orders = [
            item
            for item in orders
            if item in {"CBC", "CRP", "troponin", "blood culture", "pathogen testing"}
        ]
        if not lab_orders:
            return skipped_tool_result(
                self.name,
                "No lab orders are available for result retrieval.",
                {"orders": []},
            )
        markers = [
            f"{order}: demo_result_pending_review"
            for order in lab_orders
        ]
        return ready_tool_result(
            self.name,
            "Fetched demo lab result placeholders for interpretation.",
            {"orders": lab_orders, "markers": markers},
        )


class ImagingOrderTool:
    name = "imaging_order"

    def run(self, orders: list[str], priority: str) -> dict[str, Any]:
        imaging_orders = [
            item
            for item in orders
            if item in {"chest X-ray", "head CT if clinically indicated"}
        ]
        if not imaging_orders:
            return skipped_tool_result(
                self.name,
                "No imaging orders selected by diagnostic ordering agent.",
                {"orders": []},
            )
        return ready_tool_result(
            self.name,
            f"Created {len(imaging_orders)} demo imaging orders.",
            {"orders": imaging_orders, "priority": priority},
        )


class ImagingResultFetchTool:
    name = "imaging_result_fetch"

    def run(self, orders: list[str]) -> dict[str, Any]:
        imaging_orders = [
            item
            for item in orders
            if item in {"chest X-ray", "head CT if clinically indicated"}
        ]
        if not imaging_orders:
            return skipped_tool_result(
                self.name,
                "No imaging orders are available for result retrieval.",
                {"orders": []},
            )
        return ready_tool_result(
            self.name,
            "Fetched demo imaging result placeholders for interpretation.",
            {
                "orders": imaging_orders,
                "findings": [f"{order}: demo_interpretation_required" for order in imaging_orders],
            },
        )


class MedicationInteractionTool:
    name = "medication_interaction"

    def run(
        self,
        medication_categories: list[str],
        allergies: list[str],
        current_medications: list[str],
    ) -> dict[str, Any]:
        if not medication_categories:
            return skipped_tool_result(
                self.name,
                "No medication categories were proposed for interaction screening.",
            )
        warnings = []
        if allergies:
            warnings.append("allergy_history_requires_review")
        if current_medications:
            warnings.append("current_medications_require_reconciliation")
        return ready_tool_result(
            self.name,
            "Medication interaction screening completed at demo level.",
            {
                "medicationCategories": medication_categories,
                "allergies": allergies,
                "currentMedications": current_medications,
                "warnings": warnings,
            },
        )


class BedAvailabilityTool:
    name = "bed_availability"

    def run(self, urgency_level: str) -> dict[str, Any]:
        if urgency_level != "high":
            return skipped_tool_result(
                self.name,
                "Outpatient pathway does not need a bed availability check.",
                {"urgencyLevel": urgency_level},
            )
        return ready_tool_result(
            self.name,
            "Emergency observation bed availability checked for demo workflow.",
            {"urgencyLevel": urgency_level, "availableBeds": 2, "unit": "emergency_observation"},
        )


class ReferralSchedulingTool:
    name = "referral_scheduling"

    def run(self, specialties: list[str]) -> dict[str, Any]:
        if not specialties:
            return skipped_tool_result(
                self.name,
                "No specialty referral was selected for scheduling.",
                {"specialties": []},
            )
        return ready_tool_result(
            self.name,
            "Specialty referral scheduling placeholders created.",
            {"specialties": specialties},
        )


class FollowUpSchedulingTool:
    name = "follow_up_scheduling"

    def run(self, follow_up_plan: str) -> dict[str, Any]:
        return ready_tool_result(
            self.name,
            "Follow-up scheduling placeholder created.",
            {"followUpPlan": follow_up_plan},
        )


class HumanReviewRequestTool:
    name = "human_review_request"

    def run(self, urgency_level: str, selected_specialties: list[str]) -> dict[str, Any]:
        if urgency_level != "high" and len(selected_specialties) < 3:
            return skipped_tool_result(
                self.name,
                "No human review escalation needed for this demo encounter.",
                {"urgencyLevel": urgency_level, "selectedSpecialties": selected_specialties},
            )
        return ready_tool_result(
            self.name,
            "Human review request placeholder created for complex or urgent encounter.",
            {"urgencyLevel": urgency_level, "selectedSpecialties": selected_specialties},
        )


class ClinicalToolRegistry:
    def __init__(self) -> None:
        self.guideline_lookup = GuidelineLookupTool()
        self.lab_order = LabOrderTool()
        self.lab_result_fetch = LabResultFetchTool()
        self.imaging_order = ImagingOrderTool()
        self.imaging_result_fetch = ImagingResultFetchTool()
        self.medication_interaction = MedicationInteractionTool()
        self.bed_availability = BedAvailabilityTool()
        self.referral_scheduling = ReferralSchedulingTool()
        self.follow_up_scheduling = FollowUpSchedulingTool()
        self.human_review_request = HumanReviewRequestTool()
        self.care_coordination = CareCoordinationTool()
