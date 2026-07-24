# GWAS Catalog Pipeline — CD bNMF 서브타입 프로젝트

Crohn's Disease(CD)의 유전적 서브타입을 bNMF로 정의하기 위한 **재료 수집·검증 파이프라인**입니다.
아토피(AD)/제2형 당뇨(T2D)에서 확립된 bNMF 서브타이핑 방법론을 CD로 이식하는 파일럿의 일부로,
"bNMF matrix에 넣을 재료(질병 SNP × 형질 GWAS)를 GWAS Catalog에서 자동 전수 조사"하고,
그 자동 조사가 **중요한 것을 놓치지 않는지 T2D로 검증**하는 두 축으로 구성됩니다.

담당: Dongeun (UM Cutaneous Lab, Dr. Matthew Patrick) · 문서 갱신: 2026-07

### 폴더 구조

```
GWAS Catalog Pipeline/
  README.md
  src/        # 코드 (아래 5개 .py)
  outputs/    # 생성되는 CSV(자동 생성; 코드가 여기로 씀)
  .venv/
```

코드는 `src/`, 생성물은 `outputs/`로 분리됩니다. 스크립트는 실행 위치(cwd)와 무관하게
자기 위치 기준으로 `outputs/`에 씁니다(환경변수 `PIPELINE_OUT_DIR`로 변경 가능).

---

## 1. 이 파이프라인이 하는 일 (한눈에)

bNMF는 질병의 genome-wide 유의 변이(SNP, matrix의 **행**)를 질환 관련 정량 형질(trait, matrix의
**열**)에 대한 GWAS 효과크기로 표현한 행렬을 soft-clustering해 기전(subtype) 클러스터를 찾는 방법입니다.
따라서 matrix를 만들기 전에 **행 재료(질병 GWAS)** 와 **열 재료(형질 GWAS)** 를 모아야 하고,
그 수집이 편향되면 클러스터도 편향됩니다. 이 저장소는 (A) 그 수집을 자동화하고, (B) 수집이
누락 없이 되는지를 선행 T2D 연구를 기준으로 검증합니다. **아직 matrix 생성(Step 3) 전 단계**입니다.

두 축:

- **(A) 자동 조사 엔진** — `gwas_catalog_survey.py`. GWAS Catalog REST API로 CD 질병 GWAS와
  4범주(바이오마커/원인/메커니즘/동반질환) 형질 GWAS를 전수 수집 → European-only 필터 → CSV.
- **(B) T2D 검증** — 우리 flow를 T2D에 그대로 적용해, bNMF 선행연구(~5편)가 실제로 쓴 질병
  GWAS·형질을 우리가 다시 잡아내는지 확인. 못 잡으면 방법에 구멍이 있다는 뜻.

---

## 2. 파일 구성

| 파일                              | 역할                                                                                                                                                          | 종류 |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- |
| `gwas_catalog_survey.py`          | **엔진**. CD 질병/형질 GWAS 자동 수집 + European 판정. 다른 검증 스크립트가 `import`해 재사용.                                                                | 코드 |
| `validate_t2d_disease_axis.py`    | **질병 축(행) 검증**. T2D 조회 → European 결과에서 대표 landmark 질병 GWAS(Mahajan 등) 회수 확인.                                                             | 코드 |
| `validate_t2d_trait_axis.py`      | **형질 축(열) 검증 (B2)**. 선행 5편이 쓴 **전체** trait 목록 대비 회수율. 3분류(recovered / label_mismatch / no_public_gwas)를 **코드가 라이브로 자동 판정**. | 코드 |
| `extract_paper_traits.py`         | 형질 축 검증용 **trait 목록을 논문 supplementary(표)에서 코드로 추출**.                                                                                       | 코드 |
| `llm_map_traits.py`               | 표가 아닌 논문의 목록 추출 + 원 라벨→canonical+후보라벨 매핑을 **LLM API로 자동화**하고, 제안을 GWAS Catalog 라이브 조회로 검증.                              | 코드 |
| `survey_disease_rows.csv`         | 엔진 출력 — CD 질병 축 European GWAS(행 재료 후보).                                                                                                           | 출력 |
| `survey_trait_cols.csv`           | 엔진 출력 — 형질 축(바이오마커/원인/동반질환) European GWAS(열 재료 후보).                                                                                    | 출력 |
| `survey_mechanism.csv`            | 엔진 출력 — 메커니즘 범주(pQTL/사이토카인/미생물 등 PMID 조회).                                                                                               | 출력 |
| `survey_mechanism_manual.csv`     | 엔진 출력 — GWAS Catalog 미등재라 수동 소스로 문서화한 메커니즘(UKB-PPP/deCODE/Nightingale).                                                                  | 출력 |
| `t2d_disease_validation.csv`      | 질병 축 검증 출력 — T2D 질병 축 European GWAS.                                                                                                                | 출력 |
| `t2d_trait_validation.csv`        | 형질 축 검증(B2) 출력 — 논문×trait별 3분류 결과.                                                                                                              | 출력 |
| `paper_traits_extracted.csv`      | 추출기 출력 — 논문별 raw trait 목록(canonical 매핑 전).                                                                                                       | 출력 |
| `Chron_s_Disease_SNP_TRAITS.xlsx` | 수동 정리본(Overview + 질병 + trait). _파일명 오타(Chron→Crohn) 있음, 정리 권장._                                                                             | 참고 |

