# INPUTS — 입력이 무엇이고 원 논문과 어디가 다른가

`manifest.xlsx` (파이프라인이 읽는 것) 와 `inputs_manifest.csv` (출처 기록) 의 내용,
그리고 **결과를 대조할 때 반드시 명시해야 하는 차이**를 정리합니다.

---

## 구성

| | 개수 |
|---|---|
| 형질 열 (전부 변환 완료) | **44** |
| 질병 GWAS (DIAGRAM v3, Morris 2012) | 1 |
| 여전히 미확보 | 3 |
| 원 논문 열 수 | 47 |

`tools/validate_inputs.py` 가 45행(형질 44 + 질병 1) 전부 통과합니다.

---

## 원 논문 47열 → 44열 (제외 3개)

**결과 대조 시 반드시 명시해야 하는 차이입니다.** 열 구성이 다르면 bNMF 의 K 와
클러스터 구성이 달라질 수 있으므로, 재현이 안 되더라도 그것이 파이프라인 문제인지
열 부재 때문인지 구분해서 해석해야 합니다.

| 제외한 열 | 사유 |
|---|---|
| `adip` (아디포넥틴) | Adipogen 사이트 404, GWAS Catalog 에 요약통계 없음 |
| `leptinbmi` | Catalog 에서 leptin 과 accession 이 겹쳐 분리 불가 |
| `fi_bmi` | Manning 2012 BMI interaction, Catalog GCST001526 요약통계 없음 |

S4 정답지 기준으로, 결측 열이 각 클러스터 가중치에서 차지하는 비중:

| 클러스터 | v1 (12개 결측) | **v2 (3개 결측)** |
|---|---|---|
| Beta-cell | 15.8% | **3.1%** |
| Proinsulin | 22.6% | **5.0%** |
| Obesity | 19.4% | **4.9%** |
| Lipodystrophy | 29.4% | **9.2%** |
| Liver/Lipid | 56.4% | **8.0%** |

v1 에서 Liver/Lipid 가 재현 안 된 것(r=0.38)은 가중치의 56%가 없었기 때문으로
설명됩니다. v2 는 전 클러스터 결측이 10% 미만이므로 **5개 클러스터 재현을
기대할 수 있는 조건**이었고, 실제로 4개가 나왔습니다.

---

## 출처를 바꾼 열 — 지질 4개

