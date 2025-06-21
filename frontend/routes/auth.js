const express = require('express');
const axios = require('axios');
const router = express.Router();

// Authentication service configuration
const AUTH_SERVICE_URL = process.env.AUTH_SERVICE_URL || 'http://authentication:8080';

// Middleware to check if user is authenticated
const requireAuth = (req, res, next) => {
  if (req.jwt_token && req.cookies.username) {
    req.user = { username: req.cookies.username };
    return next();
  }
  return res.status(401).json({ error: 'Authentication required' });
};

// Registration endpoint
router.post('/register', async (req, res) => {
  try {
    const { username, email, password } = req.body;
    
    if (!username || !email || !password) {
      return res.status(400).json({ error: 'Username, email, and password are required' });
    }

    // Call authentication service
    const response = await axios.post(`${AUTH_SERVICE_URL}/api/auth/register`, {
      username,
      email,
      password
    });

    // Don't set session - require explicit login to get JWT token
    res.status(201).json({
      message: 'User registered successfully. Please log in to continue.',
      user: {
        id: response.data.user_id,
        username: response.data.username,
        email: email
      }
    });
  } catch (error) {
    console.error('Registration error:', error.response?.data || error.message);
    
    if (error.response) {
      // Forward the error from authentication service
      res.status(error.response.status).json({ 
        error: error.response.data || 'Registration failed' 
      });
    } else {
      res.status(500).json({ error: 'Authentication service unavailable' });
    }
  }
});

// Login endpoint
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    
    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password are required' });
    }

    // Call authentication service
    const response = await axios.post(`${AUTH_SERVICE_URL}/api/auth/login`, {
      username,
      password
    });

    const cookieOptions = {
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: response.data.expires_in * 1000 // Convert to milliseconds
    };

    // Store JWT token in HTTP-only cookie (opaque to frontend)
    res.cookie('jwt_token', response.data.access_token, {
      ...cookieOptions,
      httpOnly: true  // JWT remains inaccessible to client-side JS
    });

    // Store username in a separate readable cookie for UI purposes
    res.cookie('username', username, {
      ...cookieOptions,
      httpOnly: false  // Username can be read by client-side JS for UI
    });

    res.json({
      message: 'Login successful',
      user: {
        username: username
      }
    });
  } catch (error) {
    console.error('Login error:', error.response?.data || error.message);
    
    if (error.response) {
      // Forward the error from authentication service
      res.status(error.response.status).json({ 
        error: error.response.data || 'Invalid credentials' 
      });
    } else {
      res.status(500).json({ error: 'Authentication service unavailable' });
    }
  }
});

// Logout endpoint
router.post('/logout', (req, res) => {
  // Clear both cookies
  res.clearCookie('jwt_token');
  res.clearCookie('username');
  res.json({ message: 'Logout successful' });
});

// Check authentication status
router.get('/status', async (req, res) => {
  if (req.jwt_token && req.cookies.username) {
    res.json({
      authenticated: true,
      user: {
        username: req.cookies.username
      }
    });
  } else {
    res.json({ authenticated: false });
  }
});

// Get current user info
router.get('/user', requireAuth, (req, res) => {
  res.json({
    username: req.user.username
  });
});

module.exports = { router, requireAuth };
