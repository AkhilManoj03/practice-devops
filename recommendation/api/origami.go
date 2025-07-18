package api

import (
	"github.com/gin-gonic/gin"
	"net/http"
	"recommendation/data"
)

type GetRandomProductFunc func() (data.Product, error)

func GetOrigamiOfTheDay(getProduct GetRandomProductFunc) gin.HandlerFunc {
	return func(c *gin.Context) {
		product, err := getProduct()
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve a random product"})
			return
		}
		c.JSON(http.StatusOK, product)
	}
}
