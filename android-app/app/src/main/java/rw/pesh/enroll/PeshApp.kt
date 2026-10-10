package rw.pesh.enroll

import android.app.Application
import androidx.work.Configuration
import rw.pesh.enroll.data.LearnerRepository
import rw.pesh.enroll.data.SessionManager
import rw.pesh.enroll.data.local.AppDatabase
import rw.pesh.enroll.sync.AppWorkerFactory
import rw.pesh.enroll.sync.SyncScheduler

class PeshApp : Application(), Configuration.Provider {

    val session: SessionManager by lazy { SessionManager(this) }
    private val database: AppDatabase by lazy { AppDatabase.build(this) }
    val repository: LearnerRepository by lazy { LearnerRepository(database.learnerDao(), session) }

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setWorkerFactory(AppWorkerFactory(repository))
            .build()

    override fun onCreate() {
        super.onCreate()
        SyncScheduler.schedulePeriodicSync(this)
    }
}
