package api_test

import (
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"

	"recommendation/api"
)

func TestGetRecommendationStatus(t *testing.T) {
	gin.SetMode(gin.TestMode)

	t.Run("DatabaseOperational", func(t *testing.T) {
		r := gin.New()
		r.GET("/status", api.GetRecommendationStatus(func() error { return nil }))
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/status", nil)
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "\"status\":\"operational\"")
		assert.Contains(t, w.Body.String(), "\"database_status\":\"operational\"")
	})

	t.Run("DatabaseDown", func(t *testing.T) {
		r := gin.New()
		r.GET("/status", api.GetRecommendationStatus(func() error { return errors.New("db down") }))
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/status", nil)
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "\"status\":\"degraded\"")
		assert.Contains(t, w.Body.String(), "\"database_status\":\"down\"")
	})
}
