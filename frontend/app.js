const express = require('express');
const axios = require('axios');
const os = require('os');
const fs = require('fs');
const config = require('./config.json'); // Import configuration
const origamisRouter = require('./routes/origamis');

const app = express();

app.set('view engine', 'ejs');
app.use('/api/origamis', origamisRouter);

// Endpoint to serve product data to client
app.get('/api/products', async (req, res) => {
  try {
    let response = await axios.get(`${config.productsApiBaseUri}/api/products`);
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching products:', error);
    res.status(500).send('Error fetching products');
  }
});

app.get('/', async (req, res) => {
  try {
    // Gather system info
    const systemInfo = {
      hostname: os.hostname(),
      ipAddress: getIPAddress(),
      isContainer: isContainer(),
      isKubernetes: fs.existsSync('/var/run/secrets/kubernetes.io')
    };

    res.render('index', {
      systemInfo: systemInfo,
      app_version: config.version,
    });
  } catch (error) {
    res.status(500).send('Error rendering home page');
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
  try {
    const productServiceResponse = await axios.get(`${config.productsApiBaseUri}/api/products`);

    res.json({
      Catalogue: 'up',
    });
  } catch (error) {
    console.error('Error:', error);
    res.json({
      Catalogue: 'down',
    });
  }
});

app.get('/recommendation-status', async (req, res) => {
  try {
    await axios.get(config.recommendationBaseUri + '/api/recommendation-status');
    res.json({status: "up", message: "Recommendation Service is Online"});
  } catch (error) {
    res.json({status: "down", message: "Recommendation Service is Offline"});
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

// Static Middleware
app.use('/static', express.static('public'));
app.use(express.static('public'));

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
