package api_test

import (
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"

	"recommendation/api"
	"recommendation/data"
)

func TestGetOrigamiOfTheDay(t *testing.T) {
	gin.SetMode(gin.TestMode)

	t.Run("Success", func(t *testing.T) {
		r := gin.New()
		r.GET("/origami", api.GetOrigamiOfTheDay(func() (data.Product, error) {
			return data.Product{
				ID: 1,
				Name: "Origami Crane",
				Description: "A beautiful origami crane",
				ImageURL: "/static/images/origami/001-origami.png",
				Votes: 5,
			}, nil
		}))

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/origami", nil)
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		assert.Contains(t, w.Body.String(), "Origami Crane")
		assert.Contains(t, w.Body.String(), "/static/images/origami/001-origami.png")
	})

	t.Run("Error", func(t *testing.T) {
		r := gin.New()
		r.GET("/origami", api.GetOrigamiOfTheDay(func() (data.Product, error) {
			return data.Product{}, errors.New("db error")
		}))

		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/origami", nil)
		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusInternalServerError, w.Code)
		assert.Contains(t, w.Body.String(), "Failed to retrieve a random product")
	})
}
