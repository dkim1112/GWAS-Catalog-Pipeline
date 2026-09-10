# RUN — 실행 방법과 파이프라인 구조

[SETUP.md](SETUP.md) 의 `tools/validate_inputs.py` 가 "준비 완료" 를 낸 뒤부터입니다.

---

## 한 줄 실행

```bash
cd <프로젝트 루트>
Rscript run_pipeline.R          # 약 4분
```

`run_pipeline.R` 이 `scripts/main_script_example.R` 을 구간별로 나눠 실행하고,
중간에 `udler_substitute.R` 을 끼워 넣고, Section 7(프록시)을 건너뜁니다.
로그를 남기려면:

```bash
Rscript run_pipeline.R 2>&1 | tee logs/run.log
```

산출물은 전부 `results/<version>/` 안에 모입니다. `version` 은
`scripts/main_script_example.R` 의 USER CONFIGURATION 에서 정합니다
(현재 `"udler2018_eur_v2"`). 새 조건으로 돌릴 때는 이 값을 바꾸면
이전 결과와 섞이지 않습니다.

---

## run_pipeline.R 이 하는 일

| 구간 | 어디서 | 내용 |
|---|---|---|
| Section 0-1 | `main_script_example.R` | 설정, 헬퍼 로드, `manifest.xlsx` 읽기 |
| Section 2-3-4.1 | **`scripts/udler_substitute.R` 로 대체** | 논문 변이 94개를 직접 로드 |
| Section 4.2-6 | `main_script_example.R` | 요약통계 fetch → z 행렬, 결측 필터, 프록시 대상 판정 |
| Section 7 | **건너뜀** | 프록시 탐색 (아래 참조) |
| Section 8-13 | `main_script_example.R` | 변이 확정 → allele 정렬 → QC → softImpute → **bNMF** |
| Section 14 | 제외 | post-hoc, hg38 liftover — 이 재현에 불필요 |

구간 경계는 행 번호가 아니라 섹션 주석(앵커)으로 찾습니다.
`main_script_example.R` 을 고쳐도 `run_pipeline.R` 이 따라옵니다.

### 왜 Section 2-3-4.1 을 대체했나

DIAGRAM v3 Stage 1 단독으로 Section 2 클럼핑을 돌리면 변이가 **15개**밖에 안 나옵니다
(논문은 여러 T2D GWAS 큐레이션으로 94개를 만들었음). 재현하려면 그 리스트를 직접
넣어야 하므로 `refs/udler2018_variants.csv` 에서 읽어옵니다.

부수 효과 하나: `fetch_summary_stats()` 는 primary GWAS 파일을 `SNP`(=Chr:Pos) 컬럼으로
grep 하는데 우리 변환본에는 `VAR_ID`(=CHR_POS_REF_ALT) 만 있어 매치가 안 됩니다.
그래서 `udler_substitute.R` 이 primary GWAS 를 R 안에서 미리 로드해 `SNP`/`REF`/`ALT` 를
파생시킨 데이터프레임(`main_gwas_ready`)으로 넘깁니다.

### 왜 Section 7(프록시)을 건너뛰나

`find_variants_needing_proxies` 는 23개 변이를 프록시 대상으로 판정합니다
(44개 형질 중 20% 넘게 z-score 결측). 프록시는 그 변이를 근처 LD 파트너로
**갈아끼우는** 단계인데, 이번에는 쓰지 않습니다.

1. 지금 목표는 bNMF clustering 검증이지 프록시 모듈 검증이 아님.
2. 갈아끼우면 최종 변이가 Udler 변이가 아니게 되어 **S3 정답지와 변이 1:1 대조가
   깨짐.** "Udler 94개를 그대로 쓴다"는 방침에 어긋남.
3. 애초에 지금 구조에서는 작동하지 않음 — `udler_substitute.R` 이 `fetch_input` 을
   sentinel 94개로만 두어 z 행렬에 프록시 후보 위치가 없습니다.
   로그: `Found 7157 potential proxies` → `0 of 7157 potential proxies in the
   full z-matrix`. LDlink 는 정상이고 우리 fetch 그리드가 좁은 것이 원인.

