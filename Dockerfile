FROM docker.io/library/alpine:latest

# Install runtime dependencies
RUN apk add --no-cache rclone python3 openssl ca-certificates curl

WORKDIR /app

# Copy application scripts
COPY app/ /app/

# Make application executable
RUN chmod -R 755 /app

ENV DATA_DIR="/var/lib/maple-drive"
ENV PORT="8080"
ENV BASE_URL=""

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --retries=3 --start-period=5s \
  CMD curl -f -k https://localhost:${PORT}/ || exit 1

# User is set at container runtime via --user
ENTRYPOINT ["/app/entrypoint.sh"]
