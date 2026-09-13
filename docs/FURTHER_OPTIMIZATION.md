# F〜Iの高速化（2026-09-13）

最新の採用決定：Fの全編比較後、ユーザーが「ok.採用して」と指定。通常`detector_graph=true`、`-NoDetectorGraph`で復元できる。以下の通常OFF/採用保留は比較当時の記録。現在はF+G+I、Hはrevert済み。FP16の新しい比較はPRECISION_COMPARISON.mdを参照。

ユーザー指定で全部ONのF→G→H→Iを実装・評価。Hは独立コミットとし遅ければrevert。通常入力はRTMW3D共有、PnPピッチ＋Z口角。実カメラは開かず録画で検証。A/E保留、揺れ物は触らない。追加案はGの前処理改善が高優先で、別のモデル/低精度化は追加しない。

## F 人物検出の固定部分Graph化

経緯の訂正（2026-09-13）：通常OFFはユーザーの指示ではなく、初回実装b3d583fでエージェントが改善幅の小ささを理由に決めた。ユーザーの当時の指定はF〜Iの実装と、Hのみ独立コミット・遅ければrevert。FをOFFにする明示指示は確認できなかった。ユーザーからFの比較動画作成を依頼され、既存録画で独立したON/OFF経路の比較を追加する。通常採用の判断と動画作成は分ける。

元YOLOX-MのNMSより前390ノードと後25ノードをONNXで分割し、元の重み/しきい値/ソート/NMSを保持。3つの固定境界テンソルはGPU上で直接渡す。可変長のNMS側はGraphにせず毎回出力bindingを更新。原本を変更せず、元SHA別のmodels内キャッシュへ生成。既存ONNX1.22.0を使用、依存追加なし。

80入力（録画全域を60フレーム間隔で抽出＋空画像）で最終ROI差0・信頼度差0、両経路の主要計算CUDAを確認。results/detector-graph-audit/report.json。全部ON/録画900観測/30warmup/Player・OBSなしではループ平均22.248→22.028ms、p95 34.303→33.669ms。人物処理平均6.689→6.445ms。results/full-optimization-F-1789235965349655900/summary.json。効果は小さいため通常既定へまだ入れず選択可能にする。

`run-avatar.ps1 -DetectorGraph`、`-NoDetectorGraph`で解除。Pythonは`--detector-graph`、省略で旧経路。設定detector_graphも利用できる。225 tests成功。

### Fの全編比較動画の再現

```powershell
.\.venv\Scripts\python.exe tools/compare_detector_graph.py --output results/comparisons/detector-graph-f
.\.venv\Scripts\python.exe tools/render_comparison_videos.py --comparison results/comparisons/detector-graph-f --output results/avatar-videos/detector-graph-f
```

再実行には新しい保存先を指定する。現在の設定を共通にして、各観測でF-OFF/F-ONの人物検出・ROI追跡を独立実行し、各々のROIで顔/体の推論と補正を実行する。モデル重みは同じ。頭/口は通常のbody3d/pnp、3平均/stride1、口角強調0。片側の制御をもう片側へコピーしない。描画は同じ録画時刻へ同期するため、処理速度/実時間の遅延比較ではない。

動画は`results/avatar-videos/detector-graph-f/side-by-side.mp4`（左F-OFF・右F-ON）と各方式単独。デスクトップ`tanakacap-compare-f.bat`で保存先を開く。実写・生成動画はGit除外、見た目はユーザーが評価する。今回の動画作成で通常設定をF-ONへ変更したわけではない。

全5,187観測の再推論でROI差のある観測0、送信packet差のある観測0。この録画/設定の制御データは完全一致した。初期未検出だけを比べた結果ではなく、有効追跡と動きを含む全編の比較。異なる人物/全環境での品質保証や、Fに高速化効果がないという意味ではない。結果は`results/comparisons/detector-graph-f/report.json`。

動画3本は完成・全編デコード検査成功。各185.03秒/30fps/5,551描画フレーム。両側の有効観測は顔5,145、目線4,951、胴体5,183、左腕4,571、右腕4,558。今回の実行は表示比較のため、交互に推論した時間を通常動作の性能値として報告しない。

