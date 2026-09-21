# 配布ZIPのビルド

ZIP不要のローカル試験は `build-release.bat -NoZip -Version <未使用版名>`。通常と同じPlayer/Exporter/UI/依存/モデル/説明書/ライセンスを組み立て、原本・可搬Python・ライセンス監査・manifest作成まで行う。展開済み`builds/releases/<版名>/TanakaCap/`が成果物。ZIP生成と公開は行わない。

開発者向け手順。利用者向けは [user_guide.txt](user_guide.txt) に分離する。

環境準備後はプロジェクト直下の **build-release.batをダブルクリック**する。AIや手作業によるソース生成は不要。Unityでこのプロジェクトを開いている場合は先に閉じる。

素材/SHA/依存版の確認→Unity PlayerとExporterをソースからビルド→同梱・監査・ZIP分割・CRC検査を行う。版名は日時から自動生成し、既存リリースを上書きしない。最後に保存先を表示し、画面はキーを押すまで閉じない。GitHubへのアップロードはしない。

必要なときだけ `build-release.bat -Version 0.1.0-test1` で名前を指定する。`build-release.bat -CheckOnly` は入力確認のみで、Unity起動やネット取得を行わない。通常ビルドはFFmpeg対応ソースZIPが欠けていれば固定版から自動準備し、他の原本不足は一覧を表示して停止する。ログは `results/release-build-<版>.log` と `results/unity-release-<版>.log`。

## 保管する原本

| 場所 | 内容・保管上の注意 |
| --- | --- |
| tanakacap / unity/TanakaCap/Assets/TanakaCap / ProjectSettings | Python UI・推論・Unity・Exporterのソース。Git管理 |
| unity/TanakaCap/Packages | 使用中のlilToon/KlakSpout等の原本。Git管理外の埋め込みパッケージも含めて保管 |
| models | 学習済み原本と取得記録。大容量のためGit管理外。release/models.lock.jsonと照合 |
| assets-source/licenses/opencv-ffmpeg-sources.zip | 配布に添付する対応ソース。Git管理外、固定版から再作成可能 |
| release / docs / tracking-settings.json / requirements.lock.txt | 通知原文・ライセンス・設定・手順・依存版。Git管理 |

**Git cloneだけではモデルや埋め込みパッケージは復元されない**。移行・バックアップ時はそれらも保管する。アバター原本や過去の比較動画・既存Playerは、通常の配布ビルドの入力ではない。

外部ツールは認証済みUnity 2022.3.22f1 PersonalとPython 3.11環境が必要。現在の.venvはインストール済みPythonを参照するため、そのフォルダーだけを別PCへコピーしてビルド環境になるとは限らない。別PCでは[開発環境](DEVELOPMENT.md)のuv/lock手順で再構成する。今回の.batはその導入やUnity認証を勝手に変更しない。

認証済みUnity 2022.3.22f1（現在Personal）、lockどおりの開発venv、同梱対象モデルが必要。公開Playerは `BuildRelease.Build` で空のシーンから作り、原本アバター/検証動画/VRChat SDKを配布へ含めない。ExporterはUnitypackageとして同時生成。Playerのビルドは `builds/release-player`、梱包結果は `builds/releases/<version>`。既存バージョンは上書きせず、新しい版名を渡す。`-SkipUnity` は既存release-playerを使用する。

## ZIPの内容

- `プラグイン/TanakaCapExporter.unitypackage`：利用者のVRCSDK環境にインポート。
- `app`：製品Player一式。アバターは埋め込まない。
- `tanakacap`：推論/制御/UI、`runtime`：再配置可能なPython・標準Tk・lockから選んだ実行ライブラリ。
- `models`：通常全身/顔専用/頭専用/虹彩/人物検出の必要モデル。SAM/HaMeR/MANO等の比較専用モデルは除外。
- `TanakaCap.bat`：UI起動。利用者によるPythonやpipの操作は不要。
- `使い方.txt`、`ライセンス`、全ファイルSHA256の `manifest.json`、公開準備状態 `release-status.json`。

