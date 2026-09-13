# 顔の推定Zによるピッチ・口角の同時試行

最新採用（2026-09-13）：ピッチはPnP・口角はZ。通常body3d/pnp_depthmouth、`-HeadPoseMode pnp`で両方旧補正へ。test/liveは採用構成。以下のdepth3d試行・通常separate/pnpは過去の状態。[最新引き継ぎ](../HANDOFF.md)。

2026-09-13、ユーザー指定。比較動画の見た目確認はユーザーが行う。エージェントは実カメラを開かず、動画の画像抽出・目視確認もしない。正常終了、時刻、フレーム数、全編デコード、数値を検査する。

## 切替

- 新方式：`run-avatar.ps1 -FaceSource body3d -HeadPoseMode depth3d`。
- 今回の対照：`-FaceSource body3d -HeadPoseMode pnp`。モデルを同一にして旧ピッチ/口角計算と比較。
- 顔モデルごと以前へ：`-FaceSource separate -HeadPoseMode pnp`。
- Python：`--face-source body3d --head-pose-mode depth3d|pnp`。設定ファイルはhead_pose_mode。depth3dにはbody3d顔が必須、不整合指定は起動前にエラー。通常設定separate/pnpを維持。

デスクトップtestは新方式、test-face-pnpは今回の対照、test-face-originalは従来RTMW-L。compare-faceは今回の動画の保存先。live/head-only/motionは維持。

## 処理

RTMW3Dの1回の出力から顔のXYと相対Zを取得する。XYは画素、Zはメートルで、単位を混ぜない。画像寸法から近似した内部パラメーターと、鼻/眼端9点の標準顔距離から、未知のカメラ距離を推定する。点対間距離の二次式の正根を求め、長さ3cm以上の複数点対の中央値を使う。推定相対Zと合わせて透視逆投影し、標準の剛体形状との3×3 SVDで頭の回転を求める。

同じ回転の逆を観測した口の3D座標へ適用し、正面座標の既存contour_controlsへ渡す。唇はモデルのZを使用。PnP、LM反復、標準唇の仮の奥行き、mouth_lip_depth_scale=1.5は新経路で使用しない。顔の寸法・カメラ内部パラメーターは依然近似であり、個人の実測3D顔を得たとは扱わない。

頭yaw/roll表示、開口幅、瞬き、虹彩モデル、顔距離、体/腕/掌/指、時間方向の補正、表示モーフ、揺れ物は既存処理を維持。頭ピッチの10安定観測基準、gain1.8、表示±40度も比較を揃えて維持する。口角のガンマ・誇張は維持。口角/口の弓形/横寄せの座標処理が同時に新方式になる。

顔Z不良・剛体残差25mm超などでは最後のピッチを保持し口輪郭更新を止める。唇だけ欠測なら頭を止めず口輪郭だけ保持。PnPへの暗黙のフォールバックはせず、不良率を診断する。Zは現行デコードの約7.55mm刻みを維持し、補間による見かけの精度追加を混ぜない。

## 検証と再現

合成透視投影でピッチ±30度、yaw/roll、距離0.4/1.2m、ルートZオフセット、片側口角変形、欠測時保持を検査。これはモデルの実人物精度の保証ではない。既存録画は体・手主体で顔の意図的な全可動域試験ではない。

```powershell
.\.venv\Scripts\python.exe tools/compare_face_sources.py --pose-comparison --output results/comparisons/face-depth-new
.\.venv\Scripts\python.exe tools/render_comparison_videos.py --comparison results/comparisons/face-depth-new --output results/avatar-videos/face-depth-new
```

同じ録画・RTMW3Dの生XY/Z・ROI・補正時刻を両側へ渡す。左body3dはPnP、右depth3dは推定Z。顔点で更新する人物ROIも共通。新旧双方に虹彩と体の補正状態を持つ。頭pitchが変わることによる下流の視線等の影響は残す。プロファイルのpose_msは各ピッチ/口角呼び出しのみで、全体fpsやカメラから表示までの遅延ではない。

座標の公式根拠：[MMPose SimCC3DLabel](https://github.com/open-mmlab/mmpose/blob/main/projects/rtmpose3d/rtmpose3d/simcc_3d_label.py)。鼻/目の標準形状・ライセンスは既存head_pose/dataを再利用。追加モデル・依存ライブラリなし。

## 録画全編の数値結果

入力はresults/comparison-takes/20260911T235327-031115Z、5187観測。結果はresults/comparisons/face-depth-trial/report.json。先頭30観測を除いたピッチ/口輪郭の処理時間は平均0.589→0.220ms、中央値0.593→0.230ms。両方式とも頭姿勢が有効だった3841観測に限定しても平均0.594→0.236ms。後者は新方式が早期棄却することで見かけ上速くなる影響を除く。GPUモデル推論・人物検出・描画・OBSの時間は含めず、全体速度がこの比率で増える意味ではない。

| 有効観測 / 5187 | 旧PnP | 顔Z |
|---|---:|---:|
| 頭姿勢fit | 5118 | 3898 |
| 口輪郭 | 5104 | 3588 |
| 視線 | 4951 | 3266 |
| 顔距離 | 4911 | 3380 |

新方式の有効率は下がり、ピッチ送信p95は40度の表示上限。頭ピッチが変わるため、既存の視線/顔距離の姿勢ゲートにも影響する。計算コスト改善と品質改善を同一視しない。数値の差を隠す追加補正やクリップ範囲の拡大は今回行わず、動画へ残した。顔Zの精度・量子化・標準顔との形状差が限界候補であり、原因の特定や通常採用は未完了。

実benchmark経路も録画300観測で完走。results/20260912T174517-019568Z-rtmw3d-x-384。RTMW3Dは顔/体の1セッション共有、RTMW3D/虹彩/人物検出のCUDA主要演算を確認、主要計算のCPUフォールバックなし。head_pose_ms平均0.264ms（プロファイルありの別試験なので上表と直接混ぜない）。実カメラは使用していない。

224 tests成功、起動スクリプトのPowerShell構文確認済み。モデル/アバター/動画はGit除外、Unity変更や再ビルドなし。

## 完成動画

results/avatar-videos/face-depth-trialにbody3d.mp4（旧PnP）/depth3d.mp4（顔Z）/side-by-side.mp4（上半身横並び）/face-closeup.mp4（顔拡大横並び）を保存。左旧PnP・右顔Z、各185.03秒/30fps/5551フレーム。単独1280×720、横並び2560×768、顔拡大1920×768。実Player描画、同じ5187観測と撮影時刻を使用。

4本の全編デコード、正常終了、観測数・描画フレーム数の整合性を検査済み。report.jsonに入力/Player/エンコーダー/動画SHAを保存。ユーザー指定に従い画像抽出・目視レビューは行っていない。前回のface-source-trial動画はそのまま保持。
