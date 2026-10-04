#!/usr/bin/env bash
# Checks the running capstone, the way an engineer would check it by hand.
# Every check prints the command idea it uses, so you can run it yourself.
#
#   ./verify.sh                 checks the running stack
#   ./verify.sh --persistence   also runs "docker compose down" + "up" and checks the data survived
set -uo pipefail
cd "$(dirname "$0")" || exit 1
# Git Bash on Windows rewrites paths like /app into C:/Program Files/Git/app; turn that off
export MSYS_NO_PATHCONV=1

PORT="${WEB_PORT:-8080}"
URL="http://localhost:${PORT}"
failures=0
if [ -t 1 ]; then G=$'\033[32m' R=$'\033[31m' N=$'\033[0m'; else G='' R='' N=''; fi
ok()   { printf '  %sPASS%s  %s\n' "$G" "$N" "$1"; }
bad()  { printf '  %sFAIL%s  %s\n' "$R" "$N" "$1"; failures=$((failures + 1)); }
check() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then ok "$name"; else bad "$name"; fi; }

health() { docker inspect --format '{{.State.Health.Status}}' "$1" 2>/dev/null; }

echo "1. Containers (docker compose ps, docker inspect)"
for c in capstone-web-1 capstone-api-1 capstone-db-1; do
  for _ in $(seq 1 30); do [ "$(health "$c")" = healthy ] && break; sleep 2; done
  if [ "$(health "$c")" = healthy ]; then ok "$c is running and healthy"; else bad "$c is $(health "$c" || echo missing)"; fi
done

echo "2. Ports (only the web container is published)"
check "web page answers on ${URL}" curl -fsS "$URL/"
check "API is NOT published on localhost:5000" bash -c "! curl -s --max-time 2 http://localhost:5000/"
check "database is NOT published on localhost:5432" bash -c "! curl -s --max-time 2 http://localhost:5432/"

echo "3. Application (browser -> web -> api -> db)"
check "GET /api/health says the database is ok" bash -c "curl -fsS $URL/api/health | grep -q '\"database\":\"ok\"'"
marker="verify-$(date +%s)"
check "POST /api/messages stores a message" curl -fsS -X POST -H 'Content-Type: application/json' -d "{\"text\":\"$marker\"}" "$URL/api/messages"
check "GET /api/messages returns it" bash -c "curl -fsS $URL/api/messages | grep -q $marker"

echo "4. Networks (frontend: web+api, backend: api+db)"
check "api can reach db (same backend network)" docker compose exec -T api python -c "import socket; socket.create_connection(('db', 5432), 2)"
check "web can NOT even resolve db (different network)" bash -c "docker compose exec -T web wget -q -T 2 -O /dev/null http://db:5432/ 2>&1 | grep -q 'bad address'"

echo "5. Security basics"
check "api runs as a normal user (uid 10001, not root)" bash -c "[ \"\$(docker compose exec -T api id -u)\" = 10001 ]"
check "web runs as a normal user (not root)" bash -c "[ \"\$(docker compose exec -T web id -u)\" != 0 ]"
check "api filesystem is read-only" bash -c "docker compose exec -T api touch /app/hacked 2>&1 | grep -q 'Read-only file system'"
check "password is not in the api's environment variables" bash -c "! docker inspect capstone-api-1 --format '{{json .Config.Env}}' | grep -qi password="
check "api memory limit is 256 MiB" bash -c "[ \"\$(docker inspect capstone-api-1 --format '{{.HostConfig.Memory}}')\" = 268435456 ]"

echo "6. Data on a volume (docker volume inspect capstone_db-data)"
check "volume capstone_db-data exists" docker volume inspect capstone_db-data
if [ "${1:-}" = "--persistence" ]; then
  echo "   docker compose down  (containers and networks are removed, the volume is kept)"
  docker compose down >/dev/null 2>&1
  docker compose up -d >/dev/null 2>&1
  for _ in $(seq 1 40); do [ "$(health capstone-web-1)" = healthy ] && break; sleep 2; done
  check "after down + up, the message $marker is still there" bash -c "curl -fsS $URL/api/messages | grep -q $marker"
fi

echo
if [ "$failures" -eq 0 ]; then echo "All checks passed."; else echo "$failures check(s) failed. Start with: docker compose ps, then docker compose logs <service>"; fi
exit "$failures"
