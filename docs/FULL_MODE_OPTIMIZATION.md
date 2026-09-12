# 全部ON高速化 B → C → D

2026-09-13。ユーザー指定順で実装・比較。通常ランチャーはB+C（graph/interval3/YOLOX-M）、D（YOLOX-tiny）は任意選択。AのTensorRT/FP16、Eの部位更新頻度は保留。頭専用・揺れ物・既存の顔/腕/肩/指補正は変更しない。

## 実装

- B：`GpuRunner`で入力GPU領域と固定形状出力を再利用し、顔/体/虹彩へCUDA Graphを使用。CPUの幾何計算へ同期読戻しする契約は維持。人物検出はNMS出力長が変わるためGraphを使わずI/O Binding。毎回出力bindingを解除・再設定し、前回の検出数に固定しない。CPUへの主要演算フォールバックは禁止を維持。
- C：3回の実検出で初期確定後、最大2観測の画像追跡を挟む。前観測の信頼できる上半身2D点（最低6点）で縮小画像の疎なLK optical flowを往復検査し、中央値の移動量だけ人物ROIへ適用。人体を剛体として回転/scale推定しない。点の残差・追跡不良・ROI左右端・120ms経過で同じ観測内に再検出。初期確定にキャッシュ観測を数えない。検出失敗は即ROI無効、姿勢は従来どおり最後の有効姿勢を保持。再確定は実検出3回。動画ループで追跡状態をリセット。
- D：公式YOLOX-tiny HumanArt416を追加。旧M640との切替であり、RTMW-L/RTMW3D/虹彩モデルは交換しない。追加依存版は不要。モデル重みは選択時取得でGit/Playerに含めない。
- 胴体停止案：現行RTMW3Dは肩・肘・手首・指を共同推論している。手を維持してモデルだけを停止する独立構成ではないため、今回の高速化として採用しない。

`run-avatar-lab.ps1`はtracking-settings.jsonのinference_mode / detector_interval / detector_modelを使う。引数で上書き可能。`-InferenceMode run -DetectorInterval 1 -DetectorModel yolox-m-human`で従来へ戻る。Python CLIの既定は再現性のためrun/1/Mを維持。デスクトップtestは全部ONの記録付き、liveは非記録無期限、head-only/motionは維持。

## 単独録画の処理時間

RTX4090、既存1280×720/30fps録画、先頭30warmup+900測定、全部ON、同一モデル/FP32/補正、Player/OBS/previewなし、ORT traceなし、最大速度で読出し。ms。異なる段階の同時刻比較ではないため、表全体を厳密な一回のA/Bと扱わない。

| 段階 | 構成 | 平均 | 中央値 | p95 |
|---|---|---:|---:|---:|
| B | 従来run | 41.38 | 40.90 | 45.18 |
| B | bindingのみ | 42.33 | 41.89 | 46.35 |
| B | graph | 37.62 | 37.39 | 40.18 |
| C | graph・毎回人物検出 | 37.28 | 37.11 | 39.32 |
| C | graph・3観測間隔 | 26.97 | 22.20 | 39.03 |
| D | graph・3間隔・M | 27.20 | 22.52 | 39.18 |
| D | graph・3間隔・tiny | 24.94 | 22.45 | 32.81 |

Cは900観測中600回を画像追跡、300回を実検出。顔/手/上半身の信頼度による有効率は両側同等。ただし正解率ではない。認識Hzは平均間隔と実Player受信で評価し、中央値の逆数だけを配信時fpsとしない。カメラの30fps制約やOBS/描画負荷を含まない。

結果：results/full-optimization-B-1789229983578447300、full-optimization-C-1789230711404183900、full-optimization-D-1789230953512235500の各summary.json。D最初の実行は可変長GPU出力の再利用エラーで無効、修正後にM/tiny双方を再測定。

## 出力と品質差の監査

`tools/audit_gpu_runner.py`：5モデルそれぞれで4枚の実入力、空画像、実入力への復帰を順番に比較。旧runと新方式は全出力max absolute difference=0。results/gpu-runner-audit-1789231210724547400/report.json。CUDA実行イベントは顔1336/体1496/人物M1878/tiny1548/虹彩1524。顔・人物にはCPU形状/制御ノードがあるがCPU Conv/Gemm/MatMul等は0。空画像でも推定され得るモデルであり、値の一致は空室の人体認識成功を意味しない。

`tools/audit_person_optimization.py`：録画の0/900/1800/2700/3600/4500フレームから各150連続観測、計900。3方式とも888有効、各区間頭の初期確定2観測×6を除く。顔・体・手のモデルは固定しROIのみ変更。

