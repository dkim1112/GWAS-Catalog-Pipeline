#!/usr/bin/env python3
"""
Generate a comprehensive DOCX report of the T2D bNMF (Udler 2018) reproduction journey.
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import date

OUT = "/Users/kde/Documents/GWAS Catalog Pipeline/T2D_bNMF_재현_보고서.docx"

doc = Document()

# --- Base styles ---
style = doc.styles["Normal"]
style.font.name = "AppleGothic"
style.font.size = Pt(10)

def set_cell_bg(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)

def add_heading(text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = "AppleGothic"
    return h

def add_para(text, bold=False, italic=False, size=10, color=None):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "AppleGothic"
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    if color:
        r.font.color.rgb = RGBColor(*color)
    return p

def add_code(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Menlo"
    r.font.size = Pt(9)
    p.paragraph_format.left_indent = Inches(0.3)
    return p

def add_bullet(text, level=0):
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.left_indent = Inches(0.3 + level * 0.3)
    for r in p.runs:
        r.font.name = "AppleGothic"
        r.font.size = Pt(10)
    return p

def add_table(headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        r = p.add_run(h)
        r.font.name = "AppleGothic"
        r.font.size = Pt(10)
        r.bold = True
        set_cell_bg(hdr[i], "D9E2F3")
    for ri, row in enumerate(rows):
        cells = table.rows[ri + 1].cells
        for ci, val in enumerate(row):
            cells[ci].text = ""
            p = cells[ci].paragraphs[0]
            r = p.add_run(str(val))
            r.font.name = "AppleGothic"
            r.font.size = Pt(9)
    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph()

# ============================================================
# 문서 시작
# ============================================================

# 제목
title = doc.add_heading("T2D bNMF (Udler 2018) 재현 실행 보고서", level=0)
for run in title.runs:
    run.font.name = "AppleGothic"

add_para(f"작성일: {date.today().strftime('%Y-%m-%d')}", italic=True, size=10, color=(90, 90, 90))
add_para("담당: Dongeun (UM Cutaneous Lab, Dr. Matthew Patrick)", italic=True, size=10, color=(90, 90, 90))
add_para(
    "본 문서는 T2D 서브타입을 bNMF 로 정의한 Udler et al. 2018 (PLoS Med) 연구를 "
    "박사님이 준비해주신 파이프라인 (gwas-partitioning/bnmf-clustering) 을 이용해 "
    "Kimlab 서버에서 재현한 전 과정을 정리한 것입니다. 발생한 모든 이슈와 결정, "
    "최종 결과, 재현 조건을 담고 있어 박사님(또는 이 작업을 이어받을 사람) 이 "
    "그대로 검토·재실행 할 수 있게 구성했습니다."
)
add_para("")

# --- 1. 개요 ---
add_heading("1. 개요", 1)
add_para(
    "CD (Crohn's Disease) 를 bNMF 로 서브타이핑하기 전에, T2D 에서 확립된 Udler 2018 "
    "파이프라인이 우리 환경에서도 재현되는지 먼저 확인하는 파일럿입니다. Udler 논문은 "
    "94 개 T2D 변이와 47 개 정량 형질로 5 개 클러스터 (Beta-Cell / Proinsulin / "
    "Obesity / Lipodystrophy / Liver-Lipid) 를 얻었습니다. 우리 목적은 그 결과를 "
    "가능한 한 재현해서, 같은 파이프라인을 CD 로 옮길 준비를 검증하는 것."
)

add_heading("1-1. 작업 위치", 2)
add_table(
    ["구분", "위치"],
    [
        ["로컬 (git 저장소)", "/Users/kde/Documents/GWAS Catalog Pipeline"],
        ["서버", "daniel@Kimlab-server (121.169.161.184:3030)"],
        ["서버 프로젝트 폴더", "/BiO2/home/daniel/udler2018_bnmf"],
        ["SSH 별칭", "bnmf (~/.ssh/config)"],
    ],
    col_widths=[1.8, 4.5]
)

add_heading("1-2. 최종 결과 한 문장", 2)
add_para(
    "K=3 consensus (100 replicate 중 96 회) 를 얻었고, 그 중 K3 클러스터가 Udler 의 "
    "Beta-Cell 클러스터와 Pearson r=0.92 로 강력히 매칭됩니다. Liver-Lipid 는 예상대로 "
    "지질 데이터 부재로 약하게 (r=0.38) 나오고, 나머지 두 클러스터는 매칭 부족합니다. "
    "파이프라인 자체는 작동 확인, 완전 재현은 데이터 확보 시 가능.",
    bold=False
)

doc.add_page_break()

# --- 2. 진행 단계 요약 ---
add_heading("2. 진행 단계 요약", 1)
add_table(
    ["단계", "내용", "소요시간"],
    [
        ["1. 저장소 재구성", "src/outputs → cd_survey/, udler2018_bnmf/ 신설", "즉시"],
        ["2. R 스크립트 로컬 편집", "EUR-only + 우리 폴더 경로 8개 변경", "즉시"],
        ["3. 서버 접속 셋업", "SSH 키, alias bnmf, VS Code Remote-SSH", "5 분"],
        ["4. 데이터 업로드", "scripts+manifest+refs rsync, 수동 sumstats 4개 scp", "5 분"],
        ["5. 자동 다운로드", "download_inputs.sh: 32 파일 (2.5GB)", "수 분"],
        ["6. rsID 맵 생성", "build_rsid_map.py: dbSNP b151 (1.15GB, 22 파일)", "5 분"],
        ["7. sqlite 색인", "convert_sumstats.py --index (2.1GB)", "2 분"],
        ["8. 포맷 변환", "convert_sumstats.py: 36 파일 → sumstats_converted/", "10 분"],
        ["9. 매니페스트 검증", "validate_inputs.py: 준비 완료 확인", "20 초"],
        ["10. R 패키지 설치", "CRAN+Bioconductor, tidyverse 회피책", "30 분"],
        ["11. R 파이프라인 실행", "Section 0-13, Udler substitute 포함", "1 시간"],
        ["12. Udler 대조", "L2EU.H.mat.3.txt ↔ Udler S4 correlation", "즉시"],
    ],
    col_widths=[1.5, 4.0, 0.9]
)

doc.add_page_break()

# --- 3. 이슈와 결정 ---
add_heading("3. 발견된 이슈 및 해결", 1)
add_para(
    "실행 중 마주친 11 개 이슈와 각각의 결정. 재현하는 사람이 같은 곳에서 막히지 않도록 "
    "원인·결정·결과를 모두 명시합니다."
)

# --- Issue 1 ---
add_heading("Issue 1. GitHub 코드가 EUR-only 가 아니라 multi-ancestry", 2)
add_para("상황:", bold=True)
add_para(
    "박사님이 \"github 코드가 EUR-only 일 것\"이라 하셨는데, 확인해보니 지금 저장소 "
    "(bnmf-clustering) 는 반대로 multi-ancestry 가 default. README 제목이 "
    "\"T2D Multi-ancestry Partitioned Polygenic Scores\", main_script_example.R:193 "
    "이 my_pops <- c(\"EUR\",\"EAS\",\"AFR\",\"AMR\",\"SAS\") 이고 line 261 이 "
    "filter(n == num_pops) 로 5 개 population 전부에서 독립인 변이만 살림. 논문 발표 "
    "이후 (Smith/Deutsch 2024) 갱신된 것으로 보임."
)
add_para("결정:", bold=True)
add_para(
    "EUR 재현이므로 my_pops <- c(\"EUR\") 한 줄만 고침. num_pops (line 209) 와 "
    "filter (line 261) 는 자동으로 따라옴. 다른 행은 만지지 않음."
)

# --- Issue 2 ---
add_heading("Issue 2. fetch_summary_stats 호출이 주석 처리돼 있음", 2)
add_para("상황:", bold=True)
add_para(
    "main_script_example.R Section 4.2 (line 295~303) 의 fetch_summary_stats 호출이 "
    "주석 처리돼 있는데, line 308 이 그 결과물 (z_n_mats) 을 사용. 그대로 두면 "
    "'object z_n_mats not found' 로 즉시 죽음. 스크립트 상단에 \"Steps 2-3 are "
    "commented out\" 라 적혀 있지만 실제 주석 처리된 건 4.2."
)
add_para("결정:", bold=True)
add_para(
    "주석 해제. 또한 원본 호출에 있던 read_trait_method='datatable' 인자가 현 함수 "
    "시그니처에 없어서 제거."
)

# --- Issue 3 ---
add_heading("Issue 3. 매니페스트에 접근 불가 CHARGE 형질 5 개", 2)
add_para("상황:", bold=True)
add_para(
    "원 논문 47 형질 중 우리 로컬 매니페스트에 40 개가 있었지만, 그 중 5 개 "
    "(dpa, n6_1821, n6_1831, n6_2031, palmitoleic — 모두 CHARGE 컨소시엄 지방산) "
    "가 요청 승인 방식이라 확보 못함. validate_inputs.py 가 5 개 파일 없다고 실패."
)
add_para("결정:", bold=True)
add_para(
    "CHARGE 5 개를 매니페스트에서 제거 (40 → 35 형질). 하드 제외 7 개 (adip, hdl, "
    "ldl, tc, tg, leptinbmi, fi_bmi) + CHARGE 5 개 = 총 12 개 제외. Udler 5 클러스터 중 "
    "지질 4개 부재는 Liver-Lipid 클러스터를 약화시킬 것으로 예상."
)

# --- Issue 4 ---
add_heading("Issue 4. validate_inputs.py --paths 함수 버그", 2)
add_para("상황:", bold=True)
add_para(
    "validate_inputs.py 의 rewrite_paths() 가 매니페스트 full_path 를 "
    "\"/sumstats/\" 문자열 split 방식으로 재작성하는데, 우리 매니페스트는 "
    "./sumstats_converted/ 상대경로라서 결과가 sumstats/./sumstats_converted/... "
    "라는 잘못된 경로가 됨. 41 행 전부 \"파일 없음\" 으로 fail."
)
add_para("결정:", bold=True)
add_para(
    "rewrite_paths() 를 재작성. os.path.basename(v) 로 파일명만 뽑고 "
    "os.path.join(new_root, \"sumstats_converted\", basename) 로 조립. 훨씬 견고."
)

# --- Issue 5 ---
add_heading("Issue 5. R 시스템 라이브러리 부재로 tidyverse 설치 실패", 2)
add_para("상황:", bold=True)
add_para(
    "install.packages(\"tidyverse\") 가 ragg 컴파일 단계에서 실패. ragg 는 시스템 "
    "라이브러리 (harfbuzz, freetype, libpng 등) 를 필요로 하는데 서버에 없음. sudo "
    "권한 없어 apt install 불가. Posit 바이너리 저장소도 안 됨."
)
add_para("결정:", bold=True)
add_para(
    "tidyverse 메타패키지 대신 개별 컴포넌트 (tidyr, stringr, tibble, purrr, forcats, "
    "lubridate, ggplot2) 를 개별 설치. 5 개 R 스크립트 (main_script_example.R, "
    "choose_variants_2025.R, prep_bNMF_2025.R, run_bNMF_2025.R, post_bNMF_2025.R) "
    "의 library(tidyverse) 를 개별 library() 호출로 교체."
)

# --- Issue 6 ---
add_heading("Issue 6. 실행 중 발견된 미설치 패키지", 2)
add_para("상황:", bold=True)
add_para(
    "Section 2 실행 중 R.utils 가 없어서 fread 가 .gz 못 읽음. 이후 "
    "choose_variants_2025.R 의 future.apply 도 미설치. 초기 install 리스트에서 누락."
)
add_para("결정:", bold=True)
add_para(
    "R.utils 와 future.apply 를 개별 install.packages(). 이후 문제 없음."
)

# --- Issue 7 (핵심) ---
add_heading("Issue 7. DIAGRAM v3 만으로는 Udler 94 변이 재현 불가 ★", 2)
add_para("상황:", bold=True)
add_para(
    "Section 2 (변이 선택 + clumping) 을 DIAGRAM v3 Stage 1 (Morris 2012) 로 돌린 결과, "
    "sentinel 215 개 → 100kb 클럼핑 후 15 개만 남음. Udler 논문의 94 개와 격차 큼. "
    "원인: Udler 는 DIAGRAM v3 하나가 아니라 여러 T2D GWAS 논문에서 큐레이션한 리스트 "
    "94 개를 썼음. 우리 파이프라인 (DIAGRAM v3 만) 으로는 절대 94 개 안 나옴."
)
add_para("결정:", bold=True)
add_para(
    "Udler 정답지 refs/udler2018_variants.csv 의 94 변이를 pruned_vars 로 직접 로드. "
    "Section 2-3 (변이 선택 + LD pruning) 을 건너뛰고 Section 4 부터 이어감. "
    "udler_substitute.R 이라는 대체 스크립트를 만들어 이 substitution 을 담당."
)
add_para("영향:", bold=True)
add_para(
    "이걸로 재현이 진짜 Udler 정답지에서 출발하게 됨. bNMF 결과의 클러스터 정체성을 "
    "Udler S4 와 직접 비교 가능. 대신 이후 단계에서 Udler 94 중 데이터가 없는 것들이 "
    "떨어져 나감 (다음 이슈 참조)."
)

# --- Issue 8 ---
add_heading("Issue 8. Primary GWAS 파일 grep 실패 (converter vs pipeline 불일치)", 2)
add_para("상황:", bold=True)
add_para(
    "fetch_summary_stats() 가 primary GWAS 파일에서 SNP 컬럼 (Chr:Pos 형식) 을 "
    "grep 하는데, 우리 convert_sumstats.py 는 VAR_ID (CHR_POS_REF_ALT 형식) 컬럼만 "
    "생성. grep \"9:136149229\" 는 \"9_136149229_T_C\" 를 매치하지 못함."
)
add_para("결정:", bold=True)
add_para(
    "primary GWAS 를 R 안에서 미리 로드하고 SNP/REF/ALT/BETA/SE/P_VALUE 컬럼을 "
    "derive한 데이터프레임 (main_gwas_ready) 으로 만들어 fetch_summary_stats() 에 "
    "파일경로 대신 이 df 를 넘김. udler_substitute.R 이 이 준비도 담당. "
    "main_script Section 4.2 는 이 df 를 받도록 수정."
)

# --- Issue 9 ---
add_heading("Issue 9. SE 컬럼 누락 (초기 substitute)", 2)
add_para("상황:", bold=True)
add_para(
    "udler_substitute.R 초안이 main_gwas_ready 를 만들 때 select() 에서 SE 컬럼을 "
    "빠뜨림. Section 9 (allele 정렬) 에서 z_n_mats$df_gwas 에 SE 컬럼 필요로 하는데 없음."
)
add_para("결정:", bold=True)
add_para(
    "udler_substitute.R 을 수정해서 SE 도 포함. 이미 서버에서 fetch_summary_stats 를 "
    "완료한 상태였으므로 임시로 SE 를 df_gwas 에 patch (data.table::fread 로 "
    "VAR_ID 와 SE 만 뽑아 left_join). 다음 사용자는 수정된 udler_substitute.R 로 한 방에 됨."
)

# --- Issue 10 ---
add_heading("Issue 10. Section 9 에서 6개 문제 변이 발견", 2)
add_para("상황:", bold=True)
add_para(
    "Section 9 QC 로그: 2 개 NA (allele 정렬 실패), 3 개 ambiguous (palindromic "
    "AT/TA/CG/GC — strand 확정 불가), 1 개 multiallelic (rs1801282 PPARG 로 추정). "
    "파이프라인은 경고만 하고 진행."
)
add_para("결정:", bold=True)
add_para(
    "이 6 개 (중복 제거 시 실제 4 개) 를 gwas_final_filtered 와 df_final 에서 필터. "
    "최종 71 변이 확정. softImpute 로 결측 대치, bNMF 로 진입."
)

# --- Issue 11 ---
add_heading("Issue 11. summarize_bNMF() 에서 ggplot2 미로드 에러", 2)
add_para("상황:", bold=True)
add_para(
    "bNMF 실행 자체는 성공 (100 replicates, 7 초). summarize_bNMF() 가 plot 부분에서 "
    "theme_bw 를 못 찾음 → ggplot2 미로드 상태."
)
add_para("결정:", bold=True)
add_para(
    "library(ggplot2) 로드 후 summarize_bNMF() 재호출. W/H matrix 파일과 heatmap PDF "
    "정상 생성. K=2, 3, 4 세 개 모두 파일 나옴."
)

doc.add_page_break()

# --- 4. 최종 결과 ---
add_heading("4. 최종 결과", 1)

add_heading("4-1. bNMF 수렴 결과", 2)
add_para(
    "100 replicates 중 ARD prior 가 고른 K 분포:"
)
add_table(
    ["K", "선택된 횟수", "비고"],
    [
        ["2", "3", "약간 나옴, evidence -5144 (fit 나쁨)"],
        ["3", "96", "★ Consensus. evidence -5068 (fit 최상, 대다수)"],
        ["4", "1", "1 회만. evidence -4710 (수치는 높지만 unstable)"],
    ],
    col_widths=[0.8, 1.4, 4.2]
)
add_para(
    "결론: K=3 가 우리 데이터의 안정된 consensus. Udler K=5 보다 2 개 부족."
)

add_heading("4-2. Udler 정답지 (S4) 와 correlation", 2)
add_para(
    "L2EU.H.mat.3.txt (우리 클러스터 × 우리 형질 features) 를 전치해서 "
    "trait × K matrix 로 만들고, Udler S4 (trait × 5 클러스터) 와 공통 형질 "
    "(35 개, pos/neg 포함) 만 뽑아 Pearson correlation:"
)
add_table(
    ["우리 클러스터", "Beta-cell", "Proinsulin", "Obesity", "Lipodystrophy", "Liver/Lipid"],
    [
        ["K1", "-0.343", "0.132", "0.007", "0.143", "0.122"],
        ["K2", "0.247", "-0.094", "-0.045", "0.198", "0.377"],
        ["K3", "0.920 ★", "0.217", "-0.101", "-0.020", "-0.035"],
    ],
    col_widths=[1.4, 1.0, 1.0, 1.0, 1.2, 1.0]
)

add_heading("4-3. 해석", 2)
add_para("K3 ≈ Beta-cell (r = 0.92)", bold=True)
add_para(
    "명확한 재현 성공. Udler 의 Beta-cell 클러스터 (proinsulin, incr30, DI, CIR 등 "
    "베타세포 기능 형질이 주도) 를 그대로 잡아냄."
)
add_para("K2 ≈ Liver/Lipid (r = 0.38)", bold=True)
add_para(
    "약한 매칭. 지질 4 개 (hdl/ldl/tc/tg) 부재를 감안하면 이 정도 signal 있는 것도 "
    "긍정적. adiponectin, urate 같은 대체 형질이 부분 기여한 것으로 추정."
)
add_para("K1: 매칭 없음", bold=True)
add_para(
    "어느 Udler 클러스터와도 r > 0.2 미달. 다만 Beta-cell 에 음의 상관 (r = -0.34) — "
    "\"anti-Beta-cell 축\" = 인슐린 저항성 (Lipodystrophy 개념과 근접) 을 잡았을 가능성."
)
add_para("Obesity 클러스터 부재", bold=True)
add_para(
    "예상 밖. BMI, WC, WHR, hip 등 anthropometry 형질이 있는데 별도 클러스터로 "
    "안 잡힘. K=3 해상도가 부족해서 Obesity 형질이 다른 클러스터에 흡수됐을 가능성. "
    "K=4 (rare, 1 회만) 대조하면 나올 수도 있음."
)

doc.add_page_break()

# --- 5. 재현 조건 ---
add_heading("5. 재현 조건 (박사님 대조·재실행용)", 1)
add_para(
    "박사님이나 다른 사람이 같은 결과를 재현하려면 아래 조건이 정확히 일치해야 합니다. "
    "논문 재현 판정 시 필수 정보."
)
add_table(
    ["항목", "값"],
    [
        ["서버", "Kimlab-server (Ubuntu 22.04, R 4.5.2, Python 3.10.12)"],
        ["프로젝트 폴더", "/BiO2/home/daniel/udler2018_bnmf"],
        ["my_pops", "c(\"EUR\") — EUR-only 재현"],
        ["PVCUTOFF", "5e-8 (사용 안 됨, Udler substitute 로 우회)"],
        ["원본 형질 (매니페스트)", "35 개 (원 논문 47 → 하드 제외 7 + CHARGE 5 제거)"],
        ["형질 최종 (bNMF 입력)", "26 unique (prep_z_matrix corr>0.8 필터)"],
        ["원본 변이", "94 개 (Udler S1 refs/udler2018_variants.csv 직접 로드)"],
        ["fetch 후 남은 변이", "77 개 (Udler 94 중 우리 trait 파일에 없는 17 제외)"],
        ["최종 변이 (bNMF 입력)", "71 개 (Section 9 문제 변이 6개 필터 후)"],
        ["bNMF 설정", "n_reps=100, K=15, K0=10, tolerance=1e-6, phi=1"],
        ["ARD 가 고른 K", "K=3 (96/100 replicate)"],
        ["재현된 클러스터", "Beta-cell (r=0.92, 강함)"],
        ["약하게 재현된 클러스터", "Liver/Lipid (r=0.38, 지질 부재 원인)"],
    ],
    col_widths=[2.2, 4.1]
)

doc.add_page_break()

# --- 6. 파일/코드 위치 ---
add_heading("6. 파일 및 코드 위치", 1)

add_heading("6-1. 로컬 (git 저장소)", 2)
add_code(
    "/Users/kde/Documents/GWAS Catalog Pipeline/\n"
    "├── README.md                            (상위 README)\n"
    "├── .gitignore\n"
    "├── cd_survey/                           (CD Step 1-2, 별개 작업)\n"
    "│   ├── src/*.py                         (5개 스크립트)\n"
    "│   └── outputs/*.csv                    (조사 결과)\n"
    "└── udler2018_bnmf/                      (T2D Step 3 재현 - 본 보고서 대상)\n"
    "    ├── README.md, RUN_GUIDE.md          (실행 가이드)\n"
    "    ├── manifest.xlsx                    (파이프라인 입력)\n"
    "    ├── inputs_manifest.csv              (형질별 출처/URL)\n"
    "    ├── build_rsid_map.py                (dbSNP 맵 생성)\n"
    "    ├── convert_sumstats.py              (원본 → 파이프라인 포맷)\n"
    "    ├── validate_inputs.py               (사전 점검, 버그 수정됨)\n"
    "    ├── download_inputs.sh               (자동 다운로드)\n"
    "    ├── hg19ToHg38.over.chain            (post_bNMF liftover)\n"
    "    ├── refs/                            (Udler 정답지)\n"
    "    │   ├── udler2018_variants.csv       (94 변이)\n"
    "    │   ├── udler2018_S3_variant_weights.csv  (S3 정답)\n"
    "    │   ├── udler2018_S4_trait_weights.csv    (S4 정답 - 대조에 사용)\n"
    "    │   └── udler2018_column_source_status.csv\n"
    "    └── scripts/                         (R 파이프라인)\n"
    "        ├── main_script_example.R        (드라이버, 로컬 편집됨)\n"
    "        ├── udler_substitute.R           (★ Section 2-3-4.1 대체)\n"
    "        ├── choose_variants_2025.R       (원본, library 수정됨)\n"
    "        ├── prep_bNMF_2025.R\n"
    "        ├── run_bNMF_2025.R\n"
    "        ├── post_bNMF_2025.R\n"
    "        └── generate_varid_to_rsid_map_file.R"
)

add_heading("6-2. 서버 (Kimlab-server)", 2)
add_code(
    "/BiO2/home/daniel/udler2018_bnmf/\n"
    "├── (로컬 파일 전체 사본)\n"
    "├── sumstats/                            (원본 요약통계 36개, 2.5GB)\n"
    "├── sumstats_converted/                  (변환본 36개, 1.1GB)\n"
    "├── rsid_maps_by_chr/                    (chr1~22.txt, 1.15GB)\n"
    "├── logs/                                (실행 로그 4개)\n"
    "│   ├── download.log\n"
    "│   ├── rsid_map.log\n"
    "│   ├── index.log\n"
    "│   └── convert.log\n"
    "├── my_workspace_udler2018_eur_v1.RData  (R 체크포인트, 재개용)\n"
    "└── udler2018_eur_v1_results/            (bNMF 최종 결과 ★)\n"
    "    ├── run_summary.txt                  (100 replicate 의 K)\n"
    "    ├── bnmf_settings.rds                (재현 조건)\n"
    "    ├── df_traits.csv                    (트레이트 필터 로그)\n"
    "    ├── alignment_GWAS_summStats.csv     (allele 정렬된 GWAS)\n"
    "    ├── rsID_map.txt                     (최종 변이 rsID 매핑)\n"
    "    ├── L2EU.W.mat.{2,3,4}.txt           (변이 × K)\n"
    "    ├── L2EU.H.mat.{2,3,4}.txt           (K × trait — 대조에 사용)\n"
    "    ├── W_plot_K{2,3,4}.pdf              (변이 heatmap)\n"
    "    ├── H_plot_K{2,3,4}.pdf              (trait heatmap)\n"
    "    └── bNMF_cutoff_calc.png             (K 결정 elbow)"
)

doc.add_page_break()

# --- 7. 재실행 절차 ---
add_heading("7. 서버에서 처음부터 재실행 절차", 1)
add_para(
    "가상 시나리오: 박사님이 같은 서버에서 이걸 다시 돌리려면 아래 순서. 대부분의 "
    "무거운 단계는 이미 서버에 캐시돼 있어 스킵 가능 (변환본 등)."
)

add_heading("7-1. 접속 + 위치", 2)
add_code(
    "ssh daniel@Kimlab-server -p 3030   # 또는 SSH config 설정 후: ssh bnmf\n"
    "cd /BiO2/home/daniel/udler2018_bnmf\n"
    "export LDLINK_TOKEN=<본인_토큰>     # ~/.bashrc 에 저장 권장"
)

add_heading("7-2. R 세션 시작 (tmux 안)", 2)
add_code(
    "tmux new -s bnmf\n"
    "R"
)

add_heading("7-3. R 안에서 실행 순서", 2)
add_para(
    "main_script_example.R 을 절 단위로 나눠 실행 (통째로 source 금지). VS Code 서버 "
    "터미널에서 스크립트 편집기에 열고 절별로 복사-붙여넣기."
)
add_table(
    ["절", "라인", "내용", "주의"],
    [
        ["0-1", "34-152", "라이브러리 로드, 매니페스트 로드", "nrow(gwas_traits)==35 확인"],
        ["Substitute", "-", "source(scripts/udler_substitute.R)", "★ Section 2-3-4.1 대체"],
        ["4.2", "300-314", "fetch_summary_stats(main_gwas_ready, ...)", "이 호출로 z_n_mats 얻음"],
        ["4.3+", "316-343", "트레이트 필터, QC 1", "77/94 (81.9%) 경고 무시 가능"],
        ["5-7 skip", "-", "topmed_fails=NULL, 빈 proxy 변수 생성", "TOPMed off, proxy 2개는 스킵"],
        ["8", "483-516", "df_final 구성", "94 개 (proxy 없음)"],
        ["9", "528-570", "allele 정렬 + QC", "6 개 문제 변이 필터 후 71 개"],
        ["10", "583-628", "QC 리포트 저장", "quality_control_report.txt"],
        ["11", "632-664", "softImpute 결측 대치", "z_imputed 71×35"],
        ["12", "-", "시각화 (선택)", "스킵 가능"],
        ["13", "705-776", "★ bNMF 실행", "100 rep, ~7 초"],
    ],
    col_widths=[0.7, 0.7, 3.0, 2.0]
)

add_heading("7-4. Udler 대조", 2)
add_para(
    "bNMF 완료 후 별도 R 스크립트로 실행 가능. 위 §4-2 재현. base R 만 사용, 파이프 회피."
)
add_code(
    "h_raw <- read.table(file.path(main_dir, 'L2EU.H.mat.3.txt'),\n"
    "                    header=TRUE, sep='\\t', check.names=FALSE, row.names=NULL)\n"
    "our_trait_W <- t(as.matrix(h_raw))\n"
    "colnames(our_trait_W) <- paste0('K', 1:ncol(our_trait_W))\n"
    "\n"
    "udler_W <- read.csv(file.path(working_dir, 'refs/udler2018_S4_trait_weights.csv'),\n"
    "                    stringsAsFactors=FALSE, check.names=FALSE)\n"
    "udler_mat <- as.matrix(udler_W[,-1])\n"
    "rownames(udler_mat) <- udler_W[,1]\n"
    "\n"
    "udler_norm <- gsub('_zscale2', '', rownames(udler_mat))\n"
    "common <- intersect(udler_norm, rownames(our_trait_W))\n"
    "\n"
    "u_sub <- udler_mat[match(common, udler_norm), , drop=FALSE]\n"
    "o_sub <- our_trait_W[match(common, rownames(our_trait_W)), , drop=FALSE]\n"
    "cor_mat <- cor(o_sub, u_sub, method='pearson')\n"
    "round(cor_mat, 3)"
)

doc.add_page_break()

# --- 8. 다음 단계 제안 ---
add_heading("8. 다음 단계 제안", 1)

add_heading("8-1. Udler 완전 재현 강화 (선택)", 2)
add_bullet("CHARGE 5개 지방산 데이터 확보 (컨소시엄 승인 요청). 얻으면 매니페스트에 추가하고 재실행.")
add_bullet("ENGAGE 지질 4개 (hdl/ldl/tc/tg) 대체 소스 탐색. UKBB 등 최신 대체제 검토.")
add_bullet("K=4 대조 (rare 이지만 Obesity 클러스터가 여기서 분리될 가능성).")
add_bullet("bNMF n_reps 증가 (100 → 500) 로 K 안정성 재확인.")

add_heading("8-2. CD 확장 (프로젝트 본 목적)", 2)
add_bullet("cd_survey/ 결과 (CD 질병 GWAS + 형질 GWAS 후보 풀) 로 CD 매니페스트 작성.")
add_bullet(
    "udler2018_bnmf/ 의 변환 파이프라인 (convert_sumstats.py, build_rsid_map.py) 재사용."
)
add_bullet("Section 2-3 (변이 선택 + LD pruning) 을 CD 로 처음부터 돌려봄 — Udler substitute 불필요.")
add_bullet("bNMF K 자동 선택 결과 vs CD 임상 서브타이핑 (예: montreal classification) 대조.")

add_heading("8-3. 파이프라인 개선 사항 문서화", 2)
add_bullet("발견한 8 개 이슈 (특히 CHARGE 부재, validate_inputs.py 버그, tidyverse/ragg, DIAGRAM 부족) 를 파이프라인 저장소 issue 로 upstream.")
add_bullet("udler_substitute.R 을 pipeline 공식 옵션으로 제안 (\"external variant list mode\").")

# --- 부록 ---
doc.add_page_break()
add_heading("부록 A. 로컬 편집된 파일 목록", 1)
add_table(
    ["파일", "변경 내용"],
    [
        ["scripts/main_script_example.R",
         "1) 헤더 rewrite, 2) version/gwas_file/scripts_dir/my_rsid_map_dir 값, "
         "3) my_pops=c(EUR), 4) fetch_summary_stats 주석 해제 + df 인자 + read_trait_method 제거, "
         "5) library(tidyverse) 개별 컴포넌트로 교체"],
        ["scripts/udler_substitute.R", "★ 신규 파일 (Section 2-3-4.1 대체)"],
        ["scripts/choose_variants_2025.R", "library(tidyverse) 개별로 교체"],
        ["scripts/prep_bNMF_2025.R", "library(tidyverse) 개별로 교체"],
        ["scripts/run_bNMF_2025.R", "library(tidyverse) 개별로 교체"],
        ["scripts/post_bNMF_2025.R", "library(tidyverse) 개별로 교체"],
        ["validate_inputs.py", "rewrite_paths() 버그 수정"],
        ["manifest.xlsx", "CHARGE 5개 제거 (40 → 35 형질)"],
        ["README.md, RUN_GUIDE.md", "35 형질 반영, 제외 12개 반영"],
        ["(상위) README.md", "cd_survey/ + udler2018_bnmf/ 구조 설명 추가"],
        ["(상위) .gitignore", "udler2018_bnmf 대용량 산출물 제외"],
    ],
    col_widths=[2.5, 3.8]
)

add_heading("부록 B. 서버 재접속·상태확인 명령", 1)
add_code(
    "# 접속\n"
    "ssh bnmf\n"
    "\n"
    "# 세션 재개 (bNMF 결과 등 이전 R 상태 복원)\n"
    "tmux attach -t bnmf                          # 살아있으면 그대로\n"
    "# 없으면:\n"
    "tmux new -s bnmf\n"
    "cd ~/udler2018_bnmf\n"
    "R\n"
    "> load('my_workspace_udler2018_eur_v1.RData')\n"
    "\n"
    "# 결과 파일 확인\n"
    "ls ~/udler2018_bnmf/udler2018_eur_v1_results/\n"
    "\n"
    "# W/H matrix 내려받기 (로컬로)\n"
    "rsync -avz bnmf:~/udler2018_bnmf/udler2018_eur_v1_results/ ./results_from_server/"
)

add_heading("부록 C. 처음부터 완전 재생성 (전체 ~1.5 시간)", 1)
add_code(
    "# 데이터 재생성 (2~4 GB 통신 + 컴퓨트)\n"
    "bash download_inputs.sh 2>&1 | tee logs/download.log     # 2.5GB, 수 분\n"
    "python3 build_rsid_map.py 2>&1 | tee logs/rsid_map.log   # 1.15GB, ~4 분\n"
    "python3 convert_sumstats.py --index 2>&1 | tee logs/index.log      # 2.1GB, ~4 분\n"
    "python3 convert_sumstats.py 2>&1 | tee logs/convert.log            # ~10 분\n"
    "\n"
    "# 매니페스트 절대경로화\n"
    "python3 validate_inputs.py --paths $PWD\n"
    "python3 validate_inputs.py     # '→ 준비 완료.' 나와야 함\n"
    "\n"
    "# R 파이프라인 (§7-3 순서대로)"
)

# --- 저장 ---
doc.save(OUT)
print(f"Saved: {OUT}")
