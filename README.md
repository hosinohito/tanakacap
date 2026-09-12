# tanakacap

Webカメラ1台で、VRChat向け3Dアバターを動かしてOBSへ透過出力するWindows用プロジェクト。Unity Editorの書き出しプラグインと、外部アバターファイルを読み込む専用Unityアプリで構成する。

着席時の頭・目・口・上半身・腕・掌・指を対象に、RTX 4090で品質を優先して開発している。元のシェーダーの見た目を保ち、髪・服は元PhysBoneの設定を独立した近似ソルバーへ変換する。軽量化は基準品質の確立後に追加する。

**現在はHAOLAN 1.6向けの開発版。** 外部アバターの書き出し・読み込み、GPU推論、OBS透過受信、揺れ物を実装済み。汎用のVRC改変対応、本家PhysBoneとの動作一致、30分の安定性・OBS併用性能は未達成または未確認。仮想カメラ・コラボ送信・全身は後日の対象。重いゲームとの同時実行保証は要件に含めない。最新の評価は[HANDOFF.md](HANDOFF.md)、確定要件は[仕様書](docs/SPEC.md)を参照する。

## セットアップ済みの環境で起動する

デスクトップの次のbatを、使いたいもの一つだけ起動する。

| 起動ファイル | 動作 | 記録・時間制限 |
|---|---|---|
| `tanakacap-live.bat` | カメラでアバターを動かす | 動作ログなし・無制限 |
| `tanakacap-motion.bat` | カメラなしで自作モーションを繰り返す | 動作ログなし・無制限 |
| `tanakacap-test.bat` | カメラの追跡を検証する | 診断ログあり・1800フレーム |

通常はカメラ番号1。カメラプレビューのQ/Escで終了する。非記録カメラ版はアバターを閉じても推論が終了する。モーション版はアバターを閉じて終了する。詳しくは[起動モード](docs/LAUNCH_MODES.md)。

PowerShellからも起動できる。以下のコマンドはすべてリポジトリのルートで実行する。仮想環境のactivateは不要。

```powershell
Set-Location D:\work\tanakacap
.\run-avatar-lab.ps1 -Camera 1 -NoLog
```

```powershell
# カメラを使わない表示確認
.\run-motion-lab.ps1
```

```powershell
# 診断付きの短いカメラ検証
.\run-avatar-lab.ps1 -Camera 1 -Diagnose -Frames 1800
```

## 新しい環境のセットアップ

手順は現行スクリプトと照合済みだが、新しいPCでの一括導入試験は未実施。依存環境を同梱した一般配布用インストーラーはまだない。

### 1. 必要な環境

