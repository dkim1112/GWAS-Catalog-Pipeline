# 실행 가이드 (2단계 서버 준비 → 3단계 분석)

`validate_inputs.py` 가 통과한 뒤부터의 절차입니다.

---

## 2단계. 서버에 올리기

### 2-1. 폴더 위치 — DAS2 권장

필요 용량이 작지 않습니다.

| 항목 | 용량 |
|---|---|
| 원본 요약통계 `sumstats/` | 약 2.5 GB |
| 변환본 `sumstats_converted/` | 약 1.2 GB |
| rsID 맵 `rsid_maps_by_chr/` | 약 1.15 GB |
| sqlite 색인 `_rsid_map.sqlite` | 약 2.1 GB |
| dbSNP VCF (맵 생성 중 임시) | 약 1.6 GB |
| R 워크스페이스 `.RData` 체크포인트 | 수 GB (`save.image()` 를 매 단계 호출) |
| LD pruning 산출물 (염색체 x population) | 수백 MB |
| **여유 포함 권장** | **30 GB 이상** |

home 디렉토리는 보통 쿼터가 걸려 있어 중간에 `save.image()` 가 실패할 수 있습니다.
먼저 확인하세요.

```bash
# 쿼터 확인 (둘 중 되는 것으로)
quota -s 2>/dev/null || df -h ~ 
ls -ld /nfs/das2/*/$USER /das2/$USER 2>/dev/null   # DAS2 에 본인 계정 폴더가 있는지
```

DAS2 에 본인 폴더가 있으면 거기, 없으면 관리자에게 요청하거나 home 에서
쿼터를 확인하고 진행하세요. 박사님과 공유할 폴더이므로 그룹 읽기 권한을 열어둡니다.

```bash
export PROJ=/nfs/das2/<본인폴더>/udler2018_bnmf     # 실제 경로로 바꾸세요
mkdir -p $PROJ && chmod g+rx $PROJ
```

### 2-2. 파일 올리기

VS Code Remote-SSH 로 접속하면 파일 탐색기 드래그로도 되지만, 용량이 커서
터미널이 안전합니다. 로컬에서:

```bash
scp udler2018_bnmf_bundle.tar.gz <uniqname>@<서버주소>:$PROJ/..
```

서버에서:

```bash
cd $(dirname $PROJ) && tar xzf udler2018_bnmf_bundle.tar.gz && cd udler2018_bnmf
```

### 2-3. 대용량 산출물 재생성

번들에는 스크립트와 매니페스트만 들어 있습니다. 데이터는 서버에서 만듭니다.
수동으로 받은 4개는 먼저 `sumstats/` 에 넣어두세요
(`bw.txt.gz` `bl.txt.gz` `hba1c.txt.gz` `t2d_diagram_v3.txt.gz`).

```bash
cd $PROJ
bash download_inputs.sh                 # 자동 36개, 약 2.5GB
python3 build_rsid_map.py               # rsID 맵, 약 4분
python3 convert_sumstats.py --index     # sqlite 색인, 약 4분
python3 convert_sumstats.py             # 포맷 변환, 약 40분
python3 validate_inputs.py --paths $PROJ
python3 validate_inputs.py              # "준비 완료" 나와야 함
```

### 2-4. R 환경

```bash
module load R          # 서버에 모듈 시스템이 있으면
R
```

```r
install.packages(c("data.table","dplyr","magrittr","readxl","softImpute","strex",
                   "tidyverse","readr","openxlsx","vroom","LDlinkR","furrr",
                   "parallelly","curl"))
if (!requireNamespace("BiocManager", quietly=TRUE)) install.packages("BiocManager")
BiocManager::install(c("GenomicRanges","rtracklayer","Rsamtools","Homo.sapiens"))
```

### 2-5. LDlink 토큰

```bash
export LDLINK_TOKEN=<발급받은토큰>
```

`~/.bashrc` 에 넣어두면 편하지만, **공유 폴더 안의 파일에는 절대 적지 마세요.**
`main_script_example.R:63` 이 `Sys.getenv("LDLINK_TOKEN")` 으로 읽습니다.

---

## 3단계. 분석 실행

