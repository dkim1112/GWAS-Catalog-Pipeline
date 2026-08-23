#!/usr/bin/env bash
# ==============================================================================
# sync_down.sh — 서버 실행 결과를 로컬로 pull
# ==============================================================================
# bNMF 결과 폴더 + 실행 로그를 서버에서 가져와 git 에 커밋 가능한 상태로.
# 대용량 데이터 (sumstats, 변환본, rsID 맵) 은 안 가져옴.
#
# 사용: bash sync_down.sh
# ==============================================================================
set -e
cd "$(dirname "$0")"

echo "→ Pulling bNMF results from bnmf server..."
rsync -avz bnmf:~/udler2018_bnmf/udler2018_eur_v1_results/ \
  udler2018_bnmf/udler2018_eur_v1_results/

echo "→ Pulling execution logs from bnmf server..."
rsync -avz bnmf:~/udler2018_bnmf/logs/ udler2018_bnmf/logs/

echo "✓ Done. Local now has server results."
echo
echo "Optional next steps:"
echo "  git add udler2018_bnmf/udler2018_eur_v1_results/ udler2018_bnmf/logs/"
echo "  git commit -m 'sync: bNMF results from server'"
