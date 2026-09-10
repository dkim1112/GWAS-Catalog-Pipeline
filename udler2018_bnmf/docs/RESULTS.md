# RESULTS — 재현 결과와 판정

실행: `Rscript run_pipeline.R` (3.8분), 2026-09-09.
결과 파일: `results/udler2018_eur_v2/`

---

## 채점 방법

* 입력: T2D 요약통계 44개 형질, 변이 77개 × 형질 62 feature
* bNMF 가 이 z-score 행렬을 W(변이 가중치) × H(형질 가중치) 로 분해
* 논문 Supplementary S4 를 형질 정답지, S3 를 변이 정답지로 두고
  우리 H/W 의 각 축과 Pearson 상관을 전부 계산 (공유 형질 62개, 공유 변이 75개)
* **형질축과 변이축은 서로 독립적인 증거**라, 둘 다 높아야 진짜 재현으로 봤습니다

K 는 우리가 정하지 않았습니다. K=15 에서 시작해 ARD 가 스스로 줄입니다.
서로 다른 초기값 100회 결과: **K=3 3회 / K=4 70회 / K=5 27회**.
데이터가 스스로 4~5개 축을 지목했고 논문의 5와 같은 범위입니다.

---

## v2 (44열) 결과

변이 경로: `pruned 94 → df_final 94 → GWAS align 77 → bNMF 77`

| | v1 (35열) | **v2 (44열)** |
|---|---|---|
| bNMF 입력 변이 | 71 | **77** |
| 최종 trait feature | 52 (26 형질) | **62 (31 형질)** |
| ARD 가 고른 K | K=3 (96/100) | **K=4 (70/100)**, K=5 27/100 |

### 정답지 대조

K=5 해의 **전체** 상관 행렬 (argmax 만 보면 오해할 수 있어 전부 기재):

```
H (형질)     Beta-cell  Proinsulin  Obesity  Lipodystrophy  Liver/Lipid
K1              -0.26        0.19    -0.07           0.11        -0.11
K2              -0.17       -0.12     0.69           0.32        -0.09
K3               0.92        0.24    -0.04          -0.07        -0.12
K4               0.27       -0.09    -0.12           0.19         0.11
K5              -0.14       -0.12    -0.04          -0.21         0.96

W (변이)     Beta-Cell  Proinsulin  Obesity  Lipodystrophy  Liver
K1               0.34        0.07    -0.18          -0.01  -0.14
K2              -0.36       -0.15     0.65           0.38  -0.05
K3               0.59       -0.04    -0.01          -0.20  -0.08
K4               0.13        0.69    -0.09          -0.03   0.00
K5              -0.15       -0.07     0.05          -0.03   0.93
```

| Udler 클러스터 | v1 | v2 (K=4) | v2 (K=5) | 판정 |
|---|---|---|---|---|
| Beta-cell | H 0.92 / W 0.59 | H 0.91 / W 0.54 | **H 0.92 / W 0.59** | 재현 |
| Liver/Lipid | H 0.38 | H 0.96 / W 0.93 | **H 0.96 / W 0.93** | 재현 ★ |
| Proinsulin | W 0.67 | W 0.69 | **W 0.69** (H 0.24) | 변이축만 재현 |
| Obesity | 미매칭 | 미매칭 | **H 0.69 / W 0.65** | 재현 (단 아래 참조) |
| Lipodystrophy | 미매칭 | 미매칭 | H 0.32 / W 0.38 | Obesity 축에 흡수, 미분리 |

**요약: Udler 5개 중 4개 축이 식별됩니다.** v1 은 1개였습니다.

### 축별 해석

* **Liver/Lipid 가 r=0.38 → 0.96 으로 회복.** 지질 4개 + CHARGE 지방산 추가의 직접
  효과이며, **v1 의 실패가 파이프라인이 아니라 입력 부족이었음**을 확인해 줍니다.
  상위 형질: `tg_neg` `palmitoleic_neg` `dpa_neg` `tc_neg` `n6_1831_neg`.

* **Obesity 와 Lipodystrophy 가 한 축(K2)으로 합쳐졌습니다.** Obesity 0.69/0.65,
  Lipodystrophy 0.32/0.38 로 Obesity 쪽이 우세하지만 분리가 안 됩니다.
  상위 형질도 `hdl_neg` `sat_pos` `tg_pos` `isi_neg`(지방이영양증 계열) 와
  `bmi_pos`(비만 계열)가 섞여 있습니다. **유력한 원인**: 상관 pruning 이
  `wc` `hip` `hip_f` `hip_m` `wc_male` `wc_female` `bodyfat` 을 전부
  "correlated w/ bmi" 로 제거해 비만 축을 대표하는 형질이 `bmi` 하나로 줄었습니다.

* **Proinsulin 은 W(변이)로는 명확하나(0.69) H(형질)로는 안 잡힙니다.**
  `proins_pos` 하나가 가중치 5.4 로 독주해서, 여러 형질에 퍼진 논문 프로파일과
  상관이 안 잡히는 것입니다. 클러스터 정체성 자체는 맞습니다.

