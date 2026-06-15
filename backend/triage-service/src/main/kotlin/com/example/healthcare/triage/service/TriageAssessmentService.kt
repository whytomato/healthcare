package com.example.healthcare.triage.service

import com.example.healthcare.triage.model.TriageAssessmentRequest
import com.example.healthcare.triage.model.TriageAssessmentResponse
import org.springframework.stereotype.Service

@Service
class TriageAssessmentService {
    fun assess(request: TriageAssessmentRequest): TriageAssessmentResponse {
        val redFlags = matchedTerms(request.caseText, urgentTerms)
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

        val englishCues = listOf(
            "no evidence of",
            "negative for",
            "not experiencing",
            "denies",
            "denied",
            "deny",
            "without",
            "free of",
            "absence of",
            "no",
        )
        val chineseCues = listOf("没有", "未见", "未出现", "否认", "不伴", "无", "未")
        return englishCues.any { cuePresent(segment, it) } || chineseCues.any { segment.contains(it) }
    }

    private fun lastSentenceBoundary(text: String, termStart: Int): Int {
        val boundaries = listOf(".", "?", "!", "\n", ";", "。", "？", "！", "；")
            .map { text.lastIndexOf(it, startIndex = termStart.coerceAtLeast(0)) }
        val last = boundaries.maxOrNull() ?: -1
        return last + 1
    }

    private fun afterLastContrast(segment: String): String {
        val markers = listOf(" but ", " however ", " though ", " except ", "但", "但是", "不过")
        val index = markers
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

        private val urgentTerms = setOf(
            "chest discomfort",
            "chest pain",
            "shortness of breath",
            "confusion",
            "severe headache",
            "neck stiffness",
            "high fever",
            "seizure",
            "hemoptysis",
            "胸痛",
            "胸闷",
            "呼吸困难",
            "意识模糊",
            "高热",
            "抽搐",
            "咯血",
            "颈项强直",
        )
    }
}