박사님이 "복붙만 하지 말고 꼼꼼히 보라"고 하신 이유가 실재합니다.
**공개 repo 코드는 그대로 돌리면 두 군데에서 문제가 생깁니다.**

### 3-1. 반드시 고쳐야 할 두 곳

#### (가) `my_pops` — 193행

```r
my_pops <- c("EUR","EAS","AFR","AMR","SAS")     # 현재
my_pops <- c("EUR")                              # EUR 재현이면 이렇게
```

왜: 261~262행이 `filter(n == num_pops)` 로 **5개 population 전부에서 독립인
변이만** 남깁니다. EUR 테스트인데 그대로 두면 EAS/AFR/AMR/SAS 기준까지 통과해야
해서 변이 집합이 경고 없이 줄어듭니다. `num_pops <- length(my_pops)` 이므로
193행만 고치면 261행은 자동으로 따라옵니다.

참고: 박사님은 "github 코드가 EUR-only일 것"이라고 하셨는데 지금 repo 는 반대로
multi-ancestry 버전입니다. README 첫 줄도 "T2D Multi-ancestry Partitioned
Polygenic Scores" 입니다. 논문 발표 이후 갱신된 것으로 보입니다.

#### (나) `fetch_summary_stats` 호출이 주석 처리되어 있음 — 295~303행

```r
# z_n_mats <- fetch_summary_stats(
#   df_input          = fetch_input,
#   ...
# )
# save.image(file = df_save)
```

바로 아래 308행이 `zmat0 <- z_n_mats$df_z` 입니다. **주석을 풀지 않으면
`object 'z_n_mats' not found` 로 죽습니다.** 스크립트 상단 주석에 "Steps 2-3
are commented out by default" 라고 되어 있지만, 실제로 주석 처리된 건 4.2절입니다.

주석을 풀고 다음처럼 만드세요.

```r
z_n_mats <- fetch_summary_stats(
  df_input          = fetch_input,
  gwas_ss_file      = main_ss_filepath,
  trait_ss_files    = trait_ss_files,
  trait_ss_size     = trait_ss_size,
  pval_cutoff       = 0.05,
  read_trait_method = 'datatable'
)
save.image(file = df_save)
```

### 3-2. USER CONFIGURATION 수정 (35~100행)

| 행 | 항목 | 값 |
|---|---|---|
| 49 | `working_dir` | `"/nfs/das2/<본인폴더>/udler2018_bnmf"` |
| 52 | `version` | `"udler2018_eur_v1"` |
| 55 | `gwas_file` | `file.path(working_dir, "manifest.xlsx")` |
| 58 | `scripts_dir` | `file.path(working_dir, "scripts")` |
| 63 | `my_LDlink_token` | 그대로 (환경변수에서 읽음) |
| 71~73 | `PVCUTOFF` 등 | 그대로 (5e-8 / 5e-6 / 500) |
| 79 | `my_rsid_map_dir` | `file.path(working_dir, "rsid_maps_by_chr")` |
| 82 | `rename_cols` | `NULL` — 변환기가 이미 표준 컬럼명으로 맞춰놨습니다 |
| 88 | `hg19_to_hg38_chain_file` | `file.path(working_dir, "hg19ToHg38.over.chain")` |
| 97 | `USE_TOPMED_FILTER` | `FALSE` 그대로 |

### 3-3. 실행 — 통째로 돌리지 말 것

3절 LD pruning 이 LDlink API 를 염색체 x population 단위로 호출해서
**몇 시간** 걸립니다. 접속이 끊기면 처음부터가 되므로 `screen` 이나 `tmux` 안에서
돌리고, 절 단위로 끊어서 확인하며 진행하세요. 각 절 끝에 `save.image()` 가 있어
중간부터 재개할 수 있습니다.

```bash
screen -S bnmf          # 나중에 재접속: screen -r bnmf
cd $PROJ
R
```

```r
# 0~1절: 설정 + 매니페스트 로드
#   확인할 것: "Missing trait file:" 메시지가 하나도 안 나와야 함
#              nrow(gwas_traits) == 35

# 2절: 변이 선택 + clumping
#   확인할 것: "After HLA removal", "Sentinel variants", "Variants after clumping" 숫자

# 3절: LD pruning  <- 몇 시간. my_pops 고쳤는지 먼저 확인
#   확인할 것: "Sig. SNPs pruned from N to M"

# 재개할 때
load("my_workspace_udler2018_eur_v1.RData")
```

