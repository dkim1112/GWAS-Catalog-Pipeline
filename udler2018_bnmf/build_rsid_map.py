#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_rsid_map.py — 파이프라인이 요구하는 rsID <-> hg19 위치 맵 생성.

출력: rsid_maps_by_chr/chr{N}.txt   (1~22)
      헤더 없음, 탭 구분, 컬럼 4개
      hg19_posID(=chrN:POS) \t rsID \t ref_allele \t alt_allele
      choose_variants_2025.R:993~994 의 col.names 와 일치.

소스: dbSNP build 151, GRCh37p13, common 세트 (00-common_all.vcf.gz, 1.6GB)
      https://ftp.ncbi.nlm.nih.gov/snp/organisms/human_9606_b151_GRCh37p13/VCF/
      sites-only(유전형 컬럼 없음) + rsID 보유 + GRCh37 좌표.
      common = 1000G 에서 MAF>=1% 인 변이 -> LD proxy 탐색 대상과 같은 모집단.

  왜 이 파일인가 (시행착오 기록):
  * repo 의 generate_varid_to_rsid_map_file.R 은 Ensembl GRCh37 'variation' VCF 를
    받는데 그건 1000G 가 아니라 dbSNP 전체다. chr1 만 8,370만 변이 -> 출력 2GB,
    22개면 40GB 라 현실적이지 않았다.
  * 1000G 의 sites-only 파일(ALL.wgs...v5c...sites.vcf.gz, 1.46GB)은 가볍지만
    ID 컬럼이 전부 '.' 이라 rsID 가 없다. 쓸 수 없다.
  * 1000G 에서 rsID 가 있는 건 염색체별 genotypes VCF 뿐인데, 2504명 유전형이
    붙어 있어 압축을 풀면 염색체당 수십 GB 라 파싱이 현실적이지 않았다.
  * dbSNP common 세트가 세 조건(rsID / GRCh37 / 유전형 없음)을 모두 만족한다.

필터 (원본 R 에서 한 가지 바꿈):
  ID 가 rs 로 시작 / REF·ALT 모두 1염기 / A,C,G,T
  * 원본 R 은 ALT 에 쉼표가 있으면(다중 대립) 그 변이를 버린다. 1000G 에서는
    드물지만 dbSNP 에서는 흔해서, 그대로 두면 rs7903146(TCF7L2) 같은 핵심 변이가
    사라진다. 실제로 Udler 94개 중 13개가 이 필터에 걸렸다.
    그래서 ALT 를 쪼개 대립유전자마다 한 줄씩 내보낸다.
  위치 중복 제거는 스트리밍(VCF 가 POS 정렬이므로 직전 위치와만 비교).
  * 원본 R 은 rsID 중복도 제거하지만 메모리 때문에 생략했다. 한 염색체 안에서
    같은 rsID 가 다른 위치에 두 번 나오는 경우는 드물다.

사용법:
  python3 build_rsid_map.py              # 없는 염색체만 이어서
  python3 build_rsid_map.py --jobs 4     # 동시 다운로드 수 (기본 4)
  python3 build_rsid_map.py 21 22        # 특정 염색체만
"""
import os, sys, gzip, io, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "rsid_maps_by_chr")
URL = ("https://ftp.ncbi.nlm.nih.gov/snp/organisms/human_9606_b151_GRCh37p13/"
       "VCF/00-common_all.vcf.gz")
ACGT = {"A", "C", "G", "T"}


CHROMS = [str(i) for i in range(1, 23)]


def build_all():
    """dbSNP common VCF 를 스트리밍하며 염색체별로 갈라 쓴다."""
    handles = {c: open(os.path.join(OUT, f"chr{c}.txt.part"), "w", buffering=1 << 20)
               for c in CHROMS}
    counts = {c: 0 for c in CHROMS}
    prev = {c: None for c in CHROMS}
    n_in = 0
    t = time.time()
    # 스트리밍은 중간에 끊기면(EOFError) 처음부터 다시 해야 해서,
    # 디스크에 먼저 받고(curl 이어받기) 파싱한다.
    tmpdir = os.path.join(HERE, "_vcf_tmp"); os.makedirs(tmpdir, exist_ok=True)
    vcf = os.path.join(tmpdir, "dbsnp_common_grch37.vcf.gz")
    if not (os.path.exists(vcf) and os.path.getsize(vcf) > 1_500_000_000):
        print("[get ] " + URL, flush=True)
        rc = os.system(f'curl -fSL -C - --retry 8 --retry-delay 5 --retry-all-errors '
                       f'-o "{vcf}" "{URL}"')
        if rc != 0:
            raise RuntimeError(f"다운로드 실패 (curl rc={rc})")
        print(f"       {os.path.getsize(vcf)/1e9:.2f} GB", flush=True)
    with gzip.open(vcf, "rt", errors="replace") as f:
        for line in f:
            if line[0] == "#":
                continue
            n_in += 1
            if n_in % 5_000_000 == 0:
                print(f"  {n_in:,}행 처리, 출력 {sum(counts.values()):,} ({time.time()-t:.0f}s)",
                      flush=True)
            p = line.split("\t", 5)
            if len(p) < 5:
                continue
            c, pos, vid, ref, alt = p[0], p[1], p[2], p[3], p[4]
            h = handles.get(c)
            if h is None:
                continue
            if vid[:2] != "rs":
                continue
            if len(ref) != 1 or ref not in ACGT:
                continue
            # dbSNP 는 한 위치의 여러 대립유전자를 "T,G" 처럼 합쳐 적는다.
            # 원본 R 은 쉼표가 있으면 통째로 버리는데(1000G 기준), dbSNP 에서는
            # rs7903146(TCF7L2) 같은 핵심 변이가 그렇게 사라진다.
            # 그래서 쪼개서 ALT 마다 한 줄씩 낸다.
            alts = [a for a in alt.split(",") if len(a) == 1 and a in ACGT]
            if not alts:
                continue
            if pos == prev[c]:
                continue
            prev[c] = pos
            for a in alts:
                h.write(f"chr{c}:{pos}\t{vid}\t{ref}\t{a}\n")
                counts[c] += 1
    for c, h in handles.items():
        h.close()
        os.replace(os.path.join(OUT, f"chr{c}.txt.part"),
                   os.path.join(OUT, f"chr{c}.txt"))
    print(f"[done] 입력 {n_in:,}행 -> 출력 {sum(counts.values()):,}변이 "
          f"({time.time()-t:.0f}s)", flush=True)
    if "--keep-vcf" not in sys.argv:
        os.remove(vcf)
    return counts


def main():
    os.makedirs(OUT, exist_ok=True)
    print(f"소스: {URL}", flush=True)
    build_all()
    print("\n결과:", flush=True)
    total = 0
    for c in [str(i) for i in range(1, 23)]:
        p = os.path.join(OUT, f"chr{c}.txt")
        if os.path.exists(p):
            sz = os.path.getsize(p) / 1e6
            total += sz
            print(f"  chr{c:<3s} {sz:8.1f} MB")
        else:
            print(f"  chr{c:<3s} 없음")
    print(f"  합계 {total/1000:.2f} GB")


if __name__ == "__main__":
    main()
