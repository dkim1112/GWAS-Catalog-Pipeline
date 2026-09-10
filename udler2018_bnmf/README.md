# Udler 2018 T2D bNMF 재현

Udler et al. 2018 (PLoS Med) 의 T2D 소프트 클러스터링을 공개 파이프라인
([gwas-partitioning/bnmf-clustering](https://github.com/gwas-partitioning/bnmf-clustering))
으로 재현합니다. 목적은 논문 결과를 다시 얻는 것 자체가 아니라, **이 파이프라인을
다른 질병에 적용하기 전에 정답지가 있는 데이터로 검증**하는 것입니다.

기준 논문: Udler MS et al. PLoS Med 2018. doi:10.1371/journal.pmed.1002654

---

## 현재 상태

**v2 (44 형질) 실행 완료.** Udler 5개 클러스터 중 **4개 재현**
(Beta-cell, Liver/Lipid, Obesity, Proinsulin). Lipodystrophy 만 Obesity 축에서
분리되지 않습니다.

| | v1 (35열) | **v2 (44열)** |
|---|---|---|
| bNMF 입력 변이 | 71 | **77** |
| 최종 trait feature | 52 (26 형질) | **62 (31 형질)** |
| ARD 가 고른 K | K=3 (96/100) | **K=4 (70/100)**, K=5 27/100 |
| 재현된 클러스터 | 1 | **4** |

자세한 대조표와 해석 → **[docs/RESULTS.md](docs/RESULTS.md)**

**검증 안 된 모듈이 하나 남아 있습니다** — `choose_variants_2025.R` (변이 선택:
클럼핑 / LD pruning / HLA 제외). 이번 재현은 논문의 변이 94개를 직접 넣어
이 모듈을 통째로 우회했습니다. 정답지 변이 리스트가 없는 다른 질병에 적용하려면
이 모듈을 반드시 별도로 검증해야 합니다. → [docs/RESULTS.md](docs/RESULTS.md#검증된-것과-안-된-것)

---

## 빠르게 돌리기

입력(요약통계·rsID 맵·sqlite 색인)이 이미 갖춰져 있다면:

```bash
cd <프로젝트 루트>
python3 tools/validate_inputs.py      # "준비 완료" 가 나와야 함
export LDLINK_TOKEN=<토큰>            # 셸에만. 폴더 안 파일에 적지 말 것
Rscript run_pipeline.R                # 약 4분
```

산출물은 `results/<version>/` 에 모입니다 (`version` 은
`scripts/main_script_example.R` 에서 지정).

처음부터 입력을 만드는 절차는 → **[docs/SETUP.md](docs/SETUP.md)**

---

## 문서

| 문서 | 내용 |
|---|---|
| **[docs/SETUP.md](docs/SETUP.md)** | 서버 준비, 필요 용량, 입력 데이터 재생성, R 패키지, LDlink 토큰 |
| **[docs/RUN.md](docs/RUN.md)** | 실행 방법, 파이프라인 구조, 공개 repo 코드에서 반드시 고쳐야 할 곳, 중간 검증 |
| **[docs/INPUTS.md](docs/INPUTS.md)** | 44개 형질의 출처, 원 논문과 다른 점, 포맷 변환 규칙, `sample_size` 주의사항 |
| **[docs/RESULTS.md](docs/RESULTS.md)** | v1/v2 결과, 정답지 대조, 재현 판정, 알려진 한계 |

---

## 폴더 구조

```
udler2018_bnmf/
├── README.md
├── run_pipeline.R              실행 드라이버 (이것만 돌리면 됨)
├── manifest.xlsx               파이프라인 입력 (main_gwas 1행 / trait_gwas 44행)
├── inputs_manifest.csv         형질별 출처·URL·상태
│
├── docs/                       문서 4개 (위 표)
├── scripts/                    파이프라인 R 스크립트 (repo 사본 + 로컬 수정)
│   ├── main_script_example.R     설정 + 13개 Section
│   ├── choose_variants_2025.R    변이 선택 (이번 재현에서는 우회됨)
│   ├── prep_bNMF_2025.R          요약통계 fetch, z 행렬, 상관 pruning
│   ├── run_bNMF_2025.R           bNMF 실행, ARD 의 K 선택
│   ├── post_bNMF_2025.R          post-hoc 분석 (이번 재현에서는 미사용)
│   └── udler_substitute.R        Section 2-3-4.1 대체 (논문 94개 변이 직접 로드)
├── tools/                      입력 준비 (Python/셸)
│   ├── download_inputs.sh        요약통계 자동 내려받기
│   ├── build_rsid_map.py         rsID ↔ hg19 위치 맵 생성
│   ├── convert_sumstats.py       원본 → 파이프라인 포맷 변환
│   ├── validate_inputs.py        돌리기 전 점검
│   └── one_off/                  이미 적용 완료된 일회성 열 추가 스크립트 (기록용)
├── refs/                       논문에서 추출한 기준 데이터 + 정답지
│   ├── udler2018_variants.csv          변이 94개
│   ├── udler2018_S3_variant_weights.csv  정답지: 변이 × 클러스터
│   ├── udler2018_S4_trait_weights.csv    정답지: 형질 × 클러스터
│   ├── udler2018_column_source_status.csv
│   ├── hg19ToHg38.over.chain           post_bNMF liftover 용 (이 재현엔 불필요)
│   └── provenance/                     위 CSV 를 supplement 에서 뽑은 스크립트
│
├── data/                       ← 용량 큼. 번들에 동봉 안 함, 서버에서 생성
│   ├── sumstats/                 원본 요약통계 (약 3.5 GB)
│   ├── sumstats_converted/       변환본 — manifest.xlsx 가 가리키는 곳 (약 1.3 GB)
│   ├── rsid_maps_by_chr/         chr1~22.txt (약 1.1 GB)
│   └── _rsid_map.sqlite          convert_sumstats.py 색인 (약 2.1 GB)
├── results/
│   ├── udler2018_eur_v1/         v1 (35열) — 대조용 보존
│   └── udler2018_eur_v2/         v2 (44열) — 현재 결과
├── reports/                    보고 산출물
│   ├── T2D_bNMF_검증보고서_v2.docx
│   ├── bnmf_검증_공유문.txt
│   ├── make_figures.py
│   └── figures/
└── logs/
```

### 지우면 안 되는 것

* **`data/_rsid_map.sqlite`** (2.1 GB) — `convert_sumstats.py` 가 매번 필요로 합니다.
  용량 아끼려고 지우면 형질을 추가하거나 재변환할 때
  `python3 tools/convert_sumstats.py --index` (약 4분) 로 다시 만들어야 합니다.
* **`results/udler2018_eur_v1/`** — v1 대조군. v2 와 비교해 "무엇이 달라져서
  Liver/Lipid 가 회복됐는가"를 짚는 근거입니다.
* **`refs/`** — 정답지. 이게 없으면 재현 여부를 채점할 수 없습니다.

### LDlink 토큰

셸 환경변수로만 설정하세요. 공유되는 폴더이므로 스크립트나 파일에 적지 마세요.

```bash
export LDLINK_TOKEN=<발급받은토큰>
```

`scripts/main_script_example.R` 이 `Sys.getenv("LDLINK_TOKEN")` 으로 읽습니다.