### 3-4. 중간 검증 — 3절 끝나면 반드시

**bNMF 까지 가기 전에 여기서 한 번 맞춰봐야 합니다.**
Udler 가 쓴 변이 94개가 `refs/udler2018_variants.csv` 에 있습니다.

```r
gold <- read.csv("refs/udler2018_variants.csv")
mine <- pruned_vars$VAR_ID
cat(sprintf("우리 변이 %d개, 논문 94개, 겹침 %d개\n",
            length(mine), length(intersect(mine, gold$VAR_ID))))
setdiff(gold$VAR_ID, mine)   # 논문에는 있는데 우리에겐 없는 것
setdiff(mine, gold$VAR_ID)   # 우리에게만 있는 것
```

여기서 크게 어긋나면 **bNMF 로 넘어가지 말고** 변이 선택 단계를 먼저 보셔야 합니다.
결과가 다 나온 뒤에는 어느 단계에서 갈렸는지 짚기 어렵습니다.

`rs1801282`(PPARG) 하나는 다대립이라 빠질 수 있습니다. 93개면 정상입니다.

### 3-5. 나머지 절

| 절 | 내용 | 주의 |
|---|---|---|
| 4 | 요약통계 fetch, 결측 필터 | **주석 푸는 것 잊지 말 것.** 형질당 파일을 grep 하므로 오래 걸림 |
| 5 | TOPMed 감사 | `USE_TOPMED_FILTER=FALSE` 라 건너뜀 |
| 6~8 | proxy 탐색, 최종 변이 확정 | `my_rsid_map_dir` 이 여기서 쓰임 |
| 9~10 | allele 정렬, QC 리포트 | QC 리포트 꼭 읽어볼 것 |
| 11~12 | softImpute 결측 대치 | |
| 13 | **bNMF 실행** | `my_n_reps=100`, `K=15`, `K0=10`. 병렬로 도는데 코어를 많이 씁니다 |

13절 직전에 이 메시지가 나옵니다.

```
Final matrix dimensions: N SNPs x M traits
```

여기 M 이 35 근처인지 확인하세요. 4절의 결측 30% 필터와 저표본 필터(median N > 5000)
때문에 35보다 줄어들 수 있고, 얼마나 줄었는지가 결과 해석에 필요합니다.
빠진 형질 목록은 `df_traits.csv` 로 저장됩니다.

---

## 4단계로 넘어가기 전에 기록해둘 것

박사님과 결과를 대조하려면 두 사람이 같은 조건이어야 합니다. 다음을 적어두세요.

* `my_pops` 값
* 4절 필터 후 남은 형질 수 (`df_traits.csv`)
* `pruned_vars` 변이 수와 논문 94개와의 겹침
* bNMF 설정 (`bnmf_settings.rds` 로 저장됨)
* ARD 가 고른 K

## 우리 입력이 논문과 다른 점 (결과 해석 시 필수)

원 논문 47열 중 **12열이 빠져 있습니다**:
* 하드 제외 7개: 아디포넥틴(`adip`), 지질 4개(`hdl` `ldl` `tc` `tg`), `leptinbmi`, `fi_bmi`
* CHARGE 접근 불가 5개: 지방산 4개(`n6_1821` `n6_1831` `n6_2031` `palmitoleic`), `dpa`

특히 지질 4개(`hdl` `ldl` `tc` `tg`)는 ENGAGE 호스트가 죽어서 못 구했는데,
Udler 의 클러스터 5개 중 하나가 **Liver/Lipid** 입니다.

따라서 재현 판정은 이렇게 나누는 것이 맞습니다.

* Beta-Cell / Proinsulin / Obesity / Lipodystrophy — 재현 여부를 그대로 판정
* Liver/Lipid — 입력이 부족하므로 별도 취급. 안 나와도 파이프라인 문제로 보기 어려움
* CHARGE 지방산 5개는 원 논문에서도 소수 클러스터에만 국한된 영향이라 클러스터 정체성
  판정에는 큰 지장 없을 것으로 봄. 나중에 얻으면 매니페스트에 추가하고 재실행 가능.
