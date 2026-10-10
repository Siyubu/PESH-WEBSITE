package rw.pesh.enroll.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.viewmodel.compose.viewModel
import rw.pesh.enroll.PeshApp
import rw.pesh.enroll.sync.SyncScheduler
import rw.pesh.enroll.ui.nav.PeshNavHost
import rw.pesh.enroll.ui.theme.PeshTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val app = application as PeshApp
        SyncScheduler.syncNow(applicationContext)

        setContent {
            PeshTheme {
                val viewModel: AppViewModel = viewModel(factory = AppViewModel.Factory(app.repository, app.session))
                PeshNavHost(viewModel = viewModel, onSyncNow = { SyncScheduler.syncNow(applicationContext) })
            }
        }
    }
}
