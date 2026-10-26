# Server Watch

Server Watch is a lightweight Python application that checks whether another computer is reachable through a TCP connection. It is designed to run continuously on a reliable host (such as an Unraid server) and email you if the monitored machine becomes unreachable.

Only the monitoring host needs Server Watch installed. The target machine simply needs to accept TCP connections on the configured port (SSH port `22` is a typical choice for Linux).

## Features

- **Automatic checks:** checks the configured host and TCP port every 30 minutes by default.
- **Fewer false alarms:** requires two consecutive failed checks before declaring an outage.
- **Email alerts:** sends an initial outage notification and repeats it every 12 hours while the host remains offline.
- **Recovery notifications:** emails you when the host becomes reachable again.
- **Persistent state:** saves the last known status, failure count, and notification state in a JSON file, allowing monitoring to resume after container restarts.
- **Docker-friendly logs:** writes monitoring and SMTP errors to standard output/error for inspection with `docker logs` or Unraid's Docker interface.
- **Simple deployment:** uses only Python's standard library and does not require a database or a web interface.

> **Important:** This is a **TCP service reachability monitor**, not a direct power-state monitor. A failed SSH connection could mean the computer is turned off, but it could also mean SSH stopped responding, a firewall blocked the port, or there is a network problem.

## How it works

1. Server Watch attempts a TCP connection to `TARGET_HOST:TARGET_PORT`.
2. A successful check clears the consecutive-failure counter. If the server had been marked offline, Server Watch attempts to send a recovery email.
3. A failed check increments the counter. The **second consecutive failure** marks the target offline and triggers an email.
4. While offline, Server Watch sends a reminder once **12 hours or more** have elapsed since the last successfully submitted outage email (on the next scheduled check).
5. Monitoring state is written to `STATE_FILE` after each check.

With the default 30-minute interval, the first alert is normally sent about **30–60 minutes after a shutdown**, depending on when the shutdown occurred relative to the checks. Email delivery also depends on the SMTP provider and recipient mailbox.

## Requirements

