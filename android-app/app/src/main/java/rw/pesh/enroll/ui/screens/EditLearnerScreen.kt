package rw.pesh.enroll.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import rw.pesh.enroll.data.local.LearnerEntity
import rw.pesh.enroll.data.toInput
import rw.pesh.enroll.ui.AppViewModel

/** Fix a mistake made while registering. Saving sends the corrected details to the server on the next sync. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditLearnerScreen(viewModel: AppViewModel, clientId: String, onSyncNow: () -> Unit, onDone: () -> Unit) {
    val learners by viewModel.learners.collectAsState(initial = null)
    val learner = learners?.firstOrNull { it.clientId == clientId }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Edit learner") },
                navigationIcon = {
                    IconButton(onClick = onDone) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        },
    ) { padding ->
        when {
            learners == null -> Column(
                modifier = Modifier.padding(padding).fillMaxSize(),
                verticalArrangement = Arrangement.Center,
                horizontalAlignment = Alignment.CenterHorizontally,
            ) { CircularProgressIndicator() }

            learner == null -> Text(
                "This learner could not be found.",
                modifier = Modifier.padding(padding).padding(24.dp).fillMaxWidth(),
                textAlign = TextAlign.Center,
            )

            else -> Column(
                modifier = Modifier
                    .padding(padding)
                    .padding(20.dp)
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                if (learner.status == LearnerEntity.STATUS_ERROR && learner.errorMessage != null) {
                    Text(
                        "The server did not accept this learner: ${learner.errorMessage}",
                        color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
                Text(
                    "Changes are saved on this phone and sent to the server when you are online.",
                    style = MaterialTheme.typography.bodySmall,
                )
                LearnerForm(
                    initial = learner.toInput(),
                    formKey = learner.clientId,
                    submitLabel = "Save changes",
                    resetPersonalFieldsOnSubmit = false,
                    onSubmit = { input ->
                        viewModel.updateLearner(learner.clientId, input)
                        onSyncNow()
                        onDone()
                    },
                )
            }
        }
    }
}
