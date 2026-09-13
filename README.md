# tanakacap

目線の上下応答は横と共通基準の連続カーブを使用します。Player `--legacy-gaze-response` で旧上限クリップへ復帰できます。範囲・比較・検出側の残件は [目線応答](docs/GAZE_RESPONSE.md) を参照。

UIの「表情」で眉・目線・まぶた・口の大げさ度を個別に0〜1で調整できる（0は追加強調なし）。デモ用アバターは全項目を常に最大へ固定。デモ起動は最新Playerを使い、口寄せ等の不足キーを実行時コピーへ補完する。既存のキーは置き換えず、保存デモ原本は不変。[設定と比較動画](docs/FACIAL_EXAGGERATION.md)。

眉は4フレーム処理後に可変速度で追従する。小さい差はゆっくり、大きい差は速く、左右内外4値を独立処理。既定ON、Playerの`--no-adaptive-brow-follow`で従来の直接反映へ戻せる。頭の可変追従の採否とは独立。

検証は保存済みデモ用シェイプキーアバターを使う。`tanakacap-test.bat`は最新Player＋`builds/demos/haolan-custom-brows/avatars/haolan.tcap`を指定する。既存の独自キーを保持し、実行時コピーへ眉の左右分割キーと不足する口寄せ・目線キーを補う。直接指定は`run-avatar-lab.ps1 -DemoAvatar`（Player側は`--avatar <デモtcap> --use-demo-shape-keys`）。保存済みデモ一式は上書きしない。眉の強調は`tracking-settings.json`の`brow_gain`で調整（既定2、1で従来、範囲0.5〜4）。通常UIも同設定を推論へ渡す。

眉はデモ/auto-customで左右分割を生成し、片側の上下・困り眉・怒り眉を独立駆動する。眼ボーンと読取可能な既知の眉モーフが必要。existingでは左右別の既存キーを優先し、左右共通キーしかなければ共通表示を維持する。既存キーモードで独自キーは生成しない。

デスクトップ直下のbatは5本に整理：`tanakacap.bat`（UI）、`tanakacap-test.bat`（診断）、`tanakacap-face-capture.bat`（30秒録画）、`tanakacap-live.bat`（ログなし無期限）、`tanakacap-motion.bat`（自作モーション）。その他の比較・個別試行・デモ用batはデスクトップの`tanakacap-tools`フォルダー内。以下で名前だけ記載する補助batも同フォルダーにある。更新スクリプトはこの配置を維持する。

頭の固定速度／可変速度の比較は`tanakacap-compare-head-follow.bat`、または`results/avatar-videos/head-follow/face-closeup.mp4`（左が従来）。試行Player引数は`--adaptive-head-follow`、通常起動は従来の固定追従を維持。[比較条件](docs/HEAD_FOLLOW_COMPARISON.md)。

顔・頭・表情の検証録画はデスクトップの`tanakacap-face-capture.bat`（30秒で自動終了）。動作案内なし、実写画面・音声なしで保存する。保存先は`results/comparison-takes/<日時>/`。直接起動は`run-comparison-lab.ps1 -Mode capture -Profile face-head`。既存の全身用撮影は従来どおり。

Webカメラ1台で、VRChat向け3Dアバターを動かしてOBSへ透過出力するWindows用プロジェクト。Unity Editorの書き出しプラグインと、外部アバターファイルを読み込む専用Unityアプリで構成する。

着席時の頭・目・口・上半身・腕・掌・指を対象に、RTX 4090で品質を優先して開発している。元のシェーダーの見た目を保ち、髪・服は元PhysBoneの設定を独立した近似ソルバーへ変換する。軽量化は基準品質の確立後に追加する。

**現在はHAOLAN 1.6向けの開発版。** 外部アバターの書き出し・読み込み、GPU推論、OBS透過受信、揺れ物を実装済み。汎用のVRC改変対応、本家PhysBoneとの動作一致、30分の安定性・OBS併用性能は未達成または未確認。仮想カメラ・コラボ送信・全身は後日の対象。重いゲームとの同時実行保証は要件に含めない。最新の評価は[HANDOFF.md](HANDOFF.md)、確定要件は[仕様書](docs/SPEC.md)を参照する。

## セットアップ済みの環境で起動する

