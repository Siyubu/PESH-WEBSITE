package rw.pesh.enroll.data

import kotlinx.coroutines.flow.Flow
import okio.IOException
import org.json.JSONObject
import retrofit2.Response
import rw.pesh.enroll.data.local.LearnerDao
import rw.pesh.enroll.data.local.LearnerEntity
import rw.pesh.enroll.data.remote.ApiClientProvider
import rw.pesh.enroll.data.remote.LearnerSyncRequest
import rw.pesh.enroll.data.remote.LoginRequest
import java.time.Instant
import java.util.UUID

data class NewLearner(
    val firstName: String,
    val lastName: String,
    val country: String,
    val age: Int,
    val grade: String,
    val isStudent: Boolean,
    val school: String,
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
    suspend fun addLearner(input: NewLearner) {
        val entity = LearnerEntity(
            clientId = UUID.randomUUID().toString(),
            firstName = input.firstName.trim(),
            lastName = input.lastName.trim(),
            country = input.country.trim(),
            age = input.age,
            grade = input.grade.trim(),
            isStudent = input.isStudent,
            school = if (input.isStudent) input.school.trim() else "",
            createdAtIso = Instant.now().toString(),
            status = LearnerEntity.STATUS_PENDING,
        )
        dao.insert(entity)
    }

    /**
     * Sends every not-yet-synced record, one at a time. Never throws: a network hiccup on one
     * record just leaves it PENDING for the next sync attempt. An expired/invalid token logs the
     * device out so the mentor is prompted to sign in again, rather than retrying forever.
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
                    response.isSuccessful -> dao.updateStatus(learner.clientId, LearnerEntity.STATUS_SYNCED)
                    response.code() == 401 -> session.logOut()
                    response.code() in 400..499 ->
                        dao.updateStatus(learner.clientId, LearnerEntity.STATUS_ERROR, parseError(response))
                    else -> { /* server/network hiccup: leave PENDING, a later sync retries it */ }
                }
            } catch (e: IOException) {
                // no connection right now; leave PENDING for the next attempt
            }
        }
    }

    private fun parseError(response: Response<*>): String {
        val raw = response.errorBody()?.string()
        val fallback = "The server rejected this (code ${response.code()})."
        if (raw.isNullOrBlank()) return fallback
        return try {
            JSONObject(raw).optString("error").ifBlank { fallback }
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
    age = age,
    grade = grade,
    isStudent = isStudent,
    school = school,
    createdAt = createdAtIso,
)
