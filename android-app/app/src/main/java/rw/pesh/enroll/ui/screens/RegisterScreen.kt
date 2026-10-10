package rw.pesh.enroll.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import rw.pesh.enroll.data.NewLearner
import rw.pesh.enroll.ui.AppViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RegisterScreen(viewModel: AppViewModel, onOpenLearners: () -> Unit, onSyncNow: () -> Unit) {
    val staffName by viewModel.session.staffName.collectAsState()
    val pendingCount by viewModel.pendingCount.collectAsState(initial = 0)
    val saveMessage by viewModel.saveMessage.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    var firstName by rememberSaveable { mutableStateOf("") }
    var lastName by rememberSaveable { mutableStateOf("") }
    var country by rememberSaveable { mutableStateOf("") }
    var age by rememberSaveable { mutableStateOf("") }
    var grade by rememberSaveable { mutableStateOf("") }
    var isStudent by rememberSaveable { mutableStateOf(true) }
    var school by rememberSaveable { mutableStateOf("") }
    var attemptedSubmit by rememberSaveable { mutableStateOf(false) }

    val ageValue = age.toIntOrNull()
    val ageError = attemptedSubmit && (ageValue == null || ageValue < 3 || ageValue > 100)
    val schoolError = attemptedSubmit && isStudent && school.isBlank()
    val formValid = firstName.isNotBlank() && lastName.isNotBlank() && country.isNotBlank() &&
        grade.isNotBlank() && ageValue != null && ageValue in 3..100 && (!isStudent || school.isNotBlank())

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
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Text(
                "Works with no internet. Saved learners sync automatically once you're back online.",
                style = MaterialTheme.typography.bodySmall,
            )

            OutlinedTextField(value = firstName, onValueChange = { firstName = it }, label = { Text("First name") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            OutlinedTextField(value = lastName, onValueChange = { lastName = it }, label = { Text("Last name") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            OutlinedTextField(value = country, onValueChange = { country = it }, label = { Text("Country of origin") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            OutlinedTextField(
                value = age,
                onValueChange = { if (it.length <= 3) age = it.filter(Char::isDigit) },
                label = { Text("Age") },
                singleLine = true,
                isError = ageError,
                supportingText = { if (ageError) Text("Enter a realistic age (3-100).") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
            )
            OutlinedTextField(value = grade, onValueChange = { grade = it }, label = { Text("Grade (e.g. P5, S3)") }, singleLine = true, modifier = Modifier.fillMaxWidth())

            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Currently a student?")
                Switch(checked = isStudent, onCheckedChange = { isStudent = it })
            }
            if (isStudent) {
                OutlinedTextField(
                    value = school,
                    onValueChange = { school = it },
                    label = { Text("School") },
                    singleLine = true,
                    isError = schoolError,
                    supportingText = { if (schoolError) Text("School is required for students.") },
                    modifier = Modifier.fillMaxWidth(),
                )
            }

            Button(
                onClick = {
                    attemptedSubmit = true
                    if (formValid) {
                        viewModel.addLearner(NewLearner(firstName, lastName, country, ageValue!!, grade, isStudent, school))
                        onSyncNow() // opportunistic: sends it now if online, otherwise WorkManager just queues it
                        // Country/grade/school/student-status usually repeat for the next learner in the same
                        // group (a whole classroom signed up in one sitting), so only the per-person fields reset.
                        firstName = ""
                        lastName = ""
                        age = ""
                        attemptedSubmit = false
                    }
                },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Save learner")
            }
        }
    }
}
