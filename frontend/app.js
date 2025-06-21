const express = require('express');
const axios = require('axios');
const os = require('os');
const fs = require('fs');
const cookieParser = require('cookie-parser');
const origamisRouter = require('./routes/origamis');
const { router: authRouter } = require('./routes/auth');

// Configuration from environment variables
const config = {
  productsApiBaseUri: process.env.PRODUCTS_API_BASE_URI || 'http://products:8000',
  recommendationBaseUri: process.env.RECOMMENDATION_BASE_URI || 'http://recommendation:8080',
  votingBaseUri: process.env.VOTING_BASE_URI || 'http://products:8000',
  version: process.env.APP_VERSION || '1.0.0'
};

const app = express();

// Cookie parsing middleware
app.use(cookieParser());

// Body parsing middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Middleware to extract JWT token from HTTP-only cookie and make it available to routes
app.use((req, res, next) => {
  // Extract JWT token from HTTP-only cookie and make it available to routes
  if (req.cookies && req.cookies.jwt_token) {
    req.jwt_token = req.cookies.jwt_token;
  }
  next();
});

app.set('view engine', 'ejs');

// Routes
app.use('/auth', authRouter);
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

    // Check if user is authenticated via JWT token and username cookie
    const isAuthenticated = !!(req.jwt_token && req.cookies.username);
    const username = req.cookies.username || null;

    res.render('index', {
      systemInfo: systemInfo,
      app_version: config.version,
      isAuthenticated: isAuthenticated,
      username: username
    });
  } catch (error) {
    res.status(500).send('Error rendering home page');
  }
});

// Login page
app.get('/login', (req, res) => {
  // If already logged in (has both JWT token and username), redirect to home
  if (req.jwt_token && req.cookies.username) {
    return res.redirect('/');
  }
  res.render('login');
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