- Docker running on Unraid, Linux, or another Docker-compatible host.
- Network access from the Docker container to the target computer and its TCP port.
- An account with an SMTP provider (the examples use [Purelymail](https://purelymail.com/)).
- An address that remains stable for the monitored machine; a **DHCP reservation** is recommended.

## Quick start: Unraid Docker interface

Once the container image has been published, go to **Unraid → Docker → Add Container** and configure:

| Setting | Value |
| --- | --- |
| Name | `server-watch` |
| Repository | `ghcr.io/sp0k/server-watch:latest` |
| Network Type | `Bridge` |
| Autostart | Enabled |
| WebUI / ports | Not needed |

Add a **Path** mapping:

| Host Path | Container Path | Access |
| --- | --- | --- |
| `/mnt/user/appdata/server-watch` | `/data` | Read/Write |

Add these **environment variables** to the container settings:

| Variable | Example | Explanation |
| --- | --- | --- |
| `TARGET_HOST` | `192.168.1.50` | LAN IP address or DNS hostname of the monitored machine |
| `TARGET_PORT` | `22` | TCP port to connect to, typically SSH for a Linux server |
| `CHECK_INTERVAL` | `1800` | Seconds between checks (default: 1800 / 30 minutes) |
| `STATE_FILE` | `/data/watch_state.json` | JSON state file inside the container; keep it under `/data` |
| `LOG_LEVEL` | `INFO` | Python logging level (`DEBUG`, `INFO`, `WARNING`, etc.) |
| `SMTP_HOST` | `smtp.purelymail.com` | SMTP hostname |
| `SMTP_PORT` | `465` | SMTP-over-TLS port used by `SMTP_SSL` |
| `SMTP_USER` | `server@example.com` | SMTP login and sender address |
| `SMTP_PASSWORD` | *(private password)* | SMTP password or provider-issued app password |
| `MAIL_TO` | `you@example.com` | Notification recipient |

**No incoming ports are required**: Server Watch initiates outbound TCP connections and does not serve a website.

For container restart behavior, enable Unraid **Autostart**. You can also set a Docker restart policy of `unless-stopped` for unexpected process exits, for example:

```bash
docker update --restart unless-stopped server-watch
```

When running, your state file will be stored on Unraid at `/mnt/user/appdata/server-watch/watch_state.json`, outside the container's writable layer.

### Check that it works

```bash
docker logs --tail 50 -f server-watch
cat /mnt/user/appdata/server-watch/watch_state.json
```

The first check begins when the Python program starts. A valid state file is written after each completed check.

## Alternative: Docker Compose

This repository includes `compose.yaml`. On any Docker host with Docker Compose:

```bash
git clone https://github.com/Sp0k/server-watch.git
cd server-watch
cp .env.example .env
```

Edit `.env` to set the target, SMTP credentials, and data directory. On Unraid, set:

```dotenv
SERVER_WATCH_DATA_DIR=/mnt/user/appdata/server-watch
```

Then start the published container image:

```bash
docker compose up -d
docker compose logs -f
```

Update it later with:

```bash
docker compose pull
docker compose up -d
```

If the GHCR package is private, authenticate Docker to `ghcr.io` with an account/token authorized to read it before pulling. Public GHCR packages can be pulled without authentication.

## Building the image locally

If you prefer to build from the repository instead of pulling from GHCR:

```bash
git clone https://github.com/Sp0k/server-watch.git
cd server-watch
docker build -t server-watch:local .
```

The `Dockerfile` is based on Python 3.13 slim, includes CA certificates, and copies the four Python modules. No `requirements.txt` is needed because the app uses only Python's standard library.

## Publishing to GitHub Container Registry

The workflow at `.github/workflows/publish.yml` builds and publishes `ghcr.io/sp0k/server-watch` using GitHub Actions. It runs when code is pushed to `main`, when a version tag such as `v1.0.0` is pushed, or when launched manually from the **Actions** tab.

1. Commit `.github/workflows/publish.yml` to the repository and push to `main`.
2. Open **GitHub → Sp0k/server-watch → Actions → Publish Server Watch image** and verify that the run succeeds.
3. Open the newly created container package from your GitHub profile's **Packages** section. GHCR packages are **private by default**. If you want Unraid to pull it without authentication, go to the package settings and change its visibility to **Public**.
4. Use `ghcr.io/sp0k/server-watch:latest` in Unraid or Compose.

The workflow uses the automatically supplied `GITHUB_TOKEN` with `packages: write`; you do **not** need to add an SMTP password or a personal access token as a GitHub Actions secret for this build.

GitHub Actions **publishes a new image**, but it does **not** automatically replace a running Unraid container. Pull the updated image and recreate the container to deploy a new release, retaining the `/data` mapping.

## Local Python development

You can run the application directly on your development machine if you export the environment variables listed above. A `.env` file is *not automatically loaded* by Python's `os.environ`; Docker Compose can load it using `env_file`, or you can export the variables in your terminal.

```bash
python3 main.py
```

During testing, you may temporarily set `CHECK_INTERVAL` to a shorter period. Restore `1800` before production use. Note that the initial outage threshold (two failures) and the 12-hour reminder interval are currently defined in `monitor.py` rather than exposed as environment variables.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| No notifications | Check `docker logs`, SMTP settings, and spam filtering |
| Repeated connection failures | Verify the LAN IP, SSH/service port, firewall, and reachability from the Docker host |
| Authentication failure | Verify your SMTP username, password/app password, and provider rules |
| SSL certificate error | Verify the certificate chain and CA trust store; do not disable certificate verification |
| State disappears after restart | Confirm `STATE_FILE=/data/watch_state.json` and a writable persistent host-to-`/data` mapping |
| Cannot pull GHCR image | Confirm the Actions build succeeded and the package is public, or authenticate for a private package |

## Security and limitations

- Do not commit `.env`, SMTP passwords, or runtime JSON state files to Git.
- The Unraid Docker configuration can expose credentials to server administrators; protect access to your Unraid server.
- The monitor's SMTP submission success log confirms acceptance by the SMTP server, not final delivery to the recipient's inbox.
- This is a single-target monitor; multiple servers would require multiple instances or additional application logic.
- Time-based reminders run during scheduled checks, not via an independent timer.
- Your monitored server requires **no Server Watch agent** or Python installation.

## Project structure

```text
server-watch/
├── checker.py                 # TCP connectivity check
├── main.py                    # Scheduler and logging setup
├── monitor.py                 # Failure/recovery state and persistence
├── notifier.py                # SMTP email submission
├── Dockerfile                 # Container build
├── compose.yaml               # Optional Docker Compose deployment
├── .env.example               # Configuration template (no secrets)
└── .github/workflows/publish.yml  # GHCR publishing
```

