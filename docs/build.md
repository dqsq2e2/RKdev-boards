# 构建板级固件

## GitHub Actions

推送和 PR 触发 **检查全部板包**。要编译固件，打开 [Actions → 按板型构建并发布](https://github.com/dqsq2e2/RKdev-boards/actions/workflows/ci.yml)，点击 **Run workflow**，选择板型和介质。手动运行只检查和构建所选板型；从 `main` 构建成功后发布。

介质选 `default` 时采用板包默认值，并计入对应介质的序列。版本日期前缀按北京时间构建日期生成，`rN` 按 **北京时间日期 + 板型 + 启动介质** 分别计数。比如 `bdy-g98` 的 SPI 当天第一次和第二次构建是 `11.26-r1`、`11.26-r2`，跨到下一天后重新从当天的 `r1` 开始；G98 eMMC、PHX eMMC 和其他板型各自独立计数。失败作业也占用序号，重跑沿用原版本。发布标签为 `<板型>-<介质>-<年份>-v<版本>`。每个板型的每种启动介质各保留一份最新发布。旧版整条工作流共用的序号不计入新序列，启用板型和介质独立计数后，各组合分别从 `r1` 开始，并清理对应的旧发布和标签。

构建完成后，工作流把完整镜像与配套清单打成 `<板型>-v1-<介质>-<版本>.zip`，同时发布独立 U-Boot 和 `SHA256SUMS`。下载后可用 `sha256sum -c SHA256SUMS` 校验 ZIP 与 U-Boot。

AIUI 可以直接构建。其他板型需要板包 `board.json` 中引用的外部固件。将 `firmware` 和所选 profile 的 `firmware` 里标为 `file` 的文件放在 ZIP 的 `<板包目录名>/<文件名>` 下，也兼容 `board_id` 目录。只有单板时可以放在 ZIP 根目录。通过 `firmware_bundle_url` 指定 HTTPS 地址，或在仓库的 Actions secrets 中设置 `RKDEV_FIRMWARE_BUNDLE_URL`。

## 本地构建

在 Linux 或 WSL 中检出相邻的 RKdev 仓库，版本见 [RKdev 源码检出配置](../.github/actions/checkout-rkdev/action.yml) 中的 `ref`。安装 [RKdev 构建依赖](https://github.com/dqsq2e2/RKdev#用外部板包构建) 后，在本仓库根目录运行：

```sh
sudo env "PATH=$PATH" python3 ../RKdev/tools/rkdev.py build --locked \
  --board boards/aiui-3588/v1 --profile emmc --out out/aiui-3588
```

对于需要外部固件的板包，加 `--firmware-dir /path/to/firmware` 指向固件文件的目录；多个目录可重复传入。
