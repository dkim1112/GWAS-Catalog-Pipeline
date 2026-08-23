#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
udler2018_fallback.py — Udler 2018 재현 입력 중 원 배포처가 죽은 형질에 대해
GWAS Catalog 대체본이 있는지 '코드로' 판정.

배경:
  udler2018_inputs.py --probe 결과, 47개 열 중 22개의 원 배포 URL이 죽었거나
  응답이 불확실했다. 이 스크립트는 그 형질들을 GWAS Catalog에서 찾아
  (a) 원 논문과 동일한 study가 Catalog에 있는지 (PMID 대조)
  (b) 그 study에 전체 요약통계 파일이 있는지 (기존 sumstats_availability.probe 재사용)
  를 판정한다.

사람이 대는 입력: 아래 TARGETS의 형질 -> 검색어/원논문 PMID 매핑뿐.
  (원논문 식별자는 Udler S2 Table의 Reference 컬럼에서 온 것으로 '데이터'이지 판단이 아님.)
판정(대체 가능/불가)은 전부 코드가 계산한다.

실행: python src/udler2018_fallback.py
출력: outputs/udler2018_fallback.csv
"""
import os, sys, csv, time
import requests

sys.path.insert(0, os.path.dirname(__file__))
import sumstats_availability as SA

BASE = "https://www.ebi.ac.uk/gwas/rest/api"
H = {"Accept": "application/json"}
OUT = os.path.join(os.path.dirname(__file__), "..", "outputs")

# 형질 -> (Udler S2의 원 출처, 원논문 PMID, Catalog reported-trait 검색어들)
TARGETS = {
    "adip":       ("Adipogen (404)",   "22479202", ["Adiponectin levels"]),
    "urate":      ("GUGC (503)",       "23263486", ["Urate levels", "Serum urate levels"]),
    "vat":        ("VATGen (NHLBI)",   "28291232", ["Visceral adipose tissue adjusted for BMI",
                                                    "Visceral adipose tissue volume"]),
    "sat":        ("VATGen (NHLBI)",   "28291232", ["Subcutaneous adipose tissue",
                                                    "Subcutaneous adipose tissue adjusted for BMI"]),
    "vat_adjbmi": ("VATGen (NHLBI)",   "28291232", ["Visceral adipose tissue/subcutaneous adipose tissue ratio",
                                                    "Visceral adipose tissue adjusted for BMI"]),
    "bodyfat":    ("mssm (차단)",       "26833246", ["Body fat percentage"]),
    "leptin":     ("mssm (차단)",       "26833098", ["Leptin levels"]),
    "leptinbmi":  ("mssm (차단)",       "26833098", ["Leptin levels adjusted for BMI"]),
    # MAGIC은 403이 봇 차단으로 확인됨(페이지 정상). 그래도 Catalog 대체본 유무는 같이 본다.
    "fg":         ("MAGIC (403=차단)",  "", ["Fasting blood glucose"]),
    "fi":         ("MAGIC (403=차단)",  "", ["Fasting blood insulin"]),
    "hba1c":      ("MAGIC (403=차단)",  "", ["Glycated hemoglobin levels"]),
    "proins":     ("MAGIC (403=차단)",  "", ["Proinsulin levels"]),
    "fg2hr":      ("MAGIC (403=차단)",  "", ["Two-hour glucose challenge"]),
    "homab":      ("MAGIC (403=차단)",  "", ["HOMA-B"]),
    "homair":     ("MAGIC (403=차단)",  "", ["HOMA-IR"]),
    "isi":        ("MAGIC (403=차단)",  "", ["Insulin sensitivity index"]),
}


def studies_by_pmid(pmid):
    try:
        j = requests.get(f"{BASE}/studies/search/findByPublicationIdPubmedId",
                         params={"pubmedId": pmid, "size": 200},
                         headers=H, timeout=60).json()
        return j.get("_embedded", {}).get("studies", [])
    except Exception:
        return []


def studies_by_trait(q):
    try:
        j = requests.get(f"{BASE}/studies/search/findByDiseaseTrait",
                         params={"diseaseTrait": q, "size": 200},
                         headers=H, timeout=60).json()
        return j.get("_embedded", {}).get("studies", [])
    except Exception:
        return []


def is_european(st):
    try:
        return SA_is_eur(st)
    except Exception:
        txt = " ".join(
            a.get("initialSampleSize", "") or ""
            for a in (st.get("ancestries") or [])
        ) + " " + (st.get("initialSampleSize") or "")
        return "european" in txt.lower()


def SA_is_eur(st):
    import gwas_catalog_survey as g
    for fn in ("is_european", "european_only", "is_eur"):
        if hasattr(g, fn):
            return bool(getattr(g, fn)(st))
    raise AttributeError


def main():
    rows = []
    for key, (orig, pmid, queries) in TARGETS.items():
        found = []
        if pmid:
            found = studies_by_pmid(pmid)
        src = "pmid" if found else ""
        if not found:
            for q in queries:
                found = studies_by_trait(q)
                if found:
                    src = "trait:" + q
                    break
        if not found:
            rows.append({"column": key, "orig_source": orig, "match_by": "",
                         "accession": "", "reported_trait": "",
                         "verdict": "no_catalog_study", "build": "", "file": ""})
            print(f"{key:12s} {orig:20s} -> Catalog에 study 없음")
            continue

        best = None
        for st in found[:25]:
            acc = st.get("accessionId", "")
            if not acc:
                continue
            p = SA.probe(acc)
            time.sleep(0.15)
            rec = {"column": key, "orig_source": orig, "match_by": src,
                   "accession": acc,
                   "reported_trait": st.get("diseaseTrait", {}).get("trait", ""),
                   "verdict": p["verdict"], "build": p.get("build", ""),
                   "file": p.get("chosen", "")}
            rank = {"hg19_direct": 0, "hg38_liftover": 1,
                    "hg18_liftover": 2, "none": 3}.get(p["verdict"], 4)
            if best is None or rank < best[0]:
                best = (rank, rec)
            if rank == 0:
                break
        rows.append(best[1])
        b = best[1]
        print(f"{key:12s} {orig:20s} -> {b['accession']:12s} {b['verdict']:14s} {b['reported_trait'][:40]}")

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "udler2018_fallback.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["column", "orig_source", "match_by",
                                          "accession", "reported_trait",
                                          "verdict", "build", "file"])
        w.writeheader()
        w.writerows(rows)
    print("\nwrote", path)
    import collections
    print(dict(collections.Counter(r["verdict"] for r in rows)))


if __name__ == "__main__":
    main()
