# Release 자산으로 배포하는 의존성

이 디렉터리의 스크립트가 받아 쓰는 아카이브는 저장소의 **Release 자산**입니다.
소스 트리가 2GB를 넘어 git tree에 넣을 수 없고, fork를 만들지 않는 대신 압축본을
그대로 보유하는 방식입니다.

Tag: `v1.0.0` — `https://github.com/<owner>/charybdis-mini36-zmk/releases/tag/v1.0.0`

| 자산 | 크기 | 내용 |
| --- | --- | --- |
| `zmk-workspace-src.tar.gz` | 310 MiB | `zephyr/`(v3.5.0+zmk-fixes 포크), `modules/`(west 모듈 37종), `zmk/`(v0.3), `zmk-pmw3610-driver/`(main) — `.git` 제외, 잠금 커밋의 작업 트리 그대로 |
| `zephyr-sdk-0.16.5-arm-zephyr-eabi.tar.gz` | 234 MiB | 설치된 Zephyr SDK 0.16.5 (`arm-zephyr-eabi` 툴체인) |
| `hosttools-dtc.tar.gz` | 49 KiB | SDK hosttools에서 꺼낸 `dtc` 1.6.0 바이너리 (ELF interpreter를 `/lib64/ld-linux-x86-64.so.2`로 재배치) |

`SHA256SUMS.txt` 가 세 파일의 해시를 고정합니다. `restore.sh` 는 다운로드 후 반드시
검증을 수행합니다.

## hosttools `dtc` 의 interpreter 재배치

SDK hosttools는 Yocto nativesdk 바이너리라서 ELF interpreter에 **relocate 당시의 절대
경로**가 그대로 박혀 있습니다(`.../hosttools/sysroots/x86_64-pokysdk-linux/lib/ld-2.27.so`).
그 경로는 아카이브에 들어 있지 않으므로, 원본 바이너리는 그 머신을 벗어나면
`exec` 자체가 `ENOENT`로 실패합니다. CMake는 이를 `dts.cmake:366` 의
`command failed with return code: no such file or directory` 로만 보여주기 때문에
원인을 찾기 어렵습니다.

보관하는 사본은 `patchelf --set-interpreter /lib64/ld-linux-x86-64.so.2` 로 시스템
loader를 가리키게 다시 만들었고, 같은 `zephyr.dts` 를 넣고 돌린 산출물이 원본과
바이트 단위로 일치하는지 확인했습니다(`restore.sh` 가 해제 후 `dtc --version` 으로
미리 점검합니다). SDK 툴체인 아카이브의 54개 ELF는 조사 결과 절대 경로 의존성이 0개라
그대로 보관합니다.

## 평면 매니페스트를 쓰는 이유

원본 설정 저장소의 `config/west.yml` 은 `zmk` 프로젝트를 `import: app/west.yml` 로
가져옵니다. west 는 import를 프로젝트의 **git 저장소**(`manifest-rev` ref)로 해석하기
때문에, `.git` 없이 소스만 풀어 놓은 워크스페이스에서는

```
FATAL ERROR: failed manifest import in zmk (zmk):
  Failed importing "app/west.yml" from revision "v0.3"
```

로 실패합니다. 그래서 `manifest.lock.yml` 은 import를 전혀 쓰지 않고 west가 열거하는
40개 프로젝트를 전부 커밋 SHA로 나열합니다. 부수적으로 두 가지 이점이 있습니다.

- 태그·브랜치 이름이 움직여도 조립 결과가 고정됩니다(원본은 `v0.3`, `main` 같은 이동 참조).
- `west update` 없이, 네트워크 없이도 조립이 끝납니다.

west는 확장 명령(`west build`)을 프로젝트별 `west-commands` 에서 찾으므로 `zephyr`
항목에 `west-commands: scripts/west-commands.yml` 을 명시했습니다. 이것이 빠지면
`west: unknown command "build"` 가 납니다.

## BUILD_VERSION (부팅 배너)

Zephyr은 부팅 배너 문자열로 `git describe --abbrev=12 --always` 결과를 이미지 안에
박아 넣습니다(`zephyr/cmake/gen_version_h.cmake`). `.git` 이 없는 소스만 풀면 이
문자열이 비어서 이미지가 달라집니다.

`build.sh` 는 `vendor/projects.lock.tsv` 에서 zephyr 잠금 커밋을 읽어 12자리
prefix를 `-DBUILD_VERSION=` 으로 직접 넘깁니다. git이 있을 때와 같은 값이라
`firmware/` 와 바이트 단위로 일치합니다(실측: left·right·reset 모두 MATCH).

## PyPI

pip 패키지 목록만 `pip.lock.txt` 에 고정했습니다(97개, 검증한 venv의 `pip freeze`).
wheel 자체는 동봉하지 않았습니다. PyPI는 GitHub 저장소가 아니라 "업스트림 저장소가
사라져도" 요구사항의 범위 밖으로 봤습니다. 설치가 실패하면 `restore.sh` 가
`zephyr/scripts/requirements.txt` 로 자동 전환합니다.
