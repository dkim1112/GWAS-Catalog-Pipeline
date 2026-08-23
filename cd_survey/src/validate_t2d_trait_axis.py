#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
validate_t2d_trait_axis.py  -  T2D 검증 [형질 축 = matrix '열(column)'] / B2
================================================================================
목적:
  우리 자동 조사 flow(gwas_catalog_survey.py)가 bNMF matrix의 '열 재료'(형질 GWAS)를
  "중요한 형질을 놓치지 않는지" 검증한다. 기존 bNMF T2D 논문들이 '실제로 쓴 trait 목록'을
  ground truth로 삼는다. (B1=유명한 것만 대조 -> 무의미. B2=부록/Methods의 전체 목록,
  안 유명한 것까지 대조.)

두 축 중 이 파일이 담당하는 것 = 형질 축(열). (README 참조)
  - 형질 축(열, trait GWAS) 검증 ....... 이 파일  (validate_t2d_trait_axis.py, B2)
  - 질병 축(행, SNP 출처) 검증 ......... validate_t2d_disease_axis.py (landmark 회수)

■ 이 스크립트가 코드로 '직접' 하는 일 (사람/웹 의존 제거):
  각 trait에 '후보 라벨 목록'만 주면, 코드가 GWAS Catalog에 라이브로 조회해
  아래 3분류를 '자동 판정'한다. 즉 회수 여부·라벨 교정 여부·데이터 부재 여부를
  사람이 손으로 정하지 않고 스크립트를 돌리면 재현된다.
    (1) recovered      : 표준(첫) 라벨로 바로 회수 (European GWAS>0)
    (2) label_mismatch : 표준 라벨은 0이지만 대체 라벨로 회수 (라벨만 고치면 됨)
    (3) no_public_gwas : 어떤 후보로도 European GWAS 0 (우리 flow 탓 아님=데이터 부재)
  + "(broad)" 접미: 그 형질의 정확한 라벨이 아니라 상위/근사 라벨로만 잡힌 경우
    (=회수로 세되 약함, 최종 matrix 편입 전 수동확인 권장).

■ 사람이 여전히 대는 입력 = '큐레이션'(gwas_catalog_survey.py의 CONFIG와 같은 성격):
  (a) 어떤 논문의 어떤 trait 목록인지  -> 각 논문 부록에서 추출(extract_paper_traits.py).
  (b) 각 trait의 후보 라벨 문자열      -> 아래 CANDIDATES. 표준 라벨을 첫 번째로 둔다.
  이 두 가지는 데이터/설정이지 코드가 아니며, 한 번 채워두면 재사용된다.
  '판정' 자체(무엇이 회수/불일치/부재인지)는 전적으로 코드가 계산한다.

후보 라벨 형식:
  CANDIDATES[trait] = [ (kind, label) , ... ]   또는  (kind, label, "broad")
  kind = "disease"(reported trait 검색) | "efo"(EFO 라벨 검색). 첫 항목 = 표준 라벨.

현재 등록 논문(5편). 각 trait 목록의 출처는 extract_paper_traits.py의 SUPPLEMENTS 참조:
  Udler 2018(PLoS Med, Methods 47->정량형질 29) / Suzuki 2024(Nature Fig.1, 37)
  / Kim 2023(Diabetologia Table S7, 64->distinct 56)
  / Smith 2024(Nat Med Table S4C, 110->distinct 62)
  / Pascat 2026(Nat Commun Supp Data 4, 45->distinct 42)
  * sex별(_female/_male)·adjBMI·ratio 변형은 distinct 표현형으로 축약(우리 flow는 성별
    분리를 안 하므로; 원 trait 수는 위 괄호, distinct 수가 아래 리스트 길이).
  * 결과 수치는 하드코딩하지 않는다 -> `python cd_survey/src/validate_t2d_trait_axis.py` 를 돌리면
    t2d_overlap_result.csv 에 논문별 3분류 집계가 그때그때 재계산된다.

