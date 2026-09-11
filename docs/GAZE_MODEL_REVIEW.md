# 目が動かない問題とモデル選定の見直し（2026-09-12）

## 記録から分かったこと

ユーザーは目が全く動かないと評価。最新 `20260911T205903-841199Z-rtmw-l-384` の453frame中389frame（85.9%）はgazeTracked/faceTrackedとも有効。送信yawは−12.97〜9.38度、pitchは−6.08〜1.77度。入力の全棄却ではない。packetは最大2124bytesでUnityの4096byte制限以内。reportはrunningのまま残っており、計測終了処理・全セッションのGPU集計は完了扱いしない。

HAOLAN Bodyの左右各1089頂点に対する眼ボーン重み合計は各38.17855、平均0.035058（約3.5%）。目の子ボーン.001の影響頂点は0。旧実装でyaw±15/pitch±8度を与えても、作者「瞳小」の対象2178頂点の最大投影変位は約2.35〜2.44pixelに留まった。通常の小さい入力ではさらに分かりにくい。これが確認できた表示上の減衰要因であり、ユーザーの全体験を再現したとまでは言えない。

前回はボーン角度と頂点変位の存在だけを確認した。目の見える部分の投影移動まで検査しておらず、不十分だった。今回、表示側を直すためにモデルの検出値を水増しすることはしていない。

## 現モデルを使った根拠と不足

採用したのはGoogle由来の旧Iris LandmarkをPINTOがONNX変換した2021年配布物。既存RTMWの68顔点に虹彩がないため、眼ROIだけ追加推論でき、顔・身体の既存挙動を変えず、現行ONNX Runtime CUDAで動かせることを試作理由とした。片目合成入力中央値6.54msの実行確認はある。

これは「4090で最高精度」「他モデルより良い」という根拠ではない。代替モデルとの比較を先に行わず有効にした点は、当初の精度優先方針に対して調査不足だった。虹彩位置を目幅で割って角度へ比例変換しており、専用の視線推定ネットワークではない。Googleも虹彩追跡自体は注視位置を推論しないと説明している。[公式Iris説明](https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/iris.md)

## 代替候補

以下は公開資料での比較。手元の4090・カメラで同じ入力を通す精度/遅延比較は未実施。ライセンス欄は公開表記の確認であり、重みや学習データを含む製品同梱の承認を意味しない。

| 候補 | 出力・性質 | このプロジェクトでの位置づけ | 導入上の確認点 |
|---|---|---|---|
| 現Iris Landmark | 眼ROIから虹彩5点と眼輪郭。頭と目の対応付けは自前 | 既存機能を独立して試す基準。最高精度候補として未評価 | 旧モデル、RTMWの眼切り出し誤差に依存。配布元Apache-2.0表記 |
| Face Landmarker V2 | 顔256×256から478点、虹彩を含む。公式Taskは別モデルで52表情係数も出す | 顔と虹彩を同じ座標系で取る比較候補。口/目の将来統合にも有用 | Google公式配布と第三者ONNX移植を区別。Windows CUDAで移植の数値一致・速度を検証する必要 |
| L2CS-Net | 顔外観から視線yaw/pitchを直接推定、公式ResNet50モデルあり | 実装/比較しやすい視線方向モデルの基準。虹彩の単純比例変換と比較する価値 | コードMIT表記。重み/データ条件別確認。頭基準の目角度へ座標変換が必要 |
| 3DGazeNet（ECCV 2024） | 密な3D眼メッシュと視線ベクトル。異なる環境への汎化を狙う | 4090で品質を比較する有力な研究候補。眼構造を扱う点も用途に合う | 公開推論コード/重みあり。確認したルートに明確なLICENSEが見当たらず、配布採用条件は未解決 |
| UniGaze（WACV 2026表記） | 大規模MAE事前学習、B/L/Hの視線モデルとCUDA推論を公開 | 精度優先の比較対象から外すべきではない。大きいモデルも検証対象になり得る | モデルはMG-NC-RAI-2.0の非商用条件表記。配布・収益配信を想定する既定機能への採用は条件解決前に決めない。4090実負荷未計測 |
| GazeTR-Hybrid（ICPR 2022） | CNNとTransformerによる視線推定、ETH-XGaze学習重み公開 | 追加の研究基準候補 | 公開コードCC BY-NC-SA 4.0表記。入力正規化と旧依存の切り離しが必要 |

出典：

- [Google Face Landmarker公式仕様](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker)、[yakhyoのONNX移植と原モデル一致検証の説明](https://github.com/yakhyo/mediapipe-face-mesh-onnx)。移植一致は視線精度の証明ではない。
- [L2CS-Net公式実装](https://github.com/Ahmednull/L2CS-Net)、[論文](https://arxiv.org/abs/2203.03339)。
- [3DGazeNet公式実装](https://github.com/eververas/3DGazeNet)、[ECCV論文](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/03191.pdf)。
- [UniGaze公式モデル一覧・ライセンス](https://github.com/ut-vision/UniGaze)、[WACV論文](https://openaccess.thecvf.com/content/WACV2026/papers/Qin_UniGaze_Towards_Universal_Gaze_Estimation_via_Large-scale_Pre-Training_WACV_2026_paper.pdf)。
- [GazeTR公式実装](https://github.com/yihuacheng/GazeTR)。

同じ「視線推定」でも、虹彩位置、カメラ基準の3D方向、画面上の注視位置は違う。頭ごと右を向いたときのカメラ基準視線を、そのまま眼球の右回転へ足すと二重回転になる。3D方向モデルは顔姿勢を逆変換して頭基準へ直す必要がある。データセット内の角度誤差とWebカメラでの微小な眼球運動の再現性も同一ではない。

## 今回の修正と次の比較

元のメッシュ/骨重みは変更せず、実行時コピーに瞳専用モーフを生成。「瞳小」の変形対象と眼ボーン影響領域の共通部分だけを支持とする。瞳と同じ対象のハイライトを動かし、横最大4mm/縦2.5mm。眼ボーン回転は中立に保ち二重適用しない。立体眼球回転の再現ではなく、HAOLANの見た目向けの表示対応。

同じ±15/±8度で最大約6.38〜6.40pixel、約3.43mmの実頂点移動を確認。符号・移動方向と対象外頂点の1μm以下の不変を実Bakeで検査。ロスト復帰/F4 OFFと旧方式も回帰成功。results/gaze-audit/verified.log、reversible.log。recorded-look.pngは記録された視線値だけを固定し頭等を変更した表示検査で、当時の映像再現ではない。

`gaze_render_mode: "iris"` が今回の表示、`"bones"` で旧方式。`gaze_enabled: false` で追加推論OFF。F4の状態・反映角度・描画方式を画面に表示する。ロストは従来通り緩やかな正面復帰。

次の比較ではFace Landmarker V2とL2CS-Netを実用基準、3DGazeNet/UniGazeを精度優先の研究基準とする案が妥当。今回はモデルを交換しておらず、新モデルの採用は未決定。生映像を保存していないため古い数値ログから別モデルの検出精度は再評価できない。同じライブ入力で頭固定の上下左右、頭だけ回転、瞬き、眼鏡/遮蔽を比較し、目方向の正しさ・復帰・遅延・総GPU負荷を確認する必要がある。
