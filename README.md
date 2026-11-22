# RKdev-boards

这里保存 RKdev 的板包。在这个仓库增加板子时，只添加一个 `boards/<板型>/<修订>/` 目录，并用指定版本的 RKdev 读取它。第三方可把同样的目录放在自己的仓库。

| 板包 | Profile | 各区域起始偏移 | 额外固件输入 |
| --- | --- | --- | --- |
| `boards/bdy-g98/v1` | SPI | 32 MiB NOR；loader `0x8000`，env `0x3f8000`，恢复 `0x400000` | 板包锁定的 `rk3588_ddr_lp4_1800MHz_lp5_2400MHz_v1.21.bin` |
| `boards/phx-r3588/v1` | eMMC | loader `0x8000`，双环境 16 MiB，恢复 32 MiB，系统 256 MiB | 板包列出的无线、Mali 和监管数据库文件 |
| `boards/i3588/v1` | eMMC | loader `0x8000`，双环境 16 MiB，恢复 32 MiB，系统 256 MiB | 板包锁定的 `bl31.elf`，以及列出的无线和 Mali 固件 |
| `boards/aiui/v1` | eMMC | loader `0x8000`，双环境 16 MiB，恢复 32 MiB，系统 256 MiB | 无，RTL8822CS 固件从 linux-firmware 下载 |
| `boards/aiot-3588a2/v1` | eMMC | loader `0x8000`，双环境 16 MiB，恢复 32 MiB，系统 256 MiB | 已验证版本的 DDR、AP6256 无线和 Mali 固件 |

所有固件按 `board.json` 的 SHA-256 检查。对 `file` 条目，用一个或多个 `--firmware-dir` 指向文件实际所在的目录；子目录需要另外指定。这个仓库不包含原厂固件、个人备份或镜像。I3588 的硬件 BOOT 键直接进入 BootROM，VOL+/RECOVERY 才由公用 U-Boot 策略处理。PHX 的下载键和 G98 的恢复键是各自的板包配置。

从 RKdev-boards 根目录，用相邻的 RKdev 校验或构建，例如：

```sh
python3 ../RKdev/tools/rkdev.py lint --board boards/phx-r3588/v1 --profile emmc
sudo env "PATH=$PATH" python3 ../RKdev/tools/rkdev.py build \
  --board boards/phx-r3588/v1 --profile emmc --locked \
  --firmware-dir /path/to/fw/brcm --firmware-dir /path/to/fw/mali \
  --firmware-dir /path/to/fw/regdb --out out/phx
```

板包构建可使用 [RKdev 的板包接口](https://github.com/dqsq2e2/RKdev/blob/main/docs/board-package.md)。提交时附上所用 RKdev 提交、构建日志和 `verify` 结果。固件仍为开发候选，既有项目的旧版实机结果不代表 RKdev 镜像已通过实机验收。

I3588 恢复系统的 PCIe 网口使用 WAN DHCP。板载网口与免密码热点 `I3588-Recovery` 桥接；接入后从 `http://192.168.88.1/` 进入刷机页。HDMI 显示原有 Logo、LAN/Wi-Fi 入口和实际 WAN 地址。SSH、串口及 HDMI 控制台沿用 `root/root`；刷机页直接打开。

## GitHub Actions 按板构建

在本仓库的 **Actions → RKdev board builds → Run workflow** 选择板型和 profile。`default` 采用板包默认的 SPI 或 eMMC。作业检出锁定提交的 `RKdev`，构建主线 U-Boot 和恢复系统，校验后从运行页面的 **Artifacts** 下载整盘 `.img`、配套 `.json`、`SHA256SUMS` 和独立 U-Boot 文件。

有 `file` 类型固件的板包还需要固件 ZIP。把 `board.json` 中 `firmware` 及对应 profile 的 `firmware` 所列 `file` 放在 ZIP 的 `<板型>/<文件名>` 下；单板 ZIP 也可以放在根目录。运行时在 `firmware_bundle_url` 填公开的 HTTPS 下载地址，或在仓库 Actions secrets 设置 `RKDEV_FIRMWARE_BUNDLE_URL`。作业只提取选中板子需要的文件并逐个核对 SHA-256。公开仓库的构建产物可被有读取权限的 GitHub 用户下载。
