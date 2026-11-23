package androidx.room

import kotlin.reflect.KClass

@Target(AnnotationTarget.CLASS)
annotation class Entity(val tableName: String = "")

@Target(AnnotationTarget.FIELD, AnnotationTarget.PROPERTY, AnnotationTarget.VALUE_PARAMETER)
annotation class PrimaryKey(val autoGenerate: Boolean = false)

@Target(AnnotationTarget.FIELD, AnnotationTarget.PROPERTY, AnnotationTarget.VALUE_PARAMETER)
annotation class ColumnInfo(val name: String = "")

@Target(AnnotationTarget.CLASS)
annotation class Dao

@Target(AnnotationTarget.FUNCTION)
annotation class Query(val value: String)

/** Значения как в настоящем Room: REPLACE = 1, ABORT = 3, IGNORE = 5. */
object OnConflictStrategy {
    const val REPLACE = 1
    const val ABORT = 3
    const val IGNORE = 5
}

@Target(AnnotationTarget.FUNCTION)
annotation class Insert(val onConflict: Int = OnConflictStrategy.ABORT)

@Target(AnnotationTarget.FUNCTION)
annotation class Update

@Target(AnnotationTarget.FUNCTION)
annotation class Delete

@Target(AnnotationTarget.CLASS)
annotation class Database(val entities: Array<KClass<*>>, val version: Int)

abstract class RoomDatabase
