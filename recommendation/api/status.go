package api

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

type PingDBFunc func() error

func GetRecommendationStatus(pingDB PingDBFunc) gin.HandlerFunc {
	return func(c *gin.Context) {
		err := pingDB()
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
}
