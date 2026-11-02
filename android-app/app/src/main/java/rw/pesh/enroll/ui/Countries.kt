package rw.pesh.enroll.ui

import java.util.Locale

object Countries {
    const val HOME = "Rwanda"
    const val OTHER = "Other"

    /** Rwanda first (most learners), then every country A-Z from the phone's own list, then "Other". */
    val all: List<String> by lazy {
        val names = Locale.getISOCountries()
            .map { Locale("", it).getDisplayCountry(Locale.ENGLISH) }
            .filter { it.isNotBlank() && it != HOME }
            .distinct()
            .sorted()
        listOf(HOME) + names + OTHER
    }
}
