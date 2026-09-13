# 3推論モードのモデル配布判定（2026-09-13）

前回「確認中」としたHumanArt版YOLOX-M、RTMW-L、頭専用MobileNetV3 smallは、**提供者が公表するライセンスに従って商用利用・再配布可**へ更新する。コードのLICENSEだけでなく、作者のモデル保管庫の宣言と現行ファイルの同一性を確認した。現在のモデルをライセンス理由で交換する必要はない。

ここでの「可」はモデルの公開ライセンスに基づく配布判断であり、学習データ自体の配布権や第三者権利の無侵害を保証する判断ではない。データを取得・同梱・再学習する計画はない。GPUライブラリ、FFmpeg、Unityの出荷監査とは分ける。

## 全部ON：頭・表情・体・腕・指・目線

| 現行モデル | 役割 | 商用利用・再配布 | 移行候補 |
| --- | --- | --- | --- |
| YOLOX-M HumanArt版 | 人物枠 | 可：Apache-2.0、今回確定 | 移行不要。RT-DETR R18は性能比較する場合の任意候補 |
| RTMW3D-X | 体・手・顔の点。顔点から頭角度と表情も計算 | 可：配布元モデルカードのApache-2.0、従来判定を維持 | 現行維持 |
| Iris Landmark | 目線 | 可：個別Apache-2.0 | 現行維持 |

## 顔・頭：頭と表情、目線なし

| 現行モデル | 役割 | 商用利用・再配布 | 移行候補 |
| --- | --- | --- | --- |
| YOLOX-M HumanArt版 | 人物枠 | 可：Apache-2.0、今回確定 | 移行不要。YuNet等への置換は任意の顔専用化案 |
| RTMW-L | 顔点から頭角度・眉・瞼・口を計算 | 可：Apache-2.0、今回確定 | 移行不要。Face Landmarker ONNXは任意の品質比較候補 |

## 頭のみ：頭角度のみ、表情・目線なし

| 現行モデル | 役割 | 商用利用・再配布 | 移行候補 |
| --- | --- | --- | --- |
| YuNet | 顔枠 | 可：個別MIT | 現行維持 |
| MobileNetV3 small頭姿勢 | 頭角度 | 可：MIT、今回確定 | 現行維持 |

## 新たに確認した根拠

### YOLOX-M HumanArt版、RTMW-L

[Tau-J/RTMPoseのモデルカード](https://huggingface.co/Tau-J/RTMPose/blob/main/README.md)に `license: apache-2.0`。対象ZIPを同じモデル保管庫で公開している。Hugging Faceの[Tau-Jプロフィール](https://huggingface.co/Tau-J)から[GitHub本人](https://github.com/Tau-J)へのリンクがあり、本人はMMPoseの元リードとRTMW/RTMW3Dの研究を明記。無関係な第三者ミラーのタグを許諾根拠にしていない。

保管庫の固定版：`cd4d7095f5cfc9cfc4f46289bee91ea4a1e1d9fd`。この版のREADMEは28 bytes、SHA256 `98b45ea81164d1e1a1dd82255207053b15cd6c69d922a1c5cf3387ce604d4b74`。

| 対象 | 作者保管庫の原本 | ZIPのSHA256 |
| --- | --- | --- |
| RTMW-L | [rtmw/onnx_sdk/rtmw-dw-x-l_simcc-cocktail14_270e-384x288_20231122.zip](https://huggingface.co/Tau-J/RTMPose/blob/main/rtmw/onnx_sdk/rtmw-dw-x-l_simcc-cocktail14_270e-384x288_20231122.zip) | a87e1af41a0a067776dba7d46e1c21c8f6e9f18e247e0e606718dd1f31e96ffd |
| YOLOX-M | [rtmposev1/onnx_sdk/yolox_m_8xb8-300e_humanart-c2c7a14a.zip](https://huggingface.co/Tau-J/RTMPose/blob/main/rtmposev1/onnx_sdk/yolox_m_8xb8-300e_humanart-c2c7a14a.zip) | a000224fd8ba283202bc62d4a5fcdfe353adb9f468777dbac1ea2ada2093adde |

作者公開のLFSポインターのZIPハッシュと、OpenMMLabから取得時に保存したローカルreceiptのZIPハッシュが一致。現在のONNXもreceiptおよびrelease/models.lock.jsonに一致。重みを再ダウンロード・再実行せずに同一性を照合した。

[MMPose issue #3271](https://github.com/open-mmlab/mmpose/issues/3271)は今回GitHub APIでもコメント0件だった。しかし、未回答の第三者質問は別に存在する作者のライセンス宣言を無効にしない。HumanArtのデータ利用条件を重みの一律禁止に読み替えない。前回はこのモデル保管庫を見落とし、コード許諾とデータ条件だけで保留していたため訂正する。

### 頭専用MobileNetV3 small

[作者のモデル別一覧](https://huggingface.co/yakhyo/uniface-weights/blob/main/README.md)はheadpose系列をMITと分類。[個別ファイル](https://huggingface.co/yakhyo/uniface-weights/blob/main/headpose_mobilenetv3_small.onnx)のSHA256 `e8ae4d932b3d13221638fc72e171603e020c6da28b770753f76146867f40e190` が手元の原本と一致した。顔認証用の同名MobileNetV3重みとは区別する。

カードとLFSポインターを同じ固定版 `4c7ed723a20deb7ff154b1ba7d6e73747d954016` から取得。カードは8928 bytes、SHA256 `e3d5747e2936944ded4c27abe2c65d8b7a082af0953c81f50e776b4e478e8dda`。原文MITはdocs/HEAD_MODEL_LICENSE.txt、配布用release/notices/HeadPose-MIT.txtを保持。

### 既に可としたモデル

[RTMW3D-Xモデルカード](https://huggingface.co/Soykaf/RTMW3D-x/blob/main/README.md)、[Iris個別LICENSE](https://github.com/PINTO0309/PINTO_model_zoo/blob/main/049_iris_landmark/LICENSE)、[YuNet個別LICENSE](https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/LICENSE)を参照。今回これらの版・判定は変更していない。

## 配布条件と実施範囲

MITは著作権表示・許諾本文を保持。Apache-2.0は本文、該当する著作権/NOTICE、変更通知を保持する。FP16化等の派生にも原条件を維持する。独自コードMITと併存可能。[Apache-2.0原文](https://www.apache.org/licenses/LICENSE-2.0)

モデルのZIP同梱と提供元からの自動取得の双方が選択可能。自動取得は容量・初回導入方法の選択であり、現在のモデルの配布条件を回避するための必須対応ではない。方式変更・モデル交換・外部問い合わせ・公開はしていない。

原文スナップショットと機械照合はresults/model-license-evidence、持ち越し用の固定メタデータはrelease/model-license-evidence.json。tools/collect_model_license_evidence.pyで再取得・照合できる。最初のネット取得は一部TLS切断で失敗し、通常権限と版固定で最終6資料取得・3モデル照合に成功。これは推論速度/品質の再検証ではない。

モデルの2残件をrelease/config.jsonから解消したが、NVIDIA契約と実DLL対応、OpenCV内部FFmpegの対応ソース、Unity契約/内部通知の3残件が残るため製品全体のpublication_approvedはfalseを維持。