| 項目 | 使用する構成 |
|---|---|
| OS / GPU | Windows 64bit、NVIDIA RTX。主な実測環境はWindows 10 / RTX 4090 |
| GPUドライバー | `nvidia-smi`でGPUを確認できるNVIDIAドライバー |
| コマンド環境 | PowerShell、Git、[uv](https://docs.astral.sh/uv/getting-started/installation/) |
| Python | 3.11系。既存検証環境は3.11.16。uvでプロジェクト内の`.venv`を作る |
| Unity | **2022.3.22f1**。Unity Hubで導入・ライセンス認証し、Windows64向けビルドができる状態にする |
| 描画 | Built-in Render Pipeline / lilToon **2.3.4**。URP/HDRPへの変更は未対応 |
| OBS（出力を使う場合） | 検証済みはOBS Studio 32.2.2 + Spout2プラグイン1.12.0 |

Python依存は[requirements-lab.lock.txt](requirements-lab.lock.txt)に固定している。主要な使用版はONNX Runtime GPU 1.30.0、OpenCV 5.0.0.93、NumPy 2.4.6。CUDA/cuDNNのPythonパッケージもlockから導入する。CPU-only実行は主構成として許可しない。別GPUやドライバーでの可否は実行確認が必要。

uvの導入先：https://docs.astral.sh/uv/getting-started/installation/

リポジトリをローカルへ用意し、そのルートへ移動する。このPCでの配置は`D:\work\tanakacap`。ドライブD自体は必須ではない。

```powershell
Set-Location D:\work\tanakacap
uv --version
nvidia-smi
```

PowerShellの実行ポリシーでスクリプトが拒否される場合は、そのターミナルだけ許可する。

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 2. Python環境と通常の推論モデル

```powershell
.\setup-lab.ps1 -Python 3.11.16
.\.venv\Scripts\python.exe -m capture_lab environment
```

[setup-lab.ps1](setup-lab.ps1)は`.venv`作成、lockに従う依存同期、RTMW-L / DWPose-L / YOLOX-m-human / RTMW3D-Xの取得を行う。初回はネットワークが必要。モデルは`models/`へ保存し、取得元は[モデルカタログ](models/catalog.json)で管理する。再実行するとPython依存はlockへ同期される。

通常のカメラ起動はRTMW-Lの顔・手などの2D点、RTMW3D-Xの身体、YOLOXの人物検出を使う。設定は[tracking-settings.json](tracking-settings.json)。SAM / HaMeR / MANOは比較研究用で、通常起動の必須依存ではない。

### 3. 目線用の追加モデル

現在のセットアップスクリプトは虹彩モデルを取得しない。既定は`gaze_enabled: true`なので、通常のカメラ起動には追加が必要。モーション版だけなら不要。

配布元：[PINTO Iris Landmark](https://github.com/PINTO0309/PINTO_model_zoo/tree/main/049_iris_landmark)

URL：https://github.com/PINTO0309/PINTO_model_zoo/tree/main/049_iris_landmark

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

上流のLICENSEも取得物とともに保管する。出典・許諾記録は[THIRD_PARTY.md](docs/THIRD_PARTY.md)。モデルの製品同梱可否を確定した手順ではない。目線を使わず確認したい場合は`tracking-settings.json`の`gaze_enabled`だけを`false`へ変更して起動できる。

### 4. Unity用のローカル素材

Gitには原本アバター・モデル重み・ビルド成果物が入っていない。次を取得して配置する。HAOLANは購入者自身がBOOTHから取得する。

| 保存先 | 取得するもの |
|---|---|
| `assets-source/HAOLAN_Ver1.6.zip` | HAOLAN 1.6原本。内部に`HAOLAN_Ver1.6/HAOLAN_PC.unitypackage`が必要 |
| `assets-source/jp.lilxyzw.liltoon-2.3.4.zip` | lilToon 2.3.4リリースの同名ZIP。GitHubの「Source code」ZIPではない |
| `assets-source/haolan-license-ja.pdf` | 作者提供の日本語利用規約PDF。現行ビルドはこのファイルを成果物へコピーするため必要 |

- HAOLAN（作者：かなリぁ）：https://booth.pm/ja/items/3818504
- 作者の利用規約配布先：https://drive.google.com/drive/folders/1YUDZYWJyZPLCqWOkAFrlyIGkYGs4dVMV
- lilToon 2.3.4：https://github.com/lilxyzw/lilToon/releases/tag/2.3.4

```powershell
.\.venv\Scripts\python.exe tools/prepare_unity.py
```

原本を保持したまま、アバターを`unity/TanakaCap/Assets/HAOLAN/`、lilToonを同プロジェクトの`Packages/jp.lilxyzw.liltoon/`へ取り込む。取り込み先に異なる内容がある場合は停止する。改変を消して再取り込みする手順ではない。

KlakSpout 2.0.6は`unity/TanakaCap/Packages/jp.keijiro.klak.spout/`にGit管理済み。標準ビルドのためにVRChat SDKを追加する必要はない。SDK欠損状態のPhysBone設定は原本テキストPrefabから変換する。

## ビルド

同じ`unity/TanakaCap`を開いているUnity Editorと、使用中のTanakaCap Playerを閉じてから実行する。

```powershell
New-Item -ItemType Directory -Force results | Out-Null
.\build-unity-lab.ps1
```

Unityの配置が異なる場合は実行ファイルを指定する。別バージョンへ読み替えず、2022.3.22f1を使う。

```powershell
.\build-unity-lab.ps1 -Unity 'C:\YourUnityPath\2022.3.22f1\Editor\Unity.exe'
```

スクリプトはUnityをバッチ起動し、HAOLANのシーン準備、検証、アバター書き出し、外部Loaderを使うPlayerとExporterのビルドを行う。ログは`results/unity-build.log`。成功時は`TANAKACAP_BUILD_OK`が記録される。

| 成果物 | 用途 |
|---|---|
| `builds/lab/TanakaCap.exe`と同じフォルダーの関連ファイル | 再生アプリ。exeだけを移動しない |
| `builds/lab/avatars/haolan.tcap` | 既定で読み込む外部アバター |
| `builds/lab/avatars/haolan.tcap.report.json` | 変換設定・省略機能の警告 |
| `builds/lab/TanakaCapExporter.unitypackage` | Unity Editor用の書き出しプラグイン |
| `builds/lab/THIRD_PARTY.md`、規約PDF、モーションのLICENSE | 素材・依存の案内 |

ビルド時は原本の依存hashが変わらないことを確認する。アバター書き出し成功後、以前の`.tcap`を日時付き`.bak`へ退避して置き換える。Playerを含む成果物フォルダー全体の更新が原子的に完了する保証ではない。ビルド失敗時はログを確認する。

Unity Editorで開くプロジェクトは`unity/TanakaCap`。生成シーンはビルド時に再作成されるため、恒久的な変更は`Assets/TanakaCap/Editor/BuildLab.cs`や各ソースへ反映する。

## 起動batを作成・更新する

```powershell
.\tools\update-desktop-launcher.ps1
```

現在のWindowsユーザーのデスクトップに起動batを作成・上書きする。プロジェクトを別フォルダーへ移動した場合も再実行する。通常・非記録・モーション版のほか、比較用のbatも生成される。比較用は録画や追加モデルなど別の準備が必要。

batのカメラ番号1が合わない環境では、まず`run-avatar-lab.ps1 -Camera 0 -NoLog`などで確認する。継続利用する番号は`tools/update-desktop-launcher.ps1`のカメラ引数へ反映し、batを再生成する。

| キー | アバターウィンドウでの操作 |
|---|---|
| F1 | 状態表示 |
| F2 | デモ切り替え。カメラ追従を確認する際はOFF |
| F3 | OBS向け表示 |
| F4 | 目線の反映ON/OFF |
| F5 | `.tcap`ファイル指定・読み込み |
| F6 | 髪・服の揺れON/OFF |
| F7 | 追加の軽量アンチエイリアスON/OFF（従来MSAAは維持） |
| C | 有効な胴体追跡中に胴体の基準姿勢を取り直す |

`tracking-settings.json`を変更したら再起動する。既定の肩ヨーは`face_ratio`、腕奥行きは`front_projection`、観測平均は3フレーム・stride 1。変更前の値を残して比較する。

## 描画品質と解像度

軽量な輪郭AAは既定ON。プレビューと透過Spout出力に同じGPUフィルターを適用する。時間方向の蓄積を使わず、RGBとアルファを同じ比率で処理する。F7、または起動時の`-NoEdgeAA`で従来の表示に戻せる（元の4倍MSAAは残る）。追加ライブラリは不要。[方式と検証](docs/ANTIALIASING.md)。

出力は従来どおり1280×720が既定。フルHDで使う場合は次のように指定する。構図は同じで、カメラ入力の解像度やモデルは変えない。OBS側のキャンバス/ソースサイズも合わせる。

```powershell
.\run-avatar-lab.ps1 -Camera 1 -NoLog -OutputHeight 1080
.\run-motion-lab.ps1 -OutputHeight 1080
# 追加AAだけを無効化して比較
.\run-motion-lab.ps1 -NoEdgeAA
```

## 自分のアバターを書き出す

現行Exporterは**HAOLAN用表情プロファイル限定**。任意のVRCアバターやModular Avatarの改変をそのまま持ち出せる完成版ではない。

1. Unity **2022.3.22f1 / Built-in / Windows64**の作業用プロジェクトへ`TanakaCapExporter.unitypackage`を導入する。
2. アバタールートを選択し、`TanakaCap > Export selected avatar (HAOLAN profile)`を実行する。
3. 新しい出力ファイル名を選ぶ。既存ファイルへの上書きは拒否される。
4. 同名の`.report.json`で省略機能・警告を確認する。未知のスクリプト等はエラーで停止する。

```powershell
.\run-avatar-lab.ps1 -Camera 1 -NoLog -Avatar 'D:\avatars\my-avatar.tcap'
.\run-motion-lab.ps1 -Avatar 'D:\avatars\my-avatar.tcap'
```

書き出しと再生はUnity版・プラットフォーム・プロファイルの一致が必要。詳細は[パッケージとOBS](docs/PHASE3_PACKAGE_OBS.md)、[PhysBone互換変換の範囲](docs/SECONDARY_MOTION.md)。

## OBSへ透過出力する

OBS側にはUnity内のKlakSpoutとは別に、[Spout2プラグイン1.12.0](https://github.com/Off-World-Live/obs-spout2-plugin/releases/tag/1.12.0)が必要。新しいPCでは導入してOBSを再起動する。この開発PCには配置済み。

配布先：https://github.com/Off-World-Live/obs-spout2-plugin/releases/tag/1.12.0

1. TanakaCapを起動する。カメラなしのモーション版でも確認できる。
2. OBSに`Spout2 Capture`ソースを追加し、送信元`TanakaCap`を選ぶ。
3. `Composite mode`を`Premultiplied Alpha`にする。
4. 背景ソースを下に置き、透過を確認する。クロマキーは使わない。

送信元登録だけで成功とは判断せず、実画像・輪郭・背景合成を確認する。複数Playerを同時に起動すると同じ送信名が競合する。詳細は[OBS手順](docs/OBS_LAB.md)と[実受信検証](docs/PHASE3_PACKAGE_OBS.md)。

## 開発時の確認

pytestは`tests/`だけを収集し、キャッシュを無効にする。Windowsの`tmp_path`は`results/pytest-scratch/`に毎回固有のフォルダーを作り、プロジェクトのアクセス権を継承する。テスト後にそのフォルダーだけ削除する。専用ACL付き一時フォルダーへのアクセス拒否を避けるための対応で、管理者実行や`--basetemp`指定は不要。

```powershell
# Pythonテスト一式（モデル・カメラを起動しない）
.\.venv\Scripts\python.exe -m pytest -q

# Python側の非記録モード：カメラを開かない
.\.venv\Scripts\python.exe -m pytest tests/test_no_log.py -q -p no:cacheprovider

# ビルド済みの実Player：合成入力で骨・表情等を確認
.\.venv\Scripts\python.exe tools/smoke_unity.py --motion-check --output results/readme-smoke/transport.png

# HAOLAN原本と現在の.tcapのPhysBone設定を照合
.\.venv\Scripts\python.exe tools/audit_secondary_package.py
```

Playerを使う検証は普段使いのPlayerを終了してから行う。これらは実人物の精度、本家との揺れの一致、長時間の性能を保証するテストではない。変更した部分に関係するテストを追加で選ぶ。モデル比較は[比較撮影手順](docs/COMPARISON_CAPTURE.md)、[身体モデル比較](docs/BODY_MODEL_COMPARISON.md)、[HaMeR比較](docs/HAMER_COMPARISON.md)を参照する。

検証bat（-Diagnose）は、推論の既存ログに加えresults/player-performanceへPlayerの描画・受信・ソフトウェア遅延を記録する。パッケージ拒否テストはresults/avatar-package-tests配下に毎回別の結果を作り、--outputで保存先を指定できる。

長時間・描画/推論性能の再検証は[フェーズ4の検証手順](docs/PHASE4_VALIDATION.md)を参照。専用診断は明示した保存先に数値を残す。通常のlive/motion起動へログや時間制限を追加しない。

## よくある停止理由

| 症状 | 確認すること |
|---|---|
| `uv is required` | uvを導入し、新しいPowerShellから`uv --version`を確認 |
| Unityが見つからない | 2022.3.22f1の導入先を`-Unity`で指定 |
| 原本/ZIP/PDFがない | 素材表のファイル名とZIP内部パスを確認。利用規約PDFもビルドに必要 |
| `Refusing to overwrite changed import` | 取り込み先が変更済み。変更を保存し、原本用コピーと改変用を分ける |
| `Iris model missing or hash mismatch` | 追加の虹彩モデル取得とSHA256を確認 |
| CUDA初期化・DLLエラー | `nvidia-smi`、`capture_lab environment`、lockに従う依存導入を確認。CPUでの代替を成功にしない |
| アバターが読めない | exe隣の`avatars/haolan.tcap`、書き出し版/プラットフォーム、変換レポートとビルドログを確認 |
| カメラが違う/開けない | `-Camera`の番号、Windowsのカメラアクセス許可、他アプリの占有を確認 |
| OBSに出ない/透明一色 | OBS側Spout2導入、送信元、複数Playerの競合を確認。モーション版で切り分ける |

非記録版では調査用ログは作られない。再現調査が必要な場合は検証版を使う。過去の記録は非記録版を起動しても削除されない。

## ファイル配置と記録の扱い

| 場所 | 内容 |
|---|---|
| `capture_lab/` | 取得・推論・追跡補正・Unityへの制御送信 |
| `unity/TanakaCap/Assets/TanakaCap/` | アバター表示・駆動・揺れ・書き出し・読み込み |
| `tools/`、`tests/` | 検証・比較・素材準備・起動bat生成 |
| `models/catalog.json`、`requirements-lab*.txt` | モデル取得先とPython依存の固定 |
| `assets-source/`、`models/`の重み | ローカル素材。Git除外 |
| `builds/`、`results/`、`.venv/`、`.cache/` | 生成物・記録・環境。Git除外 |

実写録画、購入アバター、モデル重み、`.tcap`をGitへ追加しない。ローカル実体は検証用に保持する。モーションは自作で[0BSD](docs/PROCEDURAL_MOTION_LICENSE.txt)だが、HAOLAN・シェーダー・モデル・ランタイムにはそれぞれ別の条件がある。[素材・依存の記録](docs/THIRD_PARTY.md)を参照。HAOLANのクレジット：**かなリぁ**。

## 引き継ぎとREADMEのメンテナンス

開発を再開するときは[AGENTS.md](AGENTS.md)、[HANDOFF.md](HANDOFF.md)、[仕様書](docs/SPEC.md)、[進捗ログ](docs/PROGRESS.md)の最新部分を読む。[6フェーズの状況](docs/IMPLEMENTATION_PHASES.md)で残件を確認する。

セットアップ、依存版、必要素材、ビルド引数、成果物、起動方法、設定キー、OBS連携を変更したときは、**同じ変更でREADMEの該当手順も更新する**。READMEには現在使う手順を載せ、古い日付付き説明を先頭へ積み重ねない。履歴はPROGRESS、次の作業と未確認点はHANDOFFに残す。

手順中のパス・引数・相対リンクを実ファイルと照合し、動作検証した範囲と未実施の導入試験を分けて記す。新しい会話で過去の会話がなくても、この文書群から再開できる状態を維持する。自動で会話履歴が復元されるわけではない。

## 推論の部位切替・頭専用の試験モード

通常は全モデルON。run-avatar-lab.ps1の-NoBodyで体/腕/掌/指/顔距離による胴体移動、-NoGazeで目線推論をOFFにできます。体OFFでも顔の表情・頭の向きは従来通りです。tracking-settings.jsonのbody_enabled/person_detector_enabled/gaze_enabledでも次回起動から切替できます。人物検出OFF（-NoPersonDetector）は画像全体を固定範囲にする診断用で、無人時の誤推定や精度低下があります。

-HeadOnly（デスクトップtanakacap-head-only.bat）は、小型の直接頭姿勢モデルとGPU頭領域検出で、頭の向きだけを動かします。起動時の矩形選択は不要。移動・接近に合わせて範囲を更新し、見失ったら最後の姿勢を保持、再検出後に復帰します。Pで停止/再開、Rで自動取得をリセット、Sで対象の頭を選択。表情ランドマーク・虹彩・体・従来の人物検出モデルは読み込みません。音声口パクは後日の課題。-HeadRoiMode fixedで以前の手動固定範囲へ戻せます。今回のtanakacap-test.batは全部ON高速化の記録付き検証、live.batは通常全機能、head-only.batは頭専用の非記録・無期限です。追加2モデルの取得・条件・制限は[頭専用モード](docs/HEAD_ONLY.md)、処理時間は[推論内訳](docs/INFERENCE_BREAKDOWN.md)を参照してください。

同じアプリの起動オプション-TrackingMode full / face_head / head_only、またはtracking-settings.jsonのtracking_modeで構成を選べます。fullが既定。face_headは従来の顔表情・頭のみ、head_onlyは直接頭姿勢モデル＋小型頭領域検出です。-HeadOnlyはhead_onlyの別名であり、別製品・別Playerではありません。部位の反映だけでなく不要な推論モデルの生成を止めます。

本家PhysBoneと独自揺れ物の比較動画は、生成済みの環境ではデスクトップtanakacap-compare-physbone.batから開けます。正面/髪の拡大、通常速度/半速の4本。再生成手順と比較条件は[本家比較](docs/PHYSBONE_REFERENCE.md)を参照してください。


## 全部ONの高速化

通常の`run-avatar-lab.ps1`とデスクトップtest/liveは、`tracking-settings.json`の`inference_mode=graph`、`detector_interval=3`、`detector_model=yolox-m-human`を使う。頭専用モードは従来のまま。GPU転送・起動を削減し、人物領域は最大2観測の画像追跡を挟む。顔・体・手・目線の詳細モデルは毎観測実行する。画像追跡不良、切り出し端、120ms経過で人物検出へ戻す。

```powershell
# 従来の実行・毎回の人物検出へ戻す（設定ファイルは変更しない）
.\run-avatar-lab.ps1 -InferenceMode run -DetectorInterval 1 -DetectorModel yolox-m-human

# 小型人物検出Dを試す。詳細モデル・補正は同じ
.\.venv\Scripts\python.exe -m capture_lab fetch yolox-tiny-human
.\run-avatar-lab.ps1 -DetectorModel yolox-tiny-human
```

`-InferenceMode run|binding|graph`、`-DetectorInterval 1|2|3`、`-DetectorModel yolox-m-human|yolox-tiny-human`で各変更を戻せる。Python CLIでは同名の`--inference-mode`、`--detector-interval`、`--detector-model`を使用する。Python CLIの既定は既存比較の再現のためrun/1/mediumのまま。小型モデルは切り出しの差が深度にも影響したため通常採用せず、追加取得は選択時のみ。

結果・条件・残る検証は[全部ON高速化](docs/FULL_MODE_OPTIMIZATION.md)を参照。A（TensorRT/FP16）とE（部位ごとの更新頻度）は保留。

部位別のモデル、補正、表示までの経路は[現在の推論経路](docs/INFERENCE_PIPELINE.md)を参照。
