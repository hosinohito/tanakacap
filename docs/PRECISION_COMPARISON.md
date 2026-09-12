# F採用とCUDA混合精度比較

2026-09-13。ユーザーがFを通常採用と指定。`detector_graph=true`に変更し、人物検出の固定部分をCUDA Graphで実行する。`-NoDetectorGraph`で復元可能。F自体の全5,187観測の制御完全一致はFURTHER_OPTIMIZATION参照。

## FP16の実装

通常は`graph`（FP32）、試行は`graph-fp16`。YOLOX-Mの固定部分、RTMW3D-X、batch2虹彩へ適用する。元ONNXは変更しない。既存ORT1.30.0同梱変換器で派生ONNXを作り、入出力・Softmax・ReduceMean/ReduceSum等をFP32に保つ。NMS後段も既存FP32。人体補正・3/1時間フィルター・モデル・前処理・部位更新頻度は固定する。ONNXの型検査と順序検査を通し、CPUへの暗黙フォールバックは禁止する。

FP16は[公式精度ガイド](https://docs.nvidia.com/deeplearning/tensorrt/latest/inference-library/accuracy-considerations.html)にもあるように表現範囲・集約・Softmax等が敏感。大きな見た目の劣化を必然とは考えないが、ピーク選択や信頼度の閾値を跨ぐ差は生じうる。原本維持・切替・実録画比較で判断する。モデル差を実人物の正解誤差とは扱わない。

再生成は既存の出力先とは別名で、順番に行う（GPU測定を並列実行しない）。

```powershell
.\.venv\Scripts\python.exe tools/compare_precision.py --output results/comparisons/cuda-precision --name CUDA-FP32 --mode graph
.\.venv\Scripts\python.exe tools/compare_precision.py --output results/comparisons/cuda-precision --name CUDA-FP16 --mode graph-fp16
.\.venv\Scripts\python.exe tools/render_comparison_videos.py --comparison results/comparisons/cuda-precision --output results/avatar-videos/cuda-precision
```

全編は同じ録画と観測時刻、独立ROI追跡・推論・補正。同期動画では処理速度差を表示しない。実カメラとエージェントの動画目視は実施しない。

動画4本は完成・全編デコード検査成功。各185.03秒/30fps/5,551描画フレーム、`CUDA-FP32.mp4`/`CUDA-FP16.mp4`/`side-by-side.mp4`/`face-closeup.mp4`。左FP32、右FP16。実Playerの同じアバター・カメラ・時計で生成、通常OBS出力の透過を変えるものではない。`results/avatar-videos/cuda-precision/report.json`に元replay・Player assembly・FFmpeg・動画のSHAを保存。エージェントは動画を目視しない。単体/回帰232 tests、PowerShell構文検査成功。

## 録画による数値比較

`results/comparisons/cuda-precision/report.json`と`difference.json`。両側5,187観測、顔/体推論5,185回。人物検出1,740/1,741回、虹彩4,977/4,978回。閾値を跨ぐ差が後続のROI/校正/保持へ伝わるため、同じ回数になることは強制しない。顔/体・虹彩・検出固定部分の主要演算は両側CUDA、NMS後段のGather/Less/Where/Reshape等の軽いCPU処理は既存通り。TensorRTは使っていない。

推論＋CPU補正の平均17.794→16.267ms、p95 29.424→27.236ms。デコード/JSON書込/Unity/OBSを含まず最初30観測除外、profileありの参考値。通常動作の速度は別途OBS併用で測定する。

両側XY信頼度>.3の推定点差は中央値0.363px、p95 1.647px、最大727.914px。Z差はXYと同じ信頼度集合でp95約0.00755、最大1.057（モデルの深度尺度）。ごく大きな外れがあり、正解との差や人体の実距離誤差ではない。ROIも独立に変わる。制御差のp95は頭pitch1.84度、gaze yaw0.88度、胴体yaw29.03度、左口角0.527/右0.446。小さな点の差でも補正後の差が大きくなる箇所がある。

上記の点集計は画面外の推定点も含む。両方式で画面内にある点だけなら615,841点、XY差中央値0.353px/p95 1.575px/最大549.224px。画面内判定も正解可視性を保証しない。実際のアバターにはさらに欠測判定・関節補正・保持が入る。

顔/胴体の有効フラグ差は0、左腕8/右腕4観測、左掌47/右掌179観測で有効フラグが異なる。品質劣化と断定する正解はないが、見た目同等とも断言しない。FP16の通常採用は保留し、ユーザーが動画を確認する。

## Full HD60fps＋OBSでの速度

同じ録画を最大速度でループ、全部ON/F+G+I、1920×1080・Player60fps・OBS60fps・透過合成・共有プレビュー・AA有効。各90秒、30〜90秒の統計を集約。配信・録画エンコードなし。FP32→FP16の順でGPU処理を重ねず実行。生カメラやセンサーから表示までの遅延の測定ではない。

| モード | Player受信Hz | 描画fps中央値 | フレームp95中央値 |
|---|---:|---:|---:|
| CUDA FP32 + F | 46.170 | 59.976 | 17.214ms |
| CUDA 混合FP16 + F | 49.396 | 59.998 | 17.154ms |

受信は約7.0%向上。受信Hzを推論カーネル単体の速さや実カメラの新規フレーム数と混同しない。既存ループには描画上限で推論を待たせる将来機能は未実装。両側OBSのRGBA・背景透過合成・動き・正常終了を数値確認。results/precision-fp32-fullhd、results/precision-fp16-fullhdのreport/player/systemを参照。

```powershell
.\.venv\Scripts\python.exe tools/phase4_soak.py --seconds 90 --video results/comparison-takes/20260911T235327-031115Z/camera.avi --output results/precision-fp32-fullhd --output-height 1080 --render-fps 60 --obs-fps 60 --inference-mode graph --detector-interval 3 --detector-graph --preprocess-mode crop --batch-eyes
```

FP16は出力先を別名にして`--inference-mode graph-fp16`へ置換する。再実行時は既存出力先を使わない。

## TensorRTの条件確認

通常TensorRT 10.16.1.11/cu13を候補にした。実ORT1.30のprovider DLLは`nvinfer_10.dll`/`nvonnxparser_10.dll`/CUDA13を要求する。RTX版ではない。開発venvへ3パッケージを導入して版と実契約を確認したが、モデル実行/engine構築は行っていない。

実物は`.venv/Lib/site-packages/tensorrt_cu13_libs-10.16.1.11.dist-info/LICENSE.txt`。Web最新のSDK契約と異なり、§12.2に1年自動更新/更新終了、§2.1(ix)に競合技術開発制限、§12.1に`libnvinfer`/`libnvinfer_plugin`の再配布対象記述がある。全DLL配布を許す現在Web本文だけでこのwheelを配布可能としない。既存CUDAと同条件とは未確定でユーザーへ確認中。SDK本体の配布や実行を承認済みと扱わない。

`trt-fp32`/`trt-fp16`接続は準備段階、未検証。CUDAを後段に維持し、要求TRT providerが有効でない場合は停止、profileではTRTイベントを要求する。engine cacheはモデルSHA/精度/SDK/ORT/GPU UUID/ドライバー別。通常セットアップ依存には入れない。`requirements-tensorrt.txt`は候補版の記録。初回構築時間・対応演算・メモリ・速度・品質はまだ不明。
