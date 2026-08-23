# Udler 2018 재현용 입력 폴더

T2D bNMF 파이프라인을 Udler et al. 2018 (PLoS Med) 기준으로 재현하기 위한 입력 모음.
이 폴더를 서버에 두고 두 사람이 같은 입력으로 각자 돌린 뒤 결과를 대조하는 것이 목적.

기준 논문: Udler MS et al. PLoS Med 2018. doi:10.1371/journal.pmed.1002654
파이프라인: https://github.com/gwas-partitioning/bnmf-clustering

---

## 현재 상태

**bNMF 실행까지 완료.** Kimlab 서버에서 (`/BiO2/home/daniel/udler2018_bnmf`) 파이프라인 전체를 돌렸고, K=3 consensus (96/100 replicate) 를 얻었습니다. **K3 클러스터가 Udler Beta-cell 과 Pearson r=0.92 로 매칭** — Beta-cell 재현 성공. 전 과정 상세 보고는 상위 폴더의 `T2D_bNMF_재현_보고서.docx` 참조.

### 인풋 (validate_inputs.py 36행 통과)

| | 개수 |
|---|---|
| 형질 열 (전부 변환 완료) | **35** |
| 질병 GWAS (DIAGRAMv3 Morris 2012) | 1 |
| 제외 결정 (하드 제외) | 7 |
| 접근 불가 (CHARGE) | 5 |
| 원 논문 열 수 | 47 |

### bNMF 결과 (서버)

| | 값 |
|---|---|
| 최종 변이 (bNMF 입력) | 71 (Udler 94 substitute 후 데이터 없음/문제 25 제거) |
| 최종 trait feature | 52 (35 × pos/neg → prep_z_matrix corr>0.8 filter) |
| ARD 가 고른 K | **K=3** (96/100 replicate) |
| K3 ↔ Beta-cell | **r = 0.92** (강한 재현) ★ |
| K2 ↔ Liver/Lipid | r = 0.38 (약함, 지질 부재 원인) |
| K1 | 미매칭 (anti-Beta-cell 축) |

### 원 논문 47열 -> 35열 (제외 12개)

**결과 대조 시 반드시 명시해야 하는 차이입니다.** 열 구성이 다르면 bNMF 의 K 와
클러스터 구성이 달라질 수 있으므로, 재현이 안 되더라도 그것이 파이프라인 문제인지
열 12개 부재 때문인지 구분해서 해석해야 합니다.

| 제외한 열 | 사유 |
|---|---|
| `adip` (아디포넥틴) | Adipogen 사이트 404, GWAS Catalog 에 요약통계 없음 |
| `hdl` `ldl` `tc` `tg` | ENGAGE 호스트 사망(502), Catalog 에 요약통계 없음 |
| `leptinbmi` | Catalog 에서 leptin 과 accession 이 겹쳐 분리 불가 |
| `fi_bmi` | Manning 2012 BMI interaction, Catalog GCST001526 요약통계 없음 |
| `dpa` `n6_1821` `n6_1831` `n6_2031` `palmitoleic` (CHARGE 지방산 5개) | CHARGE 요약통계는 컨소시엄 승인 요청 방식이라 파일럿 진행 중 확보 못 함. 나중에 얻으면 매니페스트에 추가 재실행 가능. |

지질 4개(`hdl` `ldl` `tc` `tg`)가 빠진 것은 Udler 의 Liver/Lipid 클러스터에
직접 영향을 줄 수 있어 특히 주의해야 합니다. CHARGE 지방산 5개는 원 논문에서도
소수 클러스터에 국한된 영향이라 클러스터 정체성 판정에는 큰 영향 없을 것으로 봄.

## 실행 방법

서버 준비와 분석 실행 절차는 **`RUN_GUIDE.md`** 를 보세요.
어떤 커맨드를 어디서 치는지, `main_script_example.R` 의 어느 행을 고쳐야 하는지가
행 번호와 함께 적혀 있습니다.

**그대로 돌리면 안 되는 곳이 두 군데입니다** (박사님이 "복붙하지 말라"고 하신 부분).

1. `my_pops` (193행) — 5개 population 전부에서 독립인 변이만 남기므로
   EUR 재현이면 `c("EUR")` 로 바꿔야 합니다.
