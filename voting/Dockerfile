FROM --platform=linux/amd64 maven:3.9-eclipse-temurin-19-alpine

WORKDIR /app

# Create non-root user and set up Maven directory permissions
RUN mkdir -p /root/.m2 && \
    chmod -R 777 /root/.m2 && \
    addgroup -S -g 1001 appuser && \
    adduser -S -G appuser -u 1001 -h /home/appuser appuser && \
    mkdir -p /home/appuser/.m2 && \
    chown -R appuser:appuser /app /home/appuser/.m2

# Switch to non-root user early
USER appuser

# Copy pom files
COPY --chown=appuser:appuser pom.xml pom.xml.orig ./

# Copy source code
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser mvnw mvnw.cmd ./

# Build the application and move the jar
RUN mvn package -DskipTests && \
    cp target/*.jar app.jar

EXPOSE 8080

CMD ["java", "-jar", "app.jar"]
