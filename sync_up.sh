#!/usr/bin/env bash
# ==============================================================================
# sync_up.sh — 로컬 코드/문서를 서버로 push
# ==============================================================================
# 로컬 udler2018_bnmf/ 폴더를 서버 ~/udler2018_bnmf/ 로 rsync.
#
# --delete 를 쓴다: 로컬에서 지운 파일이 서버에서도 지워진다.
# 폴더 구조를 바꾸면 서버에 옛 파일이 남는 문제가 있어 넣었다.
#
# 아래는 --exclude 라 --delete 대상이 아니다 (서버 쪽이 authoritative):
#   data/            대용량 입력 약 8GB. 서버에서 생성하고 git 에도 없음
#   *.RData          R 체크포인트. 서버 실행 산출물
#   results/         bNMF 결과. 서버가 원본, sync_down.sh 로 가져옴
#   logs/            실행 로그. 서버가 원본, sync_down.sh 로 가져옴
#   manifest.xlsx    tools/one_off/ 스크립트들이 서버에서 갱신하므로 서버가 원본
#   inputs_manifest.csv   위와 같음
#
# 매니페스트를 로컬에서 고쳤다면 별도 rsync 로 명시적으로 올릴 것.
#
# 사용: bash sync_up.sh   (먼저 bash sync_check.sh 로 dry-run 확인 권장)
# ==============================================================================
set -e
cd "$(dirname "$0")"

echo "→ Pushing udler2018_bnmf/ code+docs to bnmf server..."
rsync -avz --delete \
  --exclude='data/' \
  --exclude='*.RData' \
  --exclude='_vcf_tmp/' \
  --exclude='results/' \
  --exclude='logs/' \
  --exclude='manifest.xlsx' \
  --exclude='inputs_manifest.csv' \
  --exclude='.DS_Store' \
  --exclude='__pycache__' \
  udler2018_bnmf/ bnmf:~/udler2018_bnmf/

echo "✓ Done. Server code updated."
