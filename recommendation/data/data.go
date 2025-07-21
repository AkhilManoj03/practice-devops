package data

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"os"
	"time"

	_ "github.com/jackc/pgx/v4/stdlib"
)

// Product matches the structure of the 'products' table.
type Product struct {
	ID          int    `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
	ImageURL    string `json:"image_url"`
	Votes       int    `json:"votes"`
}

var db *sql.DB

// InitDB initializes the database connection.
func InitDB() error {
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		return fmt.Errorf("DATABASE_URL environment variable not set")
	}

	var err error
	db, err = sql.Open("pgx", dbURL)
	if err != nil {
		return fmt.Errorf("unable to connect to database: %w", err)
	}

	// Retry logic for database connection
	maxRetries := 10
	retryDelay := 2 * time.Second
	
	for i := 0; i < maxRetries; i++ {
		if err = PingDB(); err == nil {
			log.Println("Database connection established")
			return nil
		}
		
		log.Printf("Database connection attempt %d/%d failed: %v", i+1, maxRetries, err)
		
		if i < maxRetries-1 {
			log.Printf("Retrying in %v...", retryDelay)
			time.Sleep(retryDelay)
		}
	}

	log.Println("Database connection established")
	return nil
}

// GetRandomProduct retrieves one random product from the database.
func GetRandomProduct() (Product, error) {
	var p Product
	query := "SELECT id, name, description, image_url, votes FROM products ORDER BY RANDOM() LIMIT 1"
	err := db.QueryRowContext(context.Background(), query).Scan(&p.ID, &p.Name, &p.Description, &p.ImageURL, &p.Votes)

	if err != nil {
		if err == sql.ErrNoRows {
			return Product{}, fmt.Errorf("no products found")
		}
		return Product{}, fmt.Errorf("querying for a random product failed: %w", err)
	}

	return p, nil
}

// PingDB pings the database to check connectivity.
func PingDB() error {
	return db.Ping()
}
