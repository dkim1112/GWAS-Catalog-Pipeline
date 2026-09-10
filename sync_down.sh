#!/usr/bin/env bash
# ==============================================================================
# sync_down.sh — 서버 실행 결과를 로컬로 pull
# ==============================================================================
# 매니페스트 + bNMF 결과 + 실행 로그를 서버에서 가져와 git 에 커밋 가능한 상태로.
# 대용량 입력 (data/) 과 R 체크포인트 (*.RData) 는 안 가져온다.
#
# 사용: bash sync_down.sh   (먼저 bash sync_check.sh 로 dry-run 확인 권장)
# ==============================================================================
set -e
cd "$(dirname "$0")"

echo "→ Pulling manifest (server authoritative)..."
rsync -avz bnmf:~/udler2018_bnmf/manifest.xlsx      udler2018_bnmf/manifest.xlsx
rsync -avz bnmf:~/udler2018_bnmf/inputs_manifest.csv udler2018_bnmf/inputs_manifest.csv

echo "→ Pulling bNMF results (all versions) from bnmf server..."
rsync -avz --exclude='*.RData' \
  bnmf:~/udler2018_bnmf/results/ udler2018_bnmf/results/

echo "→ Pulling execution logs from bnmf server..."
rsync -avz bnmf:~/udler2018_bnmf/logs/ udler2018_bnmf/logs/

echo "✓ Done. Local now has server manifest + results."
echo
echo "Optional next steps:"
echo "  git add udler2018_bnmf/"
echo "  git commit -m 'sync: manifest+bNMF results from server'"
