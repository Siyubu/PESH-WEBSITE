package rw.pesh.enroll.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import rw.pesh.enroll.data.LearnerRepository
import rw.pesh.enroll.data.LoginResult
import rw.pesh.enroll.data.NewLearner
import rw.pesh.enroll.data.SessionManager

sealed class LoginUiState {
    data object Idle : LoginUiState()
    data object Loading : LoginUiState()
    data class Error(val message: String) : LoginUiState()
}

class AppViewModel(
    private val repository: LearnerRepository,
    val session: SessionManager,
) : ViewModel() {

    val learners = repository.learners
    val pendingCount = repository.pendingCount

    private val _loginState = MutableStateFlow<LoginUiState>(LoginUiState.Idle)
    val loginState: StateFlow<LoginUiState> = _loginState

    private val _saveMessage = MutableStateFlow<String?>(null)
    val saveMessage: StateFlow<String?> = _saveMessage

    fun login(baseUrl: String, email: String, password: String) {
        session.setBaseUrl(baseUrl)
        _loginState.value = LoginUiState.Loading
        viewModelScope.launch {
            _loginState.value = when (val result = repository.login(email, password)) {
                is LoginResult.Success -> LoginUiState.Idle
                is LoginResult.Failure -> LoginUiState.Error(result.message)
            }
        }
    }

    fun logOut() = session.logOut()

    fun addLearner(input: NewLearner) {
        viewModelScope.launch {
            repository.addLearner(input)
            _saveMessage.value = "Saved. It will sync automatically once online."
        }
    }

    fun clearSaveMessage() {
        _saveMessage.value = null
    }

    fun clearLoginError() {
        if (_loginState.value is LoginUiState.Error) _loginState.value = LoginUiState.Idle
    }

    class Factory(private val repository: LearnerRepository, private val session: SessionManager) :
        ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            return AppViewModel(repository, session) as T
        }
    }
}
