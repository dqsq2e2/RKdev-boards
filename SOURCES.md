# 板包来源

以下是板包迁移所据的源码与本地适配状态。构建只需要本仓库中的文本及清单声明的固件输入。

| 板型 | U-Boot DTS／配置 | Linux DTS／配置 |
| --- | --- | --- |
| BDY-G98 | G98 主线快照 `6ae769be0b534679147fb80915e9b53db6b52e14` 的 `only-spi/` | G98 恢复快照中的 only-SPI DTS、recovery defconfig 和网络驱动变更 |
| PHX-R3588 | PHX 主线快照 `ecb17469b4ae87e4da67a0742914cd4fb3e06a8b` 的 PHX DTS、配置和 regulator 初始化 | PHX 恢复快照 `dc2a6d388d0bcbe9ab97a1fd7d9aecf013965481` 的 DTS、配置和 brcmfmac 变更 |
| 9Tripod I3588 | I3588 主线快照 `a1fbbe25383824f771b4fae8c389d7f075960731` 的 DTS 与配置 | I3588 恢复快照 `7fa7bea7745c` 的 DTS 与配置 |
| LUNZN RK3588 AIUI | AIUI 主线快照 `5c173eaeec8967fc95c55b209bccb82a7b8b9caa` | AIUI 恢复分支 `7e367137806b` 与 `10.26-pwm` 使用的 DT、恢复内核配置及 Type-C、显示和风扇补丁 |
| SMDT AIOT-3588A V2.0 | `75b2dde207e10a9dbc1af2a73214fe033278394e` 的 DTS、配置与 USB 供电初始化 | `45f5f216dde1592988a058363b66d152a4dd6335` 的恢复 DTS、配置、开机界面、网络与 MCU 喂狗程序 |

源码沿用被迁移文件的 SPDX 或源树的相应许可。Rockchip DDR/BL31、厂商无线与图形固件均从板包声明的来源另行获取；其再分发按相应固件条件处理。这个仓库只附上文件名、上游 URL（如可获取）及校验和。

I3588 的 `bl31.elf` 来自 Trusted Firmware-A 提交 `a881364e03b0c5b3a8c00f20ad6fbdda53a57031` 的 RK3588 构建。由适配者提供与板包 SHA-256 一致的文件。

I3588 的 HDMI 内核 Logo 沿用旧恢复源码 `1f0455e8c` 的 `drivers/video/logo/logo_linux_clut224.ppm`。LAN/WAN、Wi-Fi AP、HDMI 地址提示和 sshd/getty 启动设置对应 `840c4d9ab` 及原配套恢复镜像。它们是板包内容；构建仍使用 RKdev 锁定的上游源码。
