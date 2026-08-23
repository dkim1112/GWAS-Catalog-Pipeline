#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
validate_t2d_disease_axis.py  -  T2D 검증 [질병 축 = matrix '행(row)']
================================================================================
목적:
  우리 자동 조사 flow(gwas_catalog_survey.py)가 bNMF matrix의 '행 재료'(질병 SNP의
  출처 = 질병 GWAS)를 놓치지 않는지 검증한다. bNMF 선행연구(Udler/Kim/Smith 등)가
  변이(SNP) 출처로 실제 쓴 '대표(landmark) T2D GWAS'를, 우리 flow가 T2D를 조회했을 때
  European 결과 안에서 다시 잡아내면 = 행 축 재료 수집이 신뢰할 만하다는 증거.

두 축 중 이 파일이 담당하는 것 = 질병 축(행). (README 참조)
  - 질병 축(행, SNP 출처) 검증 ......... 이 파일  (validate_t2d_disease_axis.py)
  - 형질 축(열, trait GWAS) 검증 ....... validate_t2d_trait_axis.py  (B2, 논문 전체 trait 목록)
  둘 다 엔진(gwas_catalog_survey.py)의 European 판정을 재사용한다(= 공정한 검증).
  * 형질 축은 여기서 다루지 않는다. 예전 이 파일에 있던 '대표 형질 회수(B1)'는
    형질 축 정밀 검증(B2)에 완전히 포함되므로 그쪽으로 이관/은퇴했다.

방식:
  T2D를 flow로 조회(reported + EFO) -> European T2D GWAS 전수 수집 -> 그 안에
  대표 T2D GWAS(Mahajan/DIAGRAM 2018, Scott, Xue, Morris)가 저자명으로 잡히는지 대조.
  multi-ancestry 연구(예: Suzuki 2024)는 European-only 기준에 걸려 정상적으로 제외된다
  (=오류가 아니라 기준대로 작동. 이 점도 결과에 명시된다).

실행: python cd_survey/src/validate_t2d_disease_axis.py   (같은 폴더에 gwas_catalog_survey.py 필요; 출력 cd_survey/outputs/)
================================================================================
"""
import csv
import gwas_catalog_survey as g   # 조사 스크립트의 함수 재사용 (동일 로직 = 공정한 검증)

# --- T2D 질병 축: reported + EFO 두 갈래 (CD와 동일 방식) ---
T2D_ROWS = [("disease","Type 2 diabetes"), ("efo","type 2 diabetes mellitus")]

# bNMF 선행연구가 실제로 변이 출처로 쓴 대표 T2D 질병 GWAS (저자명으로 대조)
#   Suzuki는 multi-ancestry라 European 필터에서 정상 제외되어야 함(=오류 아님).
LANDMARK = {"Mahajan":"Mahajan/DIAGRAM 2018", "Scott":"Scott 2017", "Xue":"Xue 2018",
            "Morris":"Morris 2012", "Suzuki":"Suzuki 2024(multi-ancestry)"}

def main():
    # ===== 질병 축: 전체 수집 후 landmark 대조 =====
    rows = g.run(T2D_ROWS, "rows", "t2d_disease_validation.csv", "[질병 축] T2D 질병 GWAS 수집")
    print("\n[질병 축] 대표 T2D GWAS가 우리 European 결과에 포함됐나:")
    hit_cnt = 0
    for k, v in LANDMARK.items():
        hit = [r for r in rows if k in r["author"]]
        if hit:
            hit_cnt += 1
            print(f"   O {v:26} -> {hit[0]['accession']} ({hit[0]['year']})")
        else:
            print(f"   X {v:26} -> 없음 (multi-ancestry면 필터가 정상 제외한 것)")
    eur_expected = [k for k in LANDMARK if k != "Suzuki"]   # Suzuki 제외(다인구)
    print(f"\n   => European landmark {sum(1 for k in eur_expected if any(k in r['author'] for r in rows))}"
          f"/{len(eur_expected)} 회수  (Suzuki는 기준상 정상 제외)")
    print("   (European landmark가 다 잡히면: 행 축 재료 수집이 대표 질병 GWAS를 놓치지 않음 = 검증 성공)")

if __name__ == "__main__":
    main()
