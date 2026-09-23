# 開発環境と検証

公開プロジェクトの入口は[README](../README.md)、利用者の導入・操作は[使い方](user_guide.txt)を参照。ここではソースから開発する手順を扱う。コマンドはリポジトリ直下のPowerShellで実行する。

## 必要な環境

| 項目 | 構成 |
| --- | --- |
| OS / GPU | Windows 64bit / NVIDIA RTX。GPU推論の確認には`nvidia-smi`を使用 |
| ツール | Git、PowerShell、[uv](https://docs.astral.sh/uv/getting-started/installation/) |
| Python | 3.11系。既存検証環境は3.11.16 |
| Unity | 2022.3.22f1、Windows64ビルド対応。Unity Hubで有効なライセンスを確認 |
| 描画 | Built-in Render Pipeline、lilToon 2.3.4、KlakSpout 2.0.6 |
| OBS検証 | OBSとSpout2プラグイン。手順は[OBS](OBS.md) |

Unity EditorはPlayer／Exporterのビルドに必要。Pythonだけの編集・単体テストでは起動しない。既存の検証用アバターや録画はGitに含まれず、新規cloneでは使えない。

## Pythonとモデル

```powershell
git clone https://github.com/hosinohito/tanakacap.git
Set-Location tanakacap
.\setup.ps1 -Python 3.11.16
.\.venv\Scripts\python.exe -m tanakacap environment
```

[setup.ps1](../setup.ps1)は`.venv`を作成し、[requirements.lock.txt](../requirements.lock.txt)に従って依存を同期する。再実行でもlockへ同期される。CUDA/cuDNNもここから導入し、CPUへの暗黙の代替をGPU動作の成功と扱わない。

初回はネットワーク接続が必要。RTMW-L、DWPose-L、YOLOX-m-human、RTMW3D-Xを`models/`へ取得する。取得先は[モデルカタログ](../models/catalog.json)、配布対象の同一性は[モデルlock](../release/models.lock.json)を参照。SAM／HaMeR／MANOは比較研究用で、通常の導入には不要。

PowerShellの実行ポリシーで拒否される環境では、必要に応じてそのターミナルだけ許可する。

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 目線用モデル


現在のセットアップスクリプトは虹彩モデルを取得しない。既定は`gaze_enabled: true`なので、通常のカメラ起動には追加が必要。モーション版だけなら不要。

配布元：[PINTO Iris Landmark](https://github.com/PINTO0309/PINTO_model_zoo/tree/main/049_iris_landmark)


```powershell
New-Item -ItemType Directory -Force results, models | Out-Null
Invoke-WebRequest -Uri 'https://s3.ap-northeast-2.wasabisys.com/pinto-model-zoo/049_iris_landmark/resources.tar.gz' -OutFile 'results/iris-resources.tar.gz'
```

次をPowerShellへまとめて貼り付ける。指定したONNXだけを取り出し、実装が要求するSHA256を確認する。既存モデルが異なる場合は上書きしない。

```powershell
@'
import hashlib, io, tarfile
from pathlib import Path
with tarfile.open('results/iris-resources.tar.gz') as outer:
    name = next(n for n in outer.getnames() if n.endswith('20_new_20211209/resources.tar.gz'))
    with tarfile.open(fileobj=io.BytesIO(outer.extractfile(name).read())) as inner:
        name = next(n for n in inner.getnames() if n.endswith('saved_model_64x64/model_float32.onnx'))
        data = inner.extractfile(name).read()
expected = 'e3c8ae73a21415e396688d655d5f1d9e1cb5a01b7ed19962de76c06458bfddcb'
assert hashlib.sha256(data).hexdigest() == expected, 'Unexpected iris model'
target = Path('models/iris-landmark.onnx')
assert not target.exists() or target.read_bytes() == data, 'Existing model differs'
target.write_bytes(data)
print(target)
'@ | .\.venv\Scripts\python.exe -
```

上流のLICENSEも取得物とともに保管する。出典・許諾記録は[THIRD_PARTY.md](THIRD_PARTY.md)。モデルの商用利用・再配布条件は[モデル監査](MODEL_LICENSE_DECISIONS.md)で確認済み。目線を使わず確認したい場合は`tracking-settings.json`の`gaze_enabled`だけを`false`へ変更して起動できる。

### 頭専用モデル

頭専用モードの2モデルはsetup.ps1の取得対象外。[頭専用モードのモデル取得](HEAD_ONLY.md#モデル取得)に従って配置する。配布ビルドでは全モードの対象モデルが必要で、モデルlockとの照合に失敗すると停止する。

## Unityと配布構成のビルド

Unityプロジェクトは`unity/TanakaCap/`。同じプロジェクトを開いたEditorと、更新先を使用中のPlayerを閉じる。Git管理外の埋め込みパッケージは別途用意する。lilToonは[2.3.4のリリースZIP](https://github.com/lilxyzw/lilToon/releases/tag/2.3.4)のパッケージを`unity/TanakaCap/Packages/jp.lilxyzw.liltoon/`へ配置し、直下に`package.json`があることを確認する。

```powershell
# 対応ソースを準備し、不足・変更された入力を確認
.\.venv\Scripts\python.exe tools/prepare_ffmpeg_sources.py
.\build-release.bat -CheckOnly

# ZIPを作らず、別PCへコピーできる構成を作る（未使用の版名を指定）
.\build-release.bat -NoZip -Version dev-check-001
```

成果物は`builds/releases/dev-check-001/TanakaCap/`。その中の`TanakaCap.bat`でUIを起動する。通常の配布Playerは空のシーンから作り、個人アバターを埋め込まない。アバターは付属Exporterで別途書き出し、UIで選択する。

Unityの場所が異なる場合は`build-release.ps1`の`-Unity`で実行ファイルを指定する。認証失敗時はUnity Hubのライセンスを確認する。必要な原本、ログ、ZIP作成、CI、ライセンス監査は[配布ビルド](RELEASE_BUILD.md)を参照。ビルドだけでGitHubへ公開はしない。

### ローカルのHAOLAN検証ビルド


既存のHAOLAN用ビルドを再現する場合だけ、次のローカル素材が必要。通常の配布Playerのビルドには不要。HAOLANは購入者自身が取得する。

| 保存先 | 取得するもの |
|---|---|
| `assets-source/HAOLAN_Ver1.6.zip` | HAOLAN 1.6原本。内部に`HAOLAN_Ver1.6/HAOLAN_PC.unitypackage`が必要 |
| `assets-source/jp.lilxyzw.liltoon-2.3.4.zip` | lilToon 2.3.4リリースの同名ZIP。GitHubの「Source code」ZIPではない |
| `assets-source/haolan-license-ja.pdf` | 作者提供の日本語利用規約PDF。HAOLAN用の開発ビルドが成果物へコピーするため必要 |

- HAOLAN（作者：かなリぁ）：https://booth.pm/ja/items/3818504
- 作者の利用規約配布先：https://drive.google.com/drive/folders/1YUDZYWJyZPLCqWOkAFrlyIGkYGs4dVMV
- lilToon 2.3.4：https://github.com/lilxyzw/lilToon/releases/tag/2.3.4

```powershell
.\.venv\Scripts\python.exe tools/prepare_unity.py
```

原本を保持したまま、アバターを`unity/TanakaCap/Assets/HAOLAN/`、lilToonを同プロジェクトの`Packages/jp.lilxyzw.liltoon/`へ取り込む。取り込み先に異なる内容がある場合は停止する。改変を消して再取り込みする手順ではない。

KlakSpout 2.0.6は`unity/TanakaCap/Packages/jp.keijiro.klak.spout/`にGit管理済み。この開発ビルドのためにVRChat SDKを追加する必要はない。SDK欠損状態のPhysBone設定は原本テキストPrefabから変換する。

```powershell
New-Item -ItemType Directory -Force results | Out-Null
.\build-player.ps1
# Unityの導入先が異なる場合
.\build-player.ps1 -Unity 'C:\YourUnityPath\2022.3.22f1\Editor\Unity.exe'
```

これは[BuildPlayer.cs](../unity/TanakaCap/Assets/TanakaCap/Editor/BuildPlayer.cs)による素材付き検証用ビルド。成果物は`builds/player/`、ログは`results/unity-build.log`。`avatars/haolan.tcap`と変換レポートも生成する。生成シーンへの直接編集ではなく、恒久的な変更はソースへ反映する。素材の改変を上書きして復元しない。

## 開発UI・設定・ログ

```powershell
.\run-ui.ps1
# デスクトップの通常／検証ランチャーを再生成
.\tools\update-desktop-launcher.ps1
```

UIでアバターと入力を選んで「保存して開始」を押す。録画での試験には録画入力を選ぶ。カメラ番号を開発PCの値に固定しない。現在の検証アバター・録画・ランチャーは[HANDOFF](../HANDOFF.md)を確認する。過去の比較用batがすべて存在するとは限らない。

| ファイル | 役割 |
| --- | --- |
| `ui-settings.json` | 個人の実行設定。Git管理外 |
| [ui-settings.example.json](../ui-settings.example.json) | 公開用の設定ひな形。配布ビルドはこちらを使用 |
| [tracking-settings.json](../tracking-settings.json) | 共通の追跡設定 |
| [docs/ui-part-costs.json](ui-part-costs.json) | UIに表示する参考負荷 |

開発UIは`logs/development-*.jsonl`へ設定・コンソール・性能値を記録し、8MiBでローテーションする。実写画像・音声は保存しない。配布版の既定はエラーのみ。Playerのエラーは起動用bat近くの`logs/player-errors.log`へ出力する。

実写は録画や診断表示も含めて通常は画面に表示しない。必要な開発試験だけ、起動時に完全一致の`--explicitly-allow-displaying-raw-camera-images-on-screen-for-this-session-only`を指定する。通常ランチャーへ自動追加しない。[表示ガード](../tanakacap/camera_display.py)と[検査](../tests/test_camera_display.py)を維持する。

## 検証

```powershell
# モデル・カメラを起動しないPythonテスト
.\.venv\Scripts\python.exe -m pytest -q

# ビルド済み開発Playerへの合成入力
.\.venv\Scripts\python.exe tools/smoke_unity.py --motion-check --output results/dev-smoke/transport.png
```

pytestは`tests/`を収集し、Windowsの一時フォルダーを`results/pytest-scratch/`へ作成・後処理する。管理者実行や手動の`--basetemp`指定は不要。Player試験は普段使いのPlayerを閉じ、必要なアバターを配置してから行う。

追跡品質の検証は既存録画を基本とする。実カメラの使用は明示した試験時だけ行う。合成入力の成功、録画での動作確認、本人による見た目評価を区別する。新規PCの完全な導入試験は、この文書の整理では実施していない。

継続利用する診断は[tools/diagnostics](../tools/diagnostics/README.md)、一時試験はデスクトップの`tanakacap-tools/`へ置く。性能条件・長時間試験は[検証仕様](PHASE4_VALIDATION.md)を参照。

## 実装・比較の参照先

| 内容 | 担当文書 |
| --- | --- |
| UI・実験項目・参考負荷 | [操作UI](CONTROL_PANEL.md)、[実験項目監査](UI_EXPERIMENT_AUDIT.md) |
| 推論と部位別更新 | [推論経路](INFERENCE_PIPELINE.md)、[部位別送受信](PARTIAL_TRACKING_DESIGN.md) |
| 表情・視線・頭角度 | [表情キー](EXPRESSION_PORTABILITY.md)、[大げさ度](FACIAL_EXAGGERATION.md)、[視線](GAZE_RESPONSE.md)、[頭角度試行](HEAD_SIZE_TRIAL.md) |
| 肩・腕・指の補正 | [肩](SHOULDER_CONTINUOUS_CORRECTION.md)、[前方補正比較](ARM_CORRECTION_ISOLATION.md)、[手の頭回避](HAND_HEAD_CONTACT.md)、[肘回転](ARM_ROTATION_COUPLED.md) |
| 揺れ・書き出し | [揺れ物](SECONDARY_MOTION.md)、[本家比較](PHYSBONE_REFERENCE.md)、[着せ替え調査](EXPORT_TOOL_RESEARCH.md) |
| 高速化の採否・測定 | [全機能](FULL_MODE_OPTIMIZATION.md)、[追加案](FURTHER_OPTIMIZATION.md)、[FP16比較](PRECISION_COMPARISON.md) |
| 描画・OBS | [AA](ANTIALIASING.md)、[描画共有](SHARED_PREVIEW.md)、[描画レート比較](RENDER_RATE_COMPARISON.md)、[OBS](OBS.md) |
| カメラ | [対応方式・制約](CAMERA_COMPATIBILITY.md) |

比較文書の日付付き結果はその時点の条件を表す。現在の採用値は設定ファイル・機能仕様と最新のHANDOFFを照合する。廃止済みのデモ専用アバターや旧起動引数は復活させない。

## 配置・引き継ぎ

`tanakacap/`がPython、`unity/TanakaCap/Assets/TanakaCap/`がPlayer／Exporter、`tests/`と`tools/`が検証・ビルド補助。`assets-source/`、モデル重み、録画、アバター、`builds/`、`results/`、環境キャッシュ、個人設定はGitへ追加しない。公開前は[データ確認](RELEASE_PRIVACY.md)と配布監査を行う。

別PCで配布構成を試す場合は生成された`TanakaCap/`全体をコピーする。更新時にPlayerのexeだけをコピーしない。ソース開発環境の移行ではモデル・埋め込みパッケージも保管し、Python環境はlockから再構成する。

文書の役割は[AGENTS](../AGENTS.md)に従う。READMEは公開入口、この文書は開発手順、機能別仕様書は現在の設計、[PROGRESS](PROGRESS.md)は履歴、[HANDOFF](../HANDOFF.md)は再開状態を担当する。手順を変えたら担当文書も同時に更新し、同じ完了報告を各文書へ複製しない。

別のCodexインスタンスで再開するときも、会話履歴を前提にしない。AGENTS → HANDOFF冒頭 → 関連仕様 → PROGRESS末尾の順に読み、採用済み・保留・撤回済みと、実装／検証／見た目確認の到達点を区別する。作業終了時は次の作業・検証方法・必要ファイルの場所をHANDOFFへ残す。


### 手のリアルタイム診断

開発Playerをビルドし、`tools/update-desktop-launcher.ps1` で生成したデスクトップ `tanakacap-tools/tanakacap-hands-video.bat`（保存録画）または `tanakacap-hands-camera.bat`（実カメラ・ユーザー操作）を使う。全身ON/auto-custom、部位別通信と実骨ログを保存する。SPACE/Qは黒いコンソールで操作。[ログ・検査方法](HAND_SIDE_AUDIT.md#6秒15秒の照合と実時間診断)。別PCの開発環境へは `builds/player/` 全体、`tools/diagnostics/realtime_hands.py`、`tools/diagnostics/summarize_realtime_hands.py`、`tools/update-desktop-launcher.ps1` を同じ配置へコピーし、そのPCでランチャーを再生成。アバターと動画パスはそのPCのUIで選び直す。Exporter/モデルの更新は不要。


手の左右反転診断は `tools/diagnostics/compare_hand_mirror.py` と `summarize_hand_mirror.py`。引数は[診断一覧](../tools/diagnostics/README.md)、現在の比較素材/動画は[HANDOFF](../HANDOFF.md)を参照。`tools/update-desktop-launcher.ps1` がデスクトップの `tanakacap-tools/tanakacap-compare-hand-mirror.bat` を生成し、アバター比較MP4の場所を開く。実写は表示しない。別PCで動画を見るだけならMP4のみコピーする。

元モデルとONNXの切り分けは [診断ツールの手順](../tools/diagnostics/README.md#公式pytorchとonnxの診断) を参照。PyTorch/MMPoseは製品と隔離した診断環境にのみ導入する。
