# MapleDrive

**MapleDrive** is a simple, containerized WebDAV server powered by rclone and a JSON config.

## Architecture

```
  [ Client (WebDAV / NPM Reverse Proxy) ]
                     │  (HTTPS / Basic Auth)
                     v
      +------------------------------+
      |  rclone serve webdav         | <── TLS (Cert/Key auto-generated)
      +--------------┬---------------+
                     │
                     │  1. Pass user/password via STDIN
                     v
         [ /app/auth.py Proxy ]
                     │
                     │  2. Verify scrypt hash against dictionary keys
                     v
        [ /var/lib/maple-drive/config/users.json ]
                     │
                     │  3. Return JSON with root path
                     v
    [ /var/lib/maple-drive/users/<username>/ ]
```

### Key Design Constraints
- **Engine**: rclone
- **Security**: Runs as any unprivileged UID/GID (e.g., `10000:10000`), drops all Linux capabilities (`--cap-drop=ALL`), and enforces `--security-opt=no-new-privileges`.

---

## Directory Structure

Inside the container (`/var/lib/maple-drive`):

```
/var/lib/maple-drive/
├── config/
│   ├── users.json      # Hashed user passwords and config schema
│   ├── cert.pem        # TLS certificate
│   └── key.pem         # TLS private key
└── users/
    └── <username>/     # Jailed user storage root
```

Application codebase (`/app/`):

```
/app/
├── auth.py             # Auth proxy script called by rclone
└── entrypoint.sh       # Container initialization script
```

---

## Configuration Schema (`users.json`)

Location: `/var/lib/maple-drive/config/users.json`

```json
{
  "users": {
    "woliver99": {
      "password": "scrypt:4a8e...:b9f1..."
    }
  }
}
```

---

## Running & Management

### Starting the Server
Using Docker / Podman Compose:
```bash
./scripts/run.sh
```
Or directly with Compose:
```bash
podman compose up --build -d
```

### Running Integration Tests
```bash
./scripts/test.sh
```

---

## Subpath Routing & Nginx Proxy Manager (NPM)

If you serve Maple Drive behind Nginx Proxy Manager or another reverse proxy under a subpath like `/dav/` (e.g. `https://example.com/dav/`), set the `BASE_URL` environment variable when running the container (e.g. `BASE_URL=/dav/`).

This tells `rclone serve webdav` to expect incoming requests prefixed with `/dav/` and construct proper WebDAV XML link references.


