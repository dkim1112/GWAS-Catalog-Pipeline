#!/usr/bin/env bash
# ==============================================================================
# sync_up.sh — 로컬 코드/문서를 서버로 push
# ==============================================================================
# 로컬 udler2018_bnmf/ 폴더를 서버 ~/udler2018_bnmf/ 로 rsync.
# 대용량 데이터 (sumstats, 변환본, rsID 맵, R checkpoint) 은 제외 —
# 서버에서 재생성한 상태를 덮어쓰지 않음.
#
# 사용: bash sync_up.sh
# ==============================================================================
set -e
cd "$(dirname "$0")"

echo "→ Pushing udler2018_bnmf/ code+docs to bnmf server..."
rsync -avz \
  --exclude='sumstats/' \
  --exclude='sumstats_converted/' \
  --exclude='rsid_maps_by_chr/' \
  --exclude='_rsid_map.sqlite' \
  --exclude='_vcf_tmp/' \
  --exclude='*.RData' \
  --exclude='udler2018_eur_v1_results/' \
  --exclude='.DS_Store' \
  --exclude='__pycache__' \
  udler2018_bnmf/ bnmf:~/udler2018_bnmf/

echo "✓ Done. Server code updated."
