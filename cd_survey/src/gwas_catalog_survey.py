#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
GWAS Catalog 전수조사 (자동화)  -  Crohn's Disease bNMF 파일럿
================================================================================
목적:
  박사님 피드백("소수 GWAS 말고 조건 맞는 거의 모든 GWAS를 조사, AI/스크립트로
  자동화")을 실제 코드로 구현한 것. bNMF matrix에 넣을 재료(질병 SNP=rows,
  형질 GWAS=columns)를 GWAS Catalog에서 자동으로 긁어온다.

무엇을 하나:
  1) 질병 축(ROWS)   : Crohn's disease 관련 study 전부
  2) 형질 축(COLUMNS): 4범주(바이오마커/원인/메커니즘/동반질환)의 형질 GWAS 전부
  각 study를 받아 -> European-only 필터 -> CSV로 출력.

기준(박사님 확정):
  - ancestry = European ONLY (다른 ancestry 섞이면 제외)
  - 표본 수(N) 하한 없음

--------------------------------------------------------------------------------
[ CONFIG는 어디서 왔나 = 이 파일의 CONFIG_* 목록의 출처 ]
--------------------------------------------------------------------------------
(a) "어떤 형질을 넣을지"(형질 목록):
    - Week 2에 우리가 T2D bNMF 논문들(Udler 2018, Suzuki 2024, Pascat 2026, Kim
      2023, Smith 2024)에서 "related trait"이 실제로 뭘 가리키는지 역추론해 만든
      4범주 틀 = 바이오마커 / 원인 / 메커니즘 연관 / 동반질환.
    - 그 틀에 IBD 도메인 지식(NOD2/IL23R 축, PSC 등 동반질환)을 채운 것.
    => 즉 형질 "선택"은 도메인 지식 큐레이션이다. (자동 발굴이 아님 = 알려진 한계.
       이 한계를 메우려면 맨 아래 [LDSC 보완] 참고.)

(b) "각 형질을 API에서 어떤 문자열로 부를지"(질의 라벨):
    - GWAS Catalog는 라벨 '정확 일치'로만 검색된다. 그래서 아래 라벨들은
      2026-07 기준으로 이 API에 실제로 질의해 결과>0인 것만 확정해 넣었다.
      (예: "C-reactive protein measurement"는 되지만 "C-reactive protein level"은 0건)
    - 라벨이 안 맞으면(0건) 스크립트가 경고를 찍으므로, 그때 대체 라벨로 교체.

(c) 메커니즘 범주의 PMID:
    - 일반 trait 라벨로는 안 잡히는 pQTL/사이토카인/미생물은 '논문 PMID'로 조회.
      아래 PMID들은 우리가 앞서 확정한 소스 논문에서 가져왔고, 역시 live 검증함.
      (Zhao 2023=37563310, Ahola-Olli 2017=27989323, MiBioGen 2021=33462485)
    - UKB-PPP/deCODE/Nightingale 대사체는 GWAS Catalog에 PMID로 없어서(0건),
      전용 포털을 코드가 아니라 '수동 소스'로 문서화(CONFIG_MECHANISM_MANUAL).

