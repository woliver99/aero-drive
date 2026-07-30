FROM docker.io/library/alpine:latest

# Install runtime dependencies
RUN apk add --no-cache rclone python3 openssl ca-certificates curl

WORKDIR /app

# Copy application scripts
COPY app/ /app/

# Make application executable and expose aerodrive CLI command
RUN chmod -R 755 /app && ln -s /app/cli.py /usr/local/bin/aerodrive

ENV AERODRIVE_DATA_DIR="/var/lib/aerodrive"
ENV PORT="8080"
ENV BASE_URL=""

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --retries=3 --start-period=5s \
  CMD curl -f -k https://localhost:${PORT}/ || exit 1

# User is set at container runtime via --user
ENTRYPOINT ["/app/entrypoint.sh"]
