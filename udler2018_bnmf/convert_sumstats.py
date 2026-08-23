#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_sumstats.py — 내려받은 원본 요약통계를 파이프라인 포맷으로 변환.

파이프라인 요구 포맷 (README + prep_bNMF_2025.R):
    VAR_ID            CHR_POS_REF_ALT (hg19, 염색체는 숫자)
    Effect_Allele_PH  효과 대립유전자
    BETA, SE          (형질 파일은 OR->BETA 변환 경로가 없으므로 필수)
    P_VALUE
    N_PH              표본수 (없으면 매니페스트의 sample_size 사용)

원본이 세 부류라 각각 다르게 처리한다.

  (a) Catalog harmonised  (*.h.tsv.gz)
      hm_variant_id 가 이미 CHR_POS_REF_ALT 이지만 좌표가 **hg38**.
      hm_rsid 로 rsID 맵을 조회해 hg19 좌표/REF/ALT 로 다시 만든다.

  (b) Catalog 원저자 제출본 (*.f.tsv.gz)
      chromosome + base_pair_location 이 hg19 이지만 어느 쪽이 REF 인지 표시가 없다.
      variant_id(rsID) 로 맵을 조회해 REF/ALT 를 확정한다.

  (c) GIANT (*.txt / tar 해제본)
      MarkerName 이 rsID 뿐이고 대부분 좌표가 아예 없다.
      맵 조회로 좌표와 REF/ALT 를 모두 채운다.

세 경우 모두 rsID 맵이 있어야 한다 -> build_rsid_map.py 를 먼저 돌릴 것.
맵은 sqlite 로 색인해서 쓴다 (8천만 행을 파이썬 dict 로 들면 메모리가 터진다).

특수 처리
  * z 만 있고 BETA/SE 가 없는 파일(VATGen 계열): z = BETA/SE 이므로
    BETA=z, SE=1 로 넣으면 z 가 그대로 보존된다. 로그에 남긴다.
  * GIANT 파일은 확장자가 .gz 이지만 실제로는 tar.gz 인 경우가 있어 자동 판별한다.

사용법
  python3 convert_sumstats.py --index      # 맵을 sqlite 로 색인 (1회, 수 분)
  python3 convert_sumstats.py              # sumstats/ -> sumstats_converted/
  python3 convert_sumstats.py fg bmi       # 특정 열만
