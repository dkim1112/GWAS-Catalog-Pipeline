#!/usr/bin/env bash
# ==============================================================================
# add_charge_traits.sh — CHARGE 지방산 5개를 인풋에 추가한다.
#
# 서버의 udler2018_bnmf 폴더 안에서 실행하세요.
# rsID 맵과 sqlite 색인이 이미 있으므로 다시 만들 필요 없습니다.
#
#   cd /BiO2/home/daniel/udler2018_bnmf
#   bash add_charge_traits.sh
#
# 하는 일
#   1) CHARGE 원본 5개 내려받기 (합계 약 1.2GB)
#   2) inputs_manifest.csv 의 해당 행을 DIRECT_URL 로 갱신
#   3) convert_sumstats.py 로 5개만 변환
#   4) manifest.xlsx 의 trait_gwas 시트에 5행 추가 (35 -> 40)
#   5) validate_inputs.py 로 점검
# ==============================================================================
set -u
cd "$(dirname "$0")"

BASE="https://faculty.washington.edu/rozenl/files"

declare -A F=(
  [dpa]="CHARGE_N3_DPA.txt"
  [palmitoleic]="CHARGE_161n7.txt"
  [n6_1821]="N6meta182.txt"
  [n6_1831]="N6meta183.txt"
  [n6_2031]="N6meta203.txt"
)

# Udler S2 Table 기재 표본수
declare -A N=( [dpa]=8866 [palmitoleic]=8961 [n6_1821]=8631 [n6_1831]=8631 [n6_2031]=8631 )

mkdir -p sumstats logs

echo "[1/5] 원본 내려받기"
for k in "${!F[@]}"; do
  if [ -s "sumstats/${k}.txt" ]; then
    echo "  [skip] $k 이미 있음"; continue
  fi
  echo "  [get ] $k <- $BASE/${F[$k]}"
  curl -fSL --retry 5 --retry-delay 5 -o "sumstats/${k}.txt" "$BASE/${F[$k]}" \
    || { echo "  !! $k 실패"; rm -f "sumstats/${k}.txt"; }
done

echo "[2/5] inputs_manifest.csv 갱신"
python3 - <<'PY'
import csv
BASE="https://faculty.washington.edu/rozenl/files"
F={"dpa":"CHARGE_N3_DPA.txt","palmitoleic":"CHARGE_161n7.txt",
   "n6_1821":"N6meta182.txt","n6_1831":"N6meta183.txt","n6_2031":"N6meta203.txt"}
rows=list(csv.DictReader(open("inputs_manifest.csv")))
n=0
for r in rows:
    if r["key"] in F:
        r["direct_url"]=f"{BASE}/{F[r['key']]}"
        r["status"]="DIRECT_URL"
        r["source"]="CHARGE"
        r["note"]="지방산; Udler S2 기준"
        n+=1
with open("inputs_manifest.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print(f"  {n}개 행 갱신")
PY

echo "[3/5] 포맷 변환 (5개, 각 10분 내외)"
# convert_sumstats.py 는 _rsid_map.sqlite 를 필요로 함. 없으면 재생성 (~4분).
if [ ! -s "_rsid_map.sqlite" ]; then
    echo "  ! _rsid_map.sqlite 없음 -> --index 로 재생성 (~4분)"
    python3 convert_sumstats.py --index
fi
python3 convert_sumstats.py dpa palmitoleic n6_1821 n6_1831 n6_2031

echo "[4/5] manifest.xlsx 에 5행 추가"
python3 - <<'PY'
import openpyxl, os
N={"dpa":8866,"palmitoleic":8961,"n6_1821":8631,"n6_1831":8631,"n6_2031":8631}
wb=openpyxl.load_workbook("manifest.xlsx"); ws=wb["trait_gwas"]
hdr=[c.value for c in ws[1]]
it,ip,isz = hdr.index("trait")+1, hdr.index("full_path")+1, hdr.index("sample_size")+1
have={ws.cell(r,it).value for r in range(2,ws.max_row+1)}
root=os.path.abspath(".")
added=0
for k,n in N.items():
    conv=os.path.join(root,"sumstats_converted",f"{k}.tsv.gz")
    if k in have:
        print(f"  [skip] {k} 이미 매니페스트에 있음"); continue
    if not os.path.exists(conv):
        print(f"  !! {k} 변환본 없음 — 건너뜀"); continue
    ws.append([k, conv, n]); added+=1
wb.save("manifest.xlsx")
print(f"  {added}행 추가 -> trait_gwas 총 {ws.max_row-1}행")
PY

echo "[5/5] 점검"
python3 validate_inputs.py

cat <<'EOM'

------------------------------------------------------------------
다음 단계
형질이 늘었으므로 z 행렬이 바뀝니다. 4절부터 다시 돌려야 합니다.
변이 목록(pruned_vars)은 그대로이므로 2~3절은 다시 안 돌려도 됩니다.

  R
  > load("my_workspace_udler2018_eur_v1.RData")
  > # 매니페스트를 다시 읽어 trait_ss_files / trait_ss_size 를 갱신한 뒤
  > # 4절(fetch_summary_stats)부터 순서대로 재실행

이전 결과와 섞이지 않게 version 값을 바꾸는 것을 권합니다
(예: version <- "udler2018_eur_v2").
------------------------------------------------------------------
EOM
