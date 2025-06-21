const express = require('express');
const axios = require('axios');
const { requireAuth } = require('./auth');
const router = express.Router();

// Voting Service base URL
const VOTING_SERVICE_BASE_URL = 'http://products:8000';

// Utility function to get authorization headers
function getAuthHeaders(req) {
    const headers = {};

    // Check for JWT token from HTTP-only cookie
    if (req.jwt_token) {
        headers['Authorization'] = `Bearer ${req.jwt_token}`;
    }

    return headers;
}

// Vote for an Origami - now requires authentication
router.post('/:origamiId/vote', requireAuth, async (req, res, next) => {
    try {
        const authHeaders = getAuthHeaders(req);
        await axios.post(
            `${VOTING_SERVICE_BASE_URL}/api/origamis/${req.params.origamiId}/vote`,
            {},
            { headers: authHeaders }
        );
        res.status(200).send('Vote recorded!');
    } catch (error) {
        console.error('Error voting:', error);
        if (error.response && error.response.status === 401) {
            res.status(401).send('Authentication required');
        } else {
            res.status(500).send('Internal Server Error');
        }
    }
});

// Get vote count for an Origami
router.get('/:origamiId/votes', async (req, res, next) => {
    try {
        const response = await axios.get(
            `${VOTING_SERVICE_BASE_URL}/api/origamis/${req.params.origamiId}/votes`
        );
        res.status(200).json(response.data);
    } catch (error) {
        console.error('Error fetching vote count:', error);
        res.status(500).send('Internal Server Error');
    }
});

module.exports = router;