| 従来ROIとの差 | C：M+追跡 | D：tiny+追跡 |
|---|---:|---:|
| 顔XY平均 / p95 (px) | 0.37 / 1.17 | 0.88 / 2.05 |
| 左手XY平均 / p95 (px) | 0.58 / 2.03 | 1.90 / 4.61 |
| 右手XY平均 / p95 (px) | 0.72 / 2.61 | 1.94 / 4.87 |
| 体モデル肩肘手首XY平均 / p95 (px) | 0.53 / 1.93 | 1.94 / 4.77 |
| 体モデル相対Z平均 / p95 (m) | 0.0076 / 0.0095 | 0.0435 / 0.2544 |

results/person-optimization-audit-1789231118191184300/report.jsonと各方式の生点JSON。いずれも正解との差ではない。DのZ差が大きく、平均約2.3msの追加削減だけで通常採用しない。Cは実装採用、実人物の見た目・遮蔽・手指精度の合格は未確認。既存の肩ヨー/腕/左指の問題が解消したとは扱わない。

## 検証と残件

pytest 214件成功。新規4件は実検出での確定、移動追跡、検出予定間隔、空画像で即再検出・欠測、復帰3検出、期限切れ/低信頼/リセット。PowerShellランチャーの構文も確認。実Player+OBS比較は下記のとおり完了。

複数人物の本人識別、激しい移動/強い遮蔽・暗所での人物不在検出は保証しない。画像追跡が背景や別人に一致すると次の検出まで最大2観測の誤追跡はあり得る。現在の実検出も最大信頼の人物を選ぶ設計で、ID trackingは追加していない。

## 一次資料・資産

- [ORT CUDA EP](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)：I/O Binding・CUDA Graph条件。依存更新なし。
- [OpenCV optical flow](https://docs.opencv.org/4.x/d4/dee/tutorial_optical_flow.html)：疎な画像追跡、ピラミッドLK。人体の推定モデルをCPU実行する変更ではない。
- [RTMlib公式Wholebody設定](https://github.com/Tau-J/rtmlib/blob/main/rtmlib/tools/solution/wholebody.py)：YOLOX-tiny HumanArt416の配布URLと入力仕様。RTMlib自体は新規依存に入れない。
- tiny ONNX SHA256：ceb11c07298f95c50d7c5abeb906d03340c85f23aa79e3e66966e7fb6c307250。models/yolox-tiny-human/model.receipt.jsonに取得URL、ZIP SHA、ONNX SHAを保存。ローカル記録で上流の署名ではない。
- [MMPose LICENSE](https://github.com/open-mmlab/mmpose/blob/main/LICENSE)：コードApache-2.0。学習データ/重みを含む一般配布の全監査完了とは扱わず、今回もモデルは別取得とする。


## 実Player＋隔離OBSの比較

同じRTX4090・既存録画を最大速度で読み出す全部ON・720p・AAあり・OBS32.2.2/60fps・配信/録画なしで各60秒。起動の影響を避け30〜60秒のPlayer統計を集計。実カメラは使っていない。速度ごとに時間内に進む録画位置が異なるため、同一フレーム群の厳密比較は前段の単独推論を参照。

| 構成 | 描画中央値fps | 受信Hz | Playerフレームp95の中央値ms |
|---|---:|---:|---:|
| 従来run/毎回/M | 59.99 | 20.24 | 17.48 |
| 通常採用graph/3間隔/M | 59.99 | 32.63 | 17.15 |
| 任意graph/3間隔/tiny | 59.97 | 35.60 | 17.15 |

結果はresults/optimization-obs-baseline、optimization-obs-bc、optimization-obs-bcdのreport.json/player.jsonl/system.jsonl。3構成ともRGBA実受信（透明・不透明・中間alpha）、背景四隅一致、画像変化、正常終了を確認。BCの最終OBS合成画像も目視確認。userの通常OBSは変更せず、各検証で起動したプロセスだけ終了。

B+Cはこの短時間の録画+OBS条件で暫定30Hzを超えた。30fpsカメラの新規観測を32.63Hzで得られる意味ではない。新構成の実カメラ+OBS30分、露光から表示までの遅延、使用者の腕/指/肩の品質判定は残る。Dの受信増はZ差を無視する理由にせず、通常Mを維持。

実カメラ1/MSMF1280×720・30fpsの取得も短く検査。120観測で人物確定0のため追従/全部ON性能の合格には数えない。人物不在とは断定しない。results/20260912T164948-822875Z-rtmw-l-384/report.json。