의존: 세 검증/추출 스크립트는 엔진(`gwas_catalog_survey.py`)의 European 판정 함수를 `import`합니다.
따라서 **엔진 파일이 같은 폴더에 있어야** 합니다(엔진을 먼저 '실행'할 필요는 없고 파일만 있으면 됨).

---

## 3. '코드가 하는 것' vs '사람이 대는 것'(큐레이션)

이 파이프라인의 핵심 원칙: **판정·수집·조회는 결정적 코드가**, **창의적/퍼지 작업은 LLM API가
제안하고 코드가 검증**. 사람은 최종적으로 플래그된 소수만 확인.

- 결정적 코드가 하는 것: GWAS Catalog 전수 조회, European-only 판정, trait 회수 여부 판정,
  라벨 불일치/데이터 부재 3분류, supplementary(표) 파싱. → 스크립트를 돌리면 재현됩니다.
- LLM API가 하는 것(`llm_map_traits.py`): (a) 표가 아닌 논문(Methods/그림)에서 trait 목록 추출,
  (b) 원 라벨→canonical 표현형 정규화 + GWAS Catalog 후보 라벨 제안.
  → 제안은 **즉시 라이브 조회로 검증**되므로, 잘못된 라벨은 자동으로 `no_public_gwas`로 노출됩니다.
- 여전히 설정으로 두는 것(`CONFIG_*`/`SUPPLEMENTS`): 어떤 질환·형질 범주를 조사할지, 어느
  supplementary sheet/컬럼을 볼지. (이건 연구 설계 선택이라 명시적으로 두는 게 안전.)

LLM 자동화의 안전 한계(정직하게): 라이브 조회는 '잘못된 라벨'은 잡지만 'trait을 통째로 빠뜨린 것'은
못 잡습니다(목록에 없으면 조회 자체를 안 하므로). 그래서 추출 개수를 논문이 밝힌 N과 대조하고,
`no_public_gwas`/`broad`로 뜬 것만 사람이 눈으로 확인합니다. 또한 "아무도 안 쓴 관련 형질"은
어느 논문 목록에도 없으므로 B2로는 못 메우며, **CD GWAS ↔ 전체 형질 LDSC 유전상관 스캔**이
그 발굴 사각을 메우는 다음 조각입니다.

---

## 4. 실행 순서

모든 스크립트는 `src/`에 있고, 어디서 실행하든 `outputs/`에 씁니다.

```
# 0) 준비 (한 번)
pip install requests pandas openpyxl        # llm_map_traits.py 쓰면 anthropic 도(선택)

# 1) 엔진: CD 재료 전수 수집
python src/gwas_catalog_survey.py
#   -> outputs/survey_disease_rows.csv / survey_trait_cols.csv / survey_mechanism.csv / survey_mechanism_manual.csv

# 2) 질병 축 검증: T2D landmark 질병 GWAS 회수
python src/validate_t2d_disease_axis.py   #  -> outputs/t2d_disease_validation.csv + 콘솔 회수표

# 3) 형질 축 검증(B2): 선행 5편 전체 trait 회수율(3분류 자동)
python src/validate_t2d_trait_axis.py     #  -> outputs/t2d_trait_validation.csv

# (선택) 논문 trait 목록을 supplementary(표)에서 추출
python src/extract_paper_traits.py               # -> outputs/paper_traits_extracted.csv
python src/extract_paper_traits.py --preview "Smith 2024"   # sheet/컬럼명 확인용

# (선택) LLM API로 추출/매핑 자동화 (새 논문·trait 추가 시)
export ANTHROPIC_API_KEY=...   ;   export LLM_MODEL=claude-...   # 본인 키/모델
python src/llm_map_traits.py --from-csv outputs/paper_traits_extracted.csv --paper "Smith 2024"
python src/llm_map_traits.py --from-text methods.txt --paper "Udler 2018" --expected 29
```

