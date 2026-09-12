# F〜Iの高速化（2026-09-13）

ユーザー指定で全部ONのF→G→H→Iを実装・評価。Hは独立コミットとし遅ければrevert。通常入力はRTMW3D共有、PnPピッチ＋Z口角。実カメラは開かず録画で検証。A/E保留、揺れ物は触らない。追加案はGの前処理改善が高優先で、別のモデル/低精度化は追加しない。

## F 人物検出の固定部分Graph化

元YOLOX-MのNMSより前390ノードと後25ノードをONNXで分割し、元の重み/しきい値/ソート/NMSを保持。3つの固定境界テンソルはGPU上で直接渡す。可変長のNMS側はGraphにせず毎回出力bindingを更新。原本を変更せず、元SHA別のmodels内キャッシュへ生成。既存ONNX1.22.0を使用、依存追加なし。

80入力（録画全域を60フレーム間隔で抽出＋空画像）で最終ROI差0・信頼度差0、両経路の主要計算CUDAを確認。results/detector-graph-audit/report.json。全部ON/録画900観測/30warmup/Player・OBSなしではループ平均22.248→22.028ms、p95 34.303→33.669ms。人物処理平均6.689→6.445ms。results/full-optimization-F-1789235965349655900/summary.json。効果は小さいため通常既定へまだ入れず選択可能にする。

`run-avatar-lab.ps1 -DetectorGraph`、`-NoDetectorGraph`で解除。Pythonは`--detector-graph`、省略で旧経路。設定detector_graphも利用できる。225 tests成功。

公式根拠：[ORT CUDA Graph](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)、[ONNX部分グラフ抽出](https://onnx.ai/onnx/api/utils.html)。これは速度保証やモデル重みの配布許諾を意味しない。元の許諾監査残件を維持する。

G/H/Iは続行中。

## G 切り出し後にRGB化

顔/体は採用済みの1モデル共有なので二重cropはない。残る全映像RGB変換を384×288へ切り出した後へ移動し、補間・正規化・配列dtypeは同じ。カラー変換とチャンネル独立warpの交換でありGPU前処理への置換ではない。整数/端外/小数ROIで入力テンソル完全一致の3 tests、全228 tests成功。results/full-optimization-G-1789236115409127600。通常preprocess_mode=cropを採用、-PreprocessMode legacyで復帰。

## H 同一観測内の虹彩GPU/身体CPU並行（測定前）

顔と体は同じ推論のため別々に並列化しない。頭推定後の虹彩を専用1 workerへ渡し、独立な顔filter/距離/体CPU処理と重ねる。入力packetをコピーし、観測末尾で必ずjoinして視線3値のみ合流。次観測へ持ち越さず更新頻度は同じ。--parallel-gazeで試行、既定OFF。H単独コミットで計測し遅ければrevertする。