**操作用UIはデスクトップの`tanakacap.bat`から開く。** 入力・アバター・推論モード、描画60/推論同期/30/自由入力、Full HD/自由解像度、表情調整を選び、「開始」を押す。開くだけではカメラを起動しない。実写はUIにも表示しない。実行中の「保存して適用」は再起動で反映する。推論Hz・アバター描画fps・受信Hz、測定済み構成の相対負荷を表示する。[操作と計測条件](docs/CONTROL_PANEL.md)。

```powershell
.\run-ui.ps1
```

UIにはPython標準のTk/ttkを使用する。`.venv/Scripts/pythonw.exe`とtkinterが必要（現環境で検証済み）。UI自体の別ビルドは不要、Playerは通常どおり`build-unity-lab.ps1`でビルドする。UI設定はローカルの`ui-settings.json`へ保存し、従来bat用の`tracking-settings.json`とは分ける。

デスクトップの次のbatを、使いたいもの一つだけ起動する。

| 起動ファイル | 動作 | 記録・時間制限 |
|---|---|---|
| `tanakacap-live.bat` | カメラでアバターを動かす | 動作ログなし・無制限 |
| `tanakacap-motion.bat` | カメラなしで自作モーションを繰り返す | 動作ログなし・無制限 |
| `tanakacap-test.bat` | 試行構成：PnPピッチ＋推定Zなしの口輪郭 | 診断ログあり・1800フレーム |
| `tanakacap-test-face-pnp.bat` | 同じRTMW3D-Xで旧PnP補正を試す | 診断ログあり・1800フレーム |
| `tanakacap-test-face-original.bat` | 従来のRTMW-L顔方式を試す | 診断ログあり・1800フレーム |
| `tanakacap-compare-face.bat` | 顔方式の比較動画の保存先を開く | カメラ不使用 |
| `tanakacap-compare-f.bat` | 高速化FのOFF／ON比較動画の保存先を開く | カメラ不使用 |
| `tanakacap-compare-fp16.bat` | CUDA FP32／FP16比較動画の保存先を開く | カメラ不使用 |
| `tanakacap-test-fp16.bat` | 通常testと同じFP16起動（旧ショートカットの互換用） | ユーザーが起動するカメラ試験 |
| `tanakacap-demo-custom-brows.bat` | 保存デモアバターを最新Playerの全項目強調で再生 | カメラなし・非記録・無期限 |
| `tanakacap-test-auto-expressions.bat` | 実験用の自動独自キー方式 | ユーザーが起動するカメラ試験 |
| `tanakacap-motion-auto-expressions.bat` | 自動独自キー方式で自作モーション再生 | カメラなし・非記録・無期限 |
| `tanakacap-compare-expressions.bat` | 従来デモ／既存キー／自動独自キーの顔拡大比較動画の場所を開く | 保存動画 |

通常はカメラ番号1。実写のカメラ映像は表示しない。検証版・非記録版ともアバターを閉じると推論が終了する。端末ではCtrl+Cでも終了できる。モーション版はアバターを閉じて終了する。詳しくは[起動モード](docs/LAUNCH_MODES.md)。

実写表示は次の長いオプションを**Pythonプロセスの起動時に完全一致で指定した場合だけ**許可する。通常bat・診断・比較撮影は非表示。旧`--preview`やオプションの省略形は拒否する。設定JSON・環境変数・UI・ショートカットから自動で有効にしない。

```text
--explicitly-allow-displaying-raw-camera-images-on-screen-for-this-session-only
```

必要な場合に限り、`python -m capture_lab benchmark ...`または`python -m capture_lab.comparison_capture ...`へ上記を自分で付ける。比較撮影は未指定でも文字ガイドと録画が使える。頭専用の固定ROIは通常`--roi X Y W H`で数値指定する。実写を見ながらの矩形選択にも上記オプションが必要。録画由来の実写プレビューも同じ条件。アバターの表示・OBS透過出力とは別で、`-NoPreview`/F8はアバター側の設定。

現在の既定は`-FaceSource body3d -HeadPoseMode pnp`。ピッチは固定3D顔型へのPnP当てはめを使う。2D比率のsize2dはUI「入力・推論」→「頭角度」で選べる任意試行として残す。口・眉の正面化は維持。頭のみモードは別モデル。[試行内容・比較動画・限界](docs/HEAD_SIZE_TRIAL.md)。

顔方式は`run-avatar-lab.ps1 -FaceSource body3d`で体の推論結果を顔にも再利用し、`-FaceSource separate -HeadPoseMode pnp`で従来の別顔モデルへ戻す。設定ファイルの`face_source`も同名。通常のliveとtestはRTMW3D共有＋PnPピッチ/推定Zなし口輪郭。[顔モデル比較の記録](docs/FACE_SOURCE_TRIAL.md)。

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

