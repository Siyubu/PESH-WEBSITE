package rw.pesh.enroll.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material3.Button
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.SelectableDates
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import rw.pesh.enroll.data.LearnerInput
import rw.pesh.enroll.ui.Countries
import java.time.Instant
import java.time.LocalDate
import java.time.Period
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.util.Locale

private const val MIN_AGE = 3
private const val MAX_AGE = 100
private val DISPLAY_DATE = DateTimeFormatter.ofPattern("d MMM yyyy", Locale.ENGLISH)

private fun LocalDate.toUtcMillis(): Long = atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli()

/**
 * The learner fields, shared by "Register" and "Edit". Grade and school are only asked (and kept) for students.
 *
 * [formKey] identifies which learner the saved field values belong to, so editing one learner never shows
 * another's text. [resetPersonalFieldsOnSubmit] clears name and birth date for the next person in a batch while
 * keeping country, student status, grade and school, which usually repeat for a whole classroom.
 */
@Composable
fun LearnerForm(
    initial: LearnerInput?,
    formKey: String,
    submitLabel: String,
    resetPersonalFieldsOnSubmit: Boolean,
    onSubmit: (LearnerInput) -> Unit,
    modifier: Modifier = Modifier,
) {
    var firstName by rememberSaveable(formKey) { mutableStateOf(initial?.firstName ?: "") }
    var lastName by rememberSaveable(formKey) { mutableStateOf(initial?.lastName ?: "") }
    var country by rememberSaveable(formKey) { mutableStateOf(initial?.country ?: "") }
    var dateOfBirth by rememberSaveable(formKey) { mutableStateOf(initial?.dateOfBirth ?: "") }
    var isStudent by rememberSaveable(formKey) { mutableStateOf(initial?.isStudent ?: true) }
    var grade by rememberSaveable(formKey) { mutableStateOf(initial?.grade ?: "") }
    var school by rememberSaveable(formKey) { mutableStateOf(initial?.school ?: "") }
    var attemptedSubmit by rememberSaveable(formKey) { mutableStateOf(false) }

    val dob = runCatching { LocalDate.parse(dateOfBirth) }.getOrNull()
    val ageYears = dob?.let { Period.between(it, LocalDate.now()).years }
    val dobValid = dob != null && !dob.isAfter(LocalDate.now()) && ageYears != null && ageYears in MIN_AGE..MAX_AGE
    val countryValid = country in Countries.all
    val gradeValid = !isStudent || grade.isNotBlank()
    val schoolValid = !isStudent || school.isNotBlank()
    val formValid = firstName.isNotBlank() && lastName.isNotBlank() && countryValid && dobValid && gradeValid && schoolValid

    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(14.dp)) {
        OutlinedTextField(
            value = firstName,
            onValueChange = { firstName = it },
            label = { Text("First name") },
            singleLine = true,
            isError = attemptedSubmit && firstName.isBlank(),
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = lastName,
            onValueChange = { lastName = it },
            label = { Text("Last name") },
            singleLine = true,
            isError = attemptedSubmit && lastName.isBlank(),
            modifier = Modifier.fillMaxWidth(),
        )
        CountryDropdown(
            selected = country,
            onSelected = { country = it },
            isError = attemptedSubmit && !countryValid,
        )
        DateOfBirthField(
            isoDate = dateOfBirth,
            onPicked = { dateOfBirth = it },
            isError = attemptedSubmit && !dobValid,
            ageYears = if (dobValid) ageYears else null,
        )

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
                value = grade,
                onValueChange = { grade = it },
                label = { Text("Grade (e.g. P5, S3)") },
                singleLine = true,
                isError = attemptedSubmit && !gradeValid,
                supportingText = { if (attemptedSubmit && !gradeValid) Text("Grade is required for students.") },
                modifier = Modifier.fillMaxWidth(),
            )
            OutlinedTextField(
                value = school,
                onValueChange = { school = it },
                label = { Text("School") },
                singleLine = true,
                isError = attemptedSubmit && !schoolValid,
                supportingText = { if (attemptedSubmit && !schoolValid) Text("School is required for students.") },
                modifier = Modifier.fillMaxWidth(),
            )
        }

        Button(
            onClick = {
                attemptedSubmit = true
                if (formValid) {
                    onSubmit(
                        LearnerInput(
                            firstName = firstName.trim(),
                            lastName = lastName.trim(),
                            country = country,
                            dateOfBirth = dateOfBirth,
                            isStudent = isStudent,
                            grade = if (isStudent) grade.trim() else "",
                            school = if (isStudent) school.trim() else "",
                        ),
                    )
                    if (resetPersonalFieldsOnSubmit) {
                        firstName = ""
                        lastName = ""
                        dateOfBirth = ""
                        attemptedSubmit = false
                    }
                }
            },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(submitLabel)
        }
    }
}

