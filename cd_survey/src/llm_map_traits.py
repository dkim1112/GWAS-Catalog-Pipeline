#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
llm_map_traits.py  -  '사람(=이전엔 LLM 어시스턴트)이 하던 두 단계'를 LLM API로 대체
================================================================================
배경:
  B2 검증에서 사람 손이 필요하다고 봤던 두 단계가 실은 'LLM이 하던 일'이었다:
    (1) 논문 부록/Methods/그림에서 '입력 trait 목록' 뽑기
    (2) 원 라벨(sex별/약어/철자 변형)을 우리 canonical 표현형으로 정규화하고,
        각 표현형의 GWAS Catalog '후보 라벨'(kind+label)을 제안하기
  이 둘은 사람이 꼭 해야 하는 게 아니라 LLM이 하던 것이므로 -> LLM API 호출로 자동화한다.
  단, LLM 제안은 '검증되어야' 한다. 그래서 이 스크립트는 제안 직후에
  gwas_catalog_survey.py의 European 판정 + GWAS Catalog 라이브 조회로 각 후보를 실제
  검증하고 3분류(recovered/label_mismatch/no_public_gwas)까지 붙여준다.

역할 분담(중요):
  - LLM이 하는 것 : 후보를 '제안'(창의적/퍼지 매핑). 절대 최종 판정이 아님.
  - 코드가 하는 것: 제안을 GWAS Catalog에 조회해 '판정'(결정적, 재현 가능).
  => 라벨을 잘못 제안해도 라이브 조회에서 0건이면 no_public_gwas로 자동 노출된다.

남는 안전 점검(코드로 못 잡는 것):
  라이브 조회는 '잘못된 라벨'은 잡지만 'trait을 통째로 빠뜨린 것'은 못 잡는다(목록에 없으면
  조회 자체를 안 하므로). 그래서 (1) 추출 목록 개수를 논문이 밝힌 N과 비교하고,
  (2) no_public_gwas / broad 로 뜬 것만 사람이 눈으로 한 번 확인하도록 리포트한다.

사용:
  export ANTHROPIC_API_KEY=...            # 본인 키
  export LLM_MODEL=claude-...(사용 가능한 모델 id)   # 미설정 시 아래 DEFAULT_MODEL
  # A) 원 라벨 CSV(extract_paper_traits.py 출력)로 후보 제안+검증:
  python llm_map_traits.py --from-csv outputs/paper_traits_extracted.csv --paper "Smith 2024"
  # B) 표가 아닌 논문(Methods/그림 텍스트 붙여넣기)에서 목록 추출:
  python llm_map_traits.py --from-text methods.txt --paper "Udler 2018" --expected 29
  출력: outputs/llm_candidates_<paper>.json + 콘솔 검증표 + 붙여넣기용 CANDIDATES 스니펫.

