package com.example.healthcare.model

data class AiSymptomResultMessage(
    val taskId: String = "",
    val status: String = "",
    val result: Any? = null,
    val errorMessage: String? = null,
)