/** Type to search or tap to browse; only a country from the list counts as chosen. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun CountryDropdown(selected: String, onSelected: (String) -> Unit, isError: Boolean) {
    var expanded by remember { mutableStateOf(false) }
    var query by remember { mutableStateOf(selected) }
    LaunchedEffect(selected) { if (selected.isNotEmpty()) query = selected }

    val options = if (query.isBlank() || query == selected) {
        Countries.all
    } else {
        Countries.all.filter { it.contains(query.trim(), ignoreCase = true) }
    }

    ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
        OutlinedTextField(
            value = query,
            onValueChange = {
                query = it
                expanded = true
                if (it != selected) onSelected("")
            },
            label = { Text("Country of origin") },
            singleLine = true,
            isError = isError,
            supportingText = { if (isError) Text("Pick a country from the list.") },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            modifier = Modifier
                .menuAnchor()
                .fillMaxWidth(),
        )
        ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = {
                expanded = false
                query = selected
            },
        ) {
            if (options.isEmpty()) {
                DropdownMenuItem(text = { Text("No match") }, onClick = {}, enabled = false)
            }
            options.forEach { name ->
                DropdownMenuItem(
                    text = { Text(name) },
                    onClick = {
                        onSelected(name)
                        query = name
                        expanded = false
                    },
                )
            }
        }
    }
}

/** A read-only field that opens a calendar. The saved value is an ISO date (yyyy-MM-dd). */
@Composable
private fun DateOfBirthField(isoDate: String, onPicked: (String) -> Unit, isError: Boolean, ageYears: Int?) {
    var showPicker by remember { mutableStateOf(false) }
    val shown = runCatching { LocalDate.parse(isoDate).format(DISPLAY_DATE) }.getOrDefault("")
    val colors = MaterialTheme.colorScheme

    Box(modifier = Modifier.fillMaxWidth()) {
        // Disabled so the keyboard never opens; the overlay below receives the tap instead.
        OutlinedTextField(
            value = shown,
            onValueChange = {},
            enabled = false,
            label = { Text("Date of birth") },
            singleLine = true,
            isError = isError,
            trailingIcon = { Icon(Icons.Filled.DateRange, contentDescription = "Choose date of birth") },
            supportingText = {
                when {
                    isError -> Text("Choose a date of birth (age $MIN_AGE-$MAX_AGE).")
                    ageYears != null -> Text("Age: $ageYears")
                }
            },
            colors = OutlinedTextFieldDefaults.colors(
                disabledTextColor = colors.onSurface,
                disabledBorderColor = if (isError) colors.error else colors.outline,
                disabledLabelColor = if (isError) colors.error else colors.onSurfaceVariant,
                disabledTrailingIconColor = colors.onSurfaceVariant,
                disabledSupportingTextColor = if (isError) colors.error else colors.onSurfaceVariant,
            ),
            modifier = Modifier.fillMaxWidth(),
        )
        Box(
            modifier = Modifier
                .matchParentSize()
                .clickable(onClickLabel = "Choose date of birth", role = Role.Button) { showPicker = true },
        )
    }

    if (showPicker) {
        DateOfBirthDialog(
            initialIso = isoDate,
            onDismiss = { showPicker = false },
            onPicked = {
                onPicked(it.toString())
                showPicker = false
            },
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DateOfBirthDialog(initialIso: String, onDismiss: () -> Unit, onPicked: (LocalDate) -> Unit) {
    val today = LocalDate.now()
    val initial = runCatching { LocalDate.parse(initialIso) }.getOrNull()
    val state = rememberDatePickerState(
        initialSelectedDateMillis = initial?.toUtcMillis(),
        // Learners are mostly children: open around ten years ago rather than today.
        initialDisplayedMonthMillis = (initial ?: today.minusYears(10)).toUtcMillis(),
        yearRange = (today.year - MAX_AGE)..today.year,
        selectableDates = object : SelectableDates {
            override fun isSelectableDate(utcTimeMillis: Long): Boolean = utcTimeMillis <= today.toUtcMillis()
        },
    )
    DatePickerDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            TextButton(
                enabled = state.selectedDateMillis != null,
                onClick = {
                    state.selectedDateMillis?.let {
                        onPicked(Instant.ofEpochMilli(it).atZone(ZoneOffset.UTC).toLocalDate())
                    }
                },
            ) { Text("OK") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } },
    ) {
        DatePicker(state = state)
    }
}
