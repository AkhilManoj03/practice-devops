package data

import "database/sql"

// GetDB returns the current global db (for testing)
func GetDB() *sql.DB {
	return db
}

// SetDB sets the global db (for testing)
func SetDB(newdb *sql.DB) {
	db = newdb
}
