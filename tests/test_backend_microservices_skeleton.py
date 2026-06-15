from pathlib import Path
import xml.etree.ElementTree as ET


POM_NS = {"m": "http://maven.apache.org/POM/4.0.0"}


def _pom(path: str) -> ET.Element:
    return ET.parse(path).getroot()


def _text(root: ET.Element, path: str) -> str:
    item = root.find(path, POM_NS)
    return item.text.strip() if item is not None and item.text else ""


def _texts(root: ET.Element, path: str) -> list[str]:
    return [
        item.text.strip()
        for item in root.findall(path, POM_NS)
        if item.text
    ]


def _find_plugin(root: ET.Element, artifact_id: str) -> ET.Element:
    for plugin in root.findall(".//m:plugin", POM_NS):
        if _text(plugin, "m:artifactId") == artifact_id:
            return plugin
    raise AssertionError(f"Plugin not found: {artifact_id}")


def test_backend_is_parent_maven_project_with_healthcare_service_modules() -> None:
    backend = Path("backend")
    root = _pom("backend/pom.xml")
    modules = [
        item.text.strip()
        for item in root.findall("m:modules/m:module", POM_NS)
        if item.text
    ]

    assert _text(root, "m:packaging") == "pom"
    assert modules == [
        "common-proto",
        "encounter-service",
        "triage-service",
        "clinical-record-service",
        "care-coordination-service",
    ]
    for module in modules:
        assert (backend / module / "pom.xml").is_file()


def test_existing_backend_api_is_migrated_to_encounter_service_module() -> None:
    assert Path("backend/encounter-service/src/main/kotlin").is_dir()
    assert Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/HealthcareBackendApplication.kt"
    ).is_file()
    assert Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/controller/AiTaskController.kt"
    ).is_file()
    assert not Path("backend/src/main/kotlin").exists()


def test_backend_kotlin_build_supports_spring_data_jpa_entities() -> None:
    root = _pom("backend/pom.xml")
    kotlin_plugin = _find_plugin(root, "kotlin-maven-plugin")
    compiler_plugins = _texts(kotlin_plugin, "m:configuration/m:compilerPlugins/m:plugin")
    plugin_dependencies = _texts(kotlin_plugin, "m:dependencies/m:dependency/m:artifactId")

    assert "spring" in compiler_plugins
    assert "jpa" in compiler_plugins
    assert "kotlin-maven-allopen" in plugin_dependencies
    assert "kotlin-maven-noarg" in plugin_dependencies


def test_docker_compose_provides_postgres_for_microservice_persistence() -> None:
    compose = Path("infra/docker-compose.kafka.yml").read_text(encoding="utf-8")

    assert "postgres:" in compose
    assert "image: postgres:15" in compose
    assert 'POSTGRES_DB: healthcare' in compose
    assert 'POSTGRES_USER: user' in compose
    assert 'POSTGRES_PASSWORD: password' in compose
    assert '"5432:5432"' in compose


def test_encounter_service_persists_patient_encounters_to_postgres() -> None:
    pom = Path("backend/encounter-service/pom.xml").read_text(encoding="utf-8")
    application_yml = Path("backend/encounter-service/src/main/resources/application.yml").read_text(
        encoding="utf-8"
    )
    entity = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/model/AiTaskEntity.kt"
    ).read_text(encoding="utf-8")
    repository = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/service/JpaAiTaskRepository.kt"
    ).read_text(encoding="utf-8")
    adapter = Path(
        "backend/encounter-service/src/main/kotlin/com/example/healthcare/service/AiTaskRepository.kt"
    ).read_text(encoding="utf-8")

    assert "spring-boot-starter-data-jpa" in pom
    assert "<artifactId>postgresql</artifactId>" in pom
    assert "jdbc:postgresql://localhost:5432/healthcare" in application_yml
    assert "ddl-auto: update" in application_yml
    assert '@Table(name = "patient_encounters")' in entity
    assert "interface JpaAiTaskRepository : JpaRepository<AiTaskEntity, String>" in repository
    assert "private val repository: JpaAiTaskRepository" in adapter
    assert "repository.save" in adapter
    assert "repository.findById" in adapter
    assert "ConcurrentHashMap" not in adapter


def test_care_coordination_service_exposes_real_care_plan_api() -> None:
    base = Path("backend/care-coordination-service/src/main/kotlin/com/example/healthcare/care")
    controller = base / "controller/CareCoordinationController.kt"
    service = base / "service/CareCoordinationService.kt"
    request = base / "model/CareCoordinationRequest.kt"
    response = base / "model/CareCoordinationPlan.kt"

    assert controller.is_file()
    assert service.is_file()
    assert request.is_file()
    assert response.is_file()

    controller_text = controller.read_text(encoding="utf-8")
    service_text = service.read_text(encoding="utf-8")
    request_text = request.read_text(encoding="utf-8")
    response_text = response.read_text(encoding="utf-8")

    assert '@PostMapping("/api/care/coordination-plans")' in controller_text
    assert "fun createPlan" in controller_text
    assert "CareCoordinationService" in controller_text
    assert "coordinate(request: CareCoordinationRequest)" in service_text
    assert "disposition" in request_text
    assert "selectedSpecialties" in request_text
    assert "followUpActions" in response_text
    assert "referralActions" in response_text
    assert "admissionActions" in response_text
    assert "humanReviewRequired" in response_text
