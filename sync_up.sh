#!/usr/bin/env bash
# ==============================================================================
# sync_up.sh — 로컬 코드/문서를 서버로 push
# ==============================================================================
# 로컬 udler2018_bnmf/ 폴더를 서버 ~/udler2018_bnmf/ 로 rsync.
# 대용량 데이터 (data/ 전체, R checkpoint) 는 제외 —
# 서버에서 재생성한 상태를 덮어쓰지 않음.
#
# --delete 를 쓰므로 로컬에서 지운 파일은 서버에서도 지워진다.
# (data/ 와 *.RData 는 --exclude 라 --delete 대상이 아님 — 안전함.)
#
# 사용: bash sync_up.sh
# ==============================================================================
set -e
cd "$(dirname "$0")"

echo "→ Pushing udler2018_bnmf/ code+docs to bnmf server..."
rsync -avz --delete \
  --exclude='data/' \
  --exclude='*.RData' \
  --exclude='_vcf_tmp/' \
  --exclude='.DS_Store' \
  --exclude='__pycache__' \
  udler2018_bnmf/ bnmf:~/udler2018_bnmf/

echo "✓ Done. Server code updated."
