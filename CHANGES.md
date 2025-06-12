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

**Related PR**: [observability: implement OpenTelemetry and Jaeger distributed tracing #7](https://github.com/AkhilManoj03/practice-devops/pull/7)

## Learning Outcomes
This project has provided valuable hands-on experience in:
- Modern containerization techniques
- Microservices architecture and optimization
- API development and performance tuning
- Database design and caching strategies
- DevOps best practices
- Service consolidation and refactoring
- Distributed tracing and observability implementation
