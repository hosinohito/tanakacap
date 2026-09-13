# 第三者部品と通知

独自コードはMIT（TanakaCap.txt）、デモモーションは0BSDです。第三者部品を独自コードのMITで再許諾するものではありません。

| 対象 | 本文・出所 | 状態 |
| --- | --- | --- |
| Python / Tk・標準ライブラリ | Python.txt、runtime/LICENSE.txt、runtime/tcl内の通知 | 同梱本文を保持 |
| NumPy、ONNX、ORT、protobuf等 | packagesの配布物ごとの本文。版はrelease-status.json | wheel内の第三者通知も保持 |
| OpenCV | packages/opencv-python | 本体Apache-2.0、FFmpegはLGPL-2.1系。対応ソースの出荷準備が未完了 |
| NVIDIAライブラリ | packages/nvidia-* | SDK実行DLLのみ。cuDNN・nvJitLinkの同梱契約とDLLの対応は未解決 |
| MMPose由来のRTMW3D/RTMW-L/YOLOX-M | notices/MMPose-Apache-2.0.txt、YOLOX-Apache-2.0.txt | モデル配布元のApache-2.0宣言も確認。下記の固定版・原本との対応を参照 |
| 虹彩モデル | notices/Iris-Apache-2.0.txt | TensorFlow Authors、PINTO model zoo 049の個別ライセンス |
| YuNet | notices/YuNet-MIT.txt | Shiqi Yu、OpenCV Zoo |
| MobileNet頭推定 | notices/HeadPose-MIT.txt | Yakhyokhuja Valikhujaev。作者の重み別MIT表記と原本SHA一致を確認 |
| 顔固定テンプレート | face_template.LICENSE | MediaPipe canonical face modelから対応点を抽出、座標を変換 |
| Unity | notices/Unity-2022.3.22f1-ThirdPartyNotices.txt | Editor同梱の通知全体を保持。Editorを配布しているという意味ではない |
| KlakSpout / Spout | notices/KlakSpout-Unlicense.txt、KlakSpout-*-NOTICE.txt | KlakSpout 2.0.6に実際に含まれるSpoutソースのBSD通知を収集 |
| Unity Native Plugin API | notices/Unity-NativePlugin-License.md、Unity-Companion-License.html | Unity依存のプラグインに適用 |
| lilToon / VRC Light Volumes | notices/lilToon-MIT.txt、VRC-Light-Volumes-MIT.txt | シェーダー関連の通知。利用者アバターの許諾は別 |

モデルの原本SHAはmodelsの取得記録およびmanifest.jsonで識別します。実行時に生成するFP16化・バッチ2化・CUDA Graph用の派生ONNXには原本の条件が引き続き適用されます。派生時の変更は数値精度、入出力バッチ形状、グラフ分割・補助出力で、重みの再学習ではありません。

RTMW-L/YOLOX-M HumanArt版は[作者のモデル保管庫](https://huggingface.co/Tau-J/RTMPose/tree/cd4d7095f5cfc9cfc4f46289bee91ea4a1e1d9fd)でApache-2.0。両ZIPのSHAは元の取得記録と一致。頭専用は[作者のモデル別一覧](https://huggingface.co/yakhyo/uniface-weights/blob/4c7ed723a20deb7ff154b1ba7d6e73747d954016/README.md)でMIT、headpose_mobilenetv3_small.onnxと原本SHAが一致。RTMW3D-Xは[Soykafの変換モデルカード](https://huggingface.co/Soykaf/RTMW3D-x/blob/main/README.md)でApache-2.0。モデル条件は学習データ自体の配布許諾ではありません。

通知の取得元とSHAはnotices/sources.json。未確定事項の原文調査は開発リポジトリのdocs/RELEASE_LICENSE_AUDIT.md。コードが公開されていること、モデルをダウンロードできること、学習データの再配布権、生成した映像の権利は区別します。

SDK本体、TensorRT、比較専用SAM/HaMeR/MANO、実写録画、HAOLAN原本、OBS、開発用FFmpeg実行ファイルはこのZIPへ含めません。OpenCV内部のFFmpeg DLLは別の同梱部品です。
