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
    val age: Int,
    val grade: String,
    @Json(name = "is_student") val isStudent: Boolean,
    val school: String,
    @Json(name = "created_at") val createdAt: String,
)

data class LearnerSyncResponse(
    @Json(name = "client_id") val clientId: String,
)
