# =============================================================================
# run_pipeline.R — Udler 2018 T2D bNMF 재현 파이프라인 실행 드라이버
# =============================================================================
# 현재 설정: udler2018_eur_v2 (44 trait). version 은 scripts/main_script_example.R
# 에서 정하고, 산출물은 전부 results/<version>/ 안에 모인다.
# 실행 경로
#   Section 0-1        main_script_example.R 의 해당 구간
#   Section 2-3-4.1    scripts/udler_substitute.R 로 대체
#                      (Udler 94개 변이를 그대로 사용 — 변이 선택 모듈은 이번에
#                       검증 대상이 아님. 목표는 bNMF clustering 자체의 검증.)
#   Section 4.2-13     main_script_example.R 의 해당 구간
#   Section 14 (post-hoc, hg38 liftover) 는 제외 — 이 재현에 불필요.
#
# 구간은 행 번호가 아니라 섹션 주석(앵커)으로 찾는다. 예전 버전은 행 번호를
# 박아둬서 main_script_example.R 을 한 줄만 고쳐도 조용히 어긋났다.
#
# 사용:  cd <프로젝트 루트> && Rscript run_pipeline.R
# =============================================================================

# 스크립트 위치를 프로젝트 루트로 잡는다 (Rscript / source() 양쪽 지원).
.proj_root <- local({
  a <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", a[grep("^--file=", a)])
  if (length(f)) dirname(normalizePath(f[1])) else getwd()
})
setwd(.proj_root)
options(warn = 1)                       # 경고를 그때그때 출력
SRC <- readLines("scripts/main_script_example.R")

# --- 섹션 앵커 찾기 -----------------------------------------------------------
# 각 섹션 헤더는  "# ====="  /  "# <번호>. <제목>"  /  "# ====="  3줄 형태.
sec_line <- function(n, title) {
  hit <- grep(sprintf("^# %s\\. %s", n, title), SRC)
  if (length(hit) != 1L) stop(sprintf("Section %s (%s) 앵커를 %d개 찾음 — main_script_example.R 확인",
                                      n, title, length(hit)))
  hit - 1L                                  # 위의 "# =====" 줄
}
line_of <- function(pattern) {
  hit <- grep(pattern, SRC)
  if (length(hit) != 1L) stop(sprintf("앵커 '%s' 를 %d개 찾음", pattern, length(hit)))
  hit
}

S2   <- sec_line(2, "Variant Selection")     # Section 2 시작
S4_2 <- line_of("^# 4\\.2 Single fetch across all traits")
S7   <- sec_line(7, "Proxy Search")
S8   <- sec_line(8, "Final Variant Assembly")
S14  <- line_of("^# ====================$")  # Section 13 뒤, post-hoc 구간 시작

run_chunk <- function(a, b, label) {
  message("\n################################################################")
  message("## ", label, "   (main_script_example.R ", a, "-", b, "행)")
  message("## ", format(Sys.time(), "%Y-%m-%d %H:%M:%S"))
  message("################################################################\n")
  tf <- tempfile(fileext = ".R")
  writeLines(SRC[a:b], tf)
  source(tf, echo = FALSE, local = FALSE)
  unlink(tf)
}

banner <- function(...) {
  message("\n---- ", paste0(...), " ----")
}

t0 <- Sys.time()

# -----------------------------------------------------------------------------
run_chunk(1, S2 - 1, "Section 0-1: Setup & Manifest")

banner("점검: 매니페스트")
message("  version      : ", version)
message("  trait 수     : ", nrow(gwas_traits), "   (기대값 44)")
message("  main GWAS    : ", main_ss_filepath)
stopifnot(nrow(gwas_traits) == 44)
miss <- trait_ss_files[!file.exists(trait_ss_files)]
if (length(miss)) stop("요약통계 파일 없음: ", paste(names(miss), collapse = ", "))
message("  파일 44개 전부 존재 OK")
message("  결과 폴더    : ", main_dir)

# -----------------------------------------------------------------------------
message("\n################################################################")
message("## Section 2-3-4.1 대체: udler_substitute.R")
message("################################################################\n")
source(file.path(scripts_dir, "udler_substitute.R"), echo = FALSE, local = FALSE)

banner("점검: 변이 집합")
message("  pruned_vars  : ", nrow(pruned_vars), "   (기대값 94)")
message("  fetch_input  : ", nrow(fetch_input))
stopifnot(nrow(pruned_vars) == 94)

# TOPMed 미사용 — Section 5 가 참조하기 전에 NULL 로 확정
topmed_fails       <- NULL
topmed_present_snps <- NULL

save.image(file = df_save)

# -----------------------------------------------------------------------------
run_chunk(S4_2, S7 - 1, "Section 4.2-6: Fetch -> Missingness -> Proxy 판정")

# -----------------------------------------------------------------------------
# Section 7 (프록시 탐색) 을 건너뛴다 — 의도적 결정.
#
# 왜: 프록시는 결측이 심한 변이를 근처 LD 파트너로 "갈아끼우는" 단계다.
#     (1) 지금 목표는 bNMF clustering 검증이고 프록시 모듈 검증이 아니다.
#     (2) 갈아끼우면 최종 변이가 Udler 변이가 아니게 되어 S3 정답지와의
#         변이 1:1 대조가 깨진다. "Udler 94개를 그대로 쓴다"는 방침에 어긋난다.
#     (3) 애초에 이 경로는 지금 구조에서 작동할 수 없다. udler_substitute.R 이
#         fetch_input 을 sentinel 94개로만 두어 z 행렬에 프록시 후보 위치가
#         없기 때문 ("0 of 7157 potential proxies in the full z-matrix").
#
# 대가: 프록시 대상 23개는 z 값 상당수가 실측이 아니라 Section 11 의
#       softImpute 대치값이 된다. 그 변이들의 클러스터 기여 정보는 약하다.
banner("Section 7 건너뜀 — 94개 전부 original 로 유지")
message("  프록시 대상으로 판정된 변이 : ", nrow(proxies_needed), " (갈아끼우지 않고 그대로 사용)")

proxies_needed_diag <- proxies_needed              # 진단용 보존
proxies_needed      <- proxies_needed_diag[0, , drop = FALSE]
all_need_proxies    <- proxies_needed_diag[0, , drop = FALSE]
if (!"VAR_ID" %in% names(all_need_proxies)) all_need_proxies$VAR_ID <- character(0)
final_proxy_results <- list(character(0), NULL)

# -----------------------------------------------------------------------------
run_chunk(S8, S14 - 1, "Section 8-13: Assembly -> Align -> Impute -> bNMF")

# -----------------------------------------------------------------------------
banner("최종 요약")
message("  변이 경로    : pruned ", nrow(pruned_vars),
        " -> df_final ", nrow(df_final),
        " -> GWAS align ", nrow(gwas_final_filtered),
        " -> bNMF ", nrow(final_zscore_matrix))
message("  최종 z 행렬  : ", nrow(final_zscore_matrix), " SNPs x ",
        ncol(final_zscore_matrix) / 2, " traits (feature ",
        ncol(final_zscore_matrix), ")")
message("  결과 폴더    : ", main_dir)
message("  총 소요      : ", round(difftime(Sys.time(), t0, units = "mins"), 1), " 분")

k_tab <- table(read.delim(file.path(main_dir, "run_summary.txt"))$K)
message("  ARD K 분포   : ",
        paste(sprintf("K=%s:%d", names(k_tab), as.integer(k_tab)), collapse = "  "))

message("\n=== run_pipeline.R 완료 ", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), " ===")
