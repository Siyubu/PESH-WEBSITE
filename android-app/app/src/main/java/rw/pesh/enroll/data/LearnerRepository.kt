package rw.pesh.enroll.data

import kotlinx.coroutines.flow.Flow
import okio.IOException
import org.json.JSONArray
import org.json.JSONObject
import retrofit2.Response
import rw.pesh.enroll.data.local.LearnerDao
import rw.pesh.enroll.data.local.LearnerEntity
import rw.pesh.enroll.data.remote.ApiClientProvider
import rw.pesh.enroll.data.remote.LearnerSyncRequest
import rw.pesh.enroll.data.remote.LoginRequest
import java.time.Instant
import java.util.UUID

/** What the form collects. Grade and school are only meaningful (and only kept) when [isStudent] is true. */
data class LearnerInput(
    val firstName: String,
    val lastName: String,
    val country: String,
    /** ISO date, yyyy-MM-dd. */
    val dateOfBirth: String,
    val isStudent: Boolean,
    val grade: String,
    val school: String,
)

fun LearnerEntity.toInput() = LearnerInput(
    firstName = firstName,
    lastName = lastName,
    country = country,
    dateOfBirth = dateOfBirth,
    isStudent = isStudent,
    grade = grade,
    school = school,
)

sealed class LoginResult {
    data object Success : LoginResult()
    data class Failure(val message: String) : LoginResult()
}

class LearnerRepository(
    private val dao: LearnerDao,
    private val session: SessionManager,
) {
    val learners: Flow<List<LearnerEntity>> = dao.observeAll()
    val pendingCount: Flow<Int> = dao.observeCount(LearnerEntity.STATUS_PENDING)

    suspend fun login(email: String, password: String): LoginResult {
        val api = ApiClientProvider.get(session.baseUrl.value)
        return try {
            val response = api.login(LoginRequest(email.trim(), password))
            val body = response.body()
            if (response.isSuccessful && body != null) {
                session.onLoggedIn(body.token, body.staffName)
                LoginResult.Success
            } else {
                LoginResult.Failure(parseError(response))
            }
        } catch (e: IOException) {
            LoginResult.Failure("Could not reach the server. Check the address and your connection.")
        }
    }

    /** Saves immediately to the local database. Works with no network at all; sync happens later. */
    suspend fun addLearner(input: LearnerInput) {
        val now = Instant.now().toString()
        dao.insert(
            LearnerEntity(
                clientId = UUID.randomUUID().toString(),
                firstName = input.firstName.trim(),
                lastName = input.lastName.trim(),
                country = input.country.trim(),
                dateOfBirth = input.dateOfBirth,
                grade = if (input.isStudent) input.grade.trim() else "",
                isStudent = input.isStudent,
                school = if (input.isStudent) input.school.trim() else "",
                createdAtIso = now,
                updatedAtIso = now,
                status = LearnerEntity.STATUS_PENDING,
            ),
        )
    }

    /** Corrects a saved learner. It goes back to PENDING and the next sync sends the corrected version. */
    suspend fun updateLearner(clientId: String, input: LearnerInput) {
        val existing = dao.getById(clientId) ?: return
        dao.update(
            existing.copy(
                firstName = input.firstName.trim(),
                lastName = input.lastName.trim(),
                country = input.country.trim(),
                dateOfBirth = input.dateOfBirth,
                grade = if (input.isStudent) input.grade.trim() else "",
                isStudent = input.isStudent,
                school = if (input.isStudent) input.school.trim() else "",
                updatedAtIso = Instant.now().toString(),
                status = LearnerEntity.STATUS_PENDING,
                errorMessage = null,
            ),
        )
    }

    /**
     * Sends every not-yet-synced record (new ones and edited ones), one at a time. Never throws: a network
     * hiccup on one record just leaves it PENDING for the next sync attempt. An expired or invalid login
     * (the server ends logins after 24 hours) logs the device out so the mentor signs in again, instead of
     * retrying forever. Saved learners stay on the phone and sync after the next login.
     */
    suspend fun syncPending() {
        val token = session.authHeader() ?: return
        val pending = dao.getUnsynced()
        if (pending.isEmpty()) return

        val api = ApiClientProvider.get(session.baseUrl.value)
        for (learner in pending) {
            if (session.authHeader() == null) break // logged out mid-batch (see the 401 case below)
            try {
                val response = api.syncLearner(token, learner.toRequest())
                when {
                    response.isSuccessful ->
                        dao.updateStatusIfUnchanged(learner.clientId, learner.updatedAtIso, LearnerEntity.STATUS_SYNCED)
                    response.code() == 401 -> session.logOut(expired = true)
                    response.code() in 400..499 ->
                        dao.updateStatusIfUnchanged(
                            learner.clientId,
                            learner.updatedAtIso,
                            LearnerEntity.STATUS_ERROR,
                            parseError(response),
                        )
                    else -> { /* server/network hiccup: leave PENDING, a later sync retries it */ }
                }
            } catch (e: IOException) {
                // no connection right now; leave PENDING for the next attempt
            }
        }
    }

    /** Server errors come back as {"error": "..."} or, for form problems, {"grade": ["Grade is required..."]}. */
    private fun parseError(response: Response<*>): String {
        val fallback = "The server rejected this (code ${response.code()})."
        val raw = response.errorBody()?.string()
        if (raw.isNullOrBlank()) return fallback
        return try {
            val json = JSONObject(raw)
            val parts = mutableListOf<String>()
            json.optString("error").takeIf { it.isNotBlank() }?.let { parts += it }
            json.keys().forEach { key ->
                if (key == "error") return@forEach
                when (val value = json.opt(key)) {
                    is JSONArray -> for (i in 0 until value.length()) parts += value.optString(i)
                    is String -> parts += value
                }
            }
            parts.joinToString(" ").ifBlank { fallback }
        } catch (e: Exception) {
            fallback
        }
    }
}

private fun LearnerEntity.toRequest() = LearnerSyncRequest(
    clientId = clientId,
    firstName = firstName,
    lastName = lastName,
    country = country,
    dateOfBirth = dateOfBirth,
    isStudent = isStudent,
    grade = grade,
    school = school,
    createdAt = createdAtIso,
    updatedAt = updatedAtIso,
)
