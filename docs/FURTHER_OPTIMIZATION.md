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

## H 実装後にrevert

独立コミット53772c7で虹彩GPUと独立CPU処理の並行を実装、229 tests。録画900観測ずつ従来→H→従来で平均20.128→20.413→20.263ms、Hが両方より遅いためユーザー指定通りrevert。results/full-optimization-H-1789236266986080600。現行コードに並行workerや--parallel-gazeは残さない。

G全体の平均は22.387→20.323ms、入力準備3.966→1.756ms。RTX4090/同じ録画900観測/Player・OBSなし。各案の別実行の差を足して全体速度と呼ばない。

## I 左右眼の一括実行

既存虹彩ONNXのbatch=1を2へ、出力reshape [1,-1]を[2,-1]へ変更した派生モデルを元SHA別にローカル生成。重み/演算は同じ。2眼を1回で推論、片眼だけ有効ならもう1枠をゼロで埋め結果を無視、両眼不良なら実行しない。左右のflip/参照/信頼度/幾何/時間ゲートは従来通り。原本と一般配布許諾の扱いは変えない。

録画80入力で両眼/左右片眼/両眼欠測を交互に検査。73観測眼の虹彩座標差0、視線有効状態一致、呼び出し73→54。モデル主要計算CUDA、results/iris-batch-audit。全部ON/Gあり/900観測の前後基準平均20.101/20.345ms、batch平均19.625ms。目線処理平均2.159/2.152→1.472ms。results/full-optimization-I-1789236444888274300。通常batch_eyes=trueを採用、-NoBatchEyesで復帰、-BatchEyesで指定。Python --batch-eyes、省略で旧。228 tests。

最終構成はG+I、Fは小幅効果のため任意、Hはrevert済み。A/E保留。追加の高優先案は今回のGで対応し、低優先の新規施策は追加していない。
