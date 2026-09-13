# モデルの自動取得と頭・顔の代替候補（2026-09-13）

調査・提案であり、配布方式変更やモデル交換は未採用。現行の実行経路、設定、公開判定は変更していない。

追補：その後の同日再監査で、現行モデルの公開条件と原本同一性の確認を完了。[確定した3モード表](MODEL_LICENSE_DECISIONS.md)。以下の移行候補は任意の比較案であり、ライセンス解消のための必須移行ではなくなった。

## 初回取得案

ZIPにはモデルを入れず、初回に使用モードに必要なモデルを提供元から直接取得する。取得元・条件・サイズを示し、版と期待SHAを固定、途中失敗からの再試行、取得済みキャッシュ、次回以降のオフライン起動を用意する。自前ミラーは再配布となるため別扱い。申請・契約同意が必要なものを自動承認しない。

既存tanakacap/models.pyに取得機能はある。ただし取得後のSHAを記録する方式で、製品向けにはrelease/models.lock.json等の事前固定した期待値との検証が必要。初回UI・再開対応は未実装。モデルだけを別取得にしても同梱CUDA/cuDNNやFFmpegの監査は残る。これらも提供元から取得する設計は可能だが、適用契約と導入方法は個別確認が必要。

再配布を避けることと利用条件の解決は別。[InsightFace公式](https://github.com/deepinsight/insightface#license)は自動ダウンロードにも非商用研究限定を明示する。現行HumanArt版YOLOX-Mは別調査で作者のApache-2.0宣言を確認して解消したもので、自動取得に変えたための解消ではない。

## 候補

| 対象 | 候補・根拠 | 判断 |
| --- | --- | --- |
| 頭専用 | [現行MobileNetV3 smallと同作者のResNet18/34/50、MobileNetV3 large](https://github.com/yakhyo/head-pose-estimation)。[作者の重み一覧](https://huggingface.co/yakhyo/uniface-weights)はheadpose系列をMITと掲載 | 現行smallはMITと原本SHA一致を確認、継続。別サイズは任意の性能比較候補 |
| 頭専用 | [6DRepNet](https://github.com/thohemp/6DRepNet)、MITリポジトリ | 頭角度の直接回帰候補。表情は出ない。現行はこの方式を基にした軽量系なので、置換だけで許諾や品質が改善するとは限らない。重み個別の確認とCUDA比較は未実施 |
| 顔・頭・眉・口・瞼 | [MediaPipe Face Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker)、[ONNX移植元](https://github.com/yakhyo/mediapipe-face-mesh-onnx) | 有力候補。移植元はモデル由来を含めApache-2.0と説明。478点、虹彩点も含む。公式バンドルの52表情係数は別モデルであり、このONNX版には含まれない。PnPや既存表情計算へ点対応を追加する案 |
| 顔の軽量候補 | 同ONNXプロジェクトのFace Mesh 468点 | 虹彩なし。既存の虹彩モデルと併用できる候補。点数だけで精度優劣を決めない |
| 顔の所在検出 | [現行YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)、個別MIT | 継続候補。顔枠と少数点を出すだけで表情モデルの代替にはならない |
| 虹彩 | 現行PINTO変換iris-landmark、個別Apache-2.0 | 継続候補。Face Landmarker内蔵虹彩との交換は品質比較後に判断 |

Face LandmarkerのONNX版は第三者移植。ORT CUDAへの接続候補であり、当環境のGPU実行・FP16精度・速度は未検証。作者の変換一致報告は当プロジェクトの実測ではない。公式Webページ末尾のコードサンプルApache表記だけを重み許諾の根拠にはしない。

通常の全部ONではRTMW3D-Xの顔点を共有し、頭角度はPnPで計算する。頭専用MobileNetは別モード。顔専用モデルを通常経路へ追加すると推論が増える可能性がある。まず顔・頭モードのRTMW-L代替として比較し、頭・眉・口の補正と4フレーム法を維持する。ただし68点と478点は直接交換できず対応付けと基準の検証が必要。

最新提案は現行モデルを維持し、初回取得方式は容量と導入体験で判断。Face LandmarkerやRT-DETR等は精度・負荷を比較したい場合の任意候補。モデルの取得・比較・交換、外部問い合わせはしていない。
