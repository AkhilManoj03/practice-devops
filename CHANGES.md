# Project Modifications and Improvements

## Overview
This document outlines the significant changes and improvements made to the original [Craftista 
project](https://github.com/craftista/craftista). The modifications were primarily focused on 
enhancing the application's performance,  reliability, and maintainability while gaining hands-on 
experience with modern DevOps practices and development techniques.

## Changes Made

### 1. Containerization and Orchestration
- Dockerized all microservices:
  - [Frontend service](frontend/Dockerfile)
  - [Catalogue service](catalogue/Dockerfile)
  - [Recommendation service](recommendation/Dockerfile)
  - [Voting service](voting/Dockerfile)
- Created a comprehensive [Docker Compose configuration](docker-compose.yml) for local development 
and testing
- Improved service isolation and deployment consistency

**Related PR**: [docker: dockerize application #1](https://github.com/AkhilManoj03/practice-devops/pull/1)

### 2. Voting Service Refactoring
- **Original Implementation**: Java Spring Boot ([original code](voting/))
- **New Implementation**: Python FastAPI ([new code](voting-fastapi/))
- **Reason for Change**: 
  - Addressed performance issues with the original Spring Boot implementation
  - Eliminated slow boot times and hanging issues
  - Improved service reliability and stability
  - Reduced resource consumption

**Related PR**: [voting: new framework for voting service #2](https://github.com/AkhilManoj03/practice-devops/pull/2)

### 3. Catalogue Service Modernization
- **Original Implementation**: Python Flask ([original code](catalogue/))
- **New Implementation**: Python FastAPI ([new code](catalogue-fastapi/))
- **Reason for Change**:
  - Prepared for service consolidation
  - Improved API performance and documentation
  - Enhanced type safety and validation
  - Better async support

**Related PR**: [catalogue: recreate service in FastAPI #3](https://github.com/AkhilManoj03/practice-devops/pull/3)

### 4. Service Consolidation
- Created a unified [Origami Product Service](combined-fastapi/)
- Combined Catalogue and Voting services into a single API
- **Benefits**:
  - Reduced service complexity
  - Eliminated redundant code
  - Improved maintainability
  - Better resource utilization
  - Simplified deployment and monitoring

**Related PR**: [combined: create combined voting and catalogue service #4](https://github.com/AkhilManoj03/practice-devops/pull/4)

### 5. Database Flexibility
- Implemented dual database support:
  - JSON file storage (for development/testing)
  - PostgreSQL database (for production)
- Added database abstraction layer
- Improved data persistence and reliability

**Related PR**: [combined: add db support in data access layer #5](https://github.com/AkhilManoj03/practice-devops/pull/5)

### 6. Performance Optimization
- Implemented Redis caching layer
- Added caching between API and database
- **Benefits**:
  - Reduced database load
  - Improved response times
  - Better scalability
  - Enhanced user experience

**Related PR**: [combined: feat: implement Redis caching for API #6](https://github.com/AkhilManoj03/practice-devops/pull/6)

### 7. Observability and Distributed Tracing
- Implemented OpenTelemetry across all microservices for comprehensive observability
- Added Jaeger for distributed tracing visualization
- **Approach**: Standardized on automatic instrumentation across all services for consistency
- **Benefits**:
  - End-to-end request tracing across microservices
  - Performance monitoring and bottleneck identification
  - Error tracking and debugging capabilities
  - Service dependency mapping
  - Improved system observability and maintainability

**Related PR**: [otel: Implement OpenTelementary and Jaegar #8](https://github.com/AkhilManoj03/practice-devops/pull/8)

### 8. Application Architecture Restructuring and Cleanup
- **Restructured Combined FastAPI Service**: Reorganized the application into distinct architectural layers
  - **API Layer**: Hosts all public API routes and their dependencies
  - **Core Layer**: Contains business logic for Product, Votes, and System services  
  - **Infrastructure Layer**: Manages data access logic and database operations
- **Removed JSON Datasource Support**:
  - Eliminated all JSON data source configurations and related code
  - Simplified data access layer to use only PostgreSQL for persistent storage
  - Updated `products.json` to serve exclusively for initial database setup
- **Service Renaming**: Renamed `combined-fastapi` folder to `product` for better clarity and representation
- **Database Configuration Improvements**: 
  - Replaced generic database configuration with specific PostgreSQL settings
  - Made database configuration required (non-optional) since database is now the only data source
  - Updated field names to follow PostgreSQL conventions (`postgres_*` prefix)
- **Benefits**:
  - Enhanced scalability and maintainability through clear separation of concerns
  - Reduced complexity by eliminating dual data source support
  - Improved code organization for easier onboarding and future development
  - Simplified configuration management
  - Better alignment with production-ready practices

**Related PR**: [product: refactor: restructure application architecture and remove JSON datasource #9](https://github.com/AkhilManoj03/practice-devops/pull/9)

### 0. Addition of Authentication Service
- **New Microservice**: Introduced a Rust-based authentication service using the Axum framework
- **Features**:
  - User registration and login with bcrypt password hashing
  - JWT token generation (RS256, 1-hour expiration, user roles)
  - JWKS and OpenID Connect endpoints for standards-based integration
  - Role-based access control for secure API usage
  - CORS support and structured logging
- **Integration**:
  - Frontend uses the authentication service for user login/registration; JWT tokens are set as 
  HTTP-only cookies
  - Product service validates JWT tokens using the JWKS endpoint, ensuring only authenticated users 
  can access protected endpoints (e.g., voting)
- **Security**:
  - BCrypt for password hashing, RSA for JWT signing
  - Environment-based configuration for database and key management

**Related PR**: [auth: implement authentication microservice #9](https://github.com/AkhilManoj03/practice-devops/pull/9)

## Learning Outcomes
This project has provided valuable hands-on experience in:
- Modern containerization techniques
- Microservices architecture and optimization
- API development and performance tuning
- Database design and caching strategies
- DevOps best practices
- Service consolidation and refactoring
- Distributed tracing and observability implementation