실행: python cd_survey/src/validate_t2d_trait_axis.py   (같은 폴더에 gwas_catalog_survey.py 필요; 출력은 cd_survey/outputs/)
================================================================================
"""
import requests, csv
from collections import Counter
import gwas_catalog_survey as g   # European 판정 로직 재사용(engine과 동일 = 공정)

BASE="https://www.ebi.ac.uk/gwas/rest/api"; H={"Accept":"application/json"}
PAGES_FOR_RECOVERY = 2   # 회수(>0) 확인용. 형질당 앞 2페이지(100건)면 존재 확인엔 충분.

# ---------------------------------------------------------------------------
# CANDIDATES: canonical trait -> 후보 라벨(표준 라벨 첫 번째).
#   '# 2후보'는 첫(표준) 라벨이 2026-07 live에서 0이라 대체 라벨을 둔 것(=label_mismatch 유발).
#   'broad'는 그 형질의 정확한 라벨이 GWAS Catalog에 없어 상위/근사 라벨로만 잡히는 경우.
# ---------------------------------------------------------------------------
CANDIDATES = {
 # ---- glycaemic / insulin ----
 "Fasting glucose":[("disease","Fasting glucose")],
 "Fasting insulin":[("disease","Fasting insulin")],
 "HbA1c":[("disease","Glycated hemoglobin levels")],
 "Two-hour glucose":[("disease","Two-hour glucose")],
 "Random glucose":[("efo","random glucose measurement"),("disease","Random blood glucose"),("efo","glucose measurement","broad")],
 "HOMA-B":[("efo","HOMA-B")],
 "HOMA-IR":[("efo","HOMA-IR")],
 "Proinsulin":[("disease","Proinsulin levels")],
 "Corrected insulin response":[("disease","Corrected insulin response")],
 "Insulin sensitivity index":[("disease","Insulin sensitivity index")],
 "Disposition index":[("disease","Disposition index"),("disease","insulin disposition index")],
 "Modified Stumvoll ISI":[("disease","Modified Stumvoll insulin sensitivity index")],
 "Incr30/Ins30":[("efo","insulin measurement","broad")],
 "Insulin fold change":[("disease","Insulin fold change"),("efo","insulin measurement","broad")],
 # ---- anthropometric / vitals ----
 "BMI":[("efo","body mass index")],
 "Height":[("efo","body height")],
 "Body fat percentage":[("efo","body fat percentage")],
 "Trunk fat percentage":[("efo","trunk fat percentage"),("efo","body fat distribution","broad")],
 "Basal metabolic rate":[("efo","basal metabolic rate"),("disease","Basal metabolic rate")],
 "Waist circumference":[("efo","waist circumference")],
 "Hip circumference":[("efo","hip circumference")],
 "Waist-hip ratio":[("efo","waist-hip ratio")],
 "Birth weight":[("efo","birth weight")],
 "Heart rate":[("efo","heart rate")],
 "Systolic blood pressure":[("efo","systolic blood pressure")],
 "Diastolic blood pressure":[("efo","diastolic blood pressure")],
 "Pulse pressure":[("efo","pulse pressure measurement")],
 # ---- adipose tissue volumes ----
 "Visceral adipose tissue volume":[("disease","Visceral adipose tissue")],
 "Gluteofemoral adipose tissue volume":[("disease","Gluteofemoral adipose tissue volume"),("efo","gluteofemoral adipose tissue measurement")],
 "Abdominal subcutaneous adipose tissue volume":[("disease","Abdominal subcutaneous adipose tissue volume")],
 # ---- lipids ----
 "HDL cholesterol":[("efo","high density lipoprotein cholesterol measurement")],
 "LDL cholesterol":[("efo","low density lipoprotein cholesterol measurement")],
 "Total cholesterol":[("efo","total cholesterol measurement")],
 "Triglycerides":[("efo","triglyceride measurement")],
 "Non-HDL cholesterol":[("efo","non-high-density lipoprotein cholesterol measurement"),("disease","Non-HDL cholesterol levels")],
 "Apolipoprotein A1":[("efo","apolipoprotein A 1 measurement")],
 "Apolipoprotein B":[("efo","apolipoprotein B measurement")],
 "Lipoprotein A":[("efo","lipoprotein A measurement")],
 "Omega-3 fatty acids":[("disease","Omega-3 fatty acid levels")],
 "Omega-6 fatty acids":[("disease","Omega-6 fatty acid levels")],
 # ---- liver ----
 "Alanine aminotransferase":[("disease","Alanine aminotransferase levels")],
 "Aspartate aminotransferase":[("disease","Aspartate aminotransferase levels")],
 "Alkaline phosphatase":[("disease","Alkaline phosphatase levels")],
 "Gamma-glutamyltransferase":[("disease","Gamma glutamyl transferase levels")],
 "Total bilirubin":[("disease","Total bilirubin levels"),("disease","Bilirubin levels")],
 "Direct bilirubin":[("disease","Direct bilirubin levels")],
 "Liver fat percentage":[("disease","Liver fat percentage"),("efo","liver fat measurement")],
 "Albumin":[("disease","Serum albumin levels")],
 "Total protein":[("disease","Total protein levels")],
 # ---- renal ----
 "Creatinine":[("efo","creatinine measurement"),("disease","Creatinine levels")],
 "Cystatin C":[("efo","cystatin C measurement")],
 "Urea":[("efo","urea measurement")],
 "Urate":[("efo","urate measurement")],
 # ---- hormones / other biomarkers ----
 "CRP":[("efo","C-reactive protein measurement")],
 "IGF-1":[("efo","insulin-like growth factor 1 measurement"),("disease","Insulin-like growth factor 1 levels")],
 "SHBG":[("efo","sex hormone-binding globulin measurement")],
 "Testosterone":[("efo","testosterone measurement")],
 "Oestradiol":[("efo","estradiol measurement")],
 "Adiponectin":[("efo","adiponectin measurement")],
 "Leptin":[("efo","leptin measurement")],
 "Calcium":[("efo","serum calcium measurement"),("efo","calcium measurement")],
 "Phosphate":[("efo","phosphate measurement")],
 "Vitamin D":[("disease","Vitamin D levels")],
 "PAI-1":[("efo","plasminogen activator inhibitor 1 measurement")],
 "Renin":[("efo","renin measurement")],
 "TRAIL-R2":[("disease","TRAIL receptor 2 levels"),("efo","TNF-related apoptosis-inducing ligand receptor 2 measurement")],
 "Age at menarche":[("efo","age at menarche")],
 "Age at menopause":[("efo","age at menopause")],
 "Heel BMD":[("efo","heel bone mineral density")],
 # ---- blood counts ----
 "White blood cell count":[("disease","White blood cell count")],
 "Lymphocyte count":[("efo","lymphocyte count")],
 "Monocyte count":[("efo","monocyte count")],
 "Eosinophil count":[("efo","eosinophil count")],
 "Basophil count":[("efo","basophil count")],
 "Platelet count":[("efo","platelet count")],
 "Mean platelet volume":[("efo","mean platelet volume"),("disease","Mean platelet volume")],
 "Platelet distribution width":[("efo","platelet distribution width"),("disease","Platelet distribution width")],
 "Hemoglobin":[("efo","hemoglobin measurement")],
 "Red blood cell count":[("efo","erythrocyte count")],
 "Red cell distribution width":[("efo","erythrocyte distribution width"),("efo","red cell distribution width")],
 "Mean corpuscular volume":[("efo","mean corpuscular volume"),("disease","Mean corpuscular volume")],
 "Mean reticulocyte volume":[("efo","reticulocyte volume"),("efo","mean reticulocyte volume")],
 "High light scatter reticulocyte count":[("efo","high light scatter reticulocyte count"),("disease","High light scatter reticulocyte count")],
 # ---- diseases (Pascat가 matrix 열로 씀; Udler는 validation-only였음 - 관례 상이) ----
 "Type 2 diabetes":[("efo","type 2 diabetes mellitus")],
 "Coronary artery disease":[("efo","coronary artery disease"),("disease","Coronary artery disease")],
 "Atrial fibrillation":[("efo","atrial fibrillation")],
 "Heart failure":[("efo","heart failure")],
 "Stroke":[("efo","stroke"),("disease","Stroke")],
 "Small vessel stroke":[("efo","small vessel stroke")],
}

# ---------------------------------------------------------------------------
# 논문별 trait 목록 (canonical 이름; 위 CANDIDATES 키를 참조).
#   목록 자체는 extract_paper_traits.py 로 각 논문 supplementary에서 추출 -> 검토 후 여기 반영.
# ---------------------------------------------------------------------------
UDLER_2018 = ["Fasting glucose","Fasting insulin","HbA1c","Two-hour glucose","HOMA-B","HOMA-IR","Proinsulin","Corrected insulin response","Insulin sensitivity index","Disposition index","Modified Stumvoll ISI","Incr30/Ins30","BMI","Height","Waist circumference","Waist-hip ratio","Body fat percentage","Birth weight","Heart rate","Visceral adipose tissue volume","HDL cholesterol","LDL cholesterol","Total cholesterol","Triglycerides","Leptin","Adiponectin","Urate","Omega-3 fatty acids","Omega-6 fatty acids"]
SUZUKI_2024 = ["Fasting glucose","Two-hour glucose","HbA1c","Proinsulin","Fasting insulin","Modified Stumvoll ISI","Insulin fold change","Systolic blood pressure","Diastolic blood pressure","Pulse pressure","Birth weight","Basal metabolic rate","BMI","Waist-hip ratio","Waist circumference","Hip circumference","Body fat percentage","Trunk fat percentage","Gluteofemoral adipose tissue volume","Visceral adipose tissue volume","Abdominal subcutaneous adipose tissue volume","Alkaline phosphatase","Gamma-glutamyltransferase","Total bilirubin","Direct bilirubin","Aspartate aminotransferase","Alanine aminotransferase","Liver fat percentage","Triglycerides","LDL cholesterol","HDL cholesterol","Total cholesterol","Non-HDL cholesterol","Apolipoprotein A1","Apolipoprotein B","CRP","IGF-1"]
KIM_2023 = ["Two-hour glucose","Corrected insulin response","Disposition index","Fasting glucose","Fasting insulin","Proinsulin","HbA1c","HOMA-B","HOMA-IR","Modified Stumvoll ISI","Random glucose","BMI","Body fat percentage","Height","Diastolic blood pressure","Systolic blood pressure","Hip circumference","Waist circumference","Waist-hip ratio","Adiponectin","Leptin","Alanine aminotransferase","Aspartate aminotransferase","Alkaline phosphatase","Gamma-glutamyltransferase","Albumin","Total protein","Direct bilirubin","Total bilirubin","Apolipoprotein B","HDL cholesterol","Triglycerides","Lipoprotein A","CRP","IGF-1","SHBG","Testosterone","Calcium","Phosphate","Urea","Urate","Vitamin D","Hemoglobin","Red blood cell count","Red cell distribution width","Mean corpuscular volume","Mean reticulocyte volume","High light scatter reticulocyte count","White blood cell count","Lymphocyte count","Monocyte count","Eosinophil count","Basophil count","Platelet count","Mean platelet volume","Platelet distribution width"]
SMITH_2024 = ["Disposition index","Modified Stumvoll ISI","Proinsulin","HOMA-B","HOMA-IR","Corrected insulin response","Fasting glucose","Fasting insulin","Two-hour glucose","HbA1c","Random glucose","Height","Waist-hip ratio","BMI","Waist circumference","Hip circumference","Trunk fat percentage","Basal metabolic rate","Abdominal subcutaneous adipose tissue volume","Gluteofemoral adipose tissue volume","Visceral adipose tissue volume","Leptin","Adiponectin","Heart rate","Systolic blood pressure","Diastolic blood pressure","Total cholesterol","Triglycerides","Apolipoprotein A1","Lipoprotein A","Alanine aminotransferase","Aspartate aminotransferase","Gamma-glutamyltransferase","Alkaline phosphatase","Total bilirubin","Creatinine","Cystatin C","Urate","Urea","CRP","Basophil count","Eosinophil count","Hemoglobin","High light scatter reticulocyte count","Lymphocyte count","Mean corpuscular volume","Mean reticulocyte volume","Monocyte count","Platelet count","Platelet distribution width","Red blood cell count","Red cell distribution width","White blood cell count","SHBG","Testosterone","Oestradiol","IGF-1","Vitamin D","Albumin","Total protein","Calcium","Phosphate"]
PASCAT_2026 = ["Type 2 diabetes","Diastolic blood pressure","Systolic blood pressure","Pulse pressure","HbA1c","Random glucose","Two-hour glucose","Fasting insulin","Proinsulin","HOMA-IR","HOMA-B","Modified Stumvoll ISI","Insulin fold change","BMI","Waist-hip ratio","Height","Birth weight","HDL cholesterol","LDL cholesterol","Triglycerides","Testosterone","SHBG","Oestradiol","Age at menarche","Age at menopause","Adiponectin","Leptin","IGF-1","PAI-1","Renin","TRAIL-R2","White blood cell count","CRP","Alanine aminotransferase","Aspartate aminotransferase","Coronary artery disease","Atrial fibrillation","Heart failure","Stroke","Small vessel stroke","Heart rate","Heel BMD"]

PAPERS = {"Udler 2018":UDLER_2018, "Suzuki 2024":SUZUKI_2024,
          "Kim 2023":KIM_2023, "Smith 2024":SMITH_2024, "Pascat 2026":PASCAT_2026}

# ===========================================================================
def eur_count(kind, val, pages=PAGES_FOR_RECOVERY):
    """해당 라벨의 European-only GWAS 개수(앞 pages 페이지 하한). engine과 동일 판정."""
    ep={"disease":"findByDiseaseTrait","efo":"findByEfoTrait"}[kind]
    key={"disease":"diseaseTrait","efo":"efoTrait"}[kind]
    cnt=0
    for page in range(pages):
        j=requests.get(f"{BASE}/studies/search/{ep}",
                       params={key:val,"size":50,"page":page},timeout=60,headers=H).json()
        for s in j.get("_embedded",{}).get("studies",[]):
            if g.is_european_only(g.ancestry_text(s)): cnt+=1
        if page>=j.get("page",{}).get("totalPages",1)-1: break
    return cnt

def classify(trait):
    """후보를 순서대로 라이브 조회해 (category, 사용라벨, EUR수, 표준0여부)를 '코드가' 판정.
       first(표준) 회수 -> recovered / later 회수 -> label_mismatch / 전부 0 -> no_public_gwas.
       회수 후보가 broad 태그면 category에 '(broad)' 접미."""
    cands = CANDIDATES.get(trait)
    if not cands:
        return "NO_CANDIDATES", "", 0
    for i, cand in enumerate(cands):
        kind, label = cand[0], cand[1]
        broad = len(cand) > 2 and cand[2] == "broad"
        n = eur_count(kind, label)
        if n > 0:
            cat = "recovered" if i == 0 else "label_mismatch"
            if broad: cat += "(broad)"
            return cat, f"{kind}:{label}", n
    # 아무 후보도 회수 못 함
    k0, l0 = cands[0][0], cands[0][1]
    return "no_public_gwas", f"{k0}:{l0}", 0

def run():
    rows=[]
    for paper, traits in PAPERS.items():
        cc=Counter()
        print(f"\n===== {paper}: {len(traits)} traits =====")
        for trait in traits:
            cat, used, n = classify(trait)
            base = cat.split("(")[0]                  # recovered / label_mismatch / no_public_gwas
            cc[base]+=1
            if "(broad)" in cat: cc["broad"]+=1
            mark = "O" if base!="no_public_gwas" else "X"
            print(f"   {mark} {trait:44} [{cat:18}] {used:52} EUR>={n}")
            rows.append({"paper":paper,"trait":trait,"category":cat,
                         "resolved_query":used,"european_gwas":n})
        recovered = cc["recovered"]+cc["label_mismatch"]
        print(f"   => 회수 {recovered}/{len(traits)}  "
              f"(recovered {cc['recovered']} · label_mismatch {cc['label_mismatch']} · "
              f"no_public_gwas {cc['no_public_gwas']}; 이 중 broad {cc['broad']})")
    with open(g.outpath("t2d_trait_validation.csv"),"w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=["paper","trait","category","resolved_query","european_gwas"])
        w.writeheader(); w.writerows(rows)
    print(f"\n-> {g.outpath('t2d_trait_validation.csv')} 저장 (논문별 3분류 = 코드가 계산한 값)")

if __name__=="__main__":
    run()