`hdl` `ldl` `tc` `tg` 는 Udler 가 쓴 **ENGAGE 2015** 배포처
(diagram-consortium.org/2015_ENGAGE_1KG/) 가 죽었고 GWAS Catalog 에도 없어,
**GLGC Willer 2013 jointGwasMc** (<http://csg.sph.umich.edu/willer/public/lipids2013/>)
로 대체했습니다. **원 논문과 출처가 다르므로 결과 대조 시 명시할 것.**

Willer 2013 을 고른 이유:

* 포맷이 `convert_sumstats.py` 컬럼 매칭에 그대로 걸림 (rsid/A1/beta/se/N/P-value,
  hg19 좌표 포함) — 변환 코드 수정 불필요.
* 표본 규모(N 중앙값 9.0~9.5만)가 ENGAGE 2015(N~6.2만)와 같은 자릿수라,
  다른 40개 형질(2010~2016) 대비 상대적 검정력이 원 논문 구도에 가깝다.
  대안인 GLGC Graham 2021 은 EUR N~1.3M 이라 지질만 검정력이 압도적이어서
  p-value 필터 / 상관 pruning 통과 양상이 논문과 어긋날 수 있다.
  (z 자체는 `prep_bNMF_2025.R` 이 √N 으로 나눠 정규화하므로 스케일 문제는 없음.)

QC: Udler 94개 변이 중 지질 4개 파일 전부 **86개** 보유 — 기존 40개 형질
(중앙값 87, 범위 86~88) 과 동일 수준.

적용 스크립트: `tools/one_off/add_glgc_lipids.py` (이미 적용 완료, 기록용).

## CHARGE 지방산 5개

`dpa` `palmitoleic` `n6_1821` `n6_1831` `n6_2031` 은
<https://faculty.washington.edu/rozenl/files> 에서 받아 추가했습니다.
표본수는 Udler S2 Table 기재값(8,631~8,961)을 씁니다.

적용 스크립트: `tools/one_off/add_charge_traits.sh` (이미 적용 완료, 기록용).

---

## `sample_size` — 조용히 결과를 왜곡할 수 있는 값

`manifest.xlsx` 의 `sample_size` 는 전 행 채워져 있습니다. 값의 출처는 Udler S2 Table
이며 임의로 넣은 값은 없습니다. 지질 4개는 S2 에 없으므로 변환본 `N_PH` 의
**실측 중앙값**을 넣었습니다 (hdl 94,302 / ldl 89,880 / tc 94,586 / tg 91,004).

**이 값이 요약통계 파일의 SNP별 N 을 덮어씁니다.**

```r
# prep_bNMF_2025.R
if ("N_PH" %in% names(dt)) dt[, N_PH := as.numeric(N_PH)]
if (!is.null(trait_ss_size) && trait %in% names(trait_ss_size) && ...) {
  dt[, N_PH := as.numeric(trait_ss_size[[trait]])]   # <- 매니페스트 값이 우선
}
```

그리고 그 값이 z 스케일링에 그대로 들어갑니다:

```r
z_mat <- z_mat / sqrt(N_mat[, colnames(z_mat)]) * mean(sqrt(medN_vec))
```

즉 매니페스트 `sample_size` 가 틀리면 **그 형질의 z 가 통째로 왜곡**됩니다.
파일에 정확한 N 컬럼이 있어도 매니페스트가 이깁니다.

---

## 포맷 변환 (`tools/convert_sumstats.py`)

전부 `VAR_ID / Effect_Allele_PH / BETA / SE / P_VALUE / N_PH` 6컬럼, hg19.
파일당 210만~285만 행. 원본 대비 제외율은 6~13% (dbSNP common 에 없는 저빈도 변이,
또는 effect allele 이 REF/ALT 어느 쪽과도 안 맞는 행).

**검증**: Udler 94개 변이가 형질 파일마다 몇 개 들어 있는지 확인한 결과
중앙값 87/94, 범위 86~88. 파일 간 편차가 거의 없어 변환이 균일하게 동작합니다.

### 특별 처리한 것

* **VATGen 3개 (`vat` `sat` `vat_adjbmi`)** — `hm_beta` / `standard_error` 컬럼은
  있으나 값이 전부 NA 이고 실제 값은 `z` 에만 있습니다. z = BETA/SE 이므로
  `BETA=z, SE=1` 로 넣어 z 를 그대로 보존했습니다. 로그에 남습니다.
* **GIANT 파일** — 확장자가 `.gz` 인데 실제로는 tar.gz 입니다. 자동 판별합니다.
* **GIANT 9개 (`bmi` `height` `hip` `hip_f` `hip_m` `wc` `wc_female` `wc_male`
  `whradjbmi`)** — 원본에 좌표가 아예 없고 rsID 뿐이라 좌표와 REF/ALT 를
  전부 맵에서 채웠습니다.
* **질병 GWAS (DIAGRAM v3)** — BETA/SE 가 없고 `OR` 와 95% CI 만 있습니다.
  `BETA = log(OR)`, `SE = (log(U95) - log(L95)) / 3.92` 로 유도했습니다.
  표본수는 `N_CASES + N_CONTROLS`. (파이프라인의 질병 경로는 `ODDS_RATIO` 도 받지만,
  형질 파일과 형식을 통일했습니다.)

---

## rsID 맵 (`tools/build_rsid_map.py`) — 시행착오 기록

공개 repo 의 `generate_varid_to_rsid_map_file.R` 은 Ensembl GRCh37 'variation' VCF 를
받는데, 그건 1000G 가 아니라 dbSNP 전체입니다 (chr1 만 8,370만 변이 → 출력 2GB,
22개면 40GB). 1000G sites 파일은 가볍지만 ID 가 전부 `.` 이고, rsID 가 있는
1000G genotypes 파일은 2504명 유전형이 붙어 압축 해제 시 염색체당 수십 GB 입니다.

그래서 **dbSNP b151 GRCh37 common 세트** (1.6GB, 유전형 없음, rsID 있음, GRCh37) 를
씁니다. 결과는 38,094,512개 변이 / 1.15GB.
`build_rsid_map.py` 가 그 역할을 대신하므로 repo 의 R 스크립트는 두지 않았습니다.

**필터를 하나 바꿨습니다.** 원본 R 은 `ALT` 에 쉼표가 있으면(다중 대립) 그 변이를
버립니다. 1000G 에서는 드물지만 dbSNP 에서는 흔해서, 그대로 두면
**rs7903146 (TCF7L2)** 같은 핵심 변이가 사라집니다. 실제로 Udler 94개 중 13개가
이 필터에 걸렸습니다. ALT 를 쪼개 대립유전자마다 한 줄씩 내보내도록 고쳤고,
고친 뒤 94개가 전부 조회되며 VAR_ID 가 93개 정확히 일치합니다
(나머지 1개는 논문이 `C_G,A` 로 적은 다대립 rs1801282 → 맵이 `C_G` 로 확정).

---

## 좌표계

파이프라인 기본이 hg19 이고 Udler S3 정답지도 hg19 (`VAR_ID` 형식) 입니다.
변환본도 전부 hg19 로 통일했으므로 정답지와 직접 대조 가능하며,
`post_bNMF` 의 hg19→hg38 liftover 는 이 재현에 필요 없습니다
(필요할 때를 위해 `refs/hg19ToHg38.over.chain` 은 동봉).

---

## `refs/` 안의 기준 데이터

| 파일 | 출처 | 내용 |
|---|---|---|
| `udler2018_variants.csv` | S1+S3 | 변이 94개 (VAR_ID hg19, rsID, locus) |
| `udler2018_S3_variant_weights.csv` | S3 | **정답지**: 변이 × 클러스터 5개 |
| `udler2018_S4_trait_weights.csv` | S4 | **정답지**: 형질 × 클러스터 5개 |
| `udler2018_column_source_status.csv` | S2 | 47개 열의 원 출처 |

`udler2018_variants.csv` 는 중간 검증용이자, `udler_substitute.R` 이 Section 2-3-4.1 을
대체할 때 읽는 파일입니다. 이 CSV 들을 supplement 에서 어떻게 뽑았는지는
`refs/provenance/README.md` 참조.
