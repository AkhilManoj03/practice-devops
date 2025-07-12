# Craftista Frontend

The frontend application for the Craftista origami marketplace with user authentication.

## Features

- User registration and login
- Session-based authentication
- Protected voting functionality
- Responsive design
- Integration with PostgreSQL database

## Authentication

Users must register and login to vote for origami designs. The authentication system includes:

- User registration with username, email, and password
- Secure password hashing using bcryptjs
- Session-based authentication with express-session
- Protected voting endpoints

### Security Features

- **Secure Registration Endpoint**: The registration endpoint is protected by a shared internal API
key that is securely configured as an environment variable. This API key is shared only between the
frontend and authentication service, ensuring that only the frontend application can access the
registration endpoint and preventing unauthorized user creation.
- **Environment-based Security**: The internal API key is stored as a secure environment variable,
keeping it separate from the codebase and allowing for different keys per environment (development,
staging, production).

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp ../.env.example .env
# Edit .env with your configuration including:
# - INTERNAL_API_KEY: Shared secret key for secure registration endpoint access
```

3. Ensure PostgreSQL database is running (via docker-compose)

4. Start the application:
```bash
npm start
```

## Database

The application uses PostgreSQL with the following user table:

- `users` table with id, username, email, password_hash, created_at, updated_at
- Automatic initialization via init-db.sql script

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/logout` - Logout user
- `GET /auth/status` - Check authentication status
- `GET /auth/user` - Get current user info

### Application
- `GET /` - Main application page
- `GET /login` - Login/registration page
- `POST /api/origamis/:id/vote` - Vote for origami (requires authentication)
