# =============================================================================
# udler_substitute.R — Section 2-3-4.1 substitute
# =============================================================================
# 왜 필요?
#   DIAGRAM v3 Stage 1 (Morris 2012) 만으로는 Section 2 클럼핑이 15개 변이로
#   끝남 (Udler 94 대비 턱없이 부족). Udler 2018 은 여러 T2D GWAS 큐레이션으로
#   94개를 만들었으므로, 재현하려면 그 리스트를 직접 로드해야 함.
#
#   또 하나: fetch_summary_stats() 는 primary GWAS 파일을 SNP(=Chr:Pos) 컬럼으로
#   grep 하는데, 우리 변환된 DIAGRAM 파일은 VAR_ID(=CHR_POS_REF_ALT) 만 있어
#   grep 매치가 안 됨. 그래서 primary GWAS 를 R 안에서 미리 로드하고 SNP/REF/ALT
#   컬럼을 파생시켜 데이터프레임으로 넘김.
#
# 사용:
#   Section 0-1 (main_script_example.R line 34~152) 실행 후 source() 한다.
#   실행 결과: pruned_vars / vars_noHLA / fetch_input / main_gwas_ready 준비 완료.
#   이후 main_script_example.R 의 Section 4.2 (fetch_summary_stats 호출) 로 진행.
# =============================================================================

message("=== udler_substitute.R: replacing Section 2-3-4.1 ===")

# --- 1. Load Udler 94 curated variants ---
udler_gold_path <- file.path(working_dir, "refs/udler2018_variants.csv")
if (!file.exists(udler_gold_path)) stop("refs/udler2018_variants.csv not found under: ", working_dir)
udler_gold <- read.csv(udler_gold_path, stringsAsFactors = FALSE)

pruned_vars <- udler_gold %>%
  tidyr::separate(VAR_ID,
                  into    = c("CHR", "POS", "REF", "ALT"),
                  sep     = "_",
                  remove  = FALSE,
                  convert = FALSE) %>%
  mutate(
    CHR        = as.integer(CHR),
    POS        = as.integer(POS),
    ChrPos     = paste(CHR, POS, sep = ":"),
    RS_Number  = rsID,
    PVALUE     = NA_real_,             # 아래에서 DIAGRAM P로 채움
    GWAS       = "DIAGRAMv3_T2D_EUR",
    Population = "EUR"
  ) %>%
  select(VAR_ID, ChrPos, CHR, POS, REF, ALT, RS_Number, Risk_Allele,
         PVALUE, GWAS, Population)

message(sprintf("Loaded %d Udler 2018 curated variants.", nrow(pruned_vars)))

# --- 2. Load primary GWAS (DIAGRAM v3), derive SNP/REF/ALT columns ---
message("Loading primary GWAS (DIAGRAM v3) into memory and deriving SNP/REF/ALT ...")
main_gwas_df <- data.table::fread(main_ss_filepath, data.table = FALSE)
main_gwas_df <- main_gwas_df %>%
  tidyr::separate(VAR_ID,
                  into    = c("CHR_g", "POS_g", "REF", "ALT"),
                  sep     = "_",
                  remove  = FALSE,
                  convert = FALSE) %>%
  mutate(SNP     = paste(CHR_g, POS_g, sep = ":"),
         P_VALUE = as.numeric(P_VALUE),
         BETA    = as.numeric(BETA),
         SE      = as.numeric(SE)) %>%
  select(SNP, VAR_ID, REF, ALT, BETA, SE, P_VALUE)

message(sprintf("Primary GWAS loaded: %d rows.", nrow(main_gwas_df)))

# --- 3. Update pruned_vars$PVALUE from DIAGRAM ---
p_lookup <- main_gwas_df %>% select(VAR_ID, PVALUE_gwas = P_VALUE)
pruned_vars <- pruned_vars %>%
  left_join(p_lookup, by = "VAR_ID") %>%
  mutate(PVALUE = if_else(!is.na(PVALUE_gwas), PVALUE_gwas, 1e-10),
         PVALUE = if_else(PVALUE == 0, 1e-300, PVALUE)) %>%
  select(-PVALUE_gwas)

n_in_diagram <- sum(pruned_vars$VAR_ID %in% main_gwas_df$VAR_ID)
message(sprintf("%d / %d Udler variants have P-value from DIAGRAM (rest: 1e-10 placeholder).",
                n_in_diagram, nrow(pruned_vars)))

# --- 4. vars_noHLA (main_script QC 참조; Udler 리스트 = HLA 이미 배제된 셋) ---
vars_noHLA <- pruned_vars

# --- 5. fetch_input for fetch_summary_stats() ---
# 원래 4.1 은 window_to_sentinels() 로 vars_noHLA 를 pruned_vars 주변 ±500kb 로
# 좁힘. 여기선 pruned_vars = vars_noHLA 이므로 그냥 pruned_vars 를 그대로 씀.
fetch_input <- pruned_vars %>%
  mutate(SNP = ChrPos)
message(sprintf("fetch_input has %d variants.", nrow(fetch_input)))

# --- 6. Pre-processed primary GWAS df for fetch_summary_stats() ---
# fetch_summary_stats() 가 데이터프레임을 받으면 filter(SNP %in% df_input$SNP) 로 필터.
# 파일 경로를 받으면 grep 하는데 우리 변환본은 VAR_ID 만 있어 grep 안 됨.
main_gwas_ready <- main_gwas_df %>% select(SNP, REF, ALT, BETA, SE, P_VALUE)

message("=== substitute done. 이제 main_script_example.R Section 4.2 를 실행하되,")
message("    fetch_summary_stats(gwas_ss_file = main_gwas_ready, ...) 로 호출하세요. ===")