"""
import os, sys, gzip, csv, sqlite3, tarfile, io, time, glob, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
MAPD = os.path.join(HERE, "rsid_maps_by_chr")
DB   = os.path.join(HERE, "_rsid_map.sqlite")
SRC  = os.path.join(HERE, "sumstats")
DST  = os.path.join(HERE, "sumstats_converted")
MAN  = os.path.join(HERE, "inputs_manifest.csv")

OUT_COLS = ["VAR_ID", "Effect_Allele_PH", "BETA", "SE", "P_VALUE", "N_PH"]


# --------------------------------------------------------------------------
# rsID 맵 -> sqlite
# --------------------------------------------------------------------------
def build_index():
    if os.path.exists(DB):
        os.remove(DB)
    files = sorted(glob.glob(os.path.join(MAPD, "chr*.txt")))
    if not files:
        sys.exit(f"{MAPD} 에 chr*.txt 가 없습니다. build_rsid_map.py 를 먼저 돌리세요.")
    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("CREATE TABLE m (rsid TEXT, chr TEXT, pos TEXT, ref TEXT, alt TEXT)")
    t = time.time(); n = 0
    for fp in files:
        chrom = os.path.basename(fp)[3:-4]
        rows = []
        with open(fp) as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) < 4:
                    continue
                pos = p[0].split(":")[1]
                rows.append((p[1], chrom, pos, p[2], p[3]))
                if len(rows) >= 200_000:
                    con.executemany("INSERT INTO m VALUES (?,?,?,?,?)", rows)
                    n += len(rows); rows = []
        if rows:
            con.executemany("INSERT INTO m VALUES (?,?,?,?,?)", rows)
            n += len(rows)
        con.commit()
        print(f"  {os.path.basename(fp)}  누적 {n:,}", flush=True)
    print("색인 생성 중...", flush=True)
    con.execute("CREATE INDEX i_rsid ON m(rsid)")
    con.commit(); con.close()
    print(f"완료: {n:,}행, {time.time()-t:.0f}s, {os.path.getsize(DB)/1e9:.2f} GB", flush=True)


def lookup_many(con, rsids):
    """rsID 목록 -> {rsid: (chr,pos,ref,alt)}"""
    out = {}
    rs = list(rsids)
    for i in range(0, len(rs), 900):
        chunk = rs[i:i + 900]
        q = "SELECT rsid,chr,pos,ref,alt FROM m WHERE rsid IN (%s)" % ",".join("?" * len(chunk))
        for r in con.execute(q, chunk):
            out[r[0]] = (r[1], r[2], r[3], r[4])
    return out


# --------------------------------------------------------------------------
# 원본 읽기 (tar.gz 위장 포함)
# --------------------------------------------------------------------------
def open_text(path):
    with open(path, "rb") as f:
        magic = f.read(2)
    if magic == b"\x1f\x8b":
        try:                       # tar.gz 인지 확인
            tf = tarfile.open(path, "r:gz")
            m = next((x for x in tf.getmembers()
                      if x.isfile() and not os.path.basename(x.name).startswith("._")
                      and not x.name.startswith("PaxHeader")), None)
            if m:
                return io.TextIOWrapper(tf.extractfile(m), errors="replace")
        except tarfile.ReadError:
            pass
        return gzip.open(path, "rt", errors="replace")
    return open(path, "rt", errors="replace")


def sniff(cols):
    s = {c.lower() for c in cols}
    if "hm_variant_id" in s:
        return "harmonised"
    if "base_pair_location" in s and "variant_id" in s:
        return "author"
    if s & {"markername", "snp"}:
        return "giant"
    return "generic"        # rsID/effect allele/P 만 찾을 수 있으면 진행한다


def pick(cols, names):
    """대소문자 무관 매칭. 원본 파일마다 표기가 제각각이다
    (snp / SNP / RSID / rsid, effect / beta / b, stderr / se / SE ...)."""
    low = {c.lower(): c for c in cols}
    for n in names:
        if n in cols:
            return n
        if n.lower() in low:
            return low[n.lower()]
    return None


# --------------------------------------------------------------------------
def convert(key, path, n_manifest, con, log):
    kind = None
    with open_text(path) as f:
        rd = csv.reader(f, delimiter="\t")
        hdr = next(rd)
        if len(hdr) < 3:
            f.seek(0)
            rd = csv.reader(f, delimiter=" ", skipinitialspace=True)
            hdr = next(rd)
        kind = sniff(hdr)

        c_rs = pick(hdr, ["hm_rsid", "variant_id", "MarkerName", "SNP", "rsid", "RSID",
                          "snpid", "snp"])
        c_ea = pick(hdr, ["hm_effect_allele", "effect_allele", "Allele1", "A1", "EA",
                          "RISK_ALLELE", "Tested_Allele"])
        c_b  = pick(hdr, ["hm_beta", "beta", "BETA", "b", "Effect", "effect"])
        c_se = pick(hdr, ["standard_error", "se", "SE", "StdErr", "stderr", "StdErrLogOR"])
        c_p  = pick(hdr, ["p_value", "P-value", "P_VALUE", "pvalue", "p", "P", "pval",
                          "Pvalue", "P.value"])
        c_n  = pick(hdr, ["n", "N", "N_PH"])
        c_z  = pick(hdr, ["z", "Z"])
        # 질병 GWAS 는 BETA/SE 없이 OR + 95% CI 만 있는 경우가 있다(DIAGRAMv3).
        c_or = pick(hdr, ["ODDS_RATIO", "OR", "odds_ratio"])
        c_lo = pick(hdr, ["OR_95L", "ci_lower", "hm_ci_lower", "L95"])
        c_hi = pick(hdr, ["OR_95U", "ci_upper", "hm_ci_upper", "U95"])
        c_nc = pick(hdr, ["N_CASES"]); c_nk = pick(hdr, ["N_CONTROLS"])
        idx  = {c: hdr.index(c) for c in
                [c_rs, c_ea, c_b, c_se, c_p, c_n, c_z, c_or, c_lo, c_hi, c_nc, c_nk] if c}

        use_or = (c_b is None or c_se is None) and c_or is not None and c_lo and c_hi
        if use_or:
            log(f"  ~  {key}: BETA/SE 없음 -> OR 과 95% CI 로 유도 "
                f"(BETA=log(OR), SE=(log(U95)-log(L95))/3.92)")

        # BETA/SE 컬럼이 '있어도' 값이 전부 NA 인 파일이 있다(VATGen 계열: 실제 값은 z 에만).
        # 헤더만 보고 정하면 전 행이 NA 로 걸려 0행이 되므로, 앞부분을 표본으로 확인한다.
        use_z = (c_b is None or c_se is None) and c_z is not None
        if not use_z and c_z is not None and c_b is not None and c_se is not None:
            NA = ("", "NA", "NaN", ".")
            sample, bad = 0, 0
            probe_rows = []
            for r in rd:
                if len(r) <= max(idx.values()):
                    continue
                probe_rows.append(r)
                sample += 1
                if r[idx[c_b]] in NA or r[idx[c_se]] in NA:
                    bad += 1
                if sample >= 1000:
                    break
            if sample and bad / sample > 0.9:
                use_z = True
                log(f"  ~  {key}: BETA/SE 컬럼은 있으나 표본 {sample}행 중 {bad}행이 NA "
                    f"-> z 로 대체")
            rd = itertools.chain(probe_rows, rd)
        if use_z:
            log(f"  ~  {key}: z 사용 (BETA=z, SE=1) — z 값이 그대로 보존됩니다")
        if c_rs is None or c_ea is None or c_p is None:
            log(f"  !! {key}: 필수 컬럼 부족 (rs={c_rs} ea={c_ea} p={c_p})")
            return 0, 0

        # 청크 단위 처리. 파일 전체를 메모리에 올리면 1천만 행짜리에서 터진다.
        os.makedirs(DST, exist_ok=True)
        out = os.path.join(DST, f"{key}.tsv.gz")
        n_ok = n_drop = 0
        CH = 200_000
        buf = []

        def flush(buf, w):
            nonlocal n_ok, n_drop
            rs_set = {r[idx[c_rs]] for r in buf if r[idx[c_rs]][:2] == "rs"}
            m = lookup_many(con, rs_set)
            for r in buf:
                hit = m.get(r[idx[c_rs]])
                if not hit:
                    n_drop += 1; continue
                ch, pos, ref, alt = hit
                ea = r[idx[c_ea]].upper()
                if ea not in (ref, alt):
                    n_drop += 1; continue
                if use_or:
                    try:
                        import math
                        o, lo, hi = (float(r[idx[c_or]]), float(r[idx[c_lo]]),
                                     float(r[idx[c_hi]]))
                        if o <= 0 or lo <= 0 or hi <= 0:
                            raise ValueError
                        beta = f"{math.log(o):.6g}"
                        se = f"{(math.log(hi) - math.log(lo)) / 3.919928:.6g}"
                    except Exception:
                        n_drop += 1; continue
                elif use_z:
                    z = r[idx[c_z]]
                    if z in ("", "NA", "NaN"):
                        n_drop += 1; continue
                    beta, se = z, "1"
                else:
                    beta, se = r[idx[c_b]], r[idx[c_se]]
                    if beta in ("", "NA", "NaN") or se in ("", "NA", "NaN"):
                        n_drop += 1; continue
                if c_n:
                    nph = r[idx[c_n]]
                elif c_nc and c_nk:
                    try: nph = str(int(float(r[idx[c_nc]])) + int(float(r[idx[c_nk]])))
                    except Exception: nph = ""
                else:
                    nph = n_manifest or ""
                w.writerow([f"{ch}_{pos}_{ref}_{alt}", ea, beta, se, r[idx[c_p]], nph])
                n_ok += 1

        mx = max(idx.values())
        with gzip.open(out, "wt", newline="") as o:
            w = csv.writer(o, delimiter="\t")
            w.writerow(OUT_COLS)
            for r in rd:
                if len(r) <= mx:
                    continue
                buf.append(r)
                if len(buf) >= CH:
                    flush(buf, w); buf = []
            if buf:
                flush(buf, w)

    log(f"  OK {key:12s} [{kind:10s}] {n_ok:,}행 변환 / {n_drop:,}행 제외 -> {os.path.basename(out)}")
    return n_ok, n_drop


def main():
    if "--index" in sys.argv:
        build_index(); return
    if not os.path.exists(DB):
        sys.exit("색인이 없습니다. 먼저:  python3 convert_sumstats.py --index")

    man = {r["key"]: r for r in csv.DictReader(open(MAN))}
    want = [a for a in sys.argv[1:] if not a.startswith("-")]
    con = sqlite3.connect(DB)
    lines = []
    def log(s):
        print(s, flush=True); lines.append(s)

    files = sorted(glob.glob(os.path.join(SRC, "*")))
    done = 0
    for fp in files:
        base = os.path.basename(fp)
        if base.startswith("."):
            continue
        key = base.split(".")[0]
        if want and key not in want:
            continue
        if key not in man:
            log(f"  ?? {key}: 매니페스트에 없음, 건너뜀"); continue
        try:
            convert(key, fp, "", con, log)
            done += 1
        except Exception as e:
            log(f"  !! {key}: {type(e).__name__}: {e}")
    log(f"\n{done}개 파일 처리")
    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    with open(os.path.join(HERE, "logs", "convert.log"), "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