2. `fetch_summary_stats` 호출 (295~303행) — **주석 처리되어 있는데 308행이
   그 결과물을 씁니다.** 주석을 안 풀면 `object 'z_n_mats' not found` 로 죽습니다.

## 폴더 구조

```
udler2018_bnmf/
  README.md
  manifest.xlsx            파이프라인 입력 (main_gwas 1행 / trait_gwas 35행)
  inputs_manifest.csv      형질별 출처/URL/상태
  download_inputs.sh       자동 가능한 것 내려받기
  build_rsid_map.py        rsID <-> hg19 위치 맵 생성
  convert_sumstats.py      원본 -> 파이프라인 포맷 변환
  validate_inputs.py       돌리기 전 점검
  scripts/                 파이프라인 R 스크립트 6개 (repo 사본)
  refs/                    논문에서 추출한 기준 데이터 + 정답지
  hg19ToHg38.over.chain    post_bNMF 의 liftover 용
  sumstats/                원본 (다운로드 결과)
  sumstats_converted/      변환본 <- manifest 가 가리키는 곳
  rsid_maps_by_chr/        chr1~22.txt
  logs/
```

## 처음부터 재현하는 순서

수동 4개(`bw` `bl` `hba1c` `t2d_diagram_v3`)는 자동 다운로드가 안 되므로
아래 1번 전에 `sumstats/` 에 넣어두세요 (파일명은 위 표 참조, `sumstats/<key>.txt.gz`).

```bash
bash download_inputs.sh                      # 1) 자동 32개 (약 2.5GB, 수 분)
python3 build_rsid_map.py                    # 2) rsID 맵 (약 4분, 1.15GB)
python3 convert_sumstats.py --index          # 3) sqlite 색인 (약 4분, 2.1GB)
python3 convert_sumstats.py                  # 4) 포맷 변환 (약 40분)
python3 validate_inputs.py --paths $PWD      # 5) 경로를 절대경로로
python3 validate_inputs.py                   # 6) 점검
```

2~4번 산출물은 용량이 커서 이 폴더에 동봉하지 않았습니다. 위 명령으로 재생성됩니다.

## 수동으로 받은 4개 (완료)

| key | 파일 | 비고 |
|---|---|---|
| `bw` | `BW3_EUR_summary_stats.txt.gz` | EGG Horikoshi 2016 fetal EUR |
| `bl` | `EGG-GWAS-BL.txt.gz` | EGG 2014 |
| `hba1c` | `MAGIC_HbA1C.txt.gz` | MAGIC (Soranzo 2010, N=46,368) |
| 질병 | `DIAGRAMv3.2012DEC17.zip` | Morris 2012 Stage 1 |

## 변환 결과 요약

전부 `VAR_ID / Effect_Allele_PH / BETA / SE / P_VALUE / N_PH` 6컬럼, hg19.
파일당 210만~285만 행. 원본 대비 제외율은 6~13%(dbSNP common 에 없는 저빈도 변이,
또는 effect allele 이 REF/ALT 어느 쪽과도 안 맞는 행).

**검증**: Udler 94개 변이가 형질 파일마다 몇 개 들어 있는지 확인한 결과
중앙값 87/94, 범위 86~88. 파일 간 편차가 거의 없어 변환이 균일하게 동작함.

### 변환 중 특별 처리한 것

* **VATGen 3개(`vat` `sat` `vat_adjbmi`)** — `hm_beta` / `standard_error` 컬럼은
  있으나 값이 전부 NA 이고 실제 값은 `z` 에만 있습니다. z = BETA/SE 이므로
  `BETA=z, SE=1` 로 넣어 z 를 그대로 보존했습니다. 로그에 남습니다.
* **GIANT 파일** — 확장자가 `.gz` 인데 실제로는 tar.gz 입니다. 자동 판별합니다.
* **GIANT 9개(`bmi` `height` `hip` `hip_f` `hip_m` `wc` `wc_female` `wc_male`
  `whradjbmi`)** — 원본에 좌표가 아예 없고 rsID 뿐이라 좌표와 REF/ALT 를
  전부 맵에서 채웠습니다.
