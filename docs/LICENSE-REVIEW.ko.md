# 라이선스 검토 및 공개 범위 — 2026-10-10

이 문서는 기술적 배포 준비 검토이며 법적 무위험이나 전문 법률 의견을 보증하지 않습니다.

## 이번 공개 범위

공유 작업 트리의 프레임워크 패치 5개, 원본 기준 커밋, 관련 고지사항, 출처 및 검토 문서만 공개합니다. 패치가 수정하는 11개 upstream 파일 모두에서 Apache-2.0 및 원본 copyright 헤더를 확인했습니다.

- `LICENSES/Apache-2.0.txt`: Apache 공식 사이트의 영문 라이선스 전문
- `third-party-notices/*.NOTICE`: 해당 upstream 프로젝트의 원본 NOTICE를 수정 없이 보존
- `third-party-notices/*.file-headers.txt`: 패치 대상 파일의 원본 copyright·라이선스 헤더 보존
- `shared-workspace-patches/PROVENANCE.md`: upstream 저장소, 기준 커밋, 대상 파일, 변경 목적
- 각 patch 앞부분: 개발 프로젝트에서 변경했음을 명시

패치의 프로젝트 변경분은 Apache-2.0으로 배포합니다. 원본 고지사항은 유지하며, 이 선언을 제외된 파일이나 제삼자 바이너리에 확대 적용하지 않습니다. 원본 NOTICE에 이번 작은 패치와 무관한 항목이 포함될 수 있으므로 파일별 근거는 원본 헤더와 출처 목록도 함께 보세요.

## 공개에서 제외한 항목

- Dangol 기기 소스·설정 21개 및 Acer 기기 소스·설정 59개: 직접 작성/외부 도입 여부와 파일별 라이선스 근거를 더 확인해야 합니다. 표기 부재 자체를 위반으로 단정하지는 않습니다.
- Intel dynamic export에서 생성한 연결 코드와 심볼 목록: 원본 바이너리의 조건 및 생성 과정 검토 미완료
- 커널·boot/system 이미지와 Wi-Fi 모듈: 대응 소스 및 모든 포함물의 배포 조건 검토 미완료
- Google APK와 GPU·오디오·Wi-Fi 등 독점 바이너리: 재배포 허용 근거 미확인
- 개인 인증키·장치별 백업·사용자 데이터: 배포 대상 아님

제외한 소스가 들어 있는 이전 비공개 로컬 커밋은 공개 브랜치의 조상으로 포함하지 않습니다. GitHub의 현재 문서 브랜치에서 별도 공개 브랜치를 만들어 검토된 파일만 추가했습니다.

## 남은 작업

1. 직접 작성한 코드의 생성·수정 기록 및 라이선스 범위 확정
2. 외부 도입 파일의 정확한 원본·고지사항 확인, 불명확한 것은 제외
3. 수정 커널에 대응하는 소스·설정·빌드 및 설치 스크립트 준비
4. 각 vendor 파일의 재배포 조건 확인 또는 적법한 사용자 추출 절차 정리
5. ROM 내용 전체의 라이선스·개인정보 점검

라이선스 준수와 기기 동작 검증은 별개입니다. 이번 패치는 두 기기가 공유한 작업 트리의 일부이며 완전한 ROM 소스가 아닙니다.

## 기준 자료

- Apache-2.0: https://www.apache.org/licenses/LICENSE-2.0.html
- GPLv2 배포 FAQ: https://www.gnu.org/licenses/old-licenses/gpl-2.0-faq.html
- GitHub 라이선스 안내: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
