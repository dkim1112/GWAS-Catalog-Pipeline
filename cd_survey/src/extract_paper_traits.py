#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
extract_paper_traits.py  -  B2 검증용: 논문 supplementary에서 trait 목록 '코드로' 추출
================================================================================
왜 이 파일이 있나:
  B2 검증(validate_t2d_trait_axis.py)의 ground truth = "각 논문이 실제로 쓴 trait 전체 목록".
  이 목록을 사람이 웹에서 눈으로 읽어 옮기면 '그 사람'에게 의존한다 -> 파이프라인이 아님.
  그래서 목록 추출을, 논문별 supplementary 파일을 '코드가 다운로드·파싱'하는 것으로 만든다.

  즉, 사람이 대는 것은 아래 SUPPLEMENTS의 '설정'(어느 파일의 어느 sheet·어느 컬럼,
  keep 필터가 있으면 그 조건)뿐이다. 이는 gwas_catalog_survey.py의 CONFIG와 같은 성격의
  '큐레이션'이고, 실제 목록 뽑기는 코드가 재현 가능하게 수행한다.

한계(정직하게):
  - Udler 2018, Suzuki 2024는 trait 목록이 '표'가 아니라 Methods 본문/Figure 1에 있어
    자동 파싱 대상이 아니다 -> method="manual"로 두고, 사람이 읽어 넣은 목록 + 출처를 기록.
    (표 형태인 Kim/Smith/Pascat만 xlsx 자동 추출.)
  - 추출된 것은 논문의 '원 라벨'(sex별/adjBMI/ratio 포함 raw 문자열)이다. 이를 우리 canonical
    표현형으로 매핑·축약하는 것은 사람 검토 단계 -> 그 결과를 validate_t2d_trait_axis.py의
    per-paper 리스트에 반영한다. (원 라벨 -> canonical 매핑까지 자동화하진 않음. 오매핑 위험.)

동작:
  python extract_paper_traits.py            # 모든 논문 추출 -> paper_traits_extracted.csv
  python extract_paper_traits.py --preview "Smith 2024"   # 그 논문 xlsx의 sheet/컬럼명만 출력
                                            # (설정한 sheet/컬럼이 안 맞을 때 config 교정용)
