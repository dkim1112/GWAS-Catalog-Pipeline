#!/usr/bin/env bash
# ==============================================================================
# sync_check.sh — 로컬 ↔ 서버 정렬 상태 확인 (실제 전송 없음, dry-run 만)
#
# 사용: bash sync_check.sh
#
# 출력:
#   [UP]   로컬 → 서버 방향에서 밀어올릴 파일 목록
#   [DOWN] 서버 → 로컬 방향에서 가져올 파일 목록
#   둘 다 비어 있으면 완벽 sync.
# ==============================================================================
set -u
cd "$(dirname "$0")"

EXCL=(
  --exclude='sumstats/'
  --exclude='sumstats_converted/'
  --exclude='rsid_maps_by_chr/'
  --exclude='_rsid_map.sqlite'
  --exclude='_vcf_tmp/'
  --exclude='*.RData'
  --exclude='.DS_Store'
  --exclude='__pycache__'
  --exclude='udler2018_eur_v1_results/'
  --exclude='udler2018_eur_v2_results/'
  --exclude='logs/'
)

echo "===================================================================="
echo "[UP] 로컬 → 서버 방향 (dry-run) — sync_up.sh 가 밀어올릴 것"
echo "===================================================================="
rsync -avzn "${EXCL[@]}" udler2018_bnmf/ bnmf:~/udler2018_bnmf/ \
  | grep -Ev '^sending|^sent |^total size|^\.$|^$|^receiving|^building' || true

echo
echo "===================================================================="
echo "[DOWN] 서버 → 로컬 방향 (dry-run) — 서버에만 있거나 새로운 것"
echo "===================================================================="
rsync -avzn "${EXCL[@]}" bnmf:~/udler2018_bnmf/ udler2018_bnmf/ \
  | grep -Ev '^sending|^sent |^total size|^\.$|^$|^receiving|^building' || true

echo
echo "===================================================================="
echo "두 섹션 모두 파일 목록 없이 총 바이트만 뜨면 = 완벽 sync"
echo "===================================================================="
