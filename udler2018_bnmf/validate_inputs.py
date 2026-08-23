#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_inputs.py — 폴더 상태를 점검한다. 파이프라인 돌리기 전에 이걸 먼저 통과시킬 것.

확인 항목
  1. manifest.xlsx 의 full_path 가 실제로 존재하는가
  2. 각 요약통계 파일이 파이프라인 필수 컬럼을 갖고 있는가
       VAR_ID(또는 SNP) / Effect_Allele_PH(또는 등가 이름) / P_VALUE / (BETA+SE 또는 ODDS_RATIO)
     * 형질 파일은 OR->BETA 변환 경로가 없으므로 BETA+SE 가 없으면 그 열이 조용히 빠진다.
       여기서 미리 잡는다.
  3. sample_size 누락 행
  4. trait_gwas 행 수가 47인가

사용법
  python3 validate_inputs.py          # 점검
  python3 validate_inputs.py --paths /절대/경로  # full_path의 앞부분을 이 경로로 바꿔 저장
"""
import os, sys, gzip, io

try:
    import openpyxl
except ImportError:
    sys.exit("openpyxl 필요:  pip install openpyxl")

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(HERE, "manifest.xlsx")

EA_NAMES = {"Effect_Allele_PH", "Effect_Allele", "effect_allele", "A1", "EA",
            "Allele1", "allele1", "ALLELE1", "Tested_Allele"}
ID_NAMES = {"VAR_ID", "SNP", "MarkerName", "rsid", "RSID", "variant_id",
            "hm_variant_id", "snpid"}
P_NAMES  = {"P_VALUE", "P", "p", "pval", "P.value", "p_value", "Pvalue", "P-value"}
B_NAMES  = {"BETA", "beta", "Effect", "b", "hm_beta"}
S_NAMES  = {"SE", "se", "StdErr", "standard_error", "hm_se"}
OR_NAMES = {"ODDS_RATIO", "OR", "odds_ratio"}


def header_of(path):
    op = gzip.open if path.endswith(".gz") else open
    try:
        with op(path, "rt", errors="replace") as f:
            line = f.readline()
    except Exception as e:
        return None, f"읽기 실패: {type(e).__name__}"
    for sep in ("\t", ",", " "):
        parts = [p.strip() for p in line.rstrip("\n").split(sep) if p.strip()]
        if len(parts) > 3:
            return parts, ""
    return None, "헤더 파싱 실패"


def check_cols(cols):
    problems = []
    if not (set(cols) & ID_NAMES):
        problems.append("변이 ID 컬럼 없음")
    if not (set(cols) & EA_NAMES):
        problems.append("effect allele 컬럼 없음")
    if not (set(cols) & P_NAMES):
        problems.append("P 컬럼 없음")
    has_bs = bool(set(cols) & B_NAMES) and bool(set(cols) & S_NAMES)
    if not has_bs:
        if set(cols) & OR_NAMES:
            problems.append("BETA+SE 없이 OR만 있음 → 형질 열은 조용히 제외됨")
        else:
            problems.append("BETA+SE 없음")
    return problems


def rewrite_paths(new_root):
    # 매니페스트의 full_path 는 항상 <new_root>/sumstats_converted/<basename> 으로 재설정.
    # convert_sumstats.py 가 항상 sumstats_converted/ 로 쓰기 때문에 basename 만 보존하면 충분.
    # (이전 버전은 "/sumstats/" 문자열 split 에 의존해 잘못된 경로가 나오는 버그가 있었음.)
    wb = openpyxl.load_workbook(XLSX)
    for sh in ("main_gwas", "trait_gwas"):
        ws = wb[sh]
        hdr = [c.value for c in ws[1]]
        ci = hdr.index("full_path") + 1
        for r in range(2, ws.max_row + 1):
            v = ws.cell(r, ci).value
            if v:
                ws.cell(r, ci).value = os.path.join(
                    new_root, "sumstats_converted", os.path.basename(v))
    wb.save(XLSX)
    print(f"full_path 를 {new_root}/sumstats_converted/ 기준으로 다시 썼습니다.")


def main():
    if "--paths" in sys.argv:
        rewrite_paths(sys.argv[sys.argv.index("--paths") + 1])
        return

    if not os.path.exists(XLSX):
        sys.exit("manifest.xlsx 가 없습니다.")
    wb = openpyxl.load_workbook(XLSX, read_only=True)

    missing, badcols, nosize, ok = [], [], [], 0
    total = 0
    for sh in ("main_gwas", "trait_gwas"):
        ws = wb[sh]
        rows = list(ws.iter_rows(values_only=True))
        hdr = list(rows[0])
        ip = hdr.index("full_path")
        it = hdr.index("trait")
        isz = hdr.index("sample_size") if "sample_size" in hdr else None
        for r in rows[1:]:
            if not r or not r[ip]:
                continue
            total += 1
            name = r[it]
            p = r[ip]
            if isz is not None and not r[isz]:
                nosize.append(name)
            ap = p if os.path.isabs(p) else os.path.join(HERE, p.lstrip("./"))
            if not os.path.exists(ap):
                missing.append((sh, name, p))
                continue
            cols, err = header_of(ap)
            if cols is None:
                badcols.append((sh, name, err))
            else:
                probs = check_cols(cols)
                if probs:
                    badcols.append((sh, name, "; ".join(probs)))
                else:
                    ok += 1

    n_trait = sum(1 for r in list(wb["trait_gwas"].iter_rows(values_only=True))[1:] if r and r[0])

    print("=" * 66)
    print(f"매니페스트 행 {total}개  (trait_gwas {n_trait}개 — 기대값 47)")
    print(f"  통과            {ok}")
    print(f"  파일 없음       {len(missing)}")
    print(f"  컬럼 문제       {len(badcols)}")
    print(f"  sample_size 없음 {len(nosize)}")
    print("=" * 66)
    if missing:
        print("\n[파일 없음] — 아직 안 받은 것")
        for s, n, p in missing:
            print(f"  {s:11s} {n:14s} {p}")
    if badcols:
        print("\n[컬럼 문제] — 받았지만 그대로는 못 쓰는 것")
        for s, n, e in badcols:
            print(f"  {s:11s} {n:14s} {e}")
    if nosize:
        print("\n[sample_size 없음] — 논문 S2에 N이 없던 형질. 직접 채워야 함")
        print("  " + ", ".join(nosize))
    print()
    if missing or badcols:
        print("→ 아직 파이프라인 돌릴 준비가 안 됐습니다.")
        sys.exit(1)
    print("→ 준비 완료.")


if __name__ == "__main__":
    main()
