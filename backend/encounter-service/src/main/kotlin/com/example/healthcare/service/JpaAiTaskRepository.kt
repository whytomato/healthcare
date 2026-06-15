package com.example.healthcare.service

import com.example.healthcare.model.AiTaskEntity
import org.springframework.data.jpa.repository.JpaRepository

interface JpaAiTaskRepository : JpaRepository<AiTaskEntity, String>
