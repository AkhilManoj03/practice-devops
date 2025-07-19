const chai = require('chai');
const chaiHttp = require('chai-http');
const sinon = require('sinon');
const nock = require('nock');
const express = require('express');
const cookieParser = require('cookie-parser');
const origamisRouter = require('../routes/origamis');

const expect = chai.expect;
chai.use(chaiHttp);

// Create a test app with the origami router
const createTestApp = () => {
  const app = express();
  app.use(cookieParser());
  app.use(express.json());
  
  // Mock middleware to extract JWT token from cookies
  app.use((req, res, next) => {
    if (req.cookies && req.cookies.jwt_token) {
      req.jwt_token = req.cookies.jwt_token;
    }
    next();
  });
  
  app.use('/api/origamis', origamisRouter);
  return app;
};

describe('Origami Routes', () => {
  let app;
  const VOTING_SERVICE_BASE_URL = 'http://products:8000';

  beforeEach(() => {
    app = createTestApp();
    // Clean up any existing nock interceptors
    nock.cleanAll();
  });

  afterEach(() => {
    nock.cleanAll();
    sinon.restore();
  });

  describe('POST /:origamiId/vote', () => {
    it('should successfully record a vote for authenticated user', (done) => {
      const origamiId = '123';
      const jwtToken = 'valid-jwt-token';

      // Mock the voting service response
      nock(VOTING_SERVICE_BASE_URL)
        .post(`/api/origamis/${origamiId}/vote`)
        .matchHeader('Authorization', `Bearer ${jwtToken}`)
        .reply(200, { success: true });

      chai.request(app)
        .post(`/api/origamis/${origamiId}/vote`)
        .set('Cookie', [`jwt_token=${jwtToken}`, 'username=testuser'])
        .end((err, res) => {
          expect(res).to.have.status(200);
          expect(res.text).to.equal('Vote recorded!');
          done();
        });
    });

    it('should return 401 when user is not authenticated', (done) => {
      const origamiId = '123';

      chai.request(app)
        .post(`/api/origamis/${origamiId}/vote`)
        .end((err, res) => {
          expect(res).to.have.status(401);
          done();
        });
    });

    it('should return 500 when voting service is unavailable', (done) => {
      const origamiId = '123';
      const jwtToken = 'valid-jwt-token';

      // Mock the voting service to return 500
      nock(VOTING_SERVICE_BASE_URL)
        .post(`/api/origamis/${origamiId}/vote`)
        .matchHeader('Authorization', `Bearer ${jwtToken}`)
        .reply(500, { error: 'Internal Server Error' });

      chai.request(app)
        .post(`/api/origamis/${origamiId}/vote`)
        .set('Cookie', [`jwt_token=${jwtToken}`, 'username=testuser'])
        .end((err, res) => {
          expect(res).to.have.status(500);
          expect(res.text).to.equal('Internal Server Error');
          done();
        });
    });

    it('should include Authorization header when JWT token is present', (done) => {
      const origamiId = '123';
      const jwtToken = 'test-jwt-token';

      // Mock with specific header expectation
      const scope = nock(VOTING_SERVICE_BASE_URL)
        .post(`/api/origamis/${origamiId}/vote`)
        .matchHeader('Authorization', `Bearer ${jwtToken}`)
        .reply(200, { success: true });

      chai.request(app)
        .post(`/api/origamis/${origamiId}/vote`)
        .set('Cookie', [`jwt_token=${jwtToken}`, 'username=testuser'])
        .end((err, res) => {
          expect(res).to.have.status(200);
          expect(scope.isDone()).to.be.true;
          done();
        });
    });

    it('should handle different origami IDs correctly', (done) => {
      const origamiId = '456';
      const jwtToken = 'valid-jwt-token';

      nock(VOTING_SERVICE_BASE_URL)
        .post(`/api/origamis/${origamiId}/vote`)
        .reply(200, { success: true });

      chai.request(app)
        .post(`/api/origamis/${origamiId}/vote`)
        .set('Cookie', [`jwt_token=${jwtToken}`, 'username=testuser'])
        .end((err, res) => {
          expect(res).to.have.status(200);
          done();
        });
    });
  });

  describe('GET /:origamiId/votes', () => {
    it('should successfully retrieve vote count for an origami', (done) => {
      const origamiId = '123';
      const mockVoteData = { votes: 42 };

      nock(VOTING_SERVICE_BASE_URL)
        .get(`/api/origamis/${origamiId}/votes`)
        .reply(200, mockVoteData);

      chai.request(app)
        .get(`/api/origamis/${origamiId}/votes`)
        .end((err, res) => {
          expect(res).to.have.status(200);
          expect(res.body).to.deep.equal(mockVoteData);
          expect(res.body.votes).to.equal(42);
          done();
        });
    });

    it('should return 500 when voting service returns error', (done) => {
      const origamiId = '123';

      nock(VOTING_SERVICE_BASE_URL)
        .get(`/api/origamis/${origamiId}/votes`)
        .reply(500, { error: 'Database error' });

      chai.request(app)
        .get(`/api/origamis/${origamiId}/votes`)
        .end((err, res) => {
          expect(res).to.have.status(500);
          expect(res.text).to.equal('Internal Server Error');
          done();
        });
    });

    it('should return 500 when voting service is completely down', (done) => {
      const origamiId = '123';

      // Don't mock the service to simulate it being down
      
      chai.request(app)
        .get(`/api/origamis/${origamiId}/votes`)
        .end((err, res) => {
          expect(res).to.have.status(500);
          expect(res.text).to.equal('Internal Server Error');
          done();
        });
    });

    it('should work without authentication (public endpoint)', (done) => {
      const origamiId = '123';
      const mockVoteData = { votes: 10 };

      nock(VOTING_SERVICE_BASE_URL)
        .get(`/api/origamis/${origamiId}/votes`)
        .reply(200, mockVoteData);

      chai.request(app)
        .get(`/api/origamis/${origamiId}/votes`)
        // No authentication cookies
        .end((err, res) => {
          expect(res).to.have.status(200);
          expect(res.body).to.deep.equal(mockVoteData);
          done();
        });
    });

    it('should handle zero votes correctly', (done) => {
      const origamiId = '123';
      const mockVoteData = { votes: 0 };

      nock(VOTING_SERVICE_BASE_URL)
        .get(`/api/origamis/${origamiId}/votes`)
        .reply(200, mockVoteData);

      chai.request(app)
        .get(`/api/origamis/${origamiId}/votes`)
        .end((err, res) => {
          expect(res).to.have.status(200);
          expect(res.body).to.deep.equal(mockVoteData);
          expect(res.body.votes).to.equal(0);
          done();
        });
    });
  });

  describe('Error handling', () => {
    it('should log errors when voting fails', (done) => {
      const origamiId = '123';
      const jwtToken = 'valid-jwt-token';
      
      // Spy on console.error
      const consoleErrorSpy = sinon.spy(console, 'error');

      nock(VOTING_SERVICE_BASE_URL)
        .post(`/api/origamis/${origamiId}/vote`)
        .reply(500, { error: 'Database error' });

      chai.request(app)
        .post(`/api/origamis/${origamiId}/vote`)
        .set('Cookie', [`jwt_token=${jwtToken}`, 'username=testuser'])
        .end((err, res) => {
          expect(res).to.have.status(500);
          expect(consoleErrorSpy.calledWith('Error voting:')).to.be.true;
          done();
        });
    });

    it('should log errors when fetching votes fails', (done) => {
      const origamiId = '123';
      
      // Spy on console.error
      const consoleErrorSpy = sinon.spy(console, 'error');

      nock(VOTING_SERVICE_BASE_URL)
        .get(`/api/origamis/${origamiId}/votes`)
        .reply(500, { error: 'Database error' });

      chai.request(app)
        .get(`/api/origamis/${origamiId}/votes`)
        .end((err, res) => {
          expect(res).to.have.status(500);
          expect(consoleErrorSpy.calledWith('Error fetching vote count:')).to.be.true;
          done();
        });
    });
  });
});
