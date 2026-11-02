package rw.pesh.enroll.data.remote

import com.squareup.moshi.Json

data class LoginRequest(
    val email: String,
    val password: String,
)

data class LoginResponse(
    val token: String,
    @Json(name = "staff_name") val staffName: String,
)

data class LearnerSyncRequest(
    @Json(name = "client_id") val clientId: String,
    @Json(name = "first_name") val firstName: String,
    @Json(name = "last_name") val lastName: String,
    val country: String,
    @Json(name = "date_of_birth") val dateOfBirth: String,
    @Json(name = "is_student") val isStudent: Boolean,
    val grade: String,
    val school: String,
    @Json(name = "created_at") val createdAt: String,
    @Json(name = "client_updated_at") val updatedAt: String,
)

data class LearnerSyncResponse(
    @Json(name = "client_id") val clientId: String,
)
