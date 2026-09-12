# 口角強調度と高速化J/K/L（2026-09-13）

ユーザー指定：口角強調度を無段階にし既定0、将来UIで指定。GPU点復号(J)、GPU前処理(K)、CPU補正の割り当て削減(L)をそれぞれ実装し、Full HD60fpsで比較。遅くなる案や目に見える影響が出る案はrevertする。実カメラ/映像目視はせず、まず数値一致を検査し差がある場合は保守的に扱う。A/E保留、以前遅かったHは再導入しない。揺れ物は変更しない。

## 口角

`tracking-settings.json`の`mouth_corner_emphasis`、両起動スクリプトの`-MouthCornerEmphasis`、Playerの`--mouth-corner-emphasis`を追加。範囲0〜1の連続値、0が追加強調なし、1が従来と同じ強調、0.5がその中間。既存モーフを最大6mm/最大3倍へ増幅していた分だけを補間する。0でも口角の検出・上下/左右非対称の駆動は続ける。符号付きガンマ2・中立補正・開口時の上げ抑制・口横寄せは変更しない。

生成済み強調モーフへの駆動量を調節し、UI用の`AvatarDriver.MouthCornerEmphasis`で実行中も変更可能。UI自体は将来。元アバターやモーフの再書き出しは不要。

Unity実モーフで0/0.5/1の連続性と1の旧駆動量、左右・口形状・腕回帰・RGBA検証成功。results/mouth-emphasis-default-retry。最初のビルドはusing不足を修正、最初の回帰は旧強調量を前提とした検査に失敗し新仕様に合わせ更新。失敗を隠さずresults/mouth-emphasis-defaultに保持。実人物の新しい口角の見た目は未評価。

## J：GPU点復号はrevert済み

RTMW3DのXYZ分布へArgMax/ReduceMax/近傍3値取得をONNXで接続。元の重み・計算精度は維持し、原本SHA別の派生モデルをローカル生成。CPUへ戻す量は1,021,440→7,980バイト。局所対数補間と画面/メートル座標変換は少量の値に対して従来と同じfloat64演算を行う。時間補正は不変。

2713bfeの`--gpu-decode`で試行、未指定は従来。80録画観測/4種類のROIでXY/Z/信頼度/補間診断差0、プロファイルはCUDAのみ。results/compact-simcc-audit、試行コミットのtools/audit_compact_simcc.py。Full HD＋OBSは45.3947Hz、基準45.4194Hzとほぼ同じ。最終判断は下記。

## K：GPU前処理はrevert済み

482c79c：ONNX GridSampleで切り出し・拡縮・色順序・正規化をGPUで実行、CUDAバッファーをモデル入力へ直接接続。常時CPU往復なし。前処理の座標MatMulだけTF32を無効化し、1/32画素への丸めを入れてOpenCVへ近づけたが、完全一致にはならなかった。元のモデル精度/重みは不変。新規ライブラリ追加なし。

80録画/同じROIで正規化入力の最大差0.0700、信頼度>0.3のXY最大差38.49px・相対Z最大差0.8834m。これは両方式の出力差であり、人体の実距離誤差ではない。小さな補間差で曖昧な分布の最大位置が切り替わるため、モデル入力の差を無視できない。前処理もモデルもCUDAのみ。初回TF32ありのさらに大きい差はreport-first-tf32.jsonへ保存。

Full HD＋OBS48.3952Hzへ高速化したが、見た目への影響を無視できない数値差があるため96af046でrevert。エージェントが目視して見た目を判定したわけではない。results/gpu-preprocess-audit、results/optimization-K-fullhd。派生キャッシュ/結果はローカル保持しGitへ入れない。試行実装は482c79cで再現可能。

## L：CPU補正バッファー再利用はrevert済み

69f1b4a：ObservationMeanの3観測を固定配列へ保持し、DirectionGateの採用値/方向/生値を再利用。平均の並び・加算順序・3/1窓・採用条件は不変。外部へ返す値はコピーを維持し、入力や戻り値の書き換えによる別観測への波及を防ぐ。

1/1・3/1・3/3・欠測/リセット・回転の境界検査13件、全232 tests成功。既存録画5,187観測の同じ顔入力/生の体点/撮影時刻で顔・体/腕/掌/指を再計算し、制御パケットが全件完全一致。results/reuse-buffers-audit.json。Full HD＋OBS45.1620Hzで改善なし。最終判断は下記。

## 一次資料

- [ONNX GridSample](https://onnx.ai/onnx/operators/onnx__GridSample.html)：補間/座標の仕様。OpenCVとの完全一致は保証されない。
- [ORT CUDA EP](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)：CUDA Graph・use_tf32・GPU実行条件。モデル本体の精度変更Aとは別に、Kの画素座標計算のみTF32を止めた。

## 最終比較と判断

RTX4090、同じ既存録画を最大速度で処理。全部ON/G+I/body3d/pnp_depthmouth、口角強調0、共有プレビューあり、Full HD/AA/描画60/隔離OBS60。各60秒、30〜60秒を集計。OBSは透過合成プレビューのみで配信/録画なし。推論が速いほど観測区間が先へ進むので、全く同じフレーム数の速度比較ではない。出力一致の監査は別に同一入力/時刻で実施した。

| 構成 | 姿勢受信Hz | 描画fps中央値 | 結果フォルダー |
| --- | ---: | ---: | --- |
| 基準・最初 | 45.419 | 59.990 | results/optimization-jkl-baseline |
| J 点復号GPU | 45.395 | 59.911 | results/optimization-J-fullhd |
| K 前処理GPU | 48.395 | 59.905 | results/optimization-K-fullhd |
| L CPUバッファー再利用 | 45.162 | 59.890 | results/optimization-L-fullhd |
| 基準・再測定 | 45.199 | 59.909 | results/optimization-jkl-baseline-repeat |

Jは基準2回の変動範囲内であり、「明確に遅い」とは断言しないが、改善が確認できない複雑化を残さずbacbc07でrevert。Lは両方の基準よりわずかに低く、統計的な有意差までは立証していないが、指示に従い保守的にfc9a905でrevert。Kは約6.6%速いが大きな推定差があるため96af046でrevert。いずれもユーザーの実映像目視待ちで停止せず、数値の一致/不一致を根拠にした。新規CLIフラグや試行ワーカーは通常コードに残さない。

全5回でRGBA/背景合成/画像更新/正常終了成功。実カメラHz・実表示遅延の測定ではなく、長時間や全入力での品質保証でもない。描画は全て約60fps。最終の推論コードは口角追加時5085cb5と同一へ復帰し、既存G+Iは維持。J/Lの結果不一致はなく、戻した理由は速度上の利点を確認できなかったため。

口角の実モーフ検証では入力64%に対し強調0/0.5/1が21.333/42.667/64%となり、連続補間と従来復帰を確認。最終228 tests成功（L試行中232）、Unityビルド・実Player回帰・PowerShell構文確認。desktop検証bat更新、UIへの口角強調度/推論Hz/描画レート/推論上限の計画を維持。実人物での新しい口角の見た目は未確認。