필요 패키지: requests  (anthropic SDK 있으면 사용, 없으면 REST 직접 호출)
================================================================================
"""
import os, sys, json, csv, argparse, requests
import gwas_catalog_survey as g   # European 판정 재사용(검증 = engine과 동일 로직)

BASE="https://www.ebi.ac.uk/gwas/rest/api"; H={"Accept":"application/json"}
DEFAULT_MODEL = os.environ.get("LLM_MODEL", "claude-sonnet-4-5")  # 본인 계정의 가용 모델로 교체
API_URL = "https://api.anthropic.com/v1/messages"

# ---------------------------------------------------------------------------
# LLM 호출 (anthropic SDK 있으면 사용, 없으면 REST). system+user -> 텍스트 반환.
# ---------------------------------------------------------------------------
def _call_llm(system, user, max_tokens=4000):
    key=os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY 미설정. 본인 키를 export 하세요.")
    try:
        import anthropic
        cl=anthropic.Anthropic(api_key=key)
        m=cl.messages.create(model=DEFAULT_MODEL, max_tokens=max_tokens,
                             system=system, messages=[{"role":"user","content":user}])
        return "".join(b.text for b in m.content if getattr(b,"type","")=="text")
    except ImportError:
        r=requests.post(API_URL, timeout=120, headers={
            "x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":DEFAULT_MODEL,"max_tokens":max_tokens,"system":system,
                  "messages":[{"role":"user","content":user}]})
        r.raise_for_status()
        return "".join(b.get("text","") for b in r.json().get("content",[]) if b.get("type")=="text")

def _json_from(text):
    """LLM 응답에서 JSON 블록만 안전 추출."""
    s=text.find("["); e=text.rfind("]")
    if s<0: s=text.find("{"); e=text.rfind("}")
    if s<0 or e<0: raise ValueError(f"JSON 파싱 실패: {text[:200]}")
    return json.loads(text[s:e+1])

# ---------------------------------------------------------------------------
# (1) 부록이 표가 아닐 때: Methods/그림 텍스트에서 입력 trait 목록 추출
# ---------------------------------------------------------------------------
EXTRACT_SYS = (
 "You extract the exact list of quantitative traits/phenotypes used as INPUT to a bNMF "
 "clustering matrix from a genetics paper's Methods/figure text. Return ONLY the input "
 "traits (matrix columns), NOT the output clusters and NOT validation-only outcomes. "
 "Do NOT invent traits; copy names as written. Output strict JSON: a list of strings.")
def extract_traits_from_text(text, expected_n=None):
    hint=f" The paper states there are {expected_n} input traits." if expected_n else ""
    out=_json_from(_call_llm(EXTRACT_SYS, f"Extract the input trait list.{hint}\n\nTEXT:\n{text}"))
    return [str(t).strip() for t in out if str(t).strip()]

# ---------------------------------------------------------------------------
# (2) 원 라벨 -> canonical 표현형 + GWAS Catalog 후보 라벨 제안
# ---------------------------------------------------------------------------
MAP_SYS = (
 "You map raw trait labels from a GWAS paper to (a) a canonical phenotype name and (b) an "
 "ORDERED list of candidate GWAS Catalog query labels to look them up. Collapse sex-stratified "
 "(_female/_male), adjBMI, and ratio variants to the underlying distinct phenotype. "
 "Each candidate is [kind, label] where kind is 'efo' (EFO trait label, e.g. 'body mass index', "
 "'creatinine measurement') or 'disease' (reported-trait string, e.g. 'Fasting glucose'). "
 "Put the MOST STANDARD label first. If the exact phenotype likely has no specific GWAS Catalog "
 "label and only a broader parent would match, add that broad candidate LAST as [kind, label, 'broad']. "
 "Do NOT invent labels you are unsure exist; it is fine to give 1-3 plausible candidates and let "
 "downstream code verify. Output strict JSON: a list of objects "
 '{"raw":..., "canonical":..., "candidates":[[kind,label],...], "note":...}.')
def propose_candidates(raw_traits):
    user="Map these raw trait labels:\n"+json.dumps(list(raw_traits), ensure_ascii=False)
    return _json_from(_call_llm(MAP_SYS, user, max_tokens=6000))

# ---------------------------------------------------------------------------
# 제안 검증: 각 후보를 GWAS Catalog에 라이브 조회 -> 3분류 (코드가 판정)
#   (validate_t2d_trait_axis.classify 와 동일 규칙. 순환 import 피하려 여기 자체 구현.)
# ---------------------------------------------------------------------------
def _eur_count(kind, val, pages=2):
    ep={"disease":"findByDiseaseTrait","efo":"findByEfoTrait"}[kind]
    key={"disease":"diseaseTrait","efo":"efoTrait"}[kind]
    cnt=0
    for page in range(pages):
        j=requests.get(f"{BASE}/studies/search/{ep}",params={key:val,"size":50,"page":page},
                       timeout=60,headers=H).json()
        for s in j.get("_embedded",{}).get("studies",[]):
            if g.is_european_only(g.ancestry_text(s)): cnt+=1
        if page>=j.get("page",{}).get("totalPages",1)-1: break
    return cnt

def verify(cands):
    """[[kind,label(,'broad')],...] -> (category, used, eur). engine 조회로 결정적 판정."""
    for i,c in enumerate(cands):
        kind,label=c[0],c[1]; broad=len(c)>2 and c[2]=="broad"
        n=_eur_count(kind,label)
        if n>0:
            cat="recovered" if i==0 else "label_mismatch"
            return (cat+"(broad)" if broad else cat), f"{kind}:{label}", n
    return "no_public_gwas", (f"{cands[0][0]}:{cands[0][1]}" if cands else ""), 0

def snippet(paper, results):
    """검증된 후보를 validate_t2d_trait_axis.py CANDIDATES/리스트에 붙여넣을 형태로 출력."""
    print(f"\n# --- 붙여넣기용: {paper} (검증 후 사람 검토) ---")
    print("# CANDIDATES 에 추가할 항목:")
    for r in results:
        cl=", ".join([f'("{c[0]}","{c[1]}"'+(',"broad")' if len(c)>2 else ")") for c in r["candidates"]])
        print(f'  "{r["canonical"]}":[{cl}],   # {r["category"]}')
    names=", ".join(f'"{r["canonical"]}"' for r in results)
    var=paper.upper().replace(" ","_").replace("-","_")
    print(f"\n{var} = [{names}]")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--from-csv"); ap.add_argument("--from-text"); ap.add_argument("--paper", required=True)
    ap.add_argument("--expected", type=int, default=None); a=ap.parse_args()

    if a.from_text:
        raw=extract_traits_from_text(open(a.from_text, encoding="utf-8").read(), a.expected)
        print(f"[추출] {a.paper}: {len(raw)}개" + (f" (기대 {a.expected})" if a.expected else ""))
        if a.expected and len(raw)!=a.expected:
            print(f"  ! 개수 불일치 -> 목록 누락/중복 가능. 사람 확인 필요.")
    elif a.from_csv:
        raw=[row["raw_trait"] for row in csv.DictReader(open(a.from_csv, encoding="utf-8-sig"))
             if row.get("paper")==a.paper and row.get("raw_trait","").strip()]
        print(f"[로드] {a.paper}: 원 라벨 {len(raw)}개")
    else:
        print("--from-csv 또는 --from-text 필요"); return

    proposals=propose_candidates(raw)
    results=[]
    print(f"\n[LLM 제안 -> 코드 검증] {a.paper}")
    for p in proposals:
        cat, used, n = verify(p.get("candidates",[]))
        p["category"]=cat; p["resolved"]=used; p["european_gwas"]=n; results.append(p)
        mark="O" if "no_public_gwas" not in cat else "X"
        print(f"   {mark} {p.get('canonical','?'):42} [{cat:18}] {used:48} EUR>={n}")
    flags=[r for r in results if "no_public_gwas" in r["category"] or "broad" in r["category"]]
    print(f"\n   => 검증 {sum('no_public_gwas' not in r['category'] for r in results)}/{len(results)}; "
          f"사람 확인 권장(부재/broad): {[r['canonical'] for r in flags]}")
    outp=os.path.join(g.OUT_DIR, f"llm_candidates_{a.paper.replace(' ','_')}.json") if hasattr(g,"OUT_DIR") \
         else f"llm_candidates_{a.paper.replace(' ','_')}.json"
    json.dump(results, open(outp,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"   -> {outp} 저장")
    snippet(a.paper, results)

if __name__=="__main__":
    main()
