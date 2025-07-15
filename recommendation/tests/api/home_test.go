package api_test

import (
	"html/template"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"

	"recommendation/api"
)

func TestGetSystemInfo(t *testing.T) {
	info := api.GetSystemInfo()
	// We can't mock os.Hostname etc. here, so just check type and fields exist
	assert.NotEmpty(t, info.Hostname)
	assert.NotNil(t, info.IPAddress)
}

func TestRenderHomePage(t *testing.T) {
	gin.SetMode(gin.TestMode)
	// Set up a test template
	r := gin.New()
	r.SetHTMLTemplate(testTemplate())
	r.GET("/", api.RenderHomePage(func() api.SystemInfo {
		return api.SystemInfo{
			Hostname:    "test-host",
			IPAddress:   "192.168.1.100",
			IsContainer: true,
			IsKubernetes: false,
		}
	}))

	// Set env var for version
	os.Setenv("APP_VERSION", "2.3.4")
	defer os.Unsetenv("APP_VERSION")

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "Craftista Test Home")
	assert.Contains(t, w.Body.String(), "2.3.4")
	assert.Contains(t, w.Body.String(), time.Now().Format("2006"))
}

// Minimal HTML template for RenderHomePage
func testTemplate() *template.Template {
	tmpl := `{{define "index.html"}}<html><body>Craftista Test Home - Version: {{.Version}} - Year: {{.Year}}</body></html>{{end}}`
	return template.Must(template.New("index.html").Parse(tmpl))
}
