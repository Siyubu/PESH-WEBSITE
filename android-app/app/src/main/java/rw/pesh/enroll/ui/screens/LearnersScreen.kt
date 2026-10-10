package rw.pesh.enroll.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Sync
import androidx.compose.material3.Card
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import rw.pesh.enroll.data.local.LearnerEntity
import rw.pesh.enroll.ui.AppViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LearnersScreen(viewModel: AppViewModel, onSyncNow: () -> Unit, onBack: () -> Unit) {
    val learners by viewModel.learners.collectAsState(initial = emptyList())

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Registered learners (${learners.size})") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = onSyncNow) {
                        Icon(Icons.Filled.Sync, contentDescription = "Sync now")
                    }
                },
            )
        },
    ) { padding ->
        if (learners.isEmpty()) {
            Column(
                modifier = Modifier.padding(padding).fillMaxSize(),
                verticalArrangement = Arrangement.Center,
            ) {
                Text("No learners registered yet.", modifier = Modifier.fillMaxWidth(), textAlign = TextAlign.Center)
            }
        } else {
            LazyColumn(modifier = Modifier.padding(padding).fillMaxSize().padding(horizontal = 12.dp)) {
                items(learners, key = { it.clientId }) { learner -> LearnerRow(learner) }
            }
        }
    }
}

@Composable
private fun LearnerRow(learner: LearnerEntity) {
    Card(modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(14.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column {
                Text("${learner.firstName} ${learner.lastName}", style = MaterialTheme.typography.titleMedium)
                Text("${learner.country}", style = MaterialTheme.typography.bodySmall)
                if (learner.status == LearnerEntity.STATUS_ERROR && learner.errorMessage != null) {
                    Text(learner.errorMessage, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                }
            }
            StatusChip(learner.status)
        }
    }
}

@Composable
private fun StatusChip(status: String) {
    val (label, color) = when (status) {
        LearnerEntity.STATUS_SYNCED -> "Synced" to Color(0xFF2E7D32)
        LearnerEntity.STATUS_ERROR -> "Error" to Color(0xFFC62828)
        else -> "Pending" to Color(0xFFB8860B)
    }
    Text(label, color = color, style = MaterialTheme.typography.labelLarge)
}
