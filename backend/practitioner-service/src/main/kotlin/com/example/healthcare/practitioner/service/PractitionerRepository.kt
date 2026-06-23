package com.example.healthcare.practitioner.service

import com.example.healthcare.practitioner.model.PractitionerEntity
import jakarta.persistence.LockModeType
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Lock

interface PractitionerRepository : JpaRepository<PractitionerEntity, String> {
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    fun findBySpecialtyAndOnShiftTrue(specialty: String): List<PractitionerEntity>
}
