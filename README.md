# RKdev-boards

RKdev 的 Rockchip 板包和固件发布仓库。每个板包定义对应主板的设备树、启动介质、外设配置和镜像布局。主线 U-Boot、恢复网页和镜像构建工具来自 [RKdev](https://github.com/dqsq2e2/RKdev)。

| 主板 | 板包 | 启动介质 |
| --- | --- | --- |
| BDY-G98 | [`bdy-g98`](boards/bdy-g98/v1) | SPI NOR |
| PHX-R3588 | [`phx-r3588`](boards/phx-r3588/v1) | eMMC |
| 九鼎 I3588 | [`i3588`](boards/i3588/v1) | eMMC |
| LUNZN RK3588 AIUI | [`aiui`](boards/aiui/v1) | eMMC |
| 视美泰 AIOT-3588A V2.0 | [`aiot-3588a2`](boards/aiot-3588a2/v1) | eMMC |

## 下载固件

在 [Releases](https://github.com/dqsq2e2/RKdev-boards/releases) 按板型和介质下载 `.img`。完整镜像包含主线 U-Boot 和 RKdev 恢复系统；每个版本也提供独立 U-Boot、镜像清单和 `SHA256SUMS`。

I3588 的恢复热点为 `I3588-Recovery`，无需 Wi-Fi 密码。接入后打开 `http://192.168.88.1/`；有线入口可查看 HDMI 上显示的地址。

## 构建与适配

在 **Actions → RKdev board builds → Run workflow** 选择板型；介质选 `default` 即采用板包默认值。从 `main` 构建成功后，固件按板型和介质发布到 Releases。

本地构建及外部固件输入见[构建指南](docs/build.md)。适配新板可在 `boards/<板型>/<修订>/` 或独立仓库中实现 [RKdev 板包接口](https://github.com/dqsq2e2/RKdev/blob/main/docs/board-package.md)。
