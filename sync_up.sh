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
# manifest.xlsx / inputs_manifest.csv 는 서버가 authoritative (add_charge_traits.sh 등이
# 서버에서 수정). 로컬이 오래된 상태로 push 하면 서버 변경사항이 손실됨.
# 로컬에서 이 파일들을 수정할 일 있으면 별도 rsync 로 명시적으로 push 할 것.
rsync -avz \
  --exclude='sumstats/' \
  --exclude='sumstats_converted/' \
  --exclude='rsid_maps_by_chr/' \
  --exclude='_rsid_map.sqlite' \
  --exclude='_vcf_tmp/' \
  --exclude='*.RData' \
  --exclude='udler2018_eur_v1_results/' \
  --exclude='udler2018_eur_v2_results/' \
  --exclude='.DS_Store' \
  --exclude='__pycache__' \
  --exclude='manifest.xlsx' \
  --exclude='inputs_manifest.csv' \
  udler2018_bnmf/ bnmf:~/udler2018_bnmf/

echo "✓ Done. Server code updated."