필요 패키지: requests   (pip install requests)   출력: cd_survey/outputs/*.csv (실행: python cd_survey/src/gwas_catalog_survey.py)
재사용: 다른 질환으로 바꾸려면 CONFIG_ROWS의 값만 교체.
================================================================================
"""
import requests, csv, time, os

BASE = "https://www.ebi.ac.uk/gwas/rest/api"      # GWAS Catalog REST API 루트
H    = {"Accept": "application/json"}

# 생성 CSV는 모두 cd_survey/outputs/ 로. 스크립트 위치(cd_survey/src/) 기준으로 잡아 실행 cwd와 무관.
# 다른 위치를 원하면 환경변수 PIPELINE_OUT_DIR 로 덮어쓴다. (검증/추출 스크립트도 g.outpath 사용)
OUT_DIR = os.environ.get("PIPELINE_OUT_DIR",
          os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")))
os.makedirs(OUT_DIR, exist_ok=True)
def outpath(name):
    """생성 파일명을 outputs/ 경로로 변환."""
    return os.path.join(OUT_DIR, name)

# European-only 판정에 쓰는 "비유럽" 키워드. initialSampleSize 텍스트에 이 중 하나라도
# 있으면 European-only가 아니라고 본다. (구조화 ancestry 리소스는 일부 study에서 404라
#  텍스트 파싱이 더 견고해서 이 방식을 씀.)
NON_EUR = ["East Asian","African","Hispanic","Latin","South Asian","Asian unspecified",
           "Sub-Saharan","Native American","Oceanian","Middle Eastern","Greater Middle Eastern",
           "Aboriginal","Central Asian","Southeast Asian","African American",
           "Afro-Caribbean","Korean","Japanese","Chinese","not reported","NR",
           "multi-ancestry","trans-ancestry"]

# ---------------------------------------------------------------------------
# CONFIG 1: 질병 축 (matrix ROWS)
#   CD를 정밀(reported trait="Crohn's disease")하게 + 광의(IBD EFO)로도 훑어 union.
#   광의를 넣는 이유: CD study가 "IBD"로만 태깅돼 정밀 검색에서 누락될 수 있어서.
#   (종류, 값)  종류: "disease"=reported trait 검색, "efo"=EFO 라벨 검색
# ---------------------------------------------------------------------------
CONFIG_ROWS = [
    ("disease", "Crohn's disease"),              # live 확인: 38건
    ("efo",     "inflammatory bowel disease"),   # live 확인: 69건 (CD가 IBD로 태깅된 것까지)
]

# ---------------------------------------------------------------------------
# CONFIG 2: 형질 축 (matrix COLUMNS) - 바이오마커 / 원인 / 동반질환
#   (범주, 우리이름, 종류, 질의값)  ; 뒤 숫자 주석 = 2026-07 live 검증 시 총 건수
#   메커니즘 범주는 라벨로 안 잡혀서 CONFIG 3에서 PMID로 별도 처리.
# ---------------------------------------------------------------------------
CONFIG_COLS = [
    # --- 바이오마커 (질환 상태/염증/간·영양 지표) ---
    ("biomarker", "CRP",              "efo",     "C-reactive protein measurement"),  # 196
    ("biomarker", "WBC count",        "disease", "White blood cell count"),          # 48
    ("biomarker", "neutrophil count", "efo",     "neutrophil count"),                # 118
    ("biomarker", "lymphocyte count", "efo",     "lymphocyte count"),                # 306
    ("biomarker", "monocyte count",   "efo",     "monocyte count"),                  # 114
    ("biomarker", "eosinophil count", "efo",     "eosinophil count"),                # 117
    ("biomarker", "platelet count",   "efo",     "platelet count"),                  # 127
    ("biomarker", "albumin",          "disease", "Serum albumin levels"),            # 19
    ("biomarker", "ALT",              "disease", "Alanine aminotransferase levels"), # 33
    ("biomarker", "vitamin D",        "disease", "Vitamin D levels"),                # 23
    # --- 원인 / 위험인자 ---
    ("cause", "BMI",                 "efo",     "body mass index"),          # 414
    ("cause", "waist-hip ratio",     "efo",     "waist-hip ratio"),          # 83
    ("cause", "waist circumference", "efo",     "waist circumference"),      # 152
    ("cause", "smoking initiation",  "efo",     "smoking initiation"),       # 22
    ("cause", "cigarettes per day",  "disease", "Cigarettes smoked per day"),# 8
    # --- 동반질환 (수집하되 matrix 아님 -> validation layer) ---
    ("comorbidity", "PSC",                  "disease", "primary sclerosing cholangitis"), # 5
    ("comorbidity", "ankylosing spondylitis","efo",    "ankylosing spondylitis"),         # 43
    ("comorbidity", "psoriasis",            "efo",     "psoriasis"),                       # 87
    ("comorbidity", "rheumatoid arthritis", "efo",     "rheumatoid arthritis"),            # 160
    ("comorbidity", "celiac disease",       "efo",     "celiac disease"),                  # 42
    ("comorbidity", "type 1 diabetes",      "efo",     "type 1 diabetes mellitus"),        # 95
    ("comorbidity", "multiple sclerosis",   "efo",     "multiple sclerosis"),              # 83
    ("comorbidity", "colorectal cancer",    "efo",     "colorectal cancer"),               # 198
]

# ---------------------------------------------------------------------------
# CONFIG 3: 메커니즘 범주 (b) - 논문 PMID로 자동 조회
#   pQTL/사이토카인/미생물은 형질 라벨이 아니라 '한 논문이 수백 개 형질을 한꺼번에'
#   올린 형태라, findByPublicationIdPubmedId 로 그 논문의 모든 study를 통째로 받는다.
#   (범주, 우리이름, PMID)  ; 뒤 숫자 = live 검증 건수
# ---------------------------------------------------------------------------
CONFIG_MECHANISM_PMID = [
    ("mechanism", "inflammatory proteins (Olink, Zhao 2023)", "37563310"),  # 91 단백질
    ("mechanism", "cytokines (Ahola-Olli 2017)",              "27989323"),  # 41 사이토카인
    ("mechanism", "gut microbiome (MiBioGen 2021)",           "33462485"),  # 225 taxa
]

# ---------------------------------------------------------------------------
# CONFIG 4: 메커니즘 범주 (b) - GWAS Catalog에 없어 '수동'으로 문서화하는 전용 소스
#   (PMID로 조회 시 0건이라 자동화 불가 -> 포털에서 직접 받아야 함. 기록용.)
# ---------------------------------------------------------------------------
CONFIG_MECHANISM_MANUAL = [
    {"category":"mechanism","our_name":"plasma proteome pQTL (UKB-PPP, Sun 2023)",
     "note":"2,923 단백질. GWAS Catalog 미등재 -> UKB-PPP 포털/Synapse에서 직접. European ~34,557."},
    {"category":"mechanism","our_name":"plasma proteome pQTL (deCODE, Ferkingstad 2021)",
     "note":"~4,900 단백질. deCODE 포털에서 직접. Icelandic(European)."},
    {"category":"mechanism","our_name":"NMR metabolites (Nightingale, Julkunen 2023 / Karjalainen 2024)",
     "note":"249 대사체. UKB-RAP 또는 Nature 논문 sumstats. 대규모 meta는 다인구 -> EUR subset 필요."},
]

# ===========================================================================
# 함수부
# ===========================================================================
def fetch_by_trait(kind, value):
    """trait 라벨/이름으로 study 전부 수집 (페이지네이션).
       kind='disease' -> findByDiseaseTrait(reported trait),
       kind='efo'     -> findByEfoTrait(EFO 라벨)."""
    ep  = {"disease":"findByDiseaseTrait", "efo":"findByEfoTrait"}[kind]
    key = {"disease":"diseaseTrait",       "efo":"efoTrait"}[kind]
    out, page = [], 0
    while True:
        r = requests.get(f"{BASE}/studies/search/{ep}",
                         params={key:value, "size":50, "page":page}, timeout=90, headers=H)
        r.raise_for_status(); j = r.json()
        out += j.get("_embedded", {}).get("studies", [])
        pg = j.get("page", {})
        if page >= pg.get("totalPages", 1) - 1:     # 마지막 페이지면 종료
            break
        page += 1; time.sleep(0.15)                 # API 예의상 잠깐 대기
    return out

def fetch_by_pmid(pmid):
    """논문 PMID로 그 논문의 모든 study 수집 (메커니즘 범주용)."""
    out, page = [], 0
    while True:
        r = requests.get(f"{BASE}/studies/search/findByPublicationIdPubmedId",
                         params={"pubmedId":pmid, "size":50, "page":page}, timeout=90, headers=H)
        r.raise_for_status(); j = r.json()
        out += j.get("_embedded", {}).get("studies", [])
        pg = j.get("page", {})
        if page >= pg.get("totalPages", 1) - 1:
            break
        page += 1; time.sleep(0.15)
    return out

def ancestry_text(s):
    """study의 ancestry 설명 문자열(초기+복제 표본)을 합쳐 반환."""
    return " | ".join(filter(None, [s.get("initialSampleSize",""), s.get("replicationSampleSize","")]))

# European(하위집단 포함) 로 인정하는 키워드. GWAS Catalog가 "Finnish/British/Icelandic
# ancestry" 처럼 하위집단명으로 적는 경우가 있어, 단순히 "European" 문자열만 찾으면
# Finnish 코호트(=European)를 놓친다(예: Ahola-Olli 2017). 그래서 아래를 European-positive로 본다.
EUR_POS = ["European","Finnish","British","Icelandic","Sardinian","Ashkenazi",
           "Scandinavian","Dutch","Estonian","Norwegian","Swedish","Danish","Italian",
           "Spanish","German","French","Greek","Irish","Orcadian","white"]

def is_european_only(txt):
    """European(하위집단 포함) 신호가 있고, 비유럽 키워드가 하나도 없으면 True.
       주: 텍스트 휴리스틱이라 'European American'/admixed 같은 경계 사례는 수동 검토 권장."""
    has_eur = any(k.lower() in txt.lower() for k in EUR_POS)
    has_non = any(k.lower() in txt.lower() for k in NON_EUR)
    return has_eur and not has_non

def rowdict(s, category, our_name, query):
    """study(JSON) -> CSV 한 줄(dict)로 정리. 필요한 필드만 뽑는다."""
    pi  = s.get("publicationInfo", {}) or {}
    acc = s.get("accessionId", "")
    txt = ancestry_text(s)
    return {
        "category": category, "our_name": our_name, "query": query,
        "accession": acc,
        "PMID":   pi.get("pubmedId", ""),
        "author": (pi.get("author") or {}).get("fullname", ""),
        "year":   (pi.get("publicationDate", "") or "")[:4],
        "reported_trait": (s.get("diseaseTrait", {}) or {}).get("trait", ""),
        "full_summary_stats": s.get("fullPvalueSet", ""),   # True면 genome-wide 요약통계 공개 = matrix에 바로 쓸 수 있음
        "european_only": is_european_only(txt),
        "ancestry_text": txt[:160],
        "url": f"https://www.ebi.ac.uk/gwas/studies/{acc}",
    }

def run(configs, kind_of_config, out_csv, label):
    """configs를 돌며 study 수집 -> European-only 필터 -> accession 중복 제거 -> CSV 저장."""
    seen, rows = set(), []
    print(f"\n===== {label} =====")
    for item in configs:
        if kind_of_config == "rows":            # (kind, value)
            kind, value = item; category, name = "disease", value
            studies = fetch_by_trait(kind, value)
        elif kind_of_config == "cols":          # (category, name, kind, value)
            category, name, kind, value = item
            studies = fetch_by_trait(kind, value)
        elif kind_of_config == "pmid":          # (category, name, pmid)
            category, name, pmid = item; value = f"PMID:{pmid}"
            studies = fetch_by_pmid(pmid)
        got = [rowdict(s, category, name, value) for s in studies]
        eur = [r for r in got if r["european_only"]]
        for r in eur:                           # accession 기준 중복 제거(여러 질의에 걸칠 수 있음)
            if r["accession"] not in seen:
                seen.add(r["accession"]); rows.append(r)
        warn = "  <-- 0건: 라벨/PMID 확인 필요" if len(studies) == 0 else ""
        print(f"  {name:42} total={len(studies):4}  EUR-only={len(eur):3}{warn}")
    cols = ["category","our_name","query","accession","PMID","author","year",
            "reported_trait","full_summary_stats","european_only","ancestry_text","url"]
    with open(outpath(out_csv), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    ss = sum(1 for r in rows if r["full_summary_stats"] in (True,"true","True"))
    print(f"  -> {outpath(out_csv)}: European-only 고유 study {len(rows)}개 (full summary stats {ss}개)")
    return rows

if __name__ == "__main__":
    run(CONFIG_ROWS,            "rows", "survey_disease_rows.csv", "질병 축 (ROWS) - CD")
    run(CONFIG_COLS,            "cols", "survey_trait_cols.csv",   "형질 축 (COLUMNS) - 바이오마커/원인/동반질환")
    run(CONFIG_MECHANISM_PMID,  "pmid", "survey_mechanism.csv",    "형질 축 (COLUMNS) - 메커니즘 (b), PMID 자동조회")
    # 메커니즘 수동 소스는 자동조회 불가 -> 별도 CSV로 문서화
    with open(outpath("survey_mechanism_manual.csv"),"w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=["category","our_name","note"]); w.writeheader()
        w.writerows(CONFIG_MECHANISM_MANUAL)
    print(f"\n  -> {outpath('survey_mechanism_manual.csv')}: 수동 소스 3건(UKB-PPP, deCODE, Nightingale) 기록")
    print("""
[LDSC 보완 = 형질 '선택'의 큐레이션 한계를 메우는 다음 단계]
  위 CONFIG는 사람이 고른 형질 목록이라, 우리가 생각 못 한 관련 형질은 안 잡힌다.
  이를 보완하려면 CD GWAS와 GWAS Catalog 전체 형질 간 LDSC 유전상관을 계산해,
  '데이터가 관련 있다고 지목하는' 형질을 추가로 끌어오면 된다. (별도 스크립트 예정)
""")
# ==== 메커니즘 범주만 이번에 검증 실행 ====