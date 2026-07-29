# AeroDrive: Technical Specification & Architecture

**AeroDrive** is an ultra-lightweight, high-performance, containerized WebDAV storage server powered by `rclone serve webdav` and an internal Python auth proxy.

---

## 1. System Overview & Architecture

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
       [ /var/lib/aerodrive/config/users.json ]
                     │
                     │  3. Return JSON with root path
                     v
   [ /var/lib/aerodrive/users/<username>/ ]
```

### Key Design Constraints
- **Engine**: `rclone serve webdav` for direct POSIX disk I/O and low overhead.
- **Dependencies**: Zero external Python libraries (uses Python 3 standard library only: `hashlib.scrypt`, `json`, `secrets`).
- **Security**: Runs as any unprivileged UID/GID (e.g., `10000:10000`), drops all Linux capabilities (`--cap-drop=ALL`), and enforces `--security-opt=no-new-privileges`.

---

## 2. Directory Structure

Inside the container (`/var/lib/aerodrive`):

```
/var/lib/aerodrive/
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
├── cli.py              # User & password management CLI
└── entrypoint.sh       # Container initialization script
```

Workspace helper:
- `run.sh`: Builds and runs the AeroDrive container locally.

---

## 3. Configuration Schema (`users.json`)

Location: `/var/lib/aerodrive/config/users.json`

```json
{
  "users": {
    "woliver99": {
      "enabled": true,
      "passwords": {
        "scrypt:4a8e...:b9f1...": "thinkpad_laptop"
      }
    }
  }
}
```

---

## 4. Quick Start (`run.sh`)

To build and launch AeroDrive locally with Podman or Docker:

```bash
./run.sh
```

---

## 5. CLI Usage

To manage users and passwords, you can `exec` into the running container directly using the `aerodrive` command:

```bash
# Add a user
podman exec -it aerodrive aerodrive user add woliver99

# List users
podman exec -it aerodrive aerodrive user list

# Remove a user
podman exec -it aerodrive aerodrive user remove woliver99

# Add a user password with a note
podman exec -it aerodrive aerodrive password add woliver99 mysecretpassword "thinkpad_laptop"

# List user passwords
podman exec -it aerodrive aerodrive password list woliver99

# Remove a password by note
podman exec -it aerodrive aerodrive password remove woliver99 "thinkpad_laptop"
```

Alternatively, if you enter an interactive container shell (`podman exec -it aerodrive sh`), you can run `aerodrive` directly from anywhere in the PATH.

---

## 6. Deployment Specification (NixOS + Podman)

```nix
{ ... }:

{
  virtualisation.oci-containers.containers.aerodrive = {
    image = "ghcr.io/yourusername/aerodrive:latest";
    autoStart = true;

    ports = [
      "10102:8080" # HTTPS WebDAV endpoint
    ];

    environment = {
      "PORT" = "8080";
      "AERODRIVE_DATA_DIR" = "/var/lib/aerodrive";
    };

    volumes = [
      "/srv/aerodrive:/var/lib/aerodrive"
    ];

    extraOptions = [
      "--user=10000:10000"
      "--security-opt=no-new-privileges"
      "--cap-drop=ALL"
    ];
  };
}
```

