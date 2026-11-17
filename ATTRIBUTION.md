# 크레딧과 라이선스

이 저장소는 다른 사람들의 작업을 모아 놓은 것이며, 저장소 자체 라이선스로 그것을 대체하지 않습니다.

## 하드웨어

- **Charybdis** — [BastardKB](https://github.com/Bastardkb/Charybdis/).
  3x6 + 엄지 3키, PMW3610 트랙볼, EC11 인코더. `config/boards/shields/charybdis/charybdis.zmk.yml`
  의 메타데이터가 가리키는 주소입니다.
- **nice_nano_v2** (nRF52840) — TinyMicro.

## 소프트웨어

| 구성 요소 | 출처 | 라이선스 |
| --- | --- | --- |
| ZMK firmware | [zmkfirmware/zmk](https://github.com/zmkfirmware/zmk) @ `edf5c0814fd3ea202e43aad2d68fd32e882a518c` (v0.3) | MIT |
| Zephyr RTOS (ZMK 포크) | [zmkfirmware/zephyr](https://github.com/zmkfirmware/zephyr) @ `dacab4875df72109b96cc8977547a0dc04875bcd` (v3.5.0+zmk-fixes) | Apache-2.0 |
| Charybdis ZMK 설정 원본 | [Vzhao-L/zmk-for-charybdis](https://github.com/Vzhao-L/zmk-for-charybdis), branch `Charybdis-mini36-Mod` @ `97e981446390f6eb529e0b5fcd8b7ba7270ce721` | 저장소에 LICENSE 파일 없음 |
| PMW3610 드라이버 | [DoctorWangWang/zmk-pmw3610-driver](https://github.com/DoctorWangWang/zmk-pmw3610-driver) @ `1d9c2c68ca76012e1b1e5f6ef02fa5eadc4ca399` | 저장소에 LICENSE 파일 없음 |
| Zephyr 모듈 37종 | [zephyrproject-rtos](https://github.com/zephyrproject-rtos) 외 | 각 저장소 라이선스(`vendor/projects.lock.tsv` 에 커밋까지 기록) |
| Zephyr SDK 0.16.5 | [zephyrproject-sdk](https://github.com/zephyrproject-rtos/sdk-ng) | toolchain별 라이선스(GCC: GPLv3 with runtime exception 등) |

`config/` 아래에 들어가는 파일은 위 설정 원본에 이 저장소 소유자의 키맵·트랙볼
설정 변경(`charybdis.keymap`, `charybdis_right.conf`, `charybdis_right.overlay`)을
올린 것입니다. 원본과의 차이는 `git diff` 로 확인할 수 있도록 각 파일 주석에
한국어로 남겨 두었습니다.

ZMK와 Zephyr의 원 라이선스 문구는 Release 자산 아카이브 안에 그대로 들어 있습니다
(`zmk/LICENSE`, `zephyr/LICENSE`).
