from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


POM_NS = {"m": "http://maven.apache.org/POM/4.0.0"}


def _pom(path: str) -> ET.Element:
    return ET.parse(path).getroot()


def _modules(path: str) -> list[str]:
    root = _pom(path)
    return [
        item.text.strip()
        for item in root.findall("m:modules/m:module", POM_NS)
        if item.text
    ]


def test_emergency_room_business_microservices_are_maven_modules() -> None:
    modules = _modules("backend/pom.xml")

    assert "emergency-encounter-service" in modules
    assert "practitioner-service" in modules
    assert "resource-service" in modules
    assert "scheduling-service" in modules
    for module in [
        "emergency-encounter-service",
        "practitioner-service",
        "resource-service",
        "scheduling-service",
    ]:
        assert Path("backend", module, "pom.xml").is_file()


def test_emergency_encounter_service_exposes_acute_care_state_contract() -> None:
    base = Path("backend/emergency-encounter-service/src/main/kotlin/com/example/healthcare/emergency")
    controller = (base / "controller/EmergencyEncounterController.kt").read_text(encoding="utf-8")
    request = (base / "model/EmergencyEncounterRequest.kt").read_text(encoding="utf-8")
    response = (base / "model/EmergencyEncounter.kt").read_text(encoding="utf-8")

    assert '@PostMapping("/api/emergency/encounters")' in controller
    assert '@GetMapping("/health")' in controller
    assert "triageUrgency" in request
    assert "redFlags" in request
    assert "emergencyEncounterId" in response
    assert "status" in response
    assert "resourceReadinessStatus" in response
    assert "reservedResources" in response
    readiness_request = (base / "model/EmergencyReadinessUpdateRequest.kt").read_text(
        encoding="utf-8"
    )

    assert '@PostMapping("/api/emergency/encounters/readiness")' in controller
    assert "emergencyEncounterId" in readiness_request
    assert "reservedResources" in readiness_request
    assert "resourceReadinessStatus" in readiness_request


def test_practitioner_service_exposes_emergency_staff_availability_contract() -> None:
    base = Path("backend/practitioner-service/src/main/kotlin/com/example/healthcare/practitioner")
    controller = (base / "controller/PractitionerController.kt").read_text(encoding="utf-8")
    request = (base / "model/PractitionerAssignmentRequest.kt").read_text(encoding="utf-8")
    response = (base / "model/PractitionerAssignment.kt").read_text(encoding="utf-8")

    assert '@PostMapping("/api/practitioners/emergency-assignments")' in controller
    assert '@GetMapping("/health")' in controller
    assert "requiredSpecialties" in request
    assert "assignedPractitioners" in response
    assert "assignmentStatus" in response


def test_practitioner_service_persists_staff_pool_and_assignments_for_er_surge() -> None:
    module = Path("backend/practitioner-service")
    pom = (module / "pom.xml").read_text(encoding="utf-8")
    config = (module / "src/main/resources/application.yml").read_text(encoding="utf-8")
    base = module / "src/main/kotlin/com/example/healthcare/practitioner"
    service = (base / "service/PractitionerAssignmentService.kt").read_text(encoding="utf-8")

    practitioner_entity = (base / "model/PractitionerEntity.kt").read_text(encoding="utf-8")
    assignment_entity = (base / "model/PractitionerAssignmentEntity.kt").read_text(encoding="utf-8")
    practitioner_repository = (base / "service/PractitionerRepository.kt").read_text(encoding="utf-8")
    assignment_repository = (base / "service/PractitionerAssignmentRepository.kt").read_text(encoding="utf-8")
    initializer_path = base / "service/PractitionerSeedInitializer.kt"
    initializer = initializer_path.read_text(encoding="utf-8")

    assert "spring-boot-starter-data-jpa" in pom
    assert "postgresql" in pom
    assert "datasource:" in config
    assert "ddl-auto: update" in config
    assert "@Entity" in practitioner_entity
    assert 'name = "practitioners"' in practitioner_entity
    assert "specialty" in practitioner_entity
    assert "activeAssignments" in practitioner_entity
    assert "maxConcurrentAssignments" in practitioner_entity
    assert "@Entity" in assignment_entity
    assert 'name = "practitioner_assignments"' in assignment_entity
    assert "assignedPractitioners" in assignment_entity
    assert "unavailableSpecialties" in assignment_entity
    assert "JpaRepository" in practitioner_repository
    assert "LockModeType.PESSIMISTIC_WRITE" in practitioner_repository
    assert "findBySpecialtyAndOnShiftTrue" in practitioner_repository
    assert "JpaRepository" in assignment_repository
    assert "@Transactional" in service
    assert "seedDefaultPractitioners" not in service
    assert initializer_path.is_file()
    assert "ApplicationRunner" in initializer
    assert "practitionerRepository.save" in initializer
    assert "assignmentRepository.save" in service
    assert "activeAssignments" in service
    assert '@PostMapping("/api/practitioners/emergency-assignments/{taskId}/release")' in (
        base / "controller/PractitionerController.kt"
    ).read_text(encoding="utf-8")
    assert "release(taskId" in service


