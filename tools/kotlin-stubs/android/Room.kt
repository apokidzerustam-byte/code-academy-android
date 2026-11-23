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

@Target(AnnotationTarget.FUNCTION)
annotation class Insert

@Target(AnnotationTarget.FUNCTION)
annotation class Update

@Target(AnnotationTarget.FUNCTION)
annotation class Delete

@Target(AnnotationTarget.CLASS)
annotation class Database(val entities: Array<KClass<*>>, val version: Int)

abstract class RoomDatabase
