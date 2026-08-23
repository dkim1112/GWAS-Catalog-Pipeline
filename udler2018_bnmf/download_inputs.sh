#!/usr/bin/env bash
# ==============================================================================
# download_inputs.sh — Udler 2018 재현용 요약통계 내려받기
#
# inputs_manifest.csv 의 status=DIRECT_URL 행만 자동으로 받는다.
# status=NEEDS_MANUAL 행은 브라우저가 필요해서 받지 않고 목록만 출력한다.
#
# 사용법:
#   bash download_inputs.sh          # 받기
#   bash download_inputs.sh --check  # 받지 않고 현황만 출력
#
# 이어받기 지원(curl -C -). 이미 있는 파일은 건너뛴다.
# ==============================================================================
set -u
cd "$(dirname "$0")"
mkdir -p sumstats logs

CHECK=0
[ "${1:-}" = "--check" ] && CHECK=1

ok=0; skip=0; fail=0
manual=()

while IFS=, read -r column key source status direct_url portal_url local_file note; do
    [ "$column" = "column" ] && continue
    [ -z "$key" ] && continue

    if [ "$status" != "DIRECT_URL" ]; then
        manual+=("$key|$source|$portal_url|$note")
        continue
    fi

    # 확장자는 원본 URL을 따른다 (.txt.gz / .tsv.gz 등)
    ext="${direct_url##*/}"; ext="${ext#*.}"
    dest="sumstats/${key}.${ext}"

    if [ -s "$dest" ]; then
        echo "[skip] $key  (이미 있음: $dest)"
        skip=$((skip+1)); continue
    fi
    if [ "$CHECK" = "1" ]; then
        echo "[todo] $key  <- $direct_url"
        continue
    fi

    echo "[get ] $key  <- $direct_url"
    if curl -fSL -C - --retry 3 --retry-delay 5 -o "$dest" "$direct_url" \
            2>> logs/download_errors.log; then
        echo "       -> $dest  ($(du -h "$dest" | cut -f1))"
        ok=$((ok+1))
    else
        echo "       !! 실패 (logs/download_errors.log 확인)"
        rm -f "$dest"; fail=$((fail+1))
    fi
done < inputs_manifest.csv

echo
echo "======================================================================"
echo "자동 다운로드: 성공 $ok / 건너뜀 $skip / 실패 $fail"
echo
echo "아래는 브라우저로 직접 받아 sumstats/ 에 넣어야 하는 것들입니다."
echo "(파일명은 sumstats/<key>.tsv.gz 형태로 맞춰주세요)"
echo "----------------------------------------------------------------------"
printf '%s\n' "${manual[@]}" | while IFS='|' read -r k s p n; do
    printf "  %-14s %-22s %s %s\n" "$k" "$s" "$p" "${n:+($n)}"
done
echo "======================================================================"
echo
echo "질병 GWAS (행 정의용) 는 매니페스트에 없습니다. 따로 받으세요:"
echo "  DIAGRAMv3 Stage 1  ->  http://diagram-consortium.org/downloads.html"
echo "  받은 뒤 sumstats/t2d_diagram_v3.txt.gz 로 두세요."
