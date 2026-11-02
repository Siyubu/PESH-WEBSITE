package rw.pesh.enroll.ui.nav

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.navArgument
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import rw.pesh.enroll.ui.AppViewModel
import rw.pesh.enroll.ui.screens.EditLearnerScreen
import rw.pesh.enroll.ui.screens.LearnersScreen
import rw.pesh.enroll.ui.screens.LoginScreen
import rw.pesh.enroll.ui.screens.RegisterScreen

private object Routes {
    const val LOGIN = "login"
    const val REGISTER = "register"
    const val LEARNERS = "learners"
    const val EDIT = "edit/{clientId}"
    fun edit(clientId: String) = "edit/$clientId"
}

@Composable
fun PeshNavHost(viewModel: AppViewModel, onSyncNow: () -> Unit) {
    val navController: NavHostController = rememberNavController()
    val token by viewModel.session.token.collectAsState()
    var wasLoggedIn by remember { mutableStateOf(token != null) }

    // Jumps screens only when login state actually flips (login, or a 401 forcing a logout mid-sync) --
    // not on every recomposition, so normal navigation within the app isn't disturbed.
    LaunchedEffect(token) {
        val loggedIn = token != null
        if (loggedIn != wasLoggedIn) {
            navController.navigate(if (loggedIn) Routes.REGISTER else Routes.LOGIN) {
                popUpTo(0) { inclusive = true }
            }
            // Learners saved while logged out (e.g. after the 24-hour login expired) should go up right away.
            if (loggedIn) onSyncNow()
        }
        wasLoggedIn = loggedIn
    }

    NavHost(
        navController = navController,
        startDestination = if (token == null) Routes.LOGIN else Routes.REGISTER,
    ) {
        composable(Routes.LOGIN) {
            LoginScreen(viewModel = viewModel)
        }
        composable(Routes.REGISTER) {
            RegisterScreen(viewModel = viewModel, onOpenLearners = { navController.navigate(Routes.LEARNERS) }, onSyncNow = onSyncNow)
        }
        composable(Routes.LEARNERS) {
            LearnersScreen(
                viewModel = viewModel,
                onSyncNow = onSyncNow,
                onBack = { navController.popBackStack() },
                onEdit = { navController.navigate(Routes.edit(it)) },
            )
        }
        composable(Routes.EDIT, arguments = listOf(navArgument("clientId") { type = NavType.StringType })) { entry ->
            EditLearnerScreen(
                viewModel = viewModel,
                clientId = entry.arguments?.getString("clientId").orEmpty(),
                onSyncNow = onSyncNow,
                onDone = { navController.popBackStack() },
            )
        }
    }
}
