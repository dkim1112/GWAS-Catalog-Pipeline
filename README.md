# GWAS Catalog Pipeline — CD bNMF 서브타입 프로젝트

Crohn's Disease(CD)의 유전적 서브타입을 bNMF로 정의하기 위한 **재료 수집·검증·재현 파이프라인**.
아토피(AD)/제2형 당뇨(T2D)에서 확립된 bNMF 서브타이핑 방법론을 CD로 이식하는 파일럿.

담당: Dongeun (UM Cutaneous Lab, Dr. Matthew Patrick) · 문서 갱신: 2026-08

> 저장소의 파일별 역할과 현재 상태를 빠르게 보려면 [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md)를 먼저 참고하세요.

## 폴더 구조

```
GWAS Catalog Pipeline/
  README.md                         <- (이 파일)
  PROJECT_STRUCTURE.md              <- 파일별 역할과 현재 상태를 정리한 코드 지도
  T2D_bNMF_재현_보고서.docx         <- Udler 2018 재현 v1 보고서
  docs/generate_report.py           <- 위 docx 재생성 스크립트
  cd_survey/                        <- (1) CD 재료 수집·검증 (Step 1-2)
    src/                            코드 5개
    outputs/                        생성 CSV
  udler2018_bnmf/                   <- (2) T2D bNMF 재현 (Step 3, v2 실행 완료)
    README.md                       이 폴더 전용 개요
    run_pipeline.R                  실행 드라이버
    manifest.xlsx                   파이프라인 입력 매니페스트 (44 trait)
    inputs_manifest.csv             형질별 출처/URL/상태
    docs/                           SETUP / RUN / INPUTS / RESULTS
    scripts/                        bnmf-clustering repo 사본 + udler_substitute.R
    tools/                          입력 준비 (다운로드·rsID 맵·변환·점검)
    refs/                           Udler 정답지 (S1/S3/S4) + liftover chain
    results/                        udler2018_eur_v1/ , udler2018_eur_v2/
    reports/                        v2 보고서 + 그림
    data/                           대용량 입력 (git 미포함, 서버에서 생성)
```

## 실행 완료 요약 (Udler 2018 재현)

**현재 상태: v2 (44 형질) 실행 완료. Udler 5개 클러스터 중 4개 재현.**
상세는 `udler2018_bnmf/docs/RESULTS.md` 와 `udler2018_bnmf/reports/` 참조.

