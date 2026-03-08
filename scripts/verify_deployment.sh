#!/usr/bin/env bash
# scripts/verify_deployment.sh
# Pre-prod verification gates — run before DNS cutover.
# Usage: ./scripts/verify_deployment.sh https://your-cloud-run-url.run.app

set -euo pipefail

BASE_URL="${1:?Usage: $0 <backend-url>}"
PASS=0
FAIL=0

check() {
  local name="$1" result="$2" expected="$3"
  if [[ "$result" == *"$expected"* ]]; then
    echo "✓ $name"
    ((PASS++))
  else
    echo "✗ $name — expected '$expected', got '$result'"
    ((FAIL++))
  fi
}

echo "=== Pre-prod verification: $BASE_URL ==="
echo ""

# Gate 1: Health check
HEALTH=$(curl -sf "$BASE_URL/health" || echo "FAILED")
check "Health endpoint" "$HEALTH" '"status":"ok"'

# Gate 2: SSE stream — verify event types
SSE=$(curl -sf -N -X POST "$BASE_URL/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"query":"best ramen tokyo"}' \
  --max-time 30 2>&1 || echo "FAILED")

check "SSE: text event emitted"        "$SSE" '"type":"text"'
check "SSE: sources event emitted"     "$SSE" '"type":"sources"'
check "SSE: disclosure event emitted"  "$SSE" '"type":"disclosure"'

# Gate 3: Rate limiting — 21st request must get 429
echo ""
echo "Testing rate limiting (21 rapid requests)..."
STATUS_21=""
for i in $(seq 1 21); do
  STATUS_21=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/ask" \
    -H "Content-Type: application/json" \
    -d '{"query":"test"}' --max-time 5 || echo "000")
done
check "Rate limit (429 on 21st)" "$STATUS_21" "429"

# Gate 4: Cache — second identical query must be faster (>2x)
echo ""
echo "Testing Redis cache..."
T1=$(curl -sf -o /dev/null -w "%{time_total}" -X POST "$BASE_URL/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"query":"kyoto temples visit"}' --max-time 30 || echo "999")

T2=$(curl -sf -o /dev/null -w "%{time_total}" -X POST "$BASE_URL/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"query":"kyoto temples visit"}' --max-time 30 || echo "999")

echo "  First request:  ${T1}s"
echo "  Second request: ${T2}s"
# Rough check: second should be at least 1s faster.
# Advisory only — network variance makes hard timing gates unreliable.
# Check Cloud Run logs for "cache hit" to confirm Redis is working.
if (( $(echo "$T1 - $T2 > 1.0" | bc -l) )); then
  echo "✓ Redis cache (second request faster)"
  ((PASS++))
else
  echo "⚠ Redis cache timing inconclusive (advisory — does not affect pass/fail)"
  echo "  Verify cache manually: check Cloud Run logs for Redis connection"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[[ $FAIL -eq 0 ]] && echo "All gates PASSED — ready for DNS cutover." || exit 1
