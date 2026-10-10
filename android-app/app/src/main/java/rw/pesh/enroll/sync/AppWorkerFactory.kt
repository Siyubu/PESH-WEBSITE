package rw.pesh.enroll.sync

import android.content.Context
import androidx.work.WorkerFactory
import androidx.work.WorkerParameters
import rw.pesh.enroll.data.LearnerRepository

/** Lets SyncWorker receive the repository directly instead of needing a no-argument constructor. */
class AppWorkerFactory(private val repository: LearnerRepository) : WorkerFactory() {
    override fun createWorker(
        appContext: Context,
        workerClassName: String,
        workerParameters: WorkerParameters,
    ) = when (workerClassName) {
        SyncWorker::class.java.name -> SyncWorker(appContext, workerParameters, repository)
        else -> null
    }
}
