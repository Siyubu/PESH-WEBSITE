package rw.pesh.enroll.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

@Dao
interface LearnerDao {

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insert(learner: LearnerEntity)

    @Update
    suspend fun update(learner: LearnerEntity)

    @Query("SELECT * FROM learners WHERE clientId = :clientId")
    suspend fun getById(clientId: String): LearnerEntity?

    @Query("SELECT * FROM learners ORDER BY createdAtIso DESC")
    fun observeAll(): Flow<List<LearnerEntity>>

    @Query("SELECT * FROM learners WHERE status != :synced ORDER BY createdAtIso ASC")
    suspend fun getUnsynced(synced: String = LearnerEntity.STATUS_SYNCED): List<LearnerEntity>

    /**
     * Records a sync result only if the row has not been edited since that version was sent. Otherwise an edit
     * made while a sync was in flight would be marked "synced" without ever reaching the server.
     */
    @Query("UPDATE learners SET status = :status, errorMessage = :error WHERE clientId = :clientId AND updatedAtIso = :version")
    suspend fun updateStatusIfUnchanged(clientId: String, version: String, status: String, error: String? = null)

    @Query("SELECT COUNT(*) FROM learners WHERE status = :status")
    fun observeCount(status: String): Flow<Int>
}
