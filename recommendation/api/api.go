package api

import (
	"github.com/gin-gonic/gin"
	"net/http"
	"recommendation/data"
)

func GetOrigamiOfTheDay(c *gin.Context) {
	product, err := data.GetRandomProduct()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve a random product"})
		return
	}

	c.JSON(http.StatusOK, product)
}
