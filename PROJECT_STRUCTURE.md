# 프로젝트 구조와 파일 역할

> 상태 기준일: 2026-09-03
> 이 문서는 저장소의 구성요소가 무엇을 담당하는지 설명하는 코드 지도다. 연구의 시간순 진행과
> 최신 분석 상태는 실행 결과와 각 하위 폴더의 README를 함께 확인해야 한다.

## 프로젝트를 한 문장으로 설명하면

Crohn's disease(CD)의 유의 SNP들이 여러 관련 형질에 미치는 효과 패턴으로 SNP x trait
행렬을 만들고, bNMF로 잠재 기전 클러스터를 찾은 뒤 cluster-specific PRS와 임상 자료로
그 의미를 검증하려는 연구다.

현재 저장소에는 목적이 다른 두 작업이 함께 있다.

- `cd_survey/`: 본 연구인 CD의 disease/trait GWAS **후보를 조사하는 수집 계층**
- `udler2018_bnmf/`: CD 적용 전에 T2D Udler 2018로 **데이터 처리와 bNMF를 시험한 검증 계층**

T2D는 CD와 별개의 최종 연구 대상이 아니라, CD 파이프라인을 de-risk하기 위한 benchmark다.

## 전체 데이터 흐름

```text
질환 및 trait 체계 결정
  -> disease/trait GWAS 후보 수집
  -> 대표 study 선정 및 실제 summary statistics 확보
  -> disease SNP 선택, LD clumping
  -> build/rsID/allele/effect-size 통일
  -> SNP x trait z-score matrix 생성
  -> 결측/표본수/상관 trait QC와 imputation
  -> bNMF (SNP weights W, trait weights H)
  -> cluster 안정성 및 생물학적 해석
  -> cluster-specific PRS와 외부/임상 검증
```

`cd_survey/outputs/`의 study 수는 이 흐름의 후보 수집 결과다. 실제 다운로드가 끝난
summary-stat 파일 수나 최종 matrix의 열 수를 뜻하지 않는다.

## 루트

| 파일 | 목적 및 현재 상태 |
| --- | --- |
| `README.md` | 전체 연구 설명과 실행 방법. 여러 시점의 기록이 함께 있어, 일부 진행 상태(예: T2D 실행 전/후, 35/40 traits)가 섞여 있다. |
| `PROJECT_STRUCTURE.md` | 이 문서. 루트와 하위 폴더의 역할 및 현재 상태를 빠르게 파악하기 위한 코드 지도. |
| `T2D_bNMF_재현_보고서.docx` | T2D v1 재현 과정에서 발견한 11개 문제와 해결, 최종 결과를 기록한 핵심 보고서. |
| `docs/generate_report.py` | 위 DOCX를 재생성하는 스크립트. 출력 경로와 보고 날짜가 하드코딩되어 있다. |
| `sync_up.sh` | 로컬의 코드/문서/매니페스트를 Kimlab 서버로 보낸다. 대용량 데이터는 제외한다. |
| `sync_down.sh` | 서버의 로그와 bNMF 결과를 로컬로 가져온다. |
| `sync_check.sh` | 로컬과 서버 간 동기화 상태를 확인한다. |
| `check_manifest.py` | 현재 `manifest.xlsx`에 CHARGE 5개 trait이 포함됐는지 빠르게 확인한다. |

## `cd_survey/`: CD 후보 수집 및 회수 검증

### 목적

GWAS Catalog에서 CD disease GWAS와 관련 trait GWAS의 study metadata를 폭넓게 수집한다.
이 계층의 출력은 최종 분석 대상이 아니라 후속 QC와 대표 study 선정을 위한 후보 풀이다.

현재 출력 스냅샷:

- CD/IBD disease study 후보: 67개
- 일반 trait study 후보: 1,286개
- PMID 기반 mechanism study 후보: 132개
- Catalog 외 수동 mechanism source: 3개

일반 trait 후보에는 biomarker, cause/risk factor, comorbidity가 포함된다. 현재 연구 설계상
comorbidity는 수집하되 matrix 입력보다 외부 validation layer로 사용하는 방향이다.

### 코드

| 파일 | 목적 |
| --- | --- |
| `cd_survey/src/gwas_catalog_survey.py` | 중심 수집 엔진. CD reported trait 및 IBD EFO, 설정된 biomarker/cause/comorbidity label, mechanism PMID를 GWAS Catalog REST API로 조회한다. 페이지네이션, accession 중복 제거, European 텍스트 판정, metadata CSV 출력을 담당한다. |
| `cd_survey/src/validate_t2d_disease_axis.py` | T2D landmark disease GWAS가 수집 결과에 포함되는지 검사한다. disease-axis 후보 회수 능력의 benchmark다. |
| `cd_survey/src/validate_t2d_trait_axis.py` | 5개 T2D 연구의 distinct trait 226개가 Catalog 검색으로 회수되는지 검사한다. `recovered`, `label_mismatch`, `no_public_gwas`로 분류한다. |
| `cd_survey/src/extract_paper_traits.py` | 논문 supplementary XLSX의 표에서 원래 trait label을 추출한다. |
| `cd_survey/src/llm_map_traits.py` | LLM이 비정형 논문에서 trait을 추출하고 canonical/query label 후보를 제안한다. 제안된 label은 결정적 코드가 Catalog에 조회해 검증한다. |

