package rw.pesh.enroll.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface LearnerDao {

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insert(learner: LearnerEntity)

    @Query("SELECT * FROM learners ORDER BY createdAtIso DESC")
    fun observeAll(): Flow<List<LearnerEntity>>

    @Query("SELECT * FROM learners WHERE status != :synced ORDER BY createdAtIso ASC")
    suspend fun getUnsynced(synced: String = LearnerEntity.STATUS_SYNCED): List<LearnerEntity>

    @Query("UPDATE learners SET status = :status, errorMessage = :error WHERE clientId = :clientId")
    suspend fun updateStatus(clientId: String, status: String, error: String? = null)

    @Query("SELECT COUNT(*) FROM learners WHERE status = :status")
    fun observeCount(status: String): Flow<Int>
}