대가는 [RESULTS.md](RESULTS.md#알려진-한계) 에 적었습니다.

---

## 공개 repo 코드에서 반드시 고쳐야 할 두 곳

`scripts/main_script_example.R` 은 **이미 고쳐둔 사본**입니다. 아래는 원본을 새로
받아 쓸 때를 위한 기록입니다. 그대로 돌리면 두 군데에서 문제가 생깁니다.

### (가) `my_pops` — multi-ancestry 기본값

```r
my_pops <- c("EUR","EAS","AFR","AMR","SAS")     # 원본
my_pops <- c("EUR")                              # EUR 재현이면 이렇게
```

Section 3 이 `filter(n == num_pops)` 로 **5개 population 전부에서 독립인 변이만**
남깁니다. EUR 테스트인데 그대로 두면 EAS/AFR/AMR/SAS 기준까지 통과해야 해서
변이 집합이 **경고 없이** 줄어듭니다. `num_pops <- length(my_pops)` 이므로
`my_pops` 한 줄만 고치면 나머지는 따라옵니다.

> 공개 repo 는 논문 발표 이후 갱신되어 지금은 multi-ancestry 버전입니다
> (repo README 첫 줄이 "T2D Multi-ancestry Partitioned Polygenic Scores").
> "github 코드가 EUR-only 일 것" 이라는 예상과 반대입니다.

### (나) `fetch_summary_stats` 호출이 주석 처리되어 있음

원본은 Section 4.2 의 `fetch_summary_stats(...)` 블록이 통째로 주석 처리돼 있는데,
바로 아래 줄이 `zmat0 <- z_n_mats$df_z` 입니다. **주석을 풀지 않으면
`object 'z_n_mats' not found` 로 죽습니다.** 스크립트 상단 주석에는
"Steps 2-3 are commented out by default" 라고 적혀 있지만 실제로 주석 처리된 건 4.2절입니다.

### 그 밖의 로컬 수정

`scripts/main_script_example.R` 헤더 주석에 전부 나열해 두었습니다.
경로 관련 수정은 다음과 같습니다.

| 항목 | 값 |
|---|---|
| `working_dir` | `getwd()` — 루트에서 실행하면 자동 |
| `gwas_file` | `manifest.xlsx` |
| `scripts_dir` | `scripts/` |
| `my_rsid_map_dir` | `data/rsid_maps_by_chr/` |
| `hg19_to_hg38_chain_file` | `refs/hg19ToHg38.over.chain` |
| `main_dir` / `df_save` | `results/<version>/` — 산출물과 체크포인트를 한곳에 모음 |
| `rename_cols` | `NULL` — 변환기가 이미 표준 컬럼명으로 맞춰놓음 |
| `PVCUTOFF` / `PVCUTOFF_PROXY` / `PROXY_WINDOW_KB` | 5e-8 / 5e-6 / 500 (원본 그대로) |
| `USE_TOPMED_FILTER` | `FALSE` (원본 그대로) |

또 파이프라인 스크립트가 작업 폴더 루트에 흘리던 임시·중간 파일들을 정리했습니다.
`trait_cor_mat.txt` 와 `scaled_filtered_zmat.csv` 는 `results/<version>/` 으로,
`*.tmp` 는 R 세션 tempdir 로, 프록시 진단 파일은
`results/<version>/proxy_diagnostics/` 로 갑니다. 여러 version 을 돌려도 서로 덮어쓰지
않습니다.

---

## 절 단위로 나눠 돌려야 할 때

`choose_variants_2025.R` 을 실제로 쓰는 경우(= 다른 질병 적용), Section 3 의
LD pruning 이 LDlink API 를 염색체 × population 단위로 호출해 **몇 시간** 걸립니다.
접속이 끊기면 처음부터가 되므로 `screen` / `tmux` 안에서 돌리고, 절 단위로 끊어
확인하며 진행하세요. 각 절 끝에 `save.image()` 가 있어 중간부터 재개할 수 있습니다.

```bash
screen -S bnmf          # 재접속: screen -r bnmf
cd $PROJ && R
```

```r
# 재개할 때
load("results/udler2018_eur_v2/my_workspace_udler2018_eur_v2.RData")
```

확인할 것:

* Section 0-1 — `"Missing trait file:"` 이 하나도 안 나와야 함, `nrow(gwas_traits) == 44`
* Section 2 — `"After HLA removal"`, `"Sentinel variants"`, `"Variants after clumping"` 숫자
* Section 3 — `"Sig. SNPs pruned from N to M"`
* Section 13 직전 — `"Final matrix dimensions: N SNPs x M traits"`.
  M 이 44 에서 얼마나 줄었는지가 결과 해석에 필요합니다
  (Section 4 의 결측 30% 필터와 저표본 필터 median N > 5000 때문에 줄어듦).
  빠진 형질 목록은 `results/<version>/df_traits.csv` 로 저장됩니다.

### 중간 검증 — 변이 선택 단계에서 한 번

**bNMF 까지 가기 전에 여기서 맞춰봐야 합니다.** 결과가 다 나온 뒤에는 어느 단계에서
갈렸는지 짚기 어렵습니다.

```r
gold <- read.csv("refs/udler2018_variants.csv")
mine <- pruned_vars$VAR_ID
cat(sprintf("우리 변이 %d개, 논문 94개, 겹침 %d개\n",
            length(mine), length(intersect(mine, gold$VAR_ID))))
setdiff(gold$VAR_ID, mine)   # 논문에는 있는데 우리에겐 없는 것
setdiff(mine, gold$VAR_ID)   # 우리에게만 있는 것
```

크게 어긋나면 bNMF 로 넘어가지 말고 변이 선택 단계를 먼저 보세요.
`rs1801282`(PPARG) 하나는 다대립이라 빠질 수 있습니다 — 93개면 정상입니다
(`prep_bNMF_2025.R` 의 allele 쌍 비교가 allele 2개를 전제).

---

## 결과를 남과 대조할 때 기록해둘 것

두 사람이 같은 조건이어야 비교가 됩니다.

* `my_pops` 값
* Section 4 필터 후 남은 형질 수 (`results/<version>/df_traits.csv`)
* `pruned_vars` 변이 수와 논문 94개와의 겹침
* bNMF 설정 (`results/<version>/bnmf_settings.rds`)
* ARD 가 고른 K (`results/<version>/run_summary.txt`)
* 입력 열 구성 — 원 논문 47열 중 어느 것이 빠졌는지, 출처를 바꾼 열이 있는지
  ([INPUTS.md](INPUTS.md))