開発venvを丸ごとコピーしない。lockと一致したdistributionのRECORD記載ファイルを集め、テスト/インストーラー向けパッケージは除外。移動後のPython/Tk/NumPy/OpenCV/ONNX/ORT/UI設定読込を検査する。原本ONNXを同梱し、FP16等の派生は初回使用時に生成。ZIP CRC全件検査、ファイル数・圧縮後サイズ・SHA256を `release-report.json` へ記録する。

## GitHub Releases

[公式制限](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)は一つの添付ファイルが2GiB未満。全内容をまず一つへ圧縮し、収まれば単独ZIP。超える場合だけ独立ZIPへ分割し、同じTanakaCapフォルダーに展開して併用する。アップロード対象は `release-report.json` のassetsだけ。分割前の `oversize-local-only.zip` は検査用でアップロードしない。

最初の同梱試験は2,088,759,516 bytesで単独ZIPに収まった。これは当該依存/モデルの構成値で、将来も収まる保証ではない。以後のビルドでも実サイズを検査する。

GitHub Actionsは `.github/workflows/release-build.yml` の手動起動のみ。`tanakacap-release` ラベルのWindowsセルフホストrunnerに認証済みUnity、uv、NVIDIAドライバーと `TANAKACAP_MODEL_DEPOT`（models相当のローカルキャッシュ）を用意する。モデルや録画をリポジトリへ追加しない。lockからvenvを再構成し、同じbuild-release.ps1を実行してActions成果物へ保存する。GitHub Release自体の公開は自動実行しない。Actions側の実実行は未検証。checkout/upload-artifact v4は既存runner互換を優先し、公式READMEで仕様を確認した。

独自コードはユーザー指定のMIT。実物の監査結果とNVIDIA/FFmpeg/Unity Personalの確定条件は[RUNTIME_LICENSE_DECISIONS.md](RUNTIME_LICENSE_DECISIONS.md)。モデル条件は[MODEL_LICENSE_DECISIONS.md](MODEL_LICENSE_DECISIONS.md)で商用利用・再配布可と判定済み。通知20件をrelease/noticesへ出所/SHA付きで固定し、ビルド時にlicense-audit.jsonへ本文・モデル・全ネイティブファイルの照合結果を記録します。NVIDIAのヘッダー/インポートライブラリは製品から除外。本文の追加取得はtools/collect_release_notices.pyで行い、更新後の差分を確認してコミットしてください。モデル同一性の再照合はtools/collect_model_license_evidence.py。通常ビルドはネット取得せず固定本文を使います。

`-Publishable` 指定時の生成物は公開用です。`release/config.json`に残件を管理し、未解決のまま `-Publishable` を指定すると停止する。公開/アップロードはこのスクリプトでは行わない。機械検査成功は新規PC導入成功や全モデルの配布許諾確定を意味しない。

## 対応ソースと最新の配布判定

ビルド前に `.\.venv\Scripts\python.exe tools/prepare_ffmpeg_sources.py` を実行する。固定ソースから約161 MBの `assets-source/licenses/opencv-ffmpeg-sources.zip` を作り、製品の `ライセンス/sources` へ同梱する。CIも同じ準備を行う。再取得時はsource lockと照合する。サイズ上限超過時は既存の連番ZIP分割を使う。通知やソースが欠ける、DLLが監査版と違う場合はビルドを失敗させる。

NVIDIA/FFmpeg/Unityの旧3残件は[解消済み](RUNTIME_LICENSE_DECISIONS.md)。`publication_approved` は最終出荷のゲートです。現在は `true`、ライセンス残件は空で、公開用ビルドが可能です。Personalの財務上限とUnityロゴ維持を守る。ビルドのバッチ起動は通常Editorであり、別商品Unity Build Server契約は使っていない。
