package rw.pesh.enroll.sync

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import rw.pesh.enroll.data.LearnerRepository

class SyncWorker(
    context: Context,
    params: WorkerParameters,
    private val repository: LearnerRepository,
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        return try {
            repository.syncPending()
            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }
}
