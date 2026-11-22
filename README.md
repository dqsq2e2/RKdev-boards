# RKdev-boards

这里保存 RKdev 的板包。在这个仓库增加板子时，只添加一个 `boards/<板型>/<修订>/` 目录，并用指定版本的 RKdev 读取它。第三方可把同样的目录放在自己的仓库。

| 板包 | Profile | 布局 | 额外固件输入 |
| --- | --- | --- | --- |
| `boards/bdy-g98/v1` | SPI | 32 MiB NOR；loader `0x8000`，env `0x3f8000`，恢复 `0x400000` | 板包锁定的 `rk3588_ddr_lp4_1800MHz_lp5_2400MHz_v1.21.bin` |
| `boards/phx-r3588/v1` | eMMC | loader `0x8000`，双环境 16 MiB，恢复 32 MiB，系统 256 MiB | 板包列出的无线、Mali 和监管数据库文件 |
| `boards/i3588/v1` | eMMC | 同类偏移、独立板型和布局身份；PCIe3 x2+x2、板级共享 PERST# | 板包锁定的 `bl31.elf`，以及列出的无线和 Mali 固件 |

所有固件按 `board.json` 的 SHA-256 检查。对 `file` 条目，用一个或多个 `--firmware-dir` 指向文件实际所在的目录；子目录需要另外指定。这个仓库不包含原厂固件、个人备份或镜像。I3588 的硬件 BOOT 键直接进入 BootROM，VOL+/RECOVERY 才由公用 U-Boot 策略处理。PHX 的下载键和 G98 的恢复键是各自的板包配置。

从 RKdev-boards 根目录，用相邻的 RKdev 校验或构建，例如：

```sh
python3 ../RKdev/tools/rkdev.py lint --board boards/phx-r3588/v1 --profile emmc
sudo env "PATH=$PATH" python3 ../RKdev/tools/rkdev.py build +  --board boards/phx-r3588/v1 --profile emmc --locked +  --firmware-dir /path/to/fw/brcm --firmware-dir /path/to/fw/mali +  --firmware-dir /path/to/fw/regdb --out out/phx
```

板包构建可使用 [RKdev 的板包接口](https://github.com/dqsq2e2/RKdev/blob/main/docs/board-package.md)。提交时附上所用 RKdev 提交、构建日志和 `verify` 结果。固件仍为开发候选，既有项目的旧版实机结果不代表 RKdev 镜像已通过实机验收。
