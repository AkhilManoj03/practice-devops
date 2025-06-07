const express = require('express');
const axios = require('axios');
const os = require('os');
const fs = require('fs');
const config = require('./config.json'); // Import configuration
const { trace } = require('@opentelemetry/api');
const app = express();
const productsApiBaseUri = config.productsApiBaseUri;
const recommendationBaseUri = config.recommendationBaseUri;
const votingBaseUri = config.votingBaseUri;
const origamisRouter = require('./routes/origamis');

const tracer = trace.getTracer('craftista-frontend');

app.set('view engine', 'ejs');
app.use(express.static('public'));
app.use('/api/origamis', origamisRouter);

// Static Middleware
app.use('/static', express.static('public'));

// Endpoint to serve product data to client
app.get('/api/products', async (req, res) => {
  const span = tracer.startSpan('get_products');
  try {
    span.setAttribute('service.name', 'craftista-frontend');
    span.setAttribute('endpoint', '/api/products');
    
    let response = await axios.get(`${productsApiBaseUri}/api/products`);
    span.setAttribute('products.count', response.data.length);
    res.json(response.data);
  } catch (error) {
    span.setAttribute('error', true);
    span.setAttribute('error.message', error.message);
    console.error('Error fetching products:', error);
    res.status(500).send('Error fetching products');
  } finally {
    span.end();
  }
});

app.get('/', async (req, res) => {
  const span = tracer.startSpan('get_home_page');
  try {
    span.setAttribute('service.name', 'craftista-frontend');
    span.setAttribute('endpoint', '/');

    // Gather system info
    const systemInfo = await tracer.startActiveSpan('gather_system_info', async (systemInfoSpan) => {
      const info = {
        hostname: os.hostname(),
        ipAddress: getIPAddress(),
        isContainer: isContainer(),
        isKubernetes: fs.existsSync('/var/run/secrets/kubernetes.io')
      };
      systemInfoSpan.end();
      return info;
    });

    res.render('index', {
      systemInfo: systemInfo,
      app_version: config.version,
    });
  } catch (error) {
    span.setAttribute('error', true);
    span.setAttribute('error.message', error.message);
    res.status(500).send('Error rendering home page');
  } finally {
    span.end();
  }
});

function getIPAddress() {
  // Logic to fetch IP Address
  const networkInterfaces = os.networkInterfaces();
  return (networkInterfaces['eth0'] && networkInterfaces['eth0'][0].address) || 'IP not found';
}

function isContainer() {
  // Logic to check if running in a container
  try {
    fs.readFileSync('/proc/1/cgroup');
    return true;
  } catch (e) {
    return false;
  }
}

app.get('/api/service-status', async (req, res) => {
  const span = tracer.startSpan('check_service_status');
  try {
    span.setAttribute('service.name', 'craftista-frontend');
    span.setAttribute('endpoint', '/api/service-status');

    const productServiceResponse = await axios.get(`${productsApiBaseUri}/api/products`);
    span.setAttribute('product_service.status', 'up');

    res.json({
      Catalogue: 'up',
    });
  } catch (error) {
    span.setAttribute('error', true);
    span.setAttribute('error.message', error.message);
    span.setAttribute('product_service.status', 'down');
    console.error('Error:', error);
    res.json({
      Catalogue: 'down',
    });
  } finally {
    span.end();
  }
});

app.get('/recommendation-status', async (req, res) => {
  const span = tracer.startSpan('check_recommendation_status');
  try {
    span.setAttribute('service.name', 'craftista-frontend');
    span.setAttribute('endpoint', '/recommendation-status');

    await axios.get(config.recommendationBaseUri + '/api/recommendation-status');
    span.setAttribute('recommendation_service.status', 'up');
    res.json({status: "up", message: "Recommendation Service is Online"});
  } catch (error) {
    span.setAttribute('error', true);
    span.setAttribute('error.message', error.message);
    span.setAttribute('recommendation_service.status', 'down');
    res.json({status: "down", message: "Recommendation Service is Offline"});
  } finally {
    span.end();
  }
});

app.get('/votingservice-status', (req, res) => {
    axios.get(config.votingBaseUri + '/api/origamis')
        .then(response => {
            res.json({status: "up", message: "Voting Service is Online"});
        })
        .catch(error => {
            res.json({status: "down", message: "Voting Service is Offline"});
        });
});

app.get('/daily-origami', (req, res) => {
    axios.get(config.recommendationBaseUri + '/api/origami-of-the-day')
        .then(response => {
            res.json(response.data);
        })
        .catch(error => {
            res.status(500).send("Error while fetching daily origami");
        });
});

// Handle 404
app.use((req, res, next) => {
    res.status(404).send('ERROR 404 - Not Found on This Server');
});

const PORT = process.env.PORT || 3000;
const server = app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});

// Graceful shutdown to ensure all spans are exported
process.on('SIGTERM', () => {
  server.close(() => {
    console.log('Server shutting down');
  });
});

module.exports = server; // Note that we're exporting the server, not app.


