package com.example.healthcare.triage.service

import com.fasterxml.jackson.annotation.JsonIgnoreProperties
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import com.example.healthcare.triage.model.TriageAssessmentRequest
import com.example.healthcare.triage.model.TriageAssessmentResponse
import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.exists
import org.springframework.stereotype.Service

@Service
class TriageAssessmentService {
    private val policy = ClinicalPolicy.load()

    fun assess(request: TriageAssessmentRequest): TriageAssessmentResponse {
        val redFlags = matchedTerms(request.caseText, policy.urgentTerms.toSet())
        val urgencyLevel = if (redFlags.isNotEmpty()) "high" else "standard"
        val department = if (redFlags.isNotEmpty()) "emergency" else "general_medicine"
        return TriageAssessmentResponse(
            encounterId = request.encounterId,
            patientId = request.patientId,
            urgencyLevel = urgencyLevel,
            recommendedDepartment = department,
            redFlags = redFlags,
        )
    }

    private fun matchedTerms(text: String, terms: Set<String>): List<String> {
        return terms
            .filter { term ->
                termRegex(term).findAll(text).any { match ->
                    !isNegatedClinicalMention(text, match.range.first)
                }
            }
            .sorted()
    }

    private fun termRegex(term: String): Regex {
        if (term.any { it.code in 0x4e00..0x9fff }) {
            return Regex(Regex.escape(term), RegexOption.IGNORE_CASE)
        }
        val pattern = term
            .trim()
            .split(Regex("\\s+"))
            .joinToString("\\s+") { Regex.escape(it) }
        return Regex("\\b$pattern\\b", RegexOption.IGNORE_CASE)
    }

    private fun isNegatedClinicalMention(text: String, termStart: Int): Boolean {
        val segmentStart = lastSentenceBoundary(text, termStart)
        var segment = text.substring(segmentStart, termStart).lowercase()
        segment = afterLastContrast(segment)
        if (segment.length > 96) {
            segment = segment.takeLast(96)
        }

        return policy.negationCues.english.any { cuePresent(segment, it) } ||
            policy.negationCues.chinese.any { segment.contains(it) }
    }

    private fun lastSentenceBoundary(text: String, termStart: Int): Int {
        val boundaries = policy.sentenceBoundaries
            .map { text.lastIndexOf(it, startIndex = termStart.coerceAtLeast(0)) }
        val last = boundaries.maxOrNull() ?: -1
        return last + 1
    }

    private fun afterLastContrast(segment: String): String {
        val index = policy.contrastMarkers
            .map { marker ->
                val position = segment.lastIndexOf(marker)
                if (position >= 0) position + marker.length else -1
            }
            .maxOrNull() ?: -1
        return if (index >= 0) segment.substring(index) else segment
    }

    private fun cuePresent(segment: String, cue: String): Boolean {
        if (cue.contains(" ")) {
            return segment.contains(cue)
        }
        return Regex("\\b${Regex.escape(cue)}\\b").containsMatchIn(segment)
    }

    companion object {
        const val NEGATED_RED_FLAG_EXAMPLE = "no chest pain, confusion or severe shortness of breath"
    }
}

@JsonIgnoreProperties(ignoreUnknown = true)
data class ClinicalPolicy(
    val urgentTerms: List<String> = emptyList(),
    val negationCues: NegationCues = NegationCues(),
    val contrastMarkers: List<String> = emptyList(),
    val sentenceBoundaries: List<String> = emptyList(),
) {
    companion object {
        private val mapper = jacksonObjectMapper()
        private val candidatePaths = listOf(
            Path.of("config", "clinical-policy.json"),
            Path.of("..", "config", "clinical-policy.json"),
            Path.of("..", "..", "config", "clinical-policy.json"),
        )

        fun load(): ClinicalPolicy {
            val path = candidatePaths.firstOrNull { it.exists() }
                ?: error("config/clinical-policy.json was not found")
            return Files.newBufferedReader(path).use { reader -> mapper.readValue(reader) }
        }
    }
}

@JsonIgnoreProperties(ignoreUnknown = true)
data class NegationCues(
    val english: List<String> = emptyList(),
    val chinese: List<String> = emptyList(),
)