def test_resource_service_exposes_emergency_resource_reservation_contract() -> None:
    base = Path("backend/resource-service/src/main/kotlin/com/example/healthcare/resource")
    controller = (base / "controller/ResourceController.kt").read_text(encoding="utf-8")
    request = (base / "model/ResourceReservationRequest.kt").read_text(encoding="utf-8")
    response = (base / "model/ResourceReservation.kt").read_text(encoding="utf-8")
    service = (base / "service/ResourceReservationService.kt").read_text(encoding="utf-8")

    assert '@PostMapping("/api/resources/emergency-reservations")' in controller
    assert '@GetMapping("/health")' in controller
    assert "requiredResources" in request
    assert "reservedResources" in response
    assert "readinessStatus" in response
    assert "unavailableResources" in response
    assert '"partial"' in service


def test_resource_service_persists_inventory_and_reservations_for_concurrent_er_surge() -> None:
    module = Path("backend/resource-service")
    pom = (module / "pom.xml").read_text(encoding="utf-8")
    config = (module / "src/main/resources/application.yml").read_text(encoding="utf-8")
    base = module / "src/main/kotlin/com/example/healthcare/resource"
    service = (base / "service/ResourceReservationService.kt").read_text(encoding="utf-8")

    resource_entity = (base / "model/EmergencyResourceEntity.kt").read_text(encoding="utf-8")
    reservation_entity = (base / "model/ResourceReservationEntity.kt").read_text(encoding="utf-8")
    resource_repository = (base / "service/EmergencyResourceRepository.kt").read_text(encoding="utf-8")
    reservation_repository = (base / "service/ResourceReservationRepository.kt").read_text(encoding="utf-8")
    initializer_path = base / "service/EmergencyResourceSeedInitializer.kt"
    initializer = initializer_path.read_text(encoding="utf-8")

    assert "spring-boot-starter-data-jpa" in pom
    assert "postgresql" in pom
    assert "datasource:" in config
    assert "ddl-auto: update" in config
    assert "@Entity" in resource_entity
    assert 'name = "emergency_resources"' in resource_entity
    assert "availableUnits" in resource_entity
    assert "version" in resource_entity
    assert "@Entity" in reservation_entity
    assert 'name = "resource_reservations"' in reservation_entity
    assert "reservedResources" in reservation_entity
    assert "unavailableResources" in reservation_entity
    assert "JpaRepository" in resource_repository
    assert "findByResourceType" in resource_repository
    assert "LockModeType.PESSIMISTIC_WRITE" in resource_repository
    assert "JpaRepository" in reservation_repository
    assert "@Transactional" in service
    assert "seedDefaultInventory" not in service
    assert initializer_path.is_file()
    assert "ApplicationRunner" in initializer
    assert "resourceRepository.save" in initializer
    assert "reservationRepository.save" in service
    assert "ConcurrentHashMap" not in service
    assert '@PostMapping("/api/resources/emergency-reservations/{taskId}/release")' in (
        base / "controller/ResourceController.kt"
    ).read_text(encoding="utf-8")
    assert "release(taskId" in service


def test_scheduling_service_exposes_emergency_exam_scheduling_contract() -> None:
    base = Path("backend/scheduling-service/src/main/kotlin/com/example/healthcare/scheduling")
    controller = (base / "controller/SchedulingController.kt").read_text(encoding="utf-8")
    request = (base / "model/ExamSchedulingRequest.kt").read_text(encoding="utf-8")
    response = (base / "model/ExamSchedule.kt").read_text(encoding="utf-8")

    assert '@PostMapping("/api/schedules/emergency-exams")' in controller
    assert '@GetMapping("/health")' in controller
    assert "orderingAgent" in request
    assert "requestedExams" in request
    assert "scheduledExams" in response
    assert "scheduleStatus" in response
