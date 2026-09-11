# 目の輪郭基準と顔サイズによる前後移動（2026-09-12）

ユーザーは目線の改修継続と、実カメラへ近づいたときアバターも近づく機能を希望。双方を可逆な試行として実装した。実人物の改善評価は未確認。

## 視線

既存のGoogle/PINTO虹彩モデル、顔のRTMW、共有3平均/stride1の方向確認は維持。モデルの輪郭出力を同時に取得し、目頭・目尻の中点と軸に対する虹彩位置を眼幅で正規化する。上下のまぶたの開きは中立基準に使わない。虹彩形状、輪郭幅/方向、位置範囲の不良は欠測とし、ROI方式へフレームごとに切り替えない。

前回は公式コメントの「left eye」を人体側の左と解釈していた。公式グラフではFaceMesh33/133側が反転なし、362/263側が反転あり。現在のRTMW68点形式では前者が59〜64（人体右眼）、後者が65〜70（人体左眼）。旧処理の反転指定が逆だったため修正した。顔・瞬き・口の左右対応は変更していない。

根拠：

- [公式の左右眼入力グラフ](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/graphs/iris_tracking/iris_tracking_cpu.pbtxt)
- [公式の片眼モデル処理](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/modules/iris_landmark/iris_landmark_cpu.pbtxt)
- [公式の輪郭→顔の点番号対応](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/graphs/iris_tracking/calculators/update_face_landmarks_calculator.cc)：輪郭0/8が眼の両端。

`tracking-settings.json` の `gaze_reference="contour"` が新方式。`"legacy"` はROI中央基準と旧左右反転をまとめて復元。CLI `--gaze-reference legacy`。gain2、最大表示範囲、ロスト時の緩やかな正面復帰は維持。虹彩と輪郭を同時取得しても追加の別モデル推論はない。診断に両方式のoffset、両端点、反転フラグを保存する。同一入力での正規化方式比較用で、legacyの反転と新反転の同時推論はしていない。

CUDA単体103call、CUDA39243イベント、CPU演算0。合成入力の中央値5.27ms/95%7.57ms。前回と環境負荷が同一とは限らず、速度改善とは主張しない。実顔の追従精度は未確認。本人の正面視線校正は未実装なので、輪郭中央と正面視線のずれは残り得る。

## 前後移動

既存FaceScaleを独立インスタンスで利用。RTMWの鼻筋と目の端8点の形状を使い、顎/口を除外する。最初の正面寄りの有効10観測から基準形状を選ぶ。腕長や肩幅の校正を変更せず、顔向きが大きい/欠測/形状不良の間は位置更新しない。

基準に対する顔サイズの逆数を距離比として送る。画像上1.25倍なら距離0.8倍、0.8倍なら距離1.25倍。弱透視の近似で、センチメートル単位の実距離測定ではない。回転縮みを緩和する既存アフィン推定を使うが、強い透視や顔向きの影響を完全除去する保証はない。

距離比は0.75〜1.5に制限、共通3/1観測ルールを通す。Playerでは起動時のカメラから頭までの奥行きを基準に、カメラ前方軸に沿ってアバター全体を平行移動する。メッシュ倍率や関節の局所形状は変えない。表示補間は時定数約45ms。欠測、通信停止、部位無効時は最後の位置を保持。近づくと耳先等が画面外になることはある。カメラ構図を自動で引き直して接近を相殺しない。

`face_distance_enabled=false` で次回起動時の移動をOFF、CLIはPlayer `--no-face-distance`。初期位置の再基準化は再起動。旧packetは距離追跡フラグなしなので移動しない。数値診断はface_distanceとUnityのfaceDistanceRatioApplied/avatarDisplacementへ。新たな画像保存なし。

## 検証

- Python146件成功。輪郭基準の平行移動/回転/倍率不変性、鏡映、欠測、距離の接近/離反、顎・回転の除外、初期化、制限を検査。初回の輪郭テスト失敗はテスト側が整数配列へ小数変換を代入して切り捨てたためで、float配列に修正。
- Unityビルド、実Playerの既存motion回帰、視線、位置の接近/離反・保持・OFF・倍率不変検査成功。`results/gaze-contour/motion.log` のFACE_DISTANCE_OK。
- 実UDP受信で距離0.8/1.25とOFFを検査、near/far/disabled画像を保存。近/遠画像を目視し、アバター全体の接近/離反を確認。nearはSpout登録込み。OBS実受信の検証ではない。
- 保存数値のみの前回記録には輪郭出力がないので、新方式の実人物精度を再計算していない。新旧比較に必要な数値を次回記録する。
- 戻し用：`results/checkpoints/before-gaze-contour-distance-20260912.zip`。デスクトップbat更新。
