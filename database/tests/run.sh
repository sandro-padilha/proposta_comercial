#!/usr/bin/env bash
# Sobe um PostgreSQL temporário, aplica o stub do Supabase + schema.sql e roda os testes de RLS.
# Requer os binários do PostgreSQL >= 15 (initdb, pg_ctl, psql). Não toca em nenhum banco existente.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
INITDB="${INITDB:-$(ls /usr/lib/postgresql/*/bin/initdb 2>/dev/null | sort -V | tail -1)}"
PGBIN="$(dirname "$INITDB")"
PORT="${PGPORT:-55432}"

if [ "$(id -u)" = 0 ]; then
  # O postgres não roda como root: usa o usuário "postgres" e um diretório que ele possa escrever.
  RUN=(runuser -u postgres --)
  WORK="/var/lib/postgresql/casa3d_test_$$"
  mkdir -p "$WORK" && chown postgres:postgres "$WORK"
else
  RUN=()
  WORK="$(mktemp -d)"
fi

cleanup() {
  "${RUN[@]}" "$PGBIN/pg_ctl" -D "$WORK/data" -m immediate stop >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT

"${RUN[@]}" "$INITDB" -D "$WORK/data" -A trust -U postgres >/dev/null
"${RUN[@]}" "$PGBIN/pg_ctl" -D "$WORK/data" -o "-p $PORT -k $WORK -c listen_addresses=''" -l "$WORK/pg.log" -w start >/dev/null

PSQL=("$PGBIN/psql" -X -q -v ON_ERROR_STOP=1 -h "$WORK" -p "$PORT" -U postgres)
"${PSQL[@]}" -d postgres -c "create database casa3d_test"
"${PSQL[@]}" -d casa3d_test -f "$HERE/00_supabase_stub.sql"
"${PSQL[@]}" -d casa3d_test -f "$HERE/../schema.sql"
"${PSQL[@]}" -d casa3d_test -f "$HERE/10_rls.test.sql" 2>&1
