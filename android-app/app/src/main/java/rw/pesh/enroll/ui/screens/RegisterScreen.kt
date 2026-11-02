package rw.pesh.enroll.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import rw.pesh.enroll.ui.AppViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RegisterScreen(viewModel: AppViewModel, onOpenLearners: () -> Unit, onSyncNow: () -> Unit) {
    val staffName by viewModel.session.staffName.collectAsState()
    val pendingCount by viewModel.pendingCount.collectAsState(initial = 0)
    val saveMessage by viewModel.saveMessage.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(saveMessage) {
        saveMessage?.let {
            snackbarHostState.showSnackbar(it)
            viewModel.clearSaveMessage()
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = { Text(staffName?.let { "Register a learner - $it" } ?: "Register a learner") },
                actions = {
                    IconButton(onClick = onOpenLearners) {
                        BadgedBox(badge = { if (pendingCount > 0) Badge { Text(pendingCount.toString()) } }) {
                            Icon(Icons.AutoMirrored.Filled.List, contentDescription = "Registered learners")
                        }
                    }
                    IconButton(onClick = { viewModel.logOut() }) {
                        Icon(Icons.AutoMirrored.Filled.Logout, contentDescription = "Log out")
                    }
                },
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .padding(20.dp)
                .fillMaxSize()
                .verticalScroll(rememberScrollState()),
            verticalArrangement = androidx.compose.foundation.layout.Arrangement.spacedBy(14.dp),
        ) {
            Text(
                "Works with no internet. Saved learners sync automatically once you're back online.",
                style = MaterialTheme.typography.bodySmall,
            )
            LearnerForm(
                initial = null,
                formKey = "register",
                submitLabel = "Save learner",
                resetPersonalFieldsOnSubmit = true,
                onSubmit = { input ->
                    viewModel.addLearner(input)
                    onSyncNow() // opportunistic: sends it now if online, otherwise WorkManager just queues it
                },
            )
        }
    }
}