- 서버: Kimlab-server (`/BiO2/home/daniel/udler2018_bnmf`)
- 최종 데이터: 77 변이 × 31 unique trait (62 feature)
- bNMF K: ARD 가 선택 — K=4 (70/100), K=5 (27/100)
- Udler 정답지 대조 (형질축 r / 변이축 r):
  Beta-cell **0.92/0.59**, Liver/Lipid **0.96/0.93**, Obesity **0.69/0.65**,
  Proinsulin 0.24/**0.69** (변이축만), Lipodystrophy 0.32/0.38 (Obesity 축에 흡수)
- v1(35 형질)은 1개만 재현됐고, 차이는 **입력 열 9개 추가**(지질 4 + CHARGE 지방산 5)뿐.
  `T2D_bNMF_재현_보고서.docx` 는 그 v1 시점 보고서.

> **아직 검증 안 된 모듈**: `choose_variants_2025.R` (변이 선택). 이번 재현은 논문의
> 변이 94개를 직접 넣어 우회했음. **CD 에는 정답지가 없으므로 이 모듈을 반드시 써야 하고,
> 별도 검증이 필요함.**

## 로컬 ↔ 서버 동기화

**원칙**: 코드/문서는 로컬에서 편집 → 서버로 push. 실행 결과는 서버에서 로컬로 pull.  
대용량 입력 `udler2018_bnmf/data/` (~8GB) 와 R 체크포인트(`*.RData`) 는 서버에만
(재생성 가능하니 git 미포함).

### 명령 두 개
```bash
bash sync_up.sh      # 로컬 → 서버: 코드/문서/매니페스트 push (데이터 exclude)
bash sync_down.sh    # 서버 → 로컬: bNMF 결과 + 로그 pull
```

`sync_down.sh` 실행 후 `git add udler2018_bnmf/results/ udler2018_bnmf/logs/` 로 결과 기록.
`sync_up.sh` 는 `--delete` 를 쓰므로 로컬에서 지운 파일이 서버에서도 지워집니다
(`data/` 와 `*.RData` 는 exclude 라 안전).

### 무엇을 어느 쪽에 두는지

| 카테고리 | 로컬 (git) | 서버 |
|---|---|---|
| 코드 (`.py` `.R` `.sh`) | ✓ | ✓ |
| 매니페스트, refs, chain | ✓ | ✓ |
| 문서 (README, docx) | ✓ (원본) | 일부 |
| bNMF 결과 (`results/`) | ✓ (백업) | ✓ (원본) |
| 로그 (`logs/`) | ✓ | ✓ |
| 원본 sumstats (`data/sumstats/`, 3.5GB) | ✗ | ✓ |
| 변환본 (`data/sumstats_converted/`, 1.3GB) | ✗ | ✓ |
| rsID 맵 + sqlite (`data/`, 3.2GB) | ✗ | ✓ |
| R 체크포인트 (`.RData`) | ✗ | ✓ |

두 폴더는 **다른 목적**을 갖는 자매 프로젝트:
- `cd_survey/` — **본 프로젝트(CD)** 의 재료 수집·검증. GWAS Catalog REST API로 자동 조사.
- `udler2018_bnmf/` — **선행 T2D 연구(Udler 2018) 재현**. 실제 bNMF matrix를 만들어
  파이프라인 자체가 재현 가능한지 확인. 나중에 CD로 확장할 때 그대로 재사용될 부품.

`cd_survey/` 는 아직 "재료가 잘 모였는지"까지의 단계이고,
`udler2018_bnmf/` 는 그 다음 단계인 **실제 bNMF 실행**을 이미 T2D에서 돌릴 준비까지 마쳐놨음.

---

## (1) cd_survey/ — CD 재료 수집·검증 (Step 1-2)

bNMF는 질병의 genome-wide 유의 변이(SNP, matrix의 **행**)를 질환 관련 정량 형질
(trait, matrix의 **열**)에 대한 GWAS 효과크기로 표현한 행렬을 soft-clustering해 기전
(subtype) 클러스터를 찾는 방법. 따라서 matrix를 만들기 전에 **행 재료(질병 GWAS)** 와
**열 재료(형질 GWAS)** 를 모아야 하고, 수집이 편향되면 클러스터도 편향된다.
이 부분은 (A) 그 수집을 자동화하고, (B) 수집이 누락 없이 되는지를 T2D로 검증한다.

두 축:
- **(A) 자동 조사 엔진** — `gwas_catalog_survey.py`. GWAS Catalog REST API로 CD 질병
  GWAS와 4범주(바이오마커/원인/메커니즘/동반질환) 형질 GWAS를 전수 수집 → European-only
  필터 → CSV.
- **(B) T2D 검증** — 우리 flow를 T2D에 그대로 적용해, bNMF 선행연구(~5편)가 실제로 쓴
  질병 GWAS·형질을 우리가 다시 잡아내는지 확인. 못 잡으면 방법에 구멍이 있다는 뜻.

### 파일 구성

| 파일                              | 역할                                                                                                          | 종류 |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------- | ---- |
| `src/gwas_catalog_survey.py`      | **엔진**. CD 질병/형질 GWAS 자동 수집 + European 판정. 다른 검증 스크립트가 `import`해 재사용.                | 코드 |
| `src/validate_t2d_disease_axis.py`| **질병 축(행) 검증**. T2D 조회 → European 결과에서 대표 landmark 질병 GWAS(Mahajan 등) 회수 확인.             | 코드 |
| `src/validate_t2d_trait_axis.py`  | **형질 축(열) 검증 (B2)**. 선행 5편이 쓴 **전체** trait 목록 대비 회수율. 3분류를 코드가 라이브로 자동 판정.  | 코드 |
| `src/extract_paper_traits.py`     | 형질 축 검증용 **trait 목록을 논문 supplementary(표)에서 코드로 추출**.                                       | 코드 |
| `src/llm_map_traits.py`           | 표가 아닌 논문의 목록 추출 + 원 라벨→canonical+후보라벨 매핑을 **LLM API로 자동화**, 라이브 조회로 검증.      | 코드 |
| `outputs/survey_disease_rows.csv` | 엔진 출력 — CD 질병 축 European GWAS(행 재료 후보).                                                           | 출력 |
| `outputs/survey_trait_cols.csv`   | 엔진 출력 — 형질 축(바이오마커/원인/동반질환) European GWAS(열 재료 후보).                                    | 출력 |
| `outputs/survey_mechanism.csv`    | 엔진 출력 — 메커니즘 범주(pQTL/사이토카인/미생물 등 PMID 조회).                                               | 출력 |
| `outputs/survey_mechanism_manual.csv` | 엔진 출력 — GWAS Catalog 미등재라 수동 소스로 문서화(UKB-PPP/deCODE/Nightingale).                         | 출력 |
| `outputs/t2d_disease_validation.csv`  | 질병 축 검증 출력 — T2D 질병 축 European GWAS.                                                            | 출력 |
| `outputs/t2d_trait_validation.csv`    | 형질 축 검증(B2) 출력 — 논문×trait별 3분류 결과.                                                          | 출력 |

의존: 검증/추출 스크립트는 엔진(`gwas_catalog_survey.py`)의 European 판정 함수를
`import` 한다. 따라서 **엔진 파일이 같은 폴더에 있어야** 함(엔진을 먼저 '실행'할 필요는
없고 파일만 있으면 됨).

### 실행

```bash
pip install requests pandas openpyxl        # llm_map_traits.py 쓰면 anthropic도 (선택)

# 1) 엔진: CD 재료 전수 수집
python cd_survey/src/gwas_catalog_survey.py
#   -> cd_survey/outputs/survey_*.csv

# 2) 질병 축 검증: T2D landmark 질병 GWAS 회수
python cd_survey/src/validate_t2d_disease_axis.py

# 3) 형질 축 검증(B2): 선행 5편 전체 trait 회수율(3분류 자동)
python cd_survey/src/validate_t2d_trait_axis.py

# (선택) 논문 trait 목록을 supplementary(표)에서 추출
python cd_survey/src/extract_paper_traits.py

# (선택) LLM API로 추출/매핑 자동화 (새 논문·trait 추가 시)
export ANTHROPIC_API_KEY=... ; export LLM_MODEL=claude-...
python cd_survey/src/llm_map_traits.py --from-csv cd_survey/outputs/paper_traits_extracted.csv --paper "Smith 2024"
```

스크립트는 실행 위치(cwd)와 무관하게 자기 위치 기준으로 `cd_survey/outputs/` 에 씀
(환경변수 `PIPELINE_OUT_DIR` 로 변경 가능).

### 코드가 하는 것 vs 사람이 대는 것 (큐레이션)

핵심 원칙: **판정·수집·조회는 결정적 코드가**, **창의적/퍼지 작업은 LLM API가 제안하고
코드가 검증**. 사람은 최종적으로 플래그된 소수만 확인.

- 결정적 코드: GWAS Catalog 전수 조회, European-only 판정, trait 회수 여부 판정,
  라벨 불일치/데이터 부재 3분류, supplementary(표) 파싱.
- LLM API (`llm_map_traits.py`): (a) 표가 아닌 논문에서 trait 목록 추출, (b) 원 라벨→
  canonical 표현형 정규화 + GWAS Catalog 후보 라벨 제안. 제안은 **즉시 라이브 조회로 검증**.
- 사람이 설정으로 두는 것 (`CONFIG_*`/`SUPPLEMENTS`): 어떤 질환·형질 범주를 조사할지,
  어느 supplementary sheet/컬럼을 볼지. (연구 설계 선택이라 명시적으로 두는 게 안전.)

### 검증 로직 요약 (B2 3분류)

각 trait에 후보 라벨 목록(표준 라벨이 첫 번째)을 주면 GWAS Catalog에 순서대로 조회:
1. **recovered** — 표준(첫) 라벨로 바로 European GWAS>0.
2. **label_mismatch** — 표준은 0이지만 대체 라벨로 회수(라벨만 고치면 됨).
3. **no_public_gwas** — 어떤 후보로도 0(우리 flow 한계가 아니라 데이터 자체가 없음).
   `(broad)` = 정확한 라벨은 없고 상위/근사 라벨로만 잡힘(회수로 세되 약함).

(1)/(2)/(3) 구분이 "공정한 회수율 판정"의 핵심. (2)는 우리 책임(라벨 교정),
(3)은 데이터 부재라 우리 flow의 흠이 아님.

등록 논문(5편): Udler 2018(PLoS Med) · Suzuki 2024(Nature) · Kim 2023(Diabetologia) ·
Smith 2024(Nat Med) · Pascat 2026(Nat Commun).

### 알려진 한계

- European 필터는 `initialSampleSize` 텍스트 휴리스틱 — "European American"/admixed
  경계 사례는 수동 검토 권장, "not reported"는 보수적으로 제외.
- 회수 완전성은 라벨 매핑 품질에 의존(label_mismatch가 그 사례).
- 현재 형질 수는 "후보 풀" — 최종 matrix는 dedup 후 훨씬 적음.
- 라이브 조회는 '잘못된 라벨'은 잡지만 'trait을 통째로 빠뜨린 것'은 못 잡음
  (목록에 없으면 조회 자체를 안 하므로). **CD GWAS ↔ 전체 형질 LDSC 유전상관 스캔**이
  그 발굴 사각을 메우는 다음 조각.

---

## (2) udler2018_bnmf/ — T2D bNMF 재현 (Step 3)

기준 논문: Udler MS et al. PLoS Med 2018. doi:10.1371/journal.pmed.1002654
파이프라인: https://github.com/gwas-partitioning/bnmf-clustering

**현재 상태: v2 실행 완료.** `tools/validate_inputs.py` 가 45행 전부 통과.
형질 열 44개(원 논문 47열에서 3개 제외) + 질병 GWAS 1개 (DIAGRAMv3 Morris 2012).
자세한 내용은 `udler2018_bnmf/README.md` 와 그 폴더의 `docs/` 참조.

### 왜 이 폴더가 여기 있나

CD로 bNMF를 돌리기 전에 **파이프라인 자체가 재현 가능한지** 먼저 T2D로 확인해야 함.
Udler 2018은 정답지(변이×클러스터, 형질×클러스터 가중치)가 공개돼 있어 재현 여부를
숫자로 판정할 수 있음. 여기서 검증된 변환기/맵 생성기/검증기는 나중에 CD 재료로
matrix를 만들 때 그대로 재사용.

### 실행 (요약)

수동 4개(`bw` `bl` `hba1c` `t2d_diagram_v3`)는 브라우저 필요라 먼저 넣어둠.

```bash
cd udler2018_bnmf
bash tools/download_inputs.sh              # 1) 자동 41개 (약 3GB)
python3 tools/build_rsid_map.py            # 2) rsID 맵 (약 4분, 1.15GB)
python3 tools/convert_sumstats.py --index  # 3) sqlite 색인 (약 4분)
python3 tools/convert_sumstats.py          # 4) 포맷 변환 (약 40분)
python3 tools/validate_inputs.py --paths $PWD
python3 tools/validate_inputs.py           # "준비 완료" 확인
Rscript run_pipeline.R                     # 5) bNMF 실행 (약 4분)
```

**대용량 산출물(`data/` 전체)은 git에 커밋되지 않음** — `udler2018_bnmf/.gitignore`
에서 제외. 위 1~4번으로 재생성 가능.

절차 상세는 `udler2018_bnmf/docs/SETUP.md` (서버 준비) 와 `docs/RUN.md` (실행) 참조.

### 우리 입력이 원 논문과 다른 점 (재현 결과 해석 시 필수)

원 논문 47열 중 **3열**이 빠져 있음 (v1 때는 12열이 빠졌음):
- `adip` (아디포넥틴) — 배포처 404, Catalog 에 요약통계 없음
- `leptinbmi` — Catalog 에서 leptin 과 accession 이 겹쳐 분리 불가
- `fi_bmi` — Manning 2012 BMI interaction, Catalog 에 요약통계 없음

또 **지질 4개(`hdl` `ldl` `tc` `tg`) 는 출처가 다름** — Udler 가 쓴 ENGAGE 2015
배포처가 죽어 GLGC Willer 2013 jointGwasMc 로 대체. **결과 대조 시 반드시 명시할 것.**

v1(12열 결측) 에서 Liver/Lipid 가 r=0.38 로 안 나왔던 것은 그 클러스터 가중치의
56%가 없었기 때문이었고, v2 에서 결측이 8%로 줄자 r=0.96 으로 회복됨.
**재현 실패의 원인이 파이프라인이 아니라 입력이었음을 보여주는 대조.**
상세는 `udler2018_bnmf/docs/INPUTS.md` / `docs/RESULTS.md`.

---

## 다음 단계

1. `cd_survey/`: 형질 축 **dedup**(같은 형질 중복 GWAS를 대표 1개로).
2. `cd_survey/`: **LDSC 유전상관 스캔**(CD GWAS ↔ 형질) — 큐레이션 발굴 사각 보완.
3. `udler2018_bnmf/`: **`choose_variants_2025.R` (변이 선택) 검증** — 이번 재현에서
   유일하게 우회한 모듈. CD 에는 정답지 변이 리스트가 없어 반드시 필요함.
   예: 더 큰 T2D GWAS 로 클럼핑을 돌려 Udler 94개와 얼마나 겹치는지 확인.
4. CD로 확장: `udler2018_bnmf/` 변환기·검증기 재사용 + `cd_survey/` 매니페스트 → CD matrix.
