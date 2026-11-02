package rw.pesh.enroll.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

@Database(entities = [LearnerEntity::class], version = 2, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {

    abstract fun learnerDao(): LearnerDao

    companion object {
        @Volatile private var instance: AppDatabase? = null

        /**
         * v1 stored an age; v2 stores a date of birth, makes grade empty for non-students, and adds an edit
         * timestamp. Old rows get an estimated birth date (1 January of the birth year) so unsynced signups
         * survive the update; staff can correct them with the new edit screen.
         */
        private val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL(
                    "CREATE TABLE `learners_new` (`clientId` TEXT NOT NULL, `firstName` TEXT NOT NULL, " +
                        "`lastName` TEXT NOT NULL, `country` TEXT NOT NULL, `dateOfBirth` TEXT NOT NULL, " +
                        "`grade` TEXT NOT NULL, `isStudent` INTEGER NOT NULL, `school` TEXT NOT NULL, " +
                        "`createdAtIso` TEXT NOT NULL, `updatedAtIso` TEXT NOT NULL, `status` TEXT NOT NULL, " +
                        "`errorMessage` TEXT, PRIMARY KEY(`clientId`))",
                )
                db.execSQL(
                    "INSERT INTO learners_new (clientId, firstName, lastName, country, dateOfBirth, grade, isStudent, " +
                        "school, createdAtIso, updatedAtIso, status, errorMessage) " +
                        "SELECT clientId, firstName, lastName, country, " +
                        "(CAST(substr(createdAtIso, 1, 4) AS INTEGER) - age) || '-01-01', " +
                        "CASE WHEN isStudent = 1 THEN grade ELSE '' END, isStudent, school, createdAtIso, createdAtIso, " +
                        "status, errorMessage FROM learners",
                )
                db.execSQL("DROP TABLE learners")
                db.execSQL("ALTER TABLE learners_new RENAME TO learners")
            }
        }

        fun build(context: Context): AppDatabase =
            instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "pesh_offline_enroll.db",
                ).addMigrations(MIGRATION_1_2).build().also { instance = it }
            }
    }
}
