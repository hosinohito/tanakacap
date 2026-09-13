# 描画30fps対60fps（2026-09-13）

後続指定：追加案1/2/3は採用され実装、既定解像度はFull HDへ変更。[描画共有](SHARED_PREVIEW.md)参照。以下の720p測定と「未実装」は今回採用前の状態。描画レート4択UIと推論上限は将来実装として確定。

ユーザー指定で描画30固定を60と比較し、追加案を挙げる。通常は60を維持する。実カメラは使わず、同じ既存録画・採用推論構成G+I/body3d/pnp_depthmouth・720p/AAあり・隔離OBS60fpsで、Playerのレートだけを変更する。

## 実装と注意

Player `--render-fps 30|60`、run-avatar.ps1 `-RenderFps 30|60`、既定60。Application.targetFrameRateとvSyncCount=0を起動時に設定。これはUnityのフレームループ全体の上限であり、カメラ描画だけを間引く実装ではない。姿勢表示の更新・揺れ物の呼び出し間隔も変わるが、推論更新頻度や揺れ物ソルバー/パラメーターは変更しない。UDPは毎フレーム最大64件を取り込み最新を反映するため受信Hzと描画fpsは別。

30ではOBSへ新規に渡る絵も約30枚/秒、OBS側は60fpsのままで同じ絵を使う観測が増える。撮影fps/認識Hz/描画fps/OBS設定を混同しない。実アバターの見た目確認はユーザー担当、エージェントは画像を目視しない。

デスクトップ通常testは60、test-30fps.batは同じ設定で30。直接起動は -RenderFps 30、60へ戻すときは省略または -RenderFps 60。

公式：[Unity 2022.3 Application.targetFrameRate](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Application-targetFrameRate.html)。デスクトップではvSyncCountが非ゼロだとtargetFrameRateは無視されるため明示0。

## 測定結果

RTX 4090、同じ既存録画を最大速度で処理、各60秒。安定区間30〜60秒を集計。OBSは720p60の隔離プレビュー/透過合成のみで配信・録画なし。

| 項目 | 60固定 | 30固定 |
| --- | ---: | ---: |
| 実描画fps（中央値） | 60.00 | 29.98 |
| 姿勢受信Hz | 44.47 | 46.14 |
| GPU使用率（平均） | 53.0% | 47.7% |
| GPU電力（平均） | 145.7W | 142.5W |
| 送信→描画投入（各窓p50の中央値） | 6.54ms | 10.32ms |
| 最新入力読込→描画投入（同上） | 25.78ms | 29.96ms |

GPU数値は10秒間隔の安定区間3標本であり、推論・Player・OBS等を含むGPU全体の参考値。描画単独のGPU時間ではなく、小差を確実な省電力改善と断言しない。受信は約3.8%増、GPU使用率は5.3ポイント減で、全体負荷が半分になる結果ではなかった。各1回の短期比較で長時間再現性は未確認。

描画投入までの時間はソフトウェア時刻による値で、カメラ露光・モニター表示・OBS最終映像までの遅延ではない。録画最大速度の受信Hzを実カメラの新規観測Hzと扱わない。30fpsでは表示の更新間隔が約33msへ増えるため、60の滑らかさと引き換えになる。通常60を維持し、30は任意設定とする。

両方とも透過受信・背景合成・画像変化・正常終了に成功。Unity再ビルド、Python/PowerShell構文確認、デスクトップ30fps bat生成・引数確認済み。実カメラ・映像目視は未実施。ソルバーの調整はしていないが、30fpsでの揺れの見え方は未評価。

結果：`results/render-rate-60/report.json`、`results/render-rate-30/report.json`、各`player.jsonl`/`system.jsonl`、`results/render-rate-summary.json`。再現：`tools/phase4_soak.py --seconds 60 --video results/comparison-takes/20260911T235327-031115Z/camera.avi --output results/<新しい保存先> --inference-mode graph --detector-interval 3 --render-fps 30`（比較側は60）。

## 追加案（未実装）

1. 最優先候補：OBS用RenderTextureをプレビューにも使い、アバターを2回描く処理を1回へ。AlphaOutputはプレビューカメラを有効のまま別の出力カメラをLateUpdateでRenderしている。背景/UIと透過、AA、色空間を維持した比較が必要。60fpsの滑らかさを維持できる可能性がある。
2. OBSの配置サイズに応じた出力解像度。小さく配置する場合は720p未満の内部出力を選べる余地がある。顔・髪・輪郭の劣化との比較が必要。描画/転送の削減案で、モデル精度を下げる案ではない。
3. 補助候補：プレビューのみ非表示/低頻度化。OBS出力と状態更新は維持。出力の再利用ができれば独立の効果は小さくなる。

受信同期の可変描画は、30固定の実測効果と滑らかさの交換を見てから判断。OBSウインドウキャプチャへの変更、揺れ物変更、A/E、H再導入は今回実施しない。
