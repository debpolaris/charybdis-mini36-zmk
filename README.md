# Charybdis mini36 — ZMK 펌웨어·설정 저장소

Charybdis mini36 (3x6 + 3x6, 42키, PMW3610 트랙볼, EC11 인코더 2개)용 ZMK 설정과,
그 설정으로 만든 펌웨어 바이너리, 그리고 **업스트림 저장소가 사라져도 이 저장소만으로
다시 빌드할 수 있게** 의존성을 동봉한 저장소입니다.

키보드 이름은 `CONFIG_ZMK_KEYBOARD_NAME="V&Z-MINI36"` 입니다.

## 검증 상태 (2026-11-17)

| 항목 | 결과 |
| --- | --- |
| `firmware/rebuilt/` 3개 이미지 | 이 저장소의 `config/`로 WSL Debian에서 직접 빌드 |
| `firmware/local-2026-05-13/` (기존 로컬 빌드) | `left`·`right` 모두 `rebuilt/`와 **SHA256 일치** → 설정이 실제 펌웨어와 동일 |
| `vendor/restore.sh` + `build.sh` 로 재빌드 | left·right·reset **3개 모두** `firmware/rebuilt/`와 SHA256 일치 (2026-11-17 실측) |

`reset` 이미지는 `settings_reset` 실드 빌드이며, 기존 백업본과 일치합니다.

## 저장소 구조

```
config/                     실제 컴파일된 ZMK 설정 (keymap·conf·overlay·west.yml)
firmware/rebuilt/           이번 작업에서 빌드한 zmk.{left,right,reset}.uf2 + SHA256SUMS.txt
firmware/local-2026-05-13/  예전에 로컬에서 빌드해 두었던 uf2 (left/right) + SHA256SUMS.txt
vendor/                     재현 빌드용 잠금 매니페스트·복원/빌드 스크립트·자산 해시
docs/                       키맵 다이어그램 (png/html/json)
tools/keymap_diagram.py     keymap 소스 → 키맵 다이어그램 생성기
ATTRIBUTION.md              원저작자·라이선스
```

`config/` 은 다음 두 가지를 합친 것입니다.

- 원본 하드웨어 정의: Vzhao-L/zmk-for-charybdis (branch `Charybdis-mini36-Mod`, `97e9814`)
- 내 설정: `charybdis.keymap`, `boards/shields/charybdis/charybdis_right.conf`,
  `boards/shields/charybdis/charybdis_right.overlay` (2026-05-13 기준)

내 설정이 원본과 다른 주요 항목: 트랙볼 CPI 800 / snipe 200, `SCROLL_TICK=120`,
`AUTOMOUSE_TIMEOUT_MS=950`, 레이어 6개(Base·Nav/Symbol·FN/MID/BT·AutoMouse·SlowMouse·ScrollOnly),
홈러 홀드-탭 HRM(`hml`/`hmr`), 한영 전환·붙여넣기 매크로.

## 펌웨어 올리기

1. `nice_nano_v2`를 PC에 연결한 뒤 리셋 버튼을 두 번 눌러 부트로더(BOOTLDR) 모드로 진입.
2. uf2를 `NANOBOOT` 드라이브에 복사. 한 번에 하나씩만 연결하는 편이 안전합니다.
   - 왼쪽: `firmware/rebuilt/zmk.left.uf2`
   - 오른쪽: `firmware/rebuilt/zmk.right.uf2`
   - 설정 초기화가 필요할 때만: `firmware/rebuilt/zmk.reset.uf2`
3. BT 페어링은 `FN/MID/BT` 레이어의 `BT 0`~`BT 4`, 해제/스왑은 같은 레이어 참조.

## 이 저장소만으로 다시 빌드하기

fork 없이, west 의존성 전체(Zephyr·모듈 40종·ZMK·PMW3610 드라이버)와 Zephyr SDK
`arm-zephyr-eabi` 0.16.5를 **Release 자산 아카이브**로 동봉했습니다.
Linux(x86_64, WSL 포함)에서 동작합니다.

```bash
git clone https://github.com/<owner>/charybdis-mini36-zmk.git
cd charybdis-mini36-zmk
./vendor/restore.sh ~/zmk-charybdis   # 자산 다운로드 → 검증 → 해제 → .venv 구성
./vendor/build.sh  ~/zmk-charybdis    # left/right/reset 3개 빌드 + sha256 출력
```

`restore.sh` 는 clone URL에서 저장소 주인을 스스로 찾아내므로 소유자를 직접
입력할 필요가 없습니다(`OWNER=` / `REPO_NAME=` 으로 덮어쓸 수도 있습니다).

- 자산 목록과 해시: `vendor/SHA256SUMS.txt`, 설명은 `vendor/README.md`
- 복원된 워크스페이스는 `vendor/manifest.lock.yml`(import 없는 평면 매니페스트, 40개
  프로젝트 전부 커밋 SHA 고정)를 사용합니다. 네트워크 없이 소스만으로도 동작하도록
  만든 이유와 주의점은 `vendor/README.md` 참조.
- 빌드가 `west: unknown command "build"` 를 띄우면 `.west/config` 의
  `manifest.path=vendor` 가 깨진 것입니다. `restore.sh` 를 다시 실행하세요.

GitHub Actions도 같은 경로를 씁니다(`.github/workflows/build.yml`): Release 자산을
내려받아 `config/`로 빌드하고 산출물을 artefact로 올립니다. 마지막 단계가 빨간불이면
`config/` 은 바뀌었는데 `firmware/rebuilt/` 의 uf2 는 그대로인 상태입니다 — 빌드를
다시 돌리고 산출물을 갱신해 커밋하면 됩니다.

`config/west.yml` 은 업스트림(zmkfirmware) 방식으로 같이 쓸 수 있게 남겨둔 매니페스트이고,
재현 빌드가 실제로 쓰는 잠금 매니페스트는 `vendor/manifest.lock.yml` 입니다.

## 설정을 바꿨을 때

1. `config/charybdis.keymap`(또는 `config/boards/shields/charybdis/*`) 편집
2. `./vendor/build.sh` 로 빌드 → 실제 컴파일되는 파일과 대조
3. 키맵 그림 재생성:

```bash
python3 tools/keymap_diagram.py config/charybdis.keymap docs/keymap-layers.html docs/keymap-layers.json
cp docs/keymap-layers.html docs/keymap.html
```

그림이 필요하면 HTML을 브라우저로 열어 전체 페이지를 이미지로 저장하면 됩니다.
생성기는 컴파일된 keymap을 직접 파싱하므로, 손으로 그린 그림처럼 실제 펌웨어와
어긋날 수 없습니다.

## 자체 완결성의 범위

- 지킨 것: 의존성 저장소(zmk·zephyr 포크·모듈·PMW3610 드라이버)와 컴파일러 SDK를
  이 저장소의 Release 자산으로 보유. 업스트림이 삭제·비공개돼도 복원 가능.
- 지키지 못한 것: 자산은 GitHub Release에 있으므로 **GitHub 저장소 자체가** 사라지면
  함께 사라집니다. fork를 만들지 않는 대신 이 저장소를 백업(클론 + 자산 사본)해 두세요.
- PyPI(pip 패키지)는 GitHub 저장소가 아니라 고정 목록만 동봉했습니다(`vendor/pip.lock.txt`).

## 라이선스

원본 하드웨어 정의와 ZMK·Zephyr의 라이선스는 [ATTRIBUTION.md](ATTRIBUTION.md) 에 정리했습니다.
