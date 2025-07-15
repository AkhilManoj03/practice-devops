package tests

import (
	"database/sql"
	"errors"
	"os"
	"testing"

	"recommendation/data"

	_ "github.com/jackc/pgx/v4/stdlib"
	"github.com/DATA-DOG/go-sqlmock"
)

// Helper to reset the global db variable after each test
func resetDB() {
	dataDB := data.GetDB()
	if dataDB != nil {
		_ = dataDB.Close()
	}
	// Set to nil for isolation
	data.SetDB(nil)
}

// Helper to set and unset env var
func withEnv(key, value string, fn func()) {
	orig, ok := os.LookupEnv(key)
	_ = os.Setenv(key, value)
	fn()
	if ok {
		_ = os.Setenv(key, orig)
	} else {
		_ = os.Unsetenv(key)
	}
}

// --- Test Data Factory ---
func testProduct() data.Product {
	return data.Product{
		ID:          1,
		Name:        "Test Product",
		Description: "A test product",
		ImageURL:    "/static/images/test.png",
		Votes:       42,
	}
}

// --- Tests for InitDB ---
func TestInitDB(t *testing.T) {
	t.Run("MissingEnvVar", func(t *testing.T) {
		resetDB()
		withEnv("DATABASE_URL", "", func() {
			err := data.InitDB()
			if err == nil || err.Error() != "DATABASE_URL environment variable not set" {
				t.Errorf("expected env var error, got: %v", err)
			}
		})
	})

	t.Run("OpenError", func(t *testing.T) {
		resetDB()
		withEnv("DATABASE_URL", "bad://url", func() {
			// Patch sql.Open to return error (simulate with invalid driver)
			err := data.InitDB()
			if err == nil || err.Error() == "" {
				t.Error("expected error from sql.Open")
			}
		})
	})
}

// --- Tests for GetRandomProduct ---
func TestGetRandomProduct(t *testing.T) {
	resetDB()
	mockDB, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer mockDB.Close()
	data.SetDB(mockDB)

	t.Run("Success", func(t *testing.T) {
		p := testProduct()
		rows := sqlmock.NewRows([]string{"id", "name", "description", "image_url", "votes"}).
			AddRow(p.ID, p.Name, p.Description, p.ImageURL, p.Votes)
		mock.ExpectQuery("SELECT id, name, description, image_url, votes FROM products ORDER BY RANDOM\\(\\) LIMIT 1").
			WillReturnRows(rows)
		got, err := data.GetRandomProduct()
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if got != p {
			t.Errorf("expected %+v, got %+v", p, got)
		}
	})

	t.Run("NoRows", func(t *testing.T) {
		mock.ExpectQuery("SELECT id, name, description, image_url, votes FROM products ORDER BY RANDOM\\(\\) LIMIT 1").
			WillReturnError(sql.ErrNoRows)
		_, err := data.GetRandomProduct()
		if err == nil || err.Error() != "no products found" && !contains(err.Error(), "no products found") {
			t.Errorf("expected no products found error, got: %v", err)
		}
	})

	t.Run("QueryError", func(t *testing.T) {
		mock.ExpectQuery("SELECT id, name, description, image_url, votes FROM products ORDER BY RANDOM\\(\\) LIMIT 1").
			WillReturnError(errors.New("query fail"))
		_, err := data.GetRandomProduct()
		if err == nil || (!contains(err.Error(), "query fail") && !contains(err.Error(), "querying for a random product failed")) {
			t.Errorf("expected query fail error, got: %v", err)
		}
	})
}

// --- Tests for PingDB ---
func TestPingDB(t *testing.T) {
	resetDB()
	mockDB, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to create sqlmock: %v", err)
	}
	defer mockDB.Close()
	data.SetDB(mockDB)

	t.Run("PingSuccess", func(t *testing.T) {
		mock.ExpectPing()
		err := data.PingDB()
		if err != nil {
			t.Errorf("expected nil error, got: %v", err)
		}
	})
}

// --- Utility ---
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || (len(s) > len(substr) && contains(s[1:], substr)))
}