필요 패키지: requests, pandas, openpyxl
================================================================================
"""
import sys, io, csv, requests
import pandas as pd
import gwas_catalog_survey as g   # 출력 경로(outputs/) 통일용

# ---------------------------------------------------------------------------
# 논문별 추출 설정. url/sheet/trait_column/keep_* 는 2026-07 확인한 공개 supplementary 기준.
# sheet/컬럼명이 실제와 다르면 --preview 로 확인해 이 값만 고치면 된다.
# ---------------------------------------------------------------------------
SUPPLEMENTS = {
 "Kim 2023": {
   "method":"xlsx",
   "citation":"Kim H, Westerman KE, Smith K, ... Udler MS. Diabetologia 2023;66:495-507. "
              "doi:10.1007/s00125-022-05848-6 (PMC10108373)",
   "url":"https://www.medrxiv.org/content/medrxiv/early/2022/08/05/2022.07.11.22277436/DC1/embed/media-1.xlsx",
   "sheet":"Table S7",            # 클러스터링에 실제 쓴 64 trait(범주 포함)
   "trait_column":"Trait",        # 안 맞으면 --preview 로 실제 컬럼명 확인
   "keep_column":None, "keep_values":None,
   "note":"Table S3(75 후보, keep/filter 플래그)에서 keep된 64 = Table S7. 원 라벨엔 sex별 변형 포함.",
 },
 "Smith 2024": {
   "method":"xlsx",
   "citation":"Smith K, ... Udler MS. Multi-ancestry polygenic mechanisms of T2D. "
              "Nature Medicine 2024. doi:10.1038/s41591-024-02865-3 (PMC10602111)",
   "url":"https://static-content.springer.com/esm/art%3A10.1038%2Fs41591-024-02865-3/MediaObjects/41591_2024_2865_MOESM2_ESM.xlsx",
   "sheet":"S4",                  # 'Trait filtering results' 패널
   "trait_column":"Trait",
   "keep_column":"trait kept",    # 165 후보 중 clustering에 kept된 110만
   "keep_values":["Yes","yes","TRUE",True,1,"kept"],
   "note":"110 = 165 후보에서 kept. 원 라벨은 sex별(_female/_male)/adjBMI/ratio -> canonical 축약 필요.",
 },
 "Pascat 2026": {
   "method":"xlsx",
   "citation":"Pascat V, ... Prokopenko I. Partitioned polygenic scores ... T2D and hypertension "
              "comorbidity. Nature Communications 2026. doi:10.1038/s41467-025-67449-2",
   "url":"https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-025-67449-2/MediaObjects/41467_2025_67449_MOESM2_ESM.xlsx",
   "sheet":"Supplementary Data 4",
   "trait_column":"GWAS Phenotype",
   "keep_column":None, "keep_values":None,
   "note":"출판본 45 endophenotype(프리프린트는 49; TNF-alpha/IL-6/IL-10/serum ACE 4개 삭제).",
 },
 # ---- 표가 아니라 본문/그림 -> 자동 파싱 불가. 사람이 읽은 목록을 출처와 함께 기록 ----
 "Udler 2018": {
   "method":"manual",
   "citation":"Udler MS, et al. PLoS Medicine 2018;15:e1002654. doi:10.1371/journal.pmed.1002654",
   "source":"Methods 'Variant and trait selection' 본문(표 아님). 정량형질만 matrix, outcome 10종은 validation-only.",
   "manual_traits":None,  # 최종 canonical 목록은 validate_t2d_trait_axis.py의 UDLER_2018 참조
 },
 "Suzuki 2024": {
   "method":"manual",
   "citation":"Suzuki K, et al. Nature 2024;627:347-357. doi:10.1038/s41586-024-07019-6",
   "source":"Figure 1 / Methods(표 아님). bNMF 입력 37 형질 7범주.",
   "manual_traits":None,  # 최종 canonical 목록은 validate_t2d_trait_axis.py의 SUZUKI_2024 참조
 },
}

def _download_xlsx(url):
    r=requests.get(url, timeout=120, headers={"User-Agent":"Mozilla/5.0 (research pipeline)"})
    r.raise_for_status()
    return pd.ExcelFile(io.BytesIO(r.content))

def preview(paper):
    cfg=SUPPLEMENTS[paper]
    if cfg["method"]!="xlsx":
        print(f"{paper}: method={cfg['method']} (표 아님) -> {cfg.get('source','')}"); return
    xl=_download_xlsx(cfg["url"])
    print(f"{paper} sheets: {xl.sheet_names}")
    sh = cfg["sheet"] if cfg["sheet"] in xl.sheet_names else xl.sheet_names[0]
    df=xl.parse(sh, header=0, nrows=5)
    print(f"  [{sh}] columns: {list(df.columns)}")

def extract(paper):
    """반환: (traits[list], source_note[str]). xlsx면 다운로드·파싱, manual이면 기록만."""
    cfg=SUPPLEMENTS[paper]
    if cfg["method"]=="manual":
        return [], f"MANUAL ({cfg['source']}) -> 목록은 validate_t2d_trait_axis.py 참조"
    xl=_download_xlsx(cfg["url"])
    if cfg["sheet"] not in xl.sheet_names:
        return [], (f"sheet '{cfg['sheet']}' 없음. 실제: {xl.sheet_names} "
                    f"-> --preview 로 확인 후 config 교정")
    df=xl.parse(cfg["sheet"], header=0)
    if cfg["trait_column"] not in df.columns:
        return [], (f"컬럼 '{cfg['trait_column']}' 없음. 실제: {list(df.columns)} -> config 교정")
    if cfg.get("keep_column"):
        if cfg["keep_column"] in df.columns:
            df=df[df[cfg["keep_column"]].isin(cfg["keep_values"])]
        else:
            return [], f"keep_column '{cfg['keep_column']}' 없음. 실제: {list(df.columns)}"
    traits=[str(t).strip() for t in df[cfg["trait_column"]].dropna().tolist() if str(t).strip()]
    return traits, f"xlsx {cfg['sheet']}::{cfg['trait_column']} ({len(traits)}개 raw 라벨)"

def main():
    if len(sys.argv)>=3 and sys.argv[1]=="--preview":
        preview(sys.argv[2]); return
    out=[]
    for paper in SUPPLEMENTS:
        try:
            traits, note = extract(paper)
        except Exception as e:
            traits, note = [], f"ERROR: {type(e).__name__}: {e}"
        print(f"\n===== {paper} =====\n  {note}")
        for t in traits: print("   -", t)
        for t in (traits or [""]):
            out.append({"paper":paper,"raw_trait":t,"note":note,"citation":SUPPLEMENTS[paper]["citation"]})
    with open(g.outpath("paper_traits_extracted.csv"),"w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=["paper","raw_trait","note","citation"]); w.writeheader(); w.writerows(out)
    print(f"\n-> {g.outpath('paper_traits_extracted.csv')} 저장. 원 라벨 -> canonical 매핑/축약은 사람 검토 후")
    print("   validate_t2d_trait_axis.py 의 per-paper 리스트에 반영.")

if __name__=="__main__":
    main()