### 출력

| 파일 | 의미 |
| --- | --- |
| `cd_survey/outputs/survey_disease_rows.csv` | CD/IBD disease study 후보 metadata. 이름의 `rows`는 향후 disease SNP row의 재료라는 뜻이며, SNP가 이미 추출됐다는 뜻은 아니다. |
| `cd_survey/outputs/survey_trait_cols.csv` | biomarker/cause/comorbidity study 후보 metadata. 아직 대표 GWAS로 deduplicate된 최종 matrix 열이 아니다. |
| `cd_survey/outputs/survey_mechanism.csv` | pQTL, cytokine, microbiome 등 PMID 단위로 수집한 mechanism study 후보. |
| `cd_survey/outputs/survey_mechanism_manual.csv` | GWAS Catalog에 없어 전용 포털에서 받아야 하는 UKB-PPP, deCODE, Nightingale source 기록. |
| `cd_survey/outputs/t2d_disease_validation.csv` | T2D disease-axis 회수 검증 결과. 현재 파일에는 181개 study가 있다. |
| `cd_survey/outputs/t2d_trait_validation.csv` | 5개 T2D 논문의 226개 trait 회수 검증 결과. |

### 자동화 및 LLM의 경계

- 자동화된 것: API 조회, 페이지네이션, metadata 파싱, accession 중복 제거, label별 회수
  판정, CSV 생성
- LLM의 역할: 논문 trait 추출과 Catalog query label 후보 제안
- 사람의 역할: 조사할 질환/trait 체계 결정, 후보의 생물학적 적합성 검토, 대표 study 선택,
  ancestry/sample overlap 및 phenotype 경계 사례 판단
- LLM이 하지 않는 것: 최종 study 포함 결정, SNP 선택, bNMF, PRS, 결과 해석

T2D 검증에서 알려진 landmark GWAS와 226개 trait을 회수했으므로 **이미 알려진 대상을 다시
찾는 능력**은 확인됐다. 그러나 관련 trait의 unbiased discovery, ancestry 판정의 정확성,
실제 summary-stat 파일 가용성, 최종 study 선택까지 검증된 것은 아니다.

### 알려진 한계 및 실패 모드

- European-only 판정은 `initialSampleSize`/`replicationSampleSize` 문자열 keyword
  heuristic이다. 혼합 또는 unknown ancestry와 예상하지 못한 민족 명칭은 오분류될 수 있다.
- minimum sample-size cutoff가 구현되어 있지 않다.
- CD와 넓은 IBD, pleiotropy/MTAG/성별/ICD phenotype study가 후보에 함께 들어갈 수 있다.
- 설정 목록에 없는 trait은 검색하지 않으므로 관련 trait 전체를 자동 발견하지 못한다.
- summary-stat 공개 flag가 실제 다운로드 성공이나 BETA/SE/allele 가용성을 보장하지 않는다.
- 이 폴더는 disease SNP 추출, study 간 SNP union, LD clumping을 수행하지 않는다.

## `udler2018_bnmf/`: T2D 데이터 처리 및 bNMF benchmark

### 목적

Udler 2018의 공개된 SNP/trait cluster weights를 기준으로, 실제 summary statistics를 공통
형식으로 변환하고 SNP x trait matrix를 만든 뒤 bNMF가 알려진 신호를 회수하는지 시험한다.

완료된 v1은 Udler의 curated 94 SNP를 직접 넣었기 때문에, disease GWAS로부터 SNP를 새로
발견하는 end-to-end 검증이 아니라 downstream matrix+bNMF feasibility 검증이다.

### 입력과 데이터 준비

| 파일 | 목적 |
| --- | --- |
| `udler2018_bnmf/manifest.xlsx` | bNMF가 읽을 disease/trait 파일 경로와 sample size. 현재 작업 사본은 기존 35개에 CHARGE 5개를 추가한 40-trait v2 상태다. |
| `udler2018_bnmf/inputs_manifest.csv` | trait별 원 데이터 출처, URL, 로컬 경로와 접근 상태를 기록한다. |
| `udler2018_bnmf/download_inputs.sh` | 승인 없이 자동으로 받을 수 있는 summary statistics를 다운로드한다. 소실된 URL이나 승인 자료는 수동 처리가 필요하다. |
| `udler2018_bnmf/build_rsid_map.py` | dbSNP b151 GRCh37 common variant 자료로 rsID-hg19 위치/allele map을 만든다. multi-allelic variant는 allele별로 보존해야 한다. |
| `udler2018_bnmf/convert_sumstats.py` | 서로 다른 원본 형식을 공통 `VAR_ID/BETA/SE/P/N` 형식으로 변환한다. |
| `udler2018_bnmf/validate_inputs.py` | 파일 존재 여부, 헤더, sample size 등 실행 전 조건을 검사한다. runtime 전체 성공을 보장하는 검사는 아니다. |
| `udler2018_bnmf/hg19ToHg38.over.chain` | 후속 gene annotation 등을 위한 hg19-to-hg38 좌표 변환 파일. |

