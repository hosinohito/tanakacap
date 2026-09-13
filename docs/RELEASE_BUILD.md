# 配布ZIPのビルド

開発者向け手順。利用者向けは [USER_GUIDE.md](USER_GUIDE.md) に分離する。

```powershell
.\build-release.ps1 -Version 0.1.0-review3
```

認証済みUnity 2022.3.22f1（現在Personal）、lockどおりの開発venv、同梱対象モデルが必要。公開Playerは `BuildRelease.Build` で空のシーンから作り、原本アバター/検証動画/VRChat SDKを配布へ含めない。ExporterはUnitypackageとして同時生成。Playerのビルドは `builds/release-player`、梱包結果は `builds/releases/<version>`。既存バージョンは上書きせず、新しい版名を渡す。`-SkipUnity` は既存release-playerを使用する。

## ZIPの内容

- `プラグイン/TanakaCapExporter.unitypackage`：利用者のVRCSDK環境にインポート。
- `builds/lab`：製品Player。開発時の相対パス互換を維持した内部配置で、アバターは埋め込まない。
- `capture_lab`：推論/制御/UI、`runtime`：再配置可能なPython・標準Tk・lockから選んだ実行ライブラリ。
- `models`：通常全身/顔専用/頭専用/虹彩/人物検出の必要モデル。SAM/HaMeR/MANO等の比較専用モデルは除外。
- `TanakaCap.bat`：UI起動。利用者によるPythonやpipの操作は不要。
- `使い方.md`、`ライセンス`、全ファイルSHA256の `manifest.json`、公開準備状態 `release-status.json`。

開発venvを丸ごとコピーしない。lockと一致したdistributionのRECORD記載ファイルを集め、テスト/インストーラー向けパッケージは除外。移動後のPython/Tk/NumPy/OpenCV/ONNX/ORT/UI設定読込を検査する。原本ONNXを同梱し、FP16等の派生は初回使用時に生成。ZIP CRC全件検査、ファイル数・圧縮後サイズ・SHA256を `release-report.json` へ記録する。

## GitHub Releases

[公式制限](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)は一つの添付ファイルが2GiB未満。全内容をまず一つへ圧縮し、収まれば単独ZIP。超える場合だけ独立ZIPへ分割し、同じTanakaCapフォルダーに展開して併用する。アップロード対象は `release-report.json` のassetsだけ。分割前の `oversize-local-only.zip` は検査用でアップロードしない。

最初の同梱試験は2,088,759,516 bytesで単独ZIPに収まった。これは当該依存/モデルの構成値で、将来も収まる保証ではない。以後のビルドでも実サイズを検査する。

GitHub Actionsは `.github/workflows/release-build.yml` の手動起動のみ。`tanakacap-release` ラベルのWindowsセルフホストrunnerに認証済みUnity、uv、NVIDIAドライバーと `TANAKACAP_MODEL_DEPOT`（models相当のローカルキャッシュ）を用意する。モデルや録画をリポジトリへ追加しない。lockからvenvを再構成し、同じbuild-release.ps1を実行してActions成果物へ保存する。GitHub Release自体の公開は自動実行しない。Actions側の実実行は未検証。checkout/upload-artifact v4は既存runner互換を優先し、公式READMEで仕様を確認した。

独自コードはユーザー指定のMIT。実物の監査結果とNVIDIA/FFmpeg/Unity Personalの確定条件は[RUNTIME_LICENSE_DECISIONS.md](RUNTIME_LICENSE_DECISIONS.md)。モデル条件は[MODEL_LICENSE_DECISIONS.md](MODEL_LICENSE_DECISIONS.md)で商用利用・再配布可と判定済み。通知20件をrelease/noticesへ出所/SHA付きで固定し、ビルド時にlicense-audit.jsonへ本文・モデル・全ネイティブファイルの照合結果を記録します。NVIDIAのヘッダー/インポートライブラリは製品から除外。本文の追加取得はtools/collect_release_notices.pyで行い、更新後の差分を確認してコミットしてください。モデル同一性の再照合はtools/collect_model_license_evidence.py。通常ビルドはネット取得せず固定本文を使います。

生成物は引き続きローカルレビュー用。`release/config.json`に残件を管理し、未解決のまま `-Publishable` を指定すると停止する。公開/アップロードはこのスクリプトでは行わない。機械検査成功は新規PC導入成功や全モデルの配布許諾確定を意味しない。

## 対応ソースと最新の配布判定

ビルド前に `.\.venv\Scripts\python.exe tools/prepare_ffmpeg_sources.py` を実行する。固定ソースから約161 MBの `assets-source/licenses/opencv-ffmpeg-sources.zip` を作り、製品の `ライセンス/sources` へ同梱する。CIも同じ準備を行う。再取得時はsource lockと照合する。サイズ上限超過時は既存の連番ZIP分割を使う。通知やソースが欠ける、DLLが監査版と違う場合はビルドを失敗させる。

NVIDIA/FFmpeg/Unityの旧3残件は[解消済み](RUNTIME_LICENSE_DECISIONS.md)。`publication_approved=false` は最終出荷のゲートで、未確定ライセンスが残っている意味ではない。Personalの財務上限とUnityロゴ維持を守る。ビルドのバッチ起動は通常Editorであり、別商品Unity Build Server契約は使っていない。