配布予定の部品・モデル・素材と未確定事項は[ライセンス棚卸し](docs/DISTRIBUTION_LICENSES.md)を参照。`tools/audit_distribution.py --output 新しい保存先`で実環境の依存版・通知・モデルSHAを記録できる。開発環境全体を配布可能と認定するツールではない。

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

口角の追加強調は`tracking-settings.json`の`mouth_corner_emphasis`、または両起動スクリプトの`-MouthCornerEmphasis 0.5`で調整できる。0〜1の連続値、既定0は追加強調なし。自動独自キーでは1で以前の強調量、既存キーでは1で入力を最大2倍にし作者の100%形状までに制限する。0でも口角追跡は続く。操作UIの「表情」タブでも変更できる。[詳細](docs/EXPRESSION_PORTABILITY.md)。

通常版の口角ガンマは既定1（直線）、開口時の上げ抑制は既定0（抑制なし）。未設定ならこの3調整は影響しない。`mouth_corner_gamma`（0.25〜4）と`mouth_open_smile_suppression`（0〜1）を設定JSONで変更できる。`null`はモード既定：通常1/0、自動独自キーは従来の2/0.9。起動引数を優先する。操作UIにも調整欄がある。

```powershell
# 通常版にも以前のガンマと開口抑制を適用する例
.\run-motion-lab.ps1 -MouthCornerGamma 2 -MouthOpenSmileSuppression 0.9 -MouthCornerEmphasis 0
```

眉も既存顔点から追跡する。表情は通常`-ExpressionMode existing`で、機能別にPerfect Sync/ARKit→MMD→VRCの既存キーを使用し、独自キーは生成しない。目線も既存方向キー、なければ眼ボーンを使う。足りない機能は無効とし、変換レポートとPlayerログに対応表を残す。Perfect Syncの推論を再実装したものではない。

`-ExpressionMode auto-custom`は実験用。既存キー優先を基本に、ARKitで不足する口角の左右分離・唇限定の横寄せ・瞳限定移動を実行時に生成する。既知の作者形状と眼ボーンが材料として必要で、任意アバターへの自動対応を保証しない。素材メッシュ原本は変更しない。

```powershell
.\run-motion-lab.ps1 -ExpressionMode auto-custom
# 通常の既存キーだけへ戻す
.\run-motion-lab.ps1 -ExpressionMode existing
```

眉を追加した従来版は`builds/demos/haolan-custom-brows/`に別保存し、通常ビルドで上書きしない。このローカル保存物はGitには含まれず、別PCではソースのチェックポイント`6806913`と正規取得した素材から再作成が必要。配布可能な自作モーションとアバター素材の許諾は別扱い。[方式・比較条件](docs/EXPRESSION_PORTABILITY.md)。

軽量な輪郭AAは既定ON。プレビューと透過Spout出力に同じGPUフィルターを適用する。時間方向の蓄積を使わず、RGBとアルファを同じ比率で処理する。F7、または起動時の`-NoEdgeAA`で従来の表示に戻せる（元の4倍MSAAは残る）。追加ライブラリは不要。[方式と検証](docs/ANTIALIASING.md)。

出力はFull HD（1920×1080）が既定。幅・高さを自由指定できる（各64〜4096、幅省略時は高さから16:9で計算）。カメラ入力の解像度やモデルは変えない。OBS側のソースサイズも合わせる。異なる縦横比は出力カメラの水平視野が変わり、プレビューは縦横比を保って余白を付ける。

```powershell
.\run-avatar-lab.ps1 -Camera 1 -NoLog -OutputWidth 1280 -OutputHeight 720
.\run-motion-lab.ps1 -OutputWidth 960 -OutputHeight 960
# 追加AAだけを無効化して比較
.\run-motion-lab.ps1 -NoEdgeAA
```

OBS用画像をプレビューにも再利用し、アバターの二重描画を省く。`-NoPreview`またはF8でプレビューだけ非表示にでき、OBS出力・追跡・操作用ウインドウは継続する。F8で再表示。`-LegacyPreview`で旧二重描画へ戻せる。どちらもavatar/motion両起動スクリプトで使用可能。詳細は[描画共有と解像度](docs/SHARED_PREVIEW.md)。

## 自分のアバターを書き出す