* **K1 은 어느 클러스터와도 매칭되지 않습니다.** Beta-cell 의 역축
  (`cir_pos` `incr30_pos` `proins_neg`) 입니다. bNMF 가 음수를 못 써서 형질을
  pos/neg 두 열로 나눠 넣기 때문에 생기는 현상이고 결함이 아닙니다.
  v1 의 미매칭 K1 과 같은 성격입니다.

---

## v1 (35열) 결과 — `results/udler2018_eur_v1/`

| | 값 |
|---|---|
| 최종 변이 (bNMF 입력) | 71 |
| 최종 trait feature | 52 (35 × pos/neg → 상관 pruning 후) |
| ARD 가 고른 K | **K=3** (96/100 replicate) |
| K3 ↔ Beta-cell | **r = 0.92** ★ |
| K2 ↔ Liver/Lipid | r = 0.38 (약함 — 지질 부재가 원인) |
| K1 | 미매칭 (anti-Beta-cell 축) |

v1 → v2 의 차이는 **입력 열 9개 추가**(지질 4 + CHARGE 지방산 5)뿐입니다.
파이프라인 설정은 동일합니다. 이 대조가 "재현 실패의 원인이 입력이었다"는
근거입니다.

---

## 알려진 한계

### 1. 변이 손실 94 → 77

프록시 건너뛰기와 **별개** 경로입니다. Section 9 가
`z_n_mats$df_gwas`(DIAGRAM v3 유래)와 `inner_join` 하므로, DIAGRAM v3 에 없거나
P ≥ 0.05 인 변이가 여기서 떨어집니다.

* Udler 94개 중 DIAGRAM v3 에 P-value 가 있는 것은 **87개** (7개는 아예 없음)
* 최종 정렬 통과: **77개**

94개를 전부 쓰려면 primary GWAS join 조건을 손봐야 하며, 이는 별개 사안입니다.
`GRB14`(rs13389219) 같은 **Lipodystrophy 대표 loci 가 여전히 이 경로로 빠집니다** —
Lipodystrophy 미분리와 무관하지 않을 수 있습니다.

### 2. 프록시를 안 쓴 대가

프록시 대상으로 판정된 23개 변이는 z 값 상당수가 실측이 아니라 Section 11 의
softImpute 대치값입니다. 또 프록시로 걸러졌을 ambiguous(AT/TA/CG/GC)·다대립 변이가
최종 집합에 남아 **QC Check 6 이 FAIL 로 뜹니다(의도된 것)**.
그 대신 살아난 대표 변이: **FTO, PPARG, PNPLA3, HNF1A, SLC35D3** (v1 대비 +5).

건너뛴 이유는 [RUN.md](RUN.md#왜-section-7프록시을-건너뛰나) 참조.
진단 파일은 `results/udler2018_eur_v2/proxy_diagnostics/` 에 있습니다.

### 3. 입력 열 3개 부재 / 지질 4개 출처 변경

[INPUTS.md](INPUTS.md) 참조. 결과를 남과 대조할 때 반드시 같이 명시해야 합니다.

---

## 검증된 것과 안 된 것

이 재현의 목적이 "파이프라인이 제대로 도는가" 확인이라면,
**지금 검증된 범위를 정확히 알아야 합니다.**

| 모듈 | 상태 |
|---|---|
| `tools/convert_sumstats.py` (포맷 변환) | 검증됨 — Udler 94 중 86~88 보유, 파일 간 균일 |
| `prep_bNMF_2025.R` (z 행렬, 상관 pruning, N 스케일링) | 검증됨 |
| `run_bNMF_2025.R` (bNMF, ARD 의 K 선택) | 검증됨 — 안정 수렴, 4개 클러스터 재현 |
| **`choose_variants_2025.R` (변이 선택: 클럼핑 / LD pruning / HLA 제외)** | **미검증 — 통째로 우회함** |

`scripts/udler_substitute.R` 이 Section 2-3-4.1 을 대체합니다. DIAGRAM v3 Stage 1
단독 클럼핑이 15개 변이밖에 안 뽑아서, 논문의 94개 리스트를
`refs/udler2018_variants.csv` 에서 직접 읽어 넣은 것입니다.

**다른 질병(예: 크론병)에 적용할 때는 정답지 변이 리스트가 없으므로 이 모듈을
반드시 써야 합니다.** 지금 상태로는 그 모듈이 한 번도 안 돌았습니다.
별도 검증 계획이 필요합니다 — 예를 들어 더 큰 T2D GWAS 로 클럼핑을 돌려
94개와 얼마나 겹치는지 확인하는 식입니다.

---

## 보고 산출물

| 파일 | 용도 |
|---|---|
| `reports/T2D_bNMF_검증보고서_v2.docx` | 정식 보고서 |
| `reports/bnmf_검증_공유문.txt` | 요약 공유용 (메신저/메일) |
| `reports/figures/` | 보고서 그림 6장 |
| `reports/make_figures.py` | 그림 생성 스크립트 (`python3 reports/make_figures.py`) |
