package rw.pesh.enroll.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "learners")
data class LearnerEntity(
    @PrimaryKey val clientId: String,
    val firstName: String,
    val lastName: String,
    val country: String,
    val age: Int,
    val grade: String,
    val isStudent: Boolean,
    val school: String,
    val createdAtIso: String,
    val status: String = STATUS_PENDING,
    val errorMessage: String? = null,
) {
    companion object {
        const val STATUS_PENDING = "PENDING"
        const val STATUS_SYNCED = "SYNCED"
        const val STATUS_ERROR = "ERROR"
    }
}
