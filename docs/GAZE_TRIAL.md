# 目線の試行（2026-09-12）

追記：目が動かない評価後の表示方式とモデル選定見直しは[最新調査](GAZE_MODEL_REVIEW.md)を優先する。既定は瞳限定モーフ、gaze_render_mode=bonesで以下の旧ボーン方式へ戻る。検出モデルは同一。

ユーザーが追加要件として調査・可逆な試作を承認。目線のみ、欠測時にゆっくり正面へ戻す。他の姿勢・表情の最終姿勢保持は維持する。正面はアバターの頭に対する中立方向。

## 調査と採用理由

現在のRTMWの顔68点は目の輪郭までで、虹彩を含まない。虹彩用の小さなネットワークを追加すれば目の中での移動を取れる。Googleも単眼RGBでの虹彩推定を公開しているが、これ自体は見ている場所を推定するモデルではない。[公式説明](https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/iris.md)

今回はGoogle由来の虹彩モデルをPINTOのONNX変換配布から導入した。配布物は2021年のモデルで、新しいモデルだから選んだわけではない。64×64の眼ROIだけを入力でき、既存の顔・身体推論を置き換えず、現在のONNX Runtime CUDAで検証できることを理由に試行する。MediaPipeのCPUランタイムは追加していない。別の学習済み視線方向モデルとの精度比較は未実施。

前処理は目尻・目頭間の2.3倍の正方形、ロールを戻してRGBの0〜1へ。モデルは左目学習のため解剖学的右目を反転し、出力で反転を戻す。[公式ROI定義](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/modules/iris_landmark/iris_landmark_landmarks_to_roi.pbtxt)、[公式入力・出力定義](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/modules/iris_landmark/iris_landmark_cpu.pbtxt)

## 実装

- tanakacap/gaze.py：眼ROI→CUDA虹彩推論→目幅で正規化した中心ずれ。yawは画像右が負、pitchは画像下が正。頭の既存座標と統一。左右の目が有効なら平均、片目だけならその目で両眼を同方向へ動かす。輻輳の追跡はしない。
- 目幅14px未満、ROI画面外、閉眼、低コントラスト、顔欠測、大きな顔角度、虹彩形状の不整合、左右不一致を棄却。モデル自体に可視性の確率出力はないので、遮蔽や眼鏡反射を確実に見抜くものではない。
- shared DirectionGateの3平均/stride1を使用。角度上限は横±20度/縦±12度の控えめな試行値。検出ずれから回転への比例換算で、個人別眼球中心・光軸の校正や正確な3D注視点を得たものではない。
- UnityはHumanoidの目を優先し、HAOLANでは未登録だったため頭配下のLeftEye/RightEyeを利用。保存した元の回転に頭基準の回転を加える。目ボーンの親や首は変形しない。
- 欠測/送信停止/顔欠測/機能OFFでは指数減衰（時定数0.5秒、約1.5秒で95%復帰）。送信停止は既存0.3秒タイムアウト後に復帰開始。瞬きも欠測になるので短い間は少しだけ戻る。復帰時の追従時定数は約45ms。
- 数値診断にgaze、送信packetにgazeTracked/gazeYaw/gazePitchを追加。推論時間をgaze_msと全pipelineへ加算。撮影画像・目ROIの保存なし。

## 戻し方

`tracking-settings.json` の `gaze_enabled` を `false` にして再起動すると追加推論を行わず従来動作へ戻る。F4はその場でアバターへの反映だけを切り替える。Python単独起動は `--gaze` がなければ無効。追加フィールドのない旧packetも中立へ戻る。

変更前はresults/checkpoints/before-gaze-20260912.zip。元アバター原本は変更していない。

## 検証と未確認事項

- Python141件成功。Unity実Playerで両眼の左右/上下、段階的な復帰、OFFを検査。実Bakeで±入力が眼の頂点を約1.3mm動かすことを確認。既存腕・口・欠測保持の回帰成功。目のみ戻る要件に合わせ、既存欠測保持テストから目ボーンだけを除外、目の復帰は別検査。results/gaze/verified.log。
- 合成入力103callのCUDAイベント39243、CPU演算0。100callの片目中央値6.54ms、95%点7.06ms（プロファイル有効、転送を含む）。両目では概ね倍の追加が見込まれるが実人物での両目負荷は未測定。results/gaze/gpu.json。
- カメラ60frameの計測は実行できたが有効顔を得られず虹彩実行0call。目線の精度・眼鏡・照明条件・頭の回転による誤差は未検証。20260911T205223-803057Z-rtmw-l-384の数値ログ参照。前のsandbox実行はカメラを開けず失敗。
- 合成packetのlook-final.pngは表示確認用。実人物の視線再現を確認した画像ではない。
