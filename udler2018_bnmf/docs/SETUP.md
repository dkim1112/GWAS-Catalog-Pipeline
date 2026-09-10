# SETUP — 서버 준비와 입력 데이터 생성

이 문서는 **빈 폴더에서 시작해 `tools/validate_inputs.py` 가 "준비 완료" 를 낼 때까지**를
다룹니다. 그 다음 단계는 [RUN.md](RUN.md) 입니다.

---

## 1. 폴더 위치 — 용량 확인 먼저

| 항목 | 용량 |
|---|---|
| `data/sumstats/` 원본 요약통계 | 약 3.5 GB |
| `data/sumstats_converted/` 변환본 | 약 1.3 GB |
| `data/rsid_maps_by_chr/` rsID 맵 | 약 1.1 GB |
| `data/_rsid_map.sqlite` 색인 | 약 2.1 GB |
| dbSNP VCF (맵 생성 중 임시) | 약 1.6 GB |
| `results/<version>/` R 체크포인트 `.RData` | 실행당 수십~수백 MB |
| LD pruning 산출물 (choose_variants 를 쓸 경우) | 수백 MB |
| **여유 포함 권장** | **30 GB 이상** |

home 디렉토리는 보통 쿼터가 걸려 있어 중간에 `save.image()` 가 실패할 수 있습니다.
먼저 확인하세요.

```bash
quota -s 2>/dev/null || df -h ~
ls -ld /nfs/das2/*/$USER /das2/$USER 2>/dev/null   # DAS2 에 본인 폴더가 있는지
```

DAS2 에 폴더가 있으면 거기에 두는 것을 권합니다. 공유 폴더라면 그룹 읽기 권한을 열어둡니다.

```bash
export PROJ=/nfs/das2/<본인폴더>/udler2018_bnmf
mkdir -p $PROJ && chmod g+rx $PROJ
```

## 2. 파일 올리기

번들에는 스크립트·문서·매니페스트·정답지만 들어 있습니다 (`data/` 는 용량이 커서 제외).

```bash
# 로컬에서
scp udler2018_bnmf_bundle.tar.gz <uniqname>@<서버주소>:$(dirname $PROJ)/
# 서버에서
cd $(dirname $PROJ) && tar xzf udler2018_bnmf_bundle.tar.gz && cd udler2018_bnmf
```

## 3. 수동으로 받아야 하는 4개

자동 다운로드가 안 되므로 **먼저** `data/sumstats/` 에 넣어두세요.

| key | 파일명 | 출처 |
|---|---|---|
| `bw` | `data/sumstats/bw.txt.gz` | EGG Horikoshi 2016 fetal EUR (`BW3_EUR_summary_stats.txt.gz`) |
| `bl` | `data/sumstats/bl.txt.gz` | EGG 2014 (`EGG-GWAS-BL.txt.gz`) |
| `hba1c` | `data/sumstats/hba1c.txt.gz` | MAGIC Soranzo 2010, N=46,368 (`MAGIC_HbA1C.txt.gz`) |
| 질병 GWAS | `data/sumstats/t2d_diagram_v3.txt.gz` | DIAGRAM v3 Stage 1, Morris 2012 (`DIAGRAMv3.2012DEC17.zip`) |

DIAGRAM v3 는 <http://diagram-consortium.org/downloads.html> 에서 받습니다.

## 4. 나머지 입력 생성

```bash
cd $PROJ
bash tools/download_inputs.sh              # 1) 자동 41개, 약 3 GB, 수 분
python3 tools/build_rsid_map.py            # 2) rsID 맵, 약 4분 → data/rsid_maps_by_chr/
python3 tools/convert_sumstats.py --index  # 3) sqlite 색인, 약 4분 → data/_rsid_map.sqlite
python3 tools/convert_sumstats.py          # 4) 포맷 변환, 약 40분 → data/sumstats_converted/
python3 tools/validate_inputs.py --paths $PWD   # 5) manifest.xlsx 의 경로를 절대경로로
python3 tools/validate_inputs.py                # 6) 점검 — "준비 완료" 가 나와야 함
```

각 스크립트가 무엇을 어떻게 변환하는지, 왜 그런 선택을 했는지는
[INPUTS.md](INPUTS.md) 에 있습니다.

`tools/one_off/` 안의 두 스크립트(`add_charge_traits.sh`, `add_glgc_lipids.py`)는
**이미 적용 완료**되어 v2 인풋에 반영돼 있습니다. 다시 돌릴 필요 없고, 해당 9개 열이
어떻게 들어왔는지의 기록으로만 두었습니다.

## 5. R 환경

```bash
module load R          # 서버에 모듈 시스템이 있으면
R
```

```r
install.packages(c("data.table","dplyr","magrittr","readxl","softImpute","strex",
                   "tidyr","readr","purrr","tibble","stringr","forcats","lubridate",
                   "ggplot2","openxlsx","vroom","LDlinkR","furrr","parallelly","curl"))
if (!requireNamespace("BiocManager", quietly=TRUE)) install.packages("BiocManager")
BiocManager::install(c("GenomicRanges","rtracklayer","Rsamtools","Homo.sapiens"))
```

> `tidyverse` 메타패키지는 시스템 라이브러리(`ragg`) 가 없으면 설치가 실패합니다.
> `scripts/main_script_example.R` 은 메타패키지 대신 개별 컴포넌트를 `library()` 하도록
> 고쳐두었으므로, 위 목록만 깔면 됩니다.

## 6. LDlink 토큰

<https://ldlink.nci.nih.gov/?tab=apiaccess> 에서 발급받아 **셸 환경변수로만** 설정합니다.

```bash
export LDLINK_TOKEN=<발급받은토큰>
```

`~/.bashrc` 에 넣어도 되지만, **공유 폴더 안의 파일에는 절대 적지 마세요.**

이번 재현(`run_pipeline.R`)은 LD pruning 과 프록시 탐색을 건너뛰므로 토큰 없이도
돌아갑니다. `choose_variants_2025.R` 을 쓰는 경우에만 필요합니다.
