# 開発用ツール

製品の起動はルートの `run-ui.ps1`、配布ビルドは `build-release.bat` を使います。

| 用途 | 主な入口 |
|---|---|
| 配布物の生成・照合 | `build_release.py`、`check_release_inputs.py`、`audit_release_licenses.py` |
| カメラ診断 | `diagnostics/diagnose-camera.bat`（利用者が起動） |
| UIの自動検査 | `check_control_panel_ui.py`（偽プロセスを使用、カメラ不使用） |
| アバターの描画・パッケージ検査 | `smoke_unity.py`、`test_avatar_package.py` |
| 録画からの比較・解析 | `compare_*.py`、`audit_*.py`、`render_comparison_videos.py` |
| 開発用ランチャー更新 | `update-desktop-launcher.ps1` |

再利用する診断は `diagnostics/` に置きます。一時限りの調査スクリプトはデスクトップの `tanakacap-tools` に置き、プロジェクト直下へ追加しません。

初期録画に固定された使い捨ての検査9本と、旧 `camera_modes.cpp`／`build-camera-probe.cmd` は2026-09-13に削除しました。旧コードはGit履歴、検査結果と録画はローカルの `results/` に残っています。現行の実験機能と再利用する比較ツールは維持しています。

`bin/` の外部ツール、`results/`、`builds/` はGit対象外です。録画や原本モデルをコミットしないでください。