- 2·3단계는 서로 독립(순서 무관). 셋 다 네트워크 필요, 형질이 많은 단계는 수 분 소요.
- 결과 수치는 코드에 하드코딩하지 않습니다 — 돌릴 때마다 GWAS Catalog 최신 상태로 재계산됩니다.

---

## 5. 출력 CSV 컬럼

**엔진/검증A 수집 CSV** (`survey_*`, `t2d_disease_validation.csv`):
`category, our_name, query, accession, PMID, author, year, reported_trait, full_summary_stats,
european_only, ancestry_text, url`
— `full_summary_stats=True`면 genome-wide 요약통계 공개(=matrix에 바로 사용 가능).

**검증B2** (`t2d_trait_validation.csv`):
`paper, trait, category, resolved_query, european_gwas`
— `category` ∈ {recovered, label_mismatch, no_public_gwas} (+`(broad)` = 상위/근사 라벨로만 잡힘).

**추출기** (`paper_traits_extracted.csv`): `paper, raw_trait, note, citation`.

---

## 6. 검증 로직 요약 (B2 3분류)

각 trait에 후보 라벨 목록(표준 라벨이 첫 번째)을 주면, 코드가 GWAS Catalog에 순서대로 조회:

1. **recovered** — 표준(첫) 라벨로 바로 European GWAS>0.
2. **label_mismatch** — 표준은 0이지만 대체 라벨로 회수(라벨만 고치면 됨).
3. **no_public_gwas** — 어떤 후보로도 0(우리 flow 한계가 아니라 데이터 자체가 없음).
   `(broad)` = 그 형질의 정확한 라벨은 없고 상위/근사 라벨로만 잡힘(회수로 세되 약함).

이 (1)/(2)/(3) 구분이 "공정한 회수율 판정"의 핵심입니다. (2)는 우리 책임(라벨 교정),
(3)은 데이터 부재라 우리 flow의 흠이 아니기 때문입니다.

등록 논문(5편): Udler 2018(PLoS Med) · Suzuki 2024(Nature) · Kim 2023(Diabetologia) ·
Smith 2024(Nat Med) · Pascat 2026(Nat Commun). 각 목록 출처는 `extract_paper_traits.py`의
`SUPPLEMENTS` 및 `validate_t2d_trait_axis.py` 상단 주석 참조.

---

## 7. 현재 상태 / 다음 단계

- **완료**: 자동 조사 엔진, 질병 축 검증, 형질 축 검증(B2, 5편·3분류 자동화), trait 추출기(표),
  LLM 기반 추출/매핑 자동화(`llm_map_traits.py`), 폴더 구조 정리(src/·outputs/).
- **다음**:
  1. 형질 축 **dedup**(같은 형질의 중복 GWAS를 대표 1개로; 형질 종류는 넓게 유지).
  2. **LDSC 유전상관 스캔**(CD GWAS ↔ 형질) — 큐레이션 발굴 사각 보완.
  3. **Step 3: matrix 구성**(allele harmonization → 표준화 → ±분리 → bNMF).

## 8. 알려진 한계

- European 필터는 `initialSampleSize` 텍스트 휴리스틱 — "European American"/admixed 경계 사례는
  수동 검토 권장, "not reported"는 보수적으로 제외.
- 회수 완전성은 라벨 매핑 품질에 의존(label_mismatch가 그 사례) — 라벨을 대충 넣으면 놓친 것처럼 보임.
- Smith 2024의 sex별/ratio raw 라벨 → canonical 표현형 축약은 사람 검토 단계(오매핑 위험).
- 현재 형질 수는 "후보 풀" — 최종 matrix는 dedup 후 훨씬 적음.
