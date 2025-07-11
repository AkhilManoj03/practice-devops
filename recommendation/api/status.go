package api

import (
	"net/http"
	"recommendation/data"

	"github.com/gin-gonic/gin"
)

func GetRecommendationStatus(c *gin.Context) {
	// Check database connectivity
	err := data.PingDB()
	dbStatus := "operational"
	if err != nil {
		dbStatus = "down"
	}

	status := "operational"
	if dbStatus == "down" {
		status = "degraded"
	}

	c.JSON(http.StatusOK, gin.H{
		"status":          status,
		"database_status": dbStatus,
	})
}