公式根拠：[ORT CUDA Graph](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)、[ONNX部分グラフ抽出](https://onnx.ai/onnx/api/utils.html)。これは速度保証やモデル重みの配布許諾を意味しない。元の許諾監査残件を維持する。

G/I採用、Hは計測後revert。詳細は以下。

## G 切り出し後にRGB化

顔/体は採用済みの1モデル共有なので二重cropはない。残る全映像RGB変換を384×288へ切り出した後へ移動し、補間・正規化・配列dtypeは同じ。カラー変換とチャンネル独立warpの交換でありGPU前処理への置換ではない。整数/端外/小数ROIで入力テンソル完全一致の3 tests、全228 tests成功。results/full-optimization-G-1789236115409127600。通常preprocess_mode=cropを採用、-PreprocessMode legacyで復帰。

## H 実装後にrevert

独立コミット53772c7で虹彩GPUと独立CPU処理の並行を実装、229 tests。録画900観測ずつ従来→H→従来で平均20.128→20.413→20.263ms、Hが両方より遅いためユーザー指定通りrevert。results/full-optimization-H-1789236266986080600。現行コードに並行workerや--parallel-gazeは残さない。

G全体の平均は22.387→20.323ms、入力準備3.966→1.756ms。RTX4090/同じ録画900観測/Player・OBSなし。各案の別実行の差を足して全体速度と呼ばない。

## I 左右眼の一括実行

既存虹彩ONNXのbatch=1を2へ、出力reshape [1,-1]を[2,-1]へ変更した派生モデルを元SHA別にローカル生成。重み/演算は同じ。2眼を1回で推論、片眼だけ有効ならもう1枠をゼロで埋め結果を無視、両眼不良なら実行しない。左右のflip/参照/信頼度/幾何/時間ゲートは従来通り。原本と一般配布許諾の扱いは変えない。

録画80入力で両眼/左右片眼/両眼欠測を交互に検査。73観測眼の虹彩座標差0、視線有効状態一致、呼び出し73→54。モデル主要計算CUDA、results/iris-batch-audit。全部ON/Gあり/900観測の前後基準平均20.101/20.345ms、batch平均19.625ms。目線処理平均2.159/2.152→1.472ms。results/full-optimization-I-1789236444888274300。通常batch_eyes=trueを採用、-NoBatchEyesで復帰、-BatchEyesで指定。Python --batch-eyes、省略で旧。228 tests。

最終構成はG+I、Fは小幅効果のため任意、Hはrevert済み。A/E保留。追加の高優先案は今回のGで対応し、低優先の新規施策は追加していない。

## 再現と復帰

```powershell
.\.venv\Scripts\python.exe tools/benchmark_full_optimization.py --stage F --frames 900
.\.venv\Scripts\python.exe tools/benchmark_full_optimization.py --stage G --frames 900
.\.venv\Scripts\python.exe tools/benchmark_full_optimization.py --stage I --frames 900
```

各段階の条件を固定した比較なので、通常設定を変更してもそのまま比較が再現される。H用コマンド/workerはrevertで削除、実装は53772c7、revertはcee5557に残る。Gは9aed8d0、Iはe925743、Fはb3d583f。

全部戻す場合は`run-avatar.ps1 -PreprocessMode legacy -NoBatchEyes -NoDetectorGraph`。顔の採用（RTMW3D共有、PnPピッチ＋Z口角）はそのまま。既存live/head-only/motionは維持。実カメラ用batをエージェントは起動しない。

## 最終Player＋OBS検証

既存録画最大速度、720p60/AAあり、隔離OBS透過合成、各60秒、配信/録画なし。RTMW3D共有・PnPピッチ/Z口角は両側同じ。基準はG/Iなし、最終はG/Iあり、Fは両方OFF。

| 計測 | 基準 | G＋I |
|---|---:|---:|
| Player受信Hz | 39.317 | 44.833 |
| 描画fps中央値 | 59.997 | 59.997 |
| 描画間隔p95の中央値ms | 17.155 | 17.118 |

results/optimization-fgi-obs-baseline-retry/report.json、results/optimization-fgi-obs-final/report.json。RGBA/背景合成/画像変化/正常終了を機械確認。カメラfpsや露光から表示までの遅延ではなく、別人物/負荷/長時間の保証でもない。最初のbaselineはOBS API207で失敗し、WebSocket接続後の準備待ちを修正して再実行。failed結果も保持。動画や画像の目視確認は行わない。現行228 tests、起動PowerShell構文確認、デスクトップ更新済み。