* **질병 GWAS (DIAGRAMv3)** — BETA/SE 가 없고 `OR` 와 95% CI 만 있습니다.
  `BETA = log(OR)`, `SE = (log(U95) - log(L95)) / 3.92` 로 유도했습니다.
  표본수는 `N_CASES + N_CONTROLS` 로 계산했습니다.
  (파이프라인의 질병 경로는 ODDS_RATIO 도 받지만, 형질 파일과 형식을 통일했습니다.)

## rsID 맵에 대해 (시행착오 기록)

repo 의 `generate_varid_to_rsid_map_file.R` 은 Ensembl GRCh37 'variation' VCF 를
받는데, 그건 1000G 가 아니라 dbSNP 전체입니다(chr1 만 8,370만 변이 → 출력 2GB,
22개면 40GB). 1000G sites 파일은 가볍지만 ID 가 전부 `.` 이고, rsID 가 있는
1000G genotypes 파일은 2504명 유전형이 붙어 압축 해제 시 염색체당 수십 GB 입니다.

그래서 **dbSNP b151 GRCh37 common 세트**(1.6GB, 유전형 없음, rsID 있음, GRCh37)를
씁니다. 결과는 38,094,512개 변이 / 1.15GB.

**필터를 하나 바꿨습니다.** 원본 R 은 `ALT` 에 쉼표가 있으면(다중 대립) 그 변이를
버립니다. 1000G 에서는 드물지만 dbSNP 에서는 흔해서, 그대로 두면
**rs7903146(TCF7L2)** 같은 핵심 변이가 사라집니다. 실제로 Udler 94개 중 13개가
이 필터에 걸렸습니다. ALT 를 쪼개 대립유전자마다 한 줄씩 내보내도록 고쳤고,
고친 뒤 94개가 전부 조회되며 VAR_ID 가 93개 정확히 일치합니다
(나머지 1개는 논문이 `C_G,A` 로 적은 다대립 rs1801282 → 맵이 `C_G` 로 확정).

## refs/ 안의 기준 데이터

| 파일 | 출처 | 내용 |
|---|---|---|
| `udler2018_variants.csv` | S1+S3 | 변이 94개 (VAR_ID hg19, rsID, locus) |
| `udler2018_S3_variant_weights.csv` | S3 | **정답지**: 변이 x 클러스터 5개 |
| `udler2018_S4_trait_weights.csv` | S4 | **정답지**: 형질 x 클러스터 5개 (94열) |
| `udler2018_column_source_status.csv` | S2 | 47개 열의 원 출처 |

`udler2018_variants.csv` 는 중간 검증용입니다. bNMF 전에 변이 선택 단계만 돌려
94개가 재현되는지 먼저 확인하면, 결과가 틀렸을 때 어느 단계인지 짚을 수 있습니다.

## 돌리기 전 확인할 것 세 가지

1. **`my_pops`** — `scripts/main_script_example.R:193` 이
   `c("EUR","EAS","AFR","AMR","SAS")` 이고 line 261 에서 5개 population **전부**에서
   독립인 변이만 남깁니다. 지금 공개 repo 는 multi-ancestry 버전입니다.
   EUR 재현이면 `my_pops <- c("EUR")` 로 바꿔야 하며, 두면 변이가 경고 없이 줄어듭니다.

2. **다대립 변이 1개** — `rs1801282`(PPARG). `prep_bNMF_2025.R` 의 allele 쌍
   비교(line 333–342)는 allele 2개를 전제합니다. 최종 변이가 93개면 정상입니다.

3. **LDlink 토큰** — 서버 셸에서 `export LDLINK_TOKEN=...` 로만 설정하세요.
   `main_script_example.R:63` 이 `Sys.getenv("LDLINK_TOKEN")` 으로 읽습니다.
   토큰을 스크립트나 이 폴더의 파일에 직접 적지 마세요 (공유되는 폴더입니다).

## sample_size

전 행 채워져 있습니다. 값의 출처는 Udler S2 Table 이며 임의로 넣은 값은 없습니다.

## 좌표계

파이프라인 기본이 hg19 이고 Udler S3 정답지도 hg19(`VAR_ID` 형식) 입니다.
변환본도 전부 hg19 로 통일했으므로 정답지와 직접 대조 가능하며,
`post_bNMF` 의 hg19→hg38 liftover 는 이 재현에는 필요 없습니다
(필요할 때를 위해 chain 파일은 동봉).
