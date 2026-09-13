# 実配布物のライセンス監査（2026-09-13）

## 代替候補の確認（2026-09-13、未採用）

ユーザーから導入前の条件確認について指摘。PROGRESSの頭専用導入記録にはコードMITを確認した一方で、重み/学習元の一般配布監査は残すと明記されていた。使用許諾の確認と製品同梱の最終確認を完了したという説明を混同しない。

人物枠検出の代替として、[PekingU/rtdetr_r18vd](https://huggingface.co/PekingU/rtdetr_r18vd)はモデルカードにApache-2.0を明示、COCO学習と記載。[RF-DETR Nano/Small](https://github.com/roboflow/rf-detr#benchmarks)は提供元がモデル別にApache-2.0を明示。Plus/XL/2XLのPML版と区別する。著作権/ライセンス/必要なNOTICEと変更通知を保持する条件で商用利用・再配布の根拠がある候補。実物の取得/版固定/ONNX変換/CUDAベンチマークは未実施。公開TensorRT性能を当プロジェクトのORT性能としない。

提案はRT-DETR R18を先に評価。人物枠のみを交換し、RTMW3D・顔/目/腕などの補正を固定して既存録画でROIの欠測/復帰と速度を比較する。顔専用RTMW-L/頭専用の代替を確定したことにはならない。通常YOLOX COCO版も移行は小さい候補だが、今回「重みへの明示」を優先するため上記2系統を先に挙げる。ユーザーの採用指示・モデルの交換はまだない。

対象は `builds/releases/0.1.0-review4/TanakaCap` の実ファイル、16実行パッケージ、モデル原本6点、Unity 2022.3.22f1製品Player。独自コードMITの決定は維持する。**通知不足の修正は実施したが、現構成を無条件で公開可能とは判定できない。** 許諾不明と禁止は区別する。問い合わせは送信していない。

## 結果

| 部品 | 確認できたこと | 判定・対応 |
| --- | --- | --- |
| 独自コード / 自作モーション | MIT / 0BSD本文あり | 通知を保持して配布可能 |
| Python / Tk / NumPy / ORT / ONNX等 | 配布wheelのLICENSE/ThirdPartyNotices、Pythonの本文、Tkのlicense.termsを同梱 | 親ライセンスだけでなく内部通知を保持。版変更時は再照合 |
| 虹彩 / YuNet / 顔固定テンプレート | 個別Apache-2.0 / MIT / MediaPipe由来Apache-2.0の本文あり | 原本SHA、出所、FP16・batch2・座標抽出等の変更通知を保持 |
| RTMW3D-X | [配布者のモデルカード](https://huggingface.co/Soykaf/RTMW3D-x/blob/main/README.md)にApache-2.0の明示 | 再配布の根拠あり。学習素材の全権利の保証ではない。MMPose本文を追加 |
| RTMW-L | [MMPose](https://github.com/open-mmlab/mmpose/blob/main/LICENSE)はApache-2.0。[一般的なモデル商用利用の回答](https://github.com/open-mmlab/mmpose/issues/2106)あり | 今回のcocktail14/DW重みまで特定した説明は未確認。全学習データの条件をコード許諾で上書きしない |
| HumanArt版YOLOX-M | [HumanArt公式](https://github.com/IDEA-Research/HumanArt#dataset-download)はデータ利用申請を非商用目的と説明 | **重みの商用再配布は保留**。データの条件が重みに当然適用されるとも、適用されないとも断定しない |
| 頭専用MobileNet V3 small | [配布作者](https://github.com/yakhyo/head-pose-estimation)のMIT、300W-LP学習の記載あり | 重み・学習由来の範囲確認が残る。学習元公式サイトは今回タイムアウト。別モデルの禁止条項をこの重みに流用しない |
| CUDA関連 | 実wheelのAttachment Aにcudart/cuBLAS/cuFFT/cuRAND/NVRTC/NVBLASの系列名あり | 20 DLLをSHA付きで列挙。不要な122 .h、14 .hpp、5 .libは今後のZIPから除外。開発環境は維持 |
| cuDNN9 / nvJitLink | 下記の契約と実DLL不一致 | **対応する実配布版の契約確認が必要**。Web本文でwheel本文を黙って置換しない |
| OpenCV内部FFmpeg | wheel自身がLGPL-2.1本文を添付。動的DLLとして同梱 | **正確な対応ソース・ビルド手順の提供が未完了**。TanakaCap全体をGPLにする要求とは区別 |
| Unity Player | Editor内のlegal.txt、Native Plugin API通知を取得。ランタイムを製品の一部として配布する規定あり | 本文追加済み。適用する契約時点・プラン要件と実ランタイム内部の照合は出荷前に確定。認証成功だけを配布条件充足の証明にしない |
| KlakSpout / Spout | 2.0.6の実ソース内のLynn Jarvis等のBSD通知を取得 | Unlicenseだけだった不足を修正。Unity Plugin APIのCompanion Licenseも追加。WIDL生成ヘッダー等の内部由来の照合はUnity/ネイティブ残件に含める |
| lilToon / VRC Light Volumes | ローカル配布パッケージ内のMIT通知あり | 両方の本文を追加。アバター/衣装の使用許諾を代替しない |

## NVIDIAの不一致の詳細

実wheelはcuDNN `9.26.0.51`だが、同梱 `License.txt` の補足は2020-01-28版でWindows対象を `cudnn64_7.dll` と記載する。実際は `cudnn64_9.dll`、`cudnn_ops64_9.dll` 等10 DLL。一方、[公式現行cuDNN契約](https://docs.nvidia.com/deeplearning/cudnn/backend/latest/reference/eula.html)の補足はruntime `.dll` を対象とする。**cuDNNの再配布自体が禁止という話ではなく、採用wheelの古い契約との適用関係が未確認**。

CUDA関連wheelにも2018年の本文が入っており、`nvidia-nvjitlink 13.4.52`の同梱Attachment AにnvJitLinkが見当たらない。CUDA系列9 DLLは一般名との対応を取れるが、全20 DLLが同一の明示的な再配布根拠に一致したという結果にはしない。原文は製品packages内、個別SHAと判定は `license-audit.json`。

製品はSDKを専用runtimeディレクトリへ配置し、推論機能の一部として使う。SDKの独立配布としない。MIT対象外の第三者部分を明示した `release/THIRD_PARTY_TERMS.md` を用意したが、原契約不一致の解消や法的有効性の最終判定を代替しない。TensorRTは不採用のまま。

## 人物検出モデル

今回と**同じ** `yolox_m_8xb8-300e_humanart-c2c7a14a` の商用デスクトップアプリへの再配布について、[MMPose issue #3271](https://github.com/open-mmlab/mmpose/issues/3271)が2026-08-19に作成され、今回閲覧時には回答がなかった。この質問自体は権利者の禁止宣言ではない。一般COCOモデルへの許可回答だけでこの重みの確認を終えない。

解決方法は、権限ある提供者からこの重みの利用・再配布条件を得るか、明示条件が揃う人物検出重みに交換して性能/精度を再検証すること。現在の検出方式をこの監査だけで勝手に交換しない。無料配布ならすべて解決する、別ダウンロードにすれば商用利用の不明点が消える、という説明はしない。

## OpenCVとFFmpeg

[OpenCV Python公式](https://github.com/opencv/opencv-python#licensing)と実wheelの第三者本文を照合。`cv2.getBuildInformation()`ではFFmpeg prebuilt、avcodec 61.19.100 / avformat 61.7.100 / avutil 59.39.100 / swscale 8.3.100。単に同じFFmpegメジャー版のソースを添えるだけでは、実バイナリの対応ソースを特定したことにならない。公式ビルドのコミット、変更、設定、リンク対象を一致させ、同じReleaseから取得できるソース一式を準備する必要がある。[FFmpeg公式配布チェック項目](https://ffmpeg.org/legal.html)も参照。

開発動画用FFmpeg.exeは製品に含めないが、OpenCV内部のDLLは別。DLLを消せば録画読込が壊れるため削除しない。LGPL部分の差し替え・デバッグ権利を独自コード/NVIDIAの制限で妨げない利用条件を追加した。

## 自動検査と成果物

`tools/collect_release_notices.py` で本文14件と出所/SHAを `release/notices` へ固定。GitHub本文は取得時のコミットURLを保存、Spoutは使用中の2.0.6に固定。Unityのlegal.txtはEditorの全体通知で、製品へEditorの全部品が含まれることを意味しない。

`tools/audit_release_licenses.py <展開フォルダー> --output <結果JSON>` は本文ハッシュ・必要通知・モデルSHA・NVIDIA実行ファイル限定・全ネイティブファイルのSHAを検査。ビルドへ接続した。機械検査合格と再配布許諾確定を別にし、未確定なら `-Publishable` は引き続き停止する。

配布者の契約プラン、第三者への問い合わせ回答はローカルコードから推定しない。次回は上記5残件を個別に閉じる。具体的に問い合わせる場合は、NVIDIAへ採用wheel版・20 DLL名と古い本文の対応、MMPoseへ#3271の対象重み、頭モデル作者へ重みのMIT適用範囲を提示する。外部連絡は未実施。

検証：review5で本文14件、NVIDIA DLL20件、モデル原本と本文のSHA照合に合格。不要なSDKファイルを除いた同梱Pythonから、合成虹彩入力でCUDA 381ノード・CPU 0ノードを確認（results/release-license-gpu）。モデル全体の新規PC試験や法的許諾確定ではない。ZIPは2,085,247,898 bytes、CRC全件成功。
