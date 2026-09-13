# キャプチャ検証ツール

製品版とは別の、モデル比較用Pythonツール。画像取得・前処理・表示にOpenCVを使い、認識はONNX Runtime CUDAで実行する。OpenCV DNNやCPU推論への代替は実装していない。

RTMW-l 384とDWPose-l 384の2D・133点を比較する。両者とも比較基準の既存ONNXモデルで、最高精度モデルの採用が決まったわけではない。YOLOX-m-humanによる人物検出を追加済み。顔専用モデル、学習済み表情係数の推定、人物ID追跡は未実装。

`--body3d`でRTMW3D-Xの身体用GPU推論を追加できる。顔は指定した2Dモデルを使い続ける。`body3d_ms`と`body_execution`へ身体モデルの時間・CUDA実行証拠を記録する。詳細と制約は[Unity検証手順](UNITY.md)。現在はこの追加経路を検証中。

## 実行

プロジェクトのPowerShellで実行する。初回導入時のみネットワークが必要。

```powershell
.\setup.ps1
.\run-capture.ps1 -Model rtmw-l-384 -Camera 1
.\run-capture.ps1 -Model dwpose-l-384 -Camera 1
```

QまたはEscでプレビューを終了する。標準は1800計測フレームで終了する。カメラ番号1はこのPCでの現在の列挙順で、他の環境やデバイス変更後の保証ではない。

```powershell
.venv\Scripts\python.exe -m tanakacap environment
.venv\Scripts\python.exe -m tanakacap probe-camera --camera 1
.venv\Scripts\python.exe -m tanakacap benchmark --model rtmw-l-384 --source synthetic --frames 100
.venv\Scripts\python.exe -m tanakacap benchmark --model dwpose-l-384 --source synthetic --frames 100
.venv\Scripts\python.exe -m tanakacap benchmark --model rtmw-l-384 --source video --video D:\path\test.mp4 --preview
.venv\Scripts\python.exe -m tanakacap benchmark --model dwpose-l-384 --source video --video D:\path\test.mp4 --preview
.venv\Scripts\python.exe -m pytest -q
```

同じ動画で同じROI・フレーム数を指定して比較する。動画は全フレーム順に処理し、ライブカメラは最新フレームのみを処理する。動画再生の実時間や通信遅延の測定ツールではない。

カメラ・動画では標準で人物検出を実行し、3回連続で重なる検出領域があると姿勢推定を開始する。検出が途切れると停止するため、遮蔽・復帰や開始遅延は今後調整する。`--roi X Y W H`は固定領域、`--fixed-roi`は全画面で検出器を省略する診断専用設定。これらの固定領域モードでは**人物不在でも点が出る**ため、信頼度を在席判定や精度の証拠にしない。

## 結果と限界

- `results/<UTC日時>-<モデル>/report.json`：環境、引数、モデルハッシュ、処理時間、実行バックエンド。
- `frames.jsonl`：フレーム別の数値。`--landmarks`時のみ詳細な座標も記録。
- ONNX Runtimeプロファイル：演算が実際にCUDAまたはCPUで実行された記録。CPUの補助演算は隠さず表示する。
- 通常は画像・音声を保存しない。`--snapshot`を明示した場合だけ計測開始時の注釈付き画像1枚をローカルに保存する。表示は`--preview`時（run-capture.ps1は既定で表示）。ネットへ映像を送らない。
- `pose_frames`で人物検出後に姿勢推定した計測フレーム数を確認する。0の場合の処理時間は人物検出の速度であり、姿勢推定込みの速度ではない。起動時には別途3回の姿勢ウォームアップがある。
- `active_pose_timings`は姿勢推定を実行した計測フレームだけの速度。該当フレームがなければnull。`inactive_detection_pipeline_ms`は不在・検出確認待ちの速度。旧レポートにはこの分離項目がない。
- `pipeline_ms`は前処理＋同期推論呼び出し＋後処理で、画像転送を含む。純粋なGPUカーネル時間や実動作から画面表示までの遅延ではない。
- 人工入力は速度と実行経路の検証専用。信頼度や点の数を認識精度とみなさない。
- プロファイラ有効時の短時間測定であり、OBS・アバター描画との同時動作は未測定。
- `interframe_displacement_px`は本人の動きとノイズが混ざる。静止条件を確認した映像以外では震えの指標と呼ばない。

## このPCのカメラ調査

ネイティブのMedia Foundation列挙で、番号0は`DroidCam Source 3`、番号1は`HD webcam-CMS-V43BK`と確認。0での640×480測定を実機の測定に流用しない。実機1はNV12/MJPGの1280×720・30fpsモードがあり、MSMFによる取得でも1280×720を確認した。

```powershell
cmd /c tools\build-camera-probe.cmd
tools\bin\camera_modes.exe
```

ビルドスクリプトはこのPCのVisual Studio 2022 Community配置を使用する。プローブは名前と対応モードを列挙し、画像は取得・保存しない。

## 参照・再現性

- [RTMlibモデル表](https://github.com/Tau-J/rtmlib)：モデルURL、入力仕様の参考。ランタイム依存には追加していない。
- [MMPose / RTMPose](https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose)：モデル・推論方式の一次資料。
- [ONNX Runtime CUDA](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)：GPUランタイムとDLL読み込み。
- [Windows Media Foundation](https://learn.microsoft.com/en-us/windows/win32/medfound/enumerating-video-capture-devices)：カメラ列挙。

モデルURLは`models/catalog.json`、取得時のハッシュと日時は各モデルの`model.receipt.json`に残す。ハッシュはローカルの再現性確認で、署名検証ではない。モデルを製品へ同梱・再配布する判断はまだ行っていない。採用時は上流コードと重み・学習データそれぞれの条件を確認する。

`requirements.txt`は直接依存、`requirements.lock.txt`は今回実際に導入した推移依存込みの版固定。Python実行環境は3.11.16、ONNX Runtime GPU 1.30.0、OpenCV 5.0.0.93。古いレシピに合わせたダウングレードは行っていない。