表情のHAOLAN限定条件は撤去し、既存キーの対応表とVRC Descriptorのviseme・眼設定を保存する。実アバターの検証はHAOLAN 1.6が中心で、任意のVRCアバターやModular Avatarの改変をそのまま持ち出せる完成版ではない。骨・カメラ構図・改変処理の汎用化は別の残件。

1. Unity **2022.3.22f1 / Built-in / Windows64**の作業用プロジェクトへ`TanakaCapExporter.unitypackage`を導入する。
2. アバタールートを選択し、`TanakaCap > Export selected avatar`を実行する。
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

自動検証は既存録画を基本とする。エージェントによる実カメラ試験はユーザーの明示指示、または必要性を説明した事前相談後に行う。以下のカメラ用batはユーザー自身が必要なときに起動する。

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

通常の`run-avatar-lab.ps1`とデスクトップtest/liveは、CUDA混合FP16（内部既定`graph-fp16`）と、`tracking-settings.json`の`detector_interval=3`、`detector_model=yolox-m-human`を使う。頭専用モードは従来のまま。GPU転送・起動を削減し、人物領域は最大2観測の画像追跡を挟む。顔・体・手・目線の詳細モデルは毎観測実行する。画像追跡不良、切り出し端、120ms経過で人物検出へ戻す。

```powershell
# 従来の実行・毎回の人物検出へ戻す（設定ファイルは変更しない）
.\run-avatar-lab.ps1 -DetectorInterval 1 -DetectorModel yolox-m-human

# 小型人物検出Dを試す。詳細モデル・補正は同じ
.\.venv\Scripts\python.exe -m capture_lab fetch yolox-tiny-human
.\run-avatar-lab.ps1 -DetectorModel yolox-tiny-human
```

`-DetectorInterval 1|2|3`、`-DetectorModel yolox-m-human|yolox-tiny-human`で人物領域更新と検出器を選べる。Python CLIは`--detector-interval`、`--detector-model`。精度はFP16固定で、`-InferenceMode`/`--inference-mode`と設定キー`inference_mode`は削除済み。Python CLIの人物更新/検出器既定は1/medium。小型モデルは切り出しの差が深度にも影響したため通常採用せず、追加取得は選択時のみ。

結果・条件・残る検証は[全部ON高速化](docs/FULL_MODE_OPTIMIZATION.md)を参照。部位ごとの更新頻度Eは保留。FP16は通常採用済み。

部位別のモデル、補正、表示までの経路は[現在の推論経路](docs/INFERENCE_PIPELINE.md)を参照。

追加高速化F：通常ON（`detector_graph=true`）。`-DetectorGraph`で明示有効、`-NoDetectorGraph`で解除。同じ人物検出の固定部分をGraph化する。全編比較後にユーザーが採用を指定。[F〜Iの進捗・測定条件](docs/FURTHER_OPTIMIZATION.md)。

精度はCUDA混合FP16を通常採用。FP32の起動オプション・設定キーは公開しない。将来UIに追加する可能性に備えた内部APIのみ保持し、UI追加を確定要件にはしない。初回はモデル原本を残してmodels内へFP16派生ONNXを生成する。入出力とSoftmax/一部集約はFP32、主な畳み込み等はFP16。頭専用モデルは今回の精度変更の対象外。追加Python依存は不要。以前の比較動画は`tanakacap-compare-fp16.bat`から開ける。[比較条件・結果](docs/PRECISION_COMPARISON.md)。TensorRTは不採用、CUDA FP16には不要。

前処理は`preprocess_mode=crop`（切り出し後のRGB化）を通常採用。`-PreprocessMode legacy`で以前へ戻せる。入力テンソルは同一。[計測](docs/FURTHER_OPTIMIZATION.md)。

左右眼は`batch_eyes=true`で1回の推論にまとめる。`-NoBatchEyes`で従来へ、`-BatchEyes`で明示指定。派生ONNXは初回にmodels内へ自動生成し原本を保持。Hの並行処理は計測で遅くなったためrevert済み。[結果](docs/FURTHER_OPTIMIZATION.md)。

従来のPowerShell起動は`-RenderFps 30|60`（既定60）。操作UIは60/推論同期/30/自由入力と推論上限の連動に対応する。[UI](docs/CONTROL_PANEL.md)。従来batでは`tanakacap-test-30fps.bat`で30fpsを試せる。OBS側fpsや推論頻度は変えない。[30/60比較・追加案](docs/RENDER_RATE_COMPARISON.md)。
