package api

import (
	"net"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
)

type SystemInfo struct {
	Hostname     string
	IPAddress    string
	IsContainer  bool
	IsKubernetes bool
}

func GetSystemInfo() SystemInfo {
	hostname, _ := os.Hostname()
	addrs, _ := net.InterfaceAddrs()
	ip := ""
	for _, addr := range addrs {
		if ipnet, ok := addr.(*net.IPNet); ok && !ipnet.IP.IsLoopback() {
			if ipnet.IP.To4() != nil {
				ip = ipnet.IP.String()
				break
			}
		}
	}
	isContainer := false
	if _, err := os.Stat("/.dockerenv"); err == nil {
		isContainer = true
	}
	isKubernetes := false

	return SystemInfo{
		Hostname:     hostname,
		IPAddress:    ip,
		IsContainer:  isContainer,
		IsKubernetes: isKubernetes,
	}
}

type SystemInfoFunc func() SystemInfo

func RenderHomePage(getInfo SystemInfoFunc) gin.HandlerFunc {
	return func(c *gin.Context) {
		appVersion := os.Getenv("APP_VERSION")
		if appVersion == "" {
			appVersion = "1.0.0" // Default version
		}
		systemInfo := getInfo()
		c.HTML(http.StatusOK, "index.html", gin.H{
			"Year":       time.Now().Year(),
			"Version":    appVersion,
			"SystemInfo": systemInfo,
		})
	}
}
