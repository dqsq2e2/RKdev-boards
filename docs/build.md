# 构建板级固件

## GitHub Actions

推送和 PR 触发 **检查全部板包**。要编译固件，打开 [Actions → 按板型构建并发布](https://github.com/dqsq2e2/RKdev-boards/actions/workflows/ci.yml)，点击 **Run workflow**，选择板型和介质。手动运行只检查和构建所选板型；从 `main` 构建成功后发布。

介质选 `default` 时采用板包默认值。版本留空时使用 `0.1-ci.<运行编号>`；发布标签为 `<板型>-<介质>-v<版本>`。每个板型只保留最近一次发布的固件。

AIUI 可以直接构建。其他板型需要板包 `board.json` 中引用的外部固件。将 `firmware` 和所选 profile 的 `firmware` 里标为 `file` 的文件放在 ZIP 的 `<板型>/<文件名>` 下，只有单板时也可以放在 ZIP 根目录。通过 `firmware_bundle_url` 指定 HTTPS 地址，或在仓库的 Actions secrets 中设置 `RKDEV_FIRMWARE_BUNDLE_URL`。

## 本地构建

在 Linux 或 WSL 中检出相邻的 RKdev 仓库，版本见 [RKdev 源码检出配置](../.github/actions/checkout-rkdev/action.yml) 中的 `ref`。安装 [RKdev 构建依赖](https://github.com/dqsq2e2/RKdev#用外部板包构建) 后，在本仓库根目录运行：

```sh
sudo env "PATH=$PATH" python3 ../RKdev/tools/rkdev.py build --locked \
  --board boards/aiui/v1 --profile emmc --out out/aiui
```

对于需要外部固件的板包，加 `--firmware-dir /path/to/firmware` 指向固件文件的目录；多个目录可重复传入。
