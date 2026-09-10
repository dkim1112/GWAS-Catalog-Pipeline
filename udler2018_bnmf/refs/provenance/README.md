# refs/provenance — 정답지가 어디서 나왔는가

`refs/` 의 CSV 4개는 이 두 스크립트가 Udler 2018 supplement 엑셀에서 뽑아낸 것입니다.
기록용으로만 두었습니다. **지금 그대로 돌아가지 않습니다** — 입력인 supplement 파일
(`udler_s006.xlsx` ~ `udler_s009.xlsx`) 을 이 폴더에 동봉하지 않았기 때문입니다.

| 스크립트 | 하는 일 | 산출물 (지금 `refs/` 에 있는 것) |
|---|---|---|
| `udler2018_inputs.py` | S1/S2/S3/S4 를 읽어 변이 목록·열 목록·출처 매니페스트를 만들고, 각 배포 URL 이 살아있는지 probe | `udler2018_variants.csv`, `udler2018_column_source_status.csv` |
| `udler2018_fallback.py` | 배포처가 죽은 형질에 GWAS Catalog 대체본이 있는지 PMID 대조로 판정 | (판정 결과는 `inputs_manifest.csv` 에 반영됨) |

다시 돌리려면 논문 supplement 를 내려받아 이 폴더에 두고, 스크립트 안의
입력/출력 경로를 현재 폴더 구조에 맞게 고쳐야 합니다.

원 논문: Udler MS et al. PLoS Med 2018. doi:10.1371/journal.pmed.1002654
