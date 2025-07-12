# 🐘 PostgreSQL Database

This directory contains the PostgreSQL database configuration and initialization scripts for the
microservices architecture. The database serves as the central data store for user credentials,
product information, and application state across all services.

## 🎯 Purpose

The PostgreSQL database provides:

- **Centralized Data Storage**: Single source of truth for all persistent data
- **ACID Compliance**: Ensures data consistency and reliability across transactions
- **Multi-Service Support**: Serves Authentication, Product, and Recommendation services
- **Scalable Foundation**: Robust relational database ready for production workloads

## 🏗️ Database Schema

### Users Table
Stores authentication and user management data for the Authentication Service.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key Features:**
- **Auto-incrementing ID**: Primary key with SERIAL type
- **Unique Constraints**: Username and email must be unique
- **Password Security**: Stores bcrypt-hashed passwords (never plaintext)
- **Role-Based Access**: Supports user roles for authorization
- **Automatic Timestamps**: Tracks creation and update times
- **Optimized Indexes**: Fast lookups on username and email

### Products Table
Stores product catalog and voting data for Product and Recommendation services.

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    image_url VARCHAR(500),
    votes INTEGER DEFAULT 0
);
```

**Key Features:**
- **Fixed IDs**: Consistent product identifiers across services
- **Rich Metadata**: Name, description, and image URL for display
- **Vote Tracking**: Persistent vote counts for the voting system
- **Pre-populated Data**: Includes 5 origami products with detailed descriptions

## 🔄 Database Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        PostgreSQL Database                       │
├──────────────────────┬───────────────────────────────────────────┤
│     Users Table      │              Products Table               │
│                      │                                           │
│ • User credentials   │ • Product catalog                         │
│ • Roles & permissions│ • Descriptions & images                   │
│ • Timestamps         │ • Vote counts                             │
└─────────────┬────────┴───────────────────┬───────────────────────┘
              │                            │
              ▼                            ▼
    ┌─────────────────┐         ┌─────────────────────────────┐
    │ Authentication  │         │   Product & Recommendation  │
    │    Service      │         │        Services             │
    │                 │         │                             │
    │ • User login    │         │ • Product catalog           │
    │ • Registration  │         │ • Vote management           │
    │ • JWT issuing   │         │ • Recommendations           │
    └─────────────────┘         └─────────────────────────────┘
```

## 🚀 Initialization Process

The database is automatically initialized when the container starts:

1. **Container Startup**: PostgreSQL starts in Alpine Linux container
2. **Schema Creation**: `init-db.sql` creates tables and indexes
3. **Data Population**: Inserts initial product data with descriptions
4. **Trigger Setup**: Configures automatic timestamp updates
5. **Ready State**: Database accepts connections from services

### Initial Data
The database comes pre-loaded with 5 origami products:
- **Origami Crane**: Symbol of peace and hope
- **Origami Frog**: Playful amphibious representation
- **Origami Kangaroo**: Australian outback icon
- **Origami Camel**: Desert wanderer
- **Origami Butterfly**: Symbol of transformation

## 🐳 Docker Configuration

**Base Image**: `postgres:17-alpine3.22`
- **Version**: PostgreSQL 17 for latest features and performance
- **Alpine**: Minimal footprint for efficient containerization
- **Initialization**: Automatic script execution via `docker-entrypoint-initdb.d/`

### Environment Variables
```bash
POSTGRES_DB=craftista
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

## 📊 Performance Features

### Indexes
Optimized for common query patterns:

```sql
-- Fast user lookups for authentication
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- Fast product retrieval for catalog and recommendations
CREATE INDEX idx_products_id ON products(id);
```

### Triggers
Automatic timestamp management:

```sql
-- Updates 'updated_at' on every user record change
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

## 🔒 Security Features

1. **Password Hashing**: All passwords stored as bcrypt hashes
2. **Role-Based Access**: User roles for fine-grained permissions
3. **Connection Security**: Isolated network within Docker environment
4. **Unique Constraints**: Prevents duplicate usernames/emails

## 🛠️ Service Integration

### Authentication Service (Rust)
- **User Management**: Registration, login, credential verification
- **JWT Claims**: User ID and role extraction for token generation
- **Password Security**: Bcrypt verification against stored hashes

### Product Service (Python)
- **Catalog Operations**: Product listing and details retrieval
- **Vote Management**: Increment vote counts and maintain consistency
- **Cache Integration**: Works with Redis for performance optimization

### Recommendation Service (Go)
- **Random Selection**: Fetches random products for recommendations
- **Real-time Data**: Direct database queries for up-to-date information

## 🚀 Getting Started

The database automatically starts with the Docker Compose setup:

```bash
# Start the entire system (includes PostgreSQL)
docker-compose up --build

# Access database directly (optional)
docker-compose exec postgres psql -U postgres -d craftista
```

## 🔍 Monitoring & Maintenance

### Health Checks
```bash
# Check database status
docker-compose logs postgres

# Verify table creation
docker-compose exec postgres psql -U postgres -d craftista -c "\dt"

# Check data population
docker-compose exec postgres psql -U postgres -d craftista -c "SELECT COUNT(*) FROM products;"
```

### Common Queries
```sql
-- View all users (without passwords)
SELECT id, username, email, role, created_at FROM users;

-- Check product vote counts
SELECT name, votes FROM products ORDER BY votes DESC;

-- Database size and statistics
SELECT schemaname, tablename, attname, avg_width, n_distinct 
FROM pg_stats WHERE schemaname = 'public';
```

## 📈 Benefits

1. **Centralized Data Management**: Single source of truth for all services
2. **ACID Compliance**: Ensures data consistency across concurrent operations
3. **Performance Optimization**: Proper indexing and query optimization
4. **Developer Friendly**: Easy setup with Docker and automatic initialization
5. **Production Ready**: Robust PostgreSQL foundation suitable for scaling

---

This PostgreSQL setup provides a solid, scalable foundation for the microservices architecture,
ensuring data integrity, performance, and ease of development.
