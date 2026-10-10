package rw.pesh.enroll.data.remote

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.POST

interface ApiService {

    @POST("mobile/login/")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>

    @POST("mobile/offline-learners/")
    suspend fun syncLearner(
        @Header("Authorization") authorization: String,
        @Body request: LearnerSyncRequest,
    ): Response<LearnerSyncResponse>
}
