package main

import (
	"context"
	"log"

	"github.com/gin-gonic/gin"
	"go.opentelemetry.io/contrib/instrumentation/github.com/gin-gonic/gin/otelgin"

	"recommendation/api"
	"recommendation/data"
	"recommendation/telemetry"
)

func main() {
	// Initialize OpenTelemetry
	shutdown, err := telemetry.InitTracer()
	if err != nil {
		log.Fatalf("Failed to initialize tracer: %v", err)
	}
	defer func() {
		if err := shutdown(context.Background()); err != nil {
			log.Printf("Error shutting down tracer provider: %v", err)
		}
	}()

	// Initialize Database
	if err := data.InitDB(); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}

	router := gin.Default()
	
	// Add OpenTelemetry middleware for automatic instrumentation
	router.Use(otelgin.Middleware("recommendation-service"))

	// Load HTML files
	router.LoadHTMLGlob("templates/*")

	// Set path to serve static files
	router.Static("/static", "./static")

	// Define routes
	router.GET("/", api.RenderHomePage)
	router.GET("/api/origami-of-the-day", api.GetOrigamiOfTheDay)
	router.GET("/api/recommendation-status", api.GetRecommendationStatus)

	// Start the server
	router.Run(":8080")
}
