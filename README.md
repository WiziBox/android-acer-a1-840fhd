# Acer Iconia Tab 8 A1-840FHD — Android 9 port

비공식 Android 9 / LineageOS 16.0 포팅 프로젝트입니다. Acer 또는 LineageOS의 공식 배포가 아닙니다.

## 지원 대상

- 모델: **Acer A1-840FHD**
- 코드명: `ducati2fhd`, 플랫폼: `baytrail`, 보드 식별: `baylake`
- CPU: Intel Atom Z3745
- 포팅 환경: x86 32비트 Android 9, 3.10.20+ 커널
- A1-810이나 A1-840 등 다른 모델에 적용하지 마세요.

## 현재 공개 상태

현재 저장소는 배포 준비 문서입니다. 재현 가능한 전체 소스나 설치 가능한 ROM을 공개한 상태가 아닙니다.

라이선스를 확인한 공유 작업 트리의 프레임워크 패치 5개만 추가 공개합니다. 기기 소스 스냅샷은 파일별 출처 확인이 부족해 이번 공개에서 제외했습니다. [라이선스 검토 결과](docs/LICENSE-REVIEW.ko.md)와 [패치 출처](shared-workspace-patches/PROVENANCE.md)를 먼저 확인하세요.

[다른 PC용 빌드·다운로드·플래싱 작업 현황](docs/PORTABLE-WORKFLOW.ko.md): boot 승인키 검사 도구와 Windows/Linux 단위 테스트를 추가했습니다. GitHub Actions도 이 도구만 검사하며 ROM을 빌드하거나 플래싱하지 않습니다.

개발 기기에서는 부팅·그래픽·내비게이션·백라이트/절전 복귀·저장소 권한·네트워크 관련 수정을 진행했습니다. 최종 후보에는 원래 그래픽 경로를 유지했으며 별도의 imported-framebuffer 실험은 포함하지 않습니다.

Wi-Fi firmware crash를 관측해 production 펌웨어로 교체했습니다. 단기 동작은 확인했으나 장기간 안정성이 입증된 것은 아닙니다. 충전 입력은 케이블 교체 후 개선됐으며, 충전 안전 제한을 해제하지 않았습니다.

ARM APK 호환성 레이어는 포함하지 않습니다. 카메라·모든 앱·DRM 영상 등의 호환성은 보장하지 않습니다. 기존 개발용 system에는 Google 앱과 독점 바이너리가 포함되어 있어 재배포 조건 검토와 배포용 구성이 필요합니다.

## 보안과 설치

현재 개발 환경에는 루트 권한, SELinux permissive, 부팅 시 TCP 5555 ADB 활성화 설정이 있습니다. ADB RSA 인증은 유지했지만 일반 사용자용 안전한 기본 설정으로 간주하지 않습니다. 배포용 기본값을 정리한 뒤 상세히 안내하겠습니다.

이 기기는 OSIP/reserved 영역을 사용하는 부팅 구조입니다. 일반 Android 기기나 dangol의 플래싱 명령을 사용하지 마세요. 개인 기기의 전체 백업·공장 설정 영역을 공개하거나 다른 기기에 기록하지 마세요.

## 배포 예정 구성

- 확인된 device tree 및 프레임워크/HAL 수정
- 커널 대응 소스, 설정, 빌드 도구 및 정확한 원본 커밋
- Google 앱을 별도 취급하는 배포 구성
- 한국어 설치·복구 안내와 알려진 문제
- 조건 검토를 마친 ROM을 GitHub Releases에 별도 제공

[배포 체크리스트](docs/RELEASE-CHECKLIST.ko.md) · [로컬 후보 기록](docs/CANDIDATES.ko.md)
