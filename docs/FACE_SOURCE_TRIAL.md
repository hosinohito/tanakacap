# RTMW3D-Xの顔XY共有試行

最新採用（2026-09-13）：ピッチはPnP・口角はZ。通常body3d/pnp_depthmouth、`-HeadPoseMode pnp`で両方旧補正へ。test/liveは採用構成。以下のdepth3d試行・通常separate/pnpは過去の状態。[最新引き継ぎ](../HANDOFF.md)。

2026-09-13。ユーザー指定で実装と既存録画によるアバター比較動画を作る。通常採用の判断はまだしていない。実カメラは開かない。

## 切替と戻し方

- `run-avatar-lab.ps1 -FaceSource body3d`：RTMW3D-XのXYを頭・顔・まばたき・口・虹彩crop・顔距離へ使用。全機能時は体の推論結果を再利用し、RTMW-Lをロードせず、体モデルの二重推論もしない。
- `-FaceSource separate`：元のRTMW-L顔＋RTMW3D-X体。Pythonは`--face-source body3d|separate`、tracking-settings.jsonは`face_source`。既定separateを維持。
- 共有するのはXYと信頼度。顔のZを表情/PnPへ新規利用する変更ではない。体への2D参照も切り替わるため、別モデルの独立した整合確認ではなくなる。ライブのROI画像追跡用参照点も変わる。
- 体OFFでbody3dを選ぶ場合、RTMW3D-Xを顔用に1回実行するため最軽量構成ではない。頭専用は既存の専用バックエンドを維持。
- GPU方式graph、人物M/3観測間隔、補正係数・3平均/重複ゲート・頭/口/視線モーフ・揺れ物は維持。新しい顔用の補正調整を比較へ混ぜない。

デスクトップtestは共有試行、test-face-originalは従来方式、compare-faceは動画フォルダーを開く。liveの既定は従来separate、head-only/motionは維持。カメラ用batはユーザーが起動する場合のみ。

## 録画比較

入力はresults/comparison-takes/20260911T235327-031115Z、全5187観測。保存された実撮影時刻を両側の補正とUnityへ渡す。現在のtracking-settingsを両側共通に使い、過去のtake内の古い腕/肩設定に戻さない。

両モデルは同一画像・同一ROIで推論。ROIは従来RTMW-L点で追跡した共通値に固定し、切り出しの変化と顔点の変化を分離する。体の生3D出力も共通、顔処理と体の参照点は各方式のXY。顔距離による体/表示への波及は残す。別途の速度比較は実際の切替経路を使用し、候補側ではRTMW-Lを生成しない。

結果：results/comparisons/face-source-trial/report.json、各方式のframes.jsonl/replay.jsonl。コード/設定・入力SHAを記録。

| 有効フラグ観測数 / 5187 | 従来separate | 共有body3d |
|---|---:|---:|
| 顔 | 5142 | 5145 |
| 目線 | 4836 | 4954 |
| 口輪郭 | 5083 | 5104 |
| 顔距離 | 4913 | 4907 |
| 左腕 / 右腕 | 4570 / 4559 | 4570 / 4559 |

有効率は精度ではない。共有側は開口値の中央値が0→0.104、まばたき値p95が左0.126→0.013/右0.103→0.003、頭ピッチ中央値が5.63→7.82度へ変わった。顔の点と校正が変わる影響であり、改善と断定しない。この録画は主に体・手の比較用で、口形状・目線の意図的な全可動域試験ではない。

## 再現

```powershell
.\.venv\Scripts\python.exe tools/compare_face_sources.py --output results/comparisons/face-source-new
.\.venv\Scripts\python.exe tools/benchmark_full_optimization.py --stage face --frames 900
.\.venv\Scripts\python.exe tools/render_comparison_videos.py --comparison results/comparisons/face-source-new --output results/avatar-videos/face-source-new
```

比較先は新しいディレクトリを使い、既存結果を上書きしない。アバター原本・モデル・実写・生成動画はGitへ追加しない。MP4は見た目比較用の不透明映像、通常OBSのRGBA出力方式は維持。

## 速度比較と検証

RTX 4090、既存録画の同じ先頭区間900観測＋warmup30、全部ON、graph/M/3間隔、Player・OBS・プレビューなし。動画読み取りからUDP送信・診断までのループ時間。センサーから表示までの遅延ではない。比較は順番に単独実行し、動画描画と重ねていない。

| 処理時間ms | 従来 | 共有 |
|---|---:|---:|
| ループ平均 | 27.53 | 22.54 |
| ループ中央値 | 22.64 | 17.70 |
| ループp95 | 39.77 | 34.62 |
| 追加の顔モデル中央値 | 4.87 | 0（体へ共有） |

平均約18%短縮。人物実検出が約3回に1回なので中央値だけを平均Hzへ変換しない。共有側もRTMW3D自体の費用は体欄へ計上され、顔処理全体が無料になる意味ではない。結果：results/full-optimization-face-1789233552678811500/summary.json。

216 tests成功。新規テストは共有で1モデル/従来で2モデルになること、warmupと観測で各モデルを1回ずつだけ呼ぶこと、終了処理が1回であることを検査。実カメラは使用していない。新構成のOBS併用性能と実人物の口・瞬きの品質は未確認。

追加の録画30観測監査（results/20260912T172632-336891Z-rtmw3d-x-384）で、顔/体の同一RTMW3Dセッション、虹彩、人物検出のCUDA実行を確認。主要計算のCPUフォールバックなし。RTMW-Lのセッション/traceは生成しない。プロファイル監査は速度評価と分離した。

## 完成動画

results/avatar-videos/face-source-trialに4本を保存。各185.03秒・30fps・5551フレーム、5187観測を元の撮影時刻で補間して実Player描画。左従来/右共有。

- face-closeup.mp4：顔を拡大して横並び（1920×768）。
- side-by-side.mp4：上半身を横並び（2560×768）。
- separate.mp4 / body3d.mp4：各方式の単独映像（1280×720）。

report.jsonに再生入力/Playerアセンブリ/エンコーダー/動画のSHAとフレーム数を記録。4本とも全編デコード成功。30/85/150秒の画像で顔の構図と左右ラベルを確認した。距離出力が変わるため顔の見かけサイズにも差があり、拡大動画はこれを正規化せず残している。見た目の採用判断は未完了。

次の試行（2026-09-13）：ピッチ・口角を同時に推定Zから計算する切替を追加。今回のtest/compare-faceは[FACE_DEPTH_TRIAL](FACE_DEPTH_TRIAL.md)へ更新。ここで作成した旧比較動画は保持する。