### R 분석 단계

| 파일 | 목적 |
| --- | --- |
| `udler2018_bnmf/scripts/choose_variants_2025.R` | disease GWAS에서 유의 변이를 선택하고 HLA 제외, clumping, LD pruning과 proxy 탐색을 수행한다. |
| `udler2018_bnmf/scripts/prep_bNMF_2025.R` | trait summary statistics에서 각 disease-risk allele 방향의 `z=BETA/SE`를 만들고, allele을 정렬하며, 결측/상관 trait을 처리해 z/N matrix를 생성한다. |
| `udler2018_bnmf/scripts/run_bNMF_2025.R` | Bayesian NMF를 반복 실행하고 replicate별 K와 W/H 결과를 요약한다. |
| `udler2018_bnmf/scripts/post_bNMF_2025.R` | cluster weight, gene annotation, liftover 및 후속 PRS용 결과를 생성한다. |
| `udler2018_bnmf/scripts/udler_substitute.R` | Udler의 curated 94 SNP를 직접 주입해 `choose_variants`의 자체 SNP 발견 단계를 대체한다. |

### 기준 자료와 결과

| 경로 | 목적 및 상태 |
| --- | --- |
| `udler2018_bnmf/refs/` | Udler의 94 SNP와 variant/trait cluster weights 등 benchmark 정답지. |
| `udler2018_bnmf/udler2018_eur_v1_results/` | 실행 완료된 v1의 W/H matrix, K 분포, alignment 및 heatmap. |

T2D v1 결과:

- 입력 trait 35개 -> QC 후 unique trait 26개
- Udler curated SNP 94개 -> summary-stat fetch 후 77개 -> 최종 71개
- bNMF의 K=3 선택: 100회 중 96회
- K3와 Udler Beta-cell: Pearson `r=0.92`
- K2와 Udler Liver/Lipid: Pearson `r=0.38`

이는 Beta-cell 신호의 강한 부분 재현이지만, Udler의 원래 5개 cluster 전체 재현은 아니다.
현재 manifest에는 CHARGE 5개를 추가한 40 traits가 들어 있으나 로컬에
`udler2018_eur_v2_results/`가 없어 v2 완료로 판단할 수 없다.

### 알려진 한계 및 실패 모드

- v1은 `udler_substitute.R`로 SNP를 주입하므로 자체 disease-SNP discovery를 검증하지 않는다.
- DIAGRAM v3 전체에 genome-wide threshold와 clumping을 적용하면 Udler 94개와 다른 SNP
  집합이 나온다. Udler는 문헌 후보를 먼저 만들고 그 후보에 별도의 필터를 적용했다.
- 오래된 배포 URL, 승인 자료, 서로 다른 build/컬럼/allele 표현 때문에 완전 자동 다운로드와
  변환이 어렵다.
- BETA/SE가 없거나 값이 비어 있는 trait이 조용히 제외되지 않도록 로그와 결과 행 수를
  반드시 확인해야 한다.
- multi-allelic, palindromic, strand/build 불일치 variant는 별도 QC가 필요하다.
- `main_script_example.R`은 section별 수동 실행과 checkpoint를 전제로 하며, 파일 끝까지
  그대로 실행하는 단일 명령형 workflow가 아니다.

## 현재 연구 위치

완료 또는 부분 검증됨:

- CD disease/trait study 후보 조사 자동화
- 알려진 T2D disease GWAS와 226개 trait의 Catalog 회수 benchmark
- T2D subset의 다운로드, rsID mapping, 포맷 변환과 allele 정렬
- Udler curated SNP를 사용한 T2D v1 matrix 및 bNMF 실행
- Beta-cell cluster의 부분 재현

아직 완료되지 않음:

- CD-specific GWAS와 넓은 IBD GWAS 중 최종 disease axis 결정
- CD 후보 study의 phenotype/ancestry/sample overlap 검토와 대표 study 선정
- 최소 표본수와 summary-stat 가용성 등 최종 inclusion/exclusion protocol
- CD disease SNP 추출, union, LD clumping과 최종 row manifest
- CD trait별 대표 summary-stat 파일 선정 및 다운로드/변환
- CD SNP x trait matrix와 bNMF
- CD cluster 안정성, gene/pathway 해석
- cluster-specific PRS와 독립/임상 검증

## 현재 파일을 읽을 때의 기준

1. `cd_survey`의 CSV 행 수를 최종 SNP 또는 최종 trait 수로 해석하지 않는다.
2. T2D v1 결과와 40-trait v2 준비 상태를 구분한다.
3. T2D의 회수 검증, 데이터 변환 검증, bNMF 검증은 서로 다른 증거다.
4. Beta-cell 부분 재현을 전체 end-to-end 파이프라인 검증으로 확대 해석하지 않는다.
5. 실제 실행 전에는 서버의 데이터·패키지·환경변수와 checkpoint 상태를 별도로 확인한다.
