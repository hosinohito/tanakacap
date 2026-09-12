# SAMのCPU/GPU負荷調査

2026-09-12。ユーザーの「GPUがあまり動かずCPU2コアが忙しい」という質問に対する実測。対象は3方式動画比較用のSAM fullワーカーであり、通常のRTMWライブアプリ全体の計測ではない。

## 結論

CUDA推論は実行されている。一方、現構成はGPUへ非常に多くの小さな処理を発行し、頻繁に同期する。現在の約0.5〜0.6秒/フレームをRTX 4090の演算能力の限界と扱うのは不適切。CPU側の制御、起動、同期にも改善対象がある。ただし、それらを削れば30fpsになると実証したわけではない。

各ワーカーにtorch.set_num_threads(1)を指定。事前の同一20フレームでは既定のCPUスレッド設定より速かったため採用した。2ワーカー並行時はCPU時間/壁時計時間が約0.99コア相当と0.85コア相当。別の5標本のnvidia-smiはGPU平均74%（71〜77%）、165.5W。results/sam-setup/observed-load.json。CPU時間にはGPU待ちが含まれ得るので、CPU使用率だけからCPU演算律速やCPU推論へのフォールバックを断定しない。GPU使用率も演算性能の達成率ではない。

## 単独トレース

動画生成・復号が終了してから、同じ撮影の2100〜2111フレームを各モデル単独で順番に推論。3観測のウォームアップ後、2103/2105だけCPU/CUDA profilerで記録。モデル、fullモード、解像度、重みは本番比較と同じ。メモリ再利用とCPUスレッド1を維持。バックボーンは各フレーム3回CUDA実行。

| 計測中の1フレーム | DINOv3（2標本の範囲） | ViT-H（2標本の範囲） |
|---|---:|---:|
| CPU上の全処理区間 | 772〜826ms | 760〜792ms |
| 実CUDAカーネルの活動区間の和集合 | 136〜147ms | 117〜128ms |
| カーネル＋転送＋memsetの和集合 | 141〜153ms | 122〜134ms |
| CUDAカーネル数 | 30,251 | 28,110〜28,113 |
| 同期呼び出し数 | 2,425 | 2,425 |
| CPU上の同期呼び出し合計 | 約135ms | 132〜147ms |
| MHR呼び出し数 | 26 | 26 |
| MHR区間（子処理・待機を含む） | 314〜333ms | 328〜339ms |
| バックボーン3回のCPU区間合計 | 88〜111ms | 53〜56ms |
| 入力prepare_batch | 3〜4ms | 3〜4ms |

プロファイラーは時間を増やす。全処理区間を通常のFPSに換算しない。GPU注釈はカーネルの間の空白も含むため、実カーネルの活動時間とは区別する。CPU区間は入れ子なので足し合わせない。同期時間は待ちを含み、CPUが数値演算していた時間ではない。入力画像のデコード等、process_one_imageの外側はこの区間に含まれない。

同じ診断実行中の非プロファイル・ウォームアップ後7観測の中央値はDINO604.5ms、ViT-H571.3ms。前回のDINO単独20観測529.5msとは計測条件が違い、計測器前後の影響もある。この短い診断を新しい確定性能やモデルの速度順位に使わない。

MHR区間内の同期は436回/約24〜28ms、aten::nonzeroは424回。全体の同期のすべてがMHRにあるわけではない。MHRはTorchScriptをCUDAへロードしており、CPU版モデルへ切り替わっているわけではない。

## 次の改善候補（未実装）

1. MHRを含む形状変換、動的インデックス、同期の発生箇所を追い、同じ出力のままCPU/GPU往復や細かい起動を減らせるか検証する。
2. 同じ記録でネイティブMHR等の実行経路や演算の統合を評価。インストール対応と出力同等性を確認してから採否を決める。
3. バックボーン単独の高速化だけでなく、全体の速度・遅延を再測定する。TensorRT等の採用はまだ決定していない。

この最適化は3方式の一次比較に混ぜない。顔等と既存補正を固定した完成動画を維持する。低頻度SAM併用や身体onlyは別案であり、採用済みではない。

## 再現と記録

- tools/profile_sam_runtime.py：SAM用venvで --output 新しいフォルダー。--wait-for-videos は完成動画待ちを指定。
- tools/audit_sam_profile.py：主venvで結果フォルダーを指定。生トレースからCPU注釈とGPU実活動の和集合を集計。
- results/sam-setup/runtime-profile/{dinov3,vith}/trace-3.json、trace-5.json、profile-summary.json。最終解釈はruntime-profile/trace-audit.jsonを使用。
- 初回profile-summaryのrangesはCPU/GPU同名注釈を混同していた。トレースからCPU区間を再集計し修正、初版はprofile-summary-before-range-audit.jsonへ保存。元の推論やトレースは不変。ツールも再発防止を修正。
- 実4トレースの集計成功。重複GPU区間、GPU注釈の除外、MHR区間内の同期、CPU区間の欠落拒否を3テストで確認（results/sam-setup/pytest-profile-audit）。本体既存177テストは今回の比較完成前に成功済み。

一次資料：PyTorch 2.11 profiler https://docs.pytorch.org/docs/2.11/profiler.html 、CUDA Runtimeの待機方式 https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__DEVICE.html 、公式SAM https://github.com/facebookresearch/sam-3d-body 。数値は上記ローカル実測から取得。
