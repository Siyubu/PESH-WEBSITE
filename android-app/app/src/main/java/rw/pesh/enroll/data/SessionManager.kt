package rw.pesh.enroll.data

import android.content.Context
import android.content.SharedPreferences
import androidx.core.content.edit
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import rw.pesh.enroll.BuildConfig

/** Staff login token + chosen server address. Deliberately simple (plain SharedPreferences) --
 *  see the project README for a note on hardening this with EncryptedSharedPreferences. */
class SessionManager(context: Context) {
    private val prefs: SharedPreferences =
        context.applicationContext.getSharedPreferences("pesh_session", Context.MODE_PRIVATE)

    private val _token = MutableStateFlow(prefs.getString(KEY_TOKEN, null))
    val token: StateFlow<String?> = _token

    private val _staffName = MutableStateFlow(prefs.getString(KEY_STAFF_NAME, null))
    val staffName: StateFlow<String?> = _staffName

    private val _baseUrl = MutableStateFlow(prefs.getString(KEY_BASE_URL, null) ?: BuildConfig.DEFAULT_API_BASE_URL)
    val baseUrl: StateFlow<String> = _baseUrl

    private val _sessionExpired = MutableStateFlow(prefs.getBoolean(KEY_EXPIRED, false))
    /** True when the server ended the login (logins last at most 24 hours), as opposed to the user tapping log out. */
    val sessionExpired: StateFlow<Boolean> = _sessionExpired

    fun setBaseUrl(url: String) {
        prefs.edit { putString(KEY_BASE_URL, url) }
        _baseUrl.value = url
    }

    fun onLoggedIn(token: String, staffName: String) {
        prefs.edit {
            putString(KEY_TOKEN, token)
            putString(KEY_STAFF_NAME, staffName)
            putBoolean(KEY_EXPIRED, false)
        }
        _sessionExpired.value = false
        _token.value = token
        _staffName.value = staffName
    }

    fun logOut(expired: Boolean = false) {
        prefs.edit {
            remove(KEY_TOKEN)
            remove(KEY_STAFF_NAME)
            putBoolean(KEY_EXPIRED, expired)
        }
        _sessionExpired.value = expired
        _token.value = null
        _staffName.value = null
    }

    fun authHeader(): String? = _token.value?.let { "Token $it" }

    companion object {
        private const val KEY_TOKEN = "token"
        private const val KEY_STAFF_NAME = "staff_name"
        private const val KEY_BASE_URL = "base_url"
        private const val KEY_EXPIRED = "session_expired"
    }
}
