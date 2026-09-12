# 配布ライセンスの棚卸し

2026-09-13。対象は現在のWindows開発版と、将来のPlayer＋Unity変換プラグイン配布。**棚卸しであり、現在のbuildsフォルダーをそのまま公開できるという判定ではない。** ソースの許諾、モデル重みの許諾、同梱DLLの許諾を分ける。無料配布でも再配布条件は必要になる。

## 現在の部品と扱い

| 部品 | 確認した条件・出所 | 配布時の扱い／残件 |
|---|---|---|
| TanakaCap独自コード | ルートの製品用ライセンスは未決定 | MIT等の許諾型を候補とするが、今回勝手に公開・再許諾しない。サードパーティ部分を自作扱いにしない |
| 自作デモモーション | 0BSD、`PROCEDURAL_MOTION_LICENSE.txt` | モーション単体は配布可能。アバターの許諾は別 |
| Python 3.11 | PSF系の利用条件 | 埋め込み配布を選ぶ場合はPython本体のLICENSEと同梱ライブラリの通知を含める。開発venv丸ごと配布はしない |
| ONNX Runtime GPU 1.30.0 | インストール済みwheelのMIT、ThirdPartyNotices等を収集 | MIT本文・同梱部品の通知を保存。NVIDIA DLLまでMITになるわけではない |
| NumPy 2.4.6 | wheel宣言はBSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | NumPy本体だけでなく、wheel内の数値ライブラリ通知を同梱 |
| OpenCV Python 5.0.0.93 | wheel宣言Apache-2.0、第三者通知あり | 動画入出力など同梱DLLの条件を別途照合。OpenCVの名称だけでApache単一とは扱わない |
| ONNX 1.22.0 / flatbuffers / ml_dtypes | Apache-2.0系の宣言 | 現行は派生ONNX生成にもONNXを使う。開発専用と決めつけず実配布経路に合わせる。変更通知とライセンスを保持 |
| protobuf、packaging、typing_extensions等 | インストール済みメタデータ・ライセンス実体を収集 | 正確な版は下記inventory。pytest等の検証専用依存は製品から除外 |
| CUDA/cuBLAS/cuDNN等 | NVIDIA独自契約。実wheel内の契約本文を収集 | 補足の再配布対象リストと実DLL名を照合し、必要なDLLだけにする。EULA条件・第三者通知を製品配布へ反映する作業は未完了 |
| RTMW3D-XのONNX | [取得先モデルカード](https://huggingface.co/Soykaf/RTMW3D-x/blob/main/README.md)はApache-2.0、[元プロジェクト](https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose3d)はMMPose | 配布可能な候補。コミュニティ変換物なので元重み・変換物のSHAと通知を維持。学習データの条件が重みへどう及ぶかをコードのApacheだけで解決済みとしない |
| YOLOX-M HumanArt / tiny、RTMW-L/X、DWPose比較用 | [MMPose](https://github.com/open-mmlab/mmpose/blob/main/LICENSE)・[YOLOX](https://github.com/Megvii-BaseDetection/YOLOX/blob/main/LICENSE)コードはApache-2.0 | 取得アーカイブ別の重み許諾・通知の確定が残る。YOLOXをUltralyticsのYOLO/AGPLと混同しない。通常使わない比較重みは除外 |
| 虹彩ONNX | [PINTO 049の個別LICENSE](https://github.com/PINTO0309/PINTO_model_zoo/blob/main/049_iris_landmark/LICENSE)はApache-2.0、TensorFlow Authors通知。ローカル`models/iris-landmark.LICENSE` | 原本とbatch2派生の出所・SHA・変更内容を記録して通知を同梱。モデル集全体のライセンスから推測しない |
| 顔の固定テンプレート | MediaPipe canonical_face_modelからの対応点抽出。`capture_lab/data/face_template.json`に元URL/SHA、同ディレクトリにApache本文 | 対応点抽出・座標変更を派生物として通知。今回の口Zなしでも使用する |
| 頭専用MobileNet V3 small | [作者リポジトリ](https://github.com/yakhyo/head-pose-estimation)はMIT。作者は300W-LP学習と記載 | 重みと学習元の配布条件を未確定として保持。コードMITだけで重みの商用配布可と結論しない。製品同梱の確定対象から外す |
| 頭領域YuNet 2023mar | [公式モデルディレクトリ](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)のMIT、`YUNET_LICENSE.txt` | 通知とモデルSHAを維持 |
| Unity Player / Editor | [Unity Editor Software Terms](https://unity.com/legal/editor-terms-of-service/software)による条件付きのランタイム配布 | 使用した2022.3.22f1に適用する契約、契約プラン、第三者通知を出荷時に固定。Editorや認証済み環境を丸ごと同梱しない。最新版Web契約を過去版へ無条件に遡及させない |
| lilToon 2.3.4 | [版指定MIT](https://github.com/lilxyzw/lilToon/blob/2.3.4/LICENSE) | 著作権・MIT本文を保持。アバターと一緒に書き出すシェーダーにも通知を添える |
| KlakSpout 2.0.6 / Spout2 | ローカルKlakSpoutはUnlicense。[Spout2](https://github.com/leadedge/Spout2/blob/master/LICENSE)はBSD-2-Clause | ネイティブプラグイン内のSpout由来コードの通知も必要。KlakSpoutのUnlicenseだけを同梱すれば足りるとはしない |
| OBS / OBS Spout2プラグイン | 別アプリの外部依存 | 現在は公式取得手順を案内し、製品へ同梱しない。OBSのGPLがプロセス間テクスチャ受信だけで当アプリ全体に当然適用されるとは扱わない。プラグイン再配布を行う場合は別途ライセンス・対応ソースを準備 |
| 比較動画用FFmpeg 7.1 gyan essentials | 実バイナリに`--enable-gpl --enable-version3 --enable-libx264`。現在の実体はGPLv3条件。[公式説明](https://ffmpeg.org/legal.html) | ローカル比較動画の開発ツールとして維持、通常リアルタイム製品へ同梱しない。将来同梱する場合は対応ソース等が必要。動画出力それ自体が自動的にGPLになるという意味ではない |
| HAOLAN 1.6 | 作者配布規約PDFと本文をローカル確認。未改変/改変の配布、ソフト組込みは許諾、クレジット等の条件あり | 一律「再配布禁止」ではない。規約・クレジットを付ける現行検証用成果物と、一般向けユーザー持込を区別。作者規約を独自MITへ置換しない。任意の改変アバター・衣装の再配布許可に一般化しない |
| VRChat SDK / 本家PhysBone | 開発Editor限定の比較対象 | SDK本体と本家ランタイムを製品へ同梱しない。ExporterはユーザーのUnity環境のSDK設定を読み、独自形式へ変換。独立揺れ物は維持 |
| SAM DINOv3 / ViT-H / MHR | SAMは専用契約、MHRはApache-2.0。詳細[既存調査](VITH_REALTIME_DISTRIBUTION.md) | 現在は比較環境のみ。モデル本体の許諾だけでDINO/人物検出器/全Python依存の同梱完了とはしない |
| HaMeR / MANO | [MANO公式契約](https://mano.is.tue.mpg.de/license.html)は用途限定・第三者配布制限 | 自由配布向け製品に現条件のMANOを同梱しない。ユーザー個別取得に変えるだけでは商用等の用途制限は解消しない。HaMeRコード/重みとMANOを分けて判断 |

HAOLANの証拠は`assets-source/haolan-license-ja.pdf`と`haolan-license-layout.txt`。規約本文第2条、個別条件M/N/R/V、クレジット欄を参照。取得先は[作者BOOTH](https://booth.pm/ja/items/3818504)。ファイルと現在のWebが異なる場合は、実際に取得した版への適用条件を確認する。

## TensorRTの今回の判断

ユーザーの「変な制約がつきそうならやめる」に合わせ、**今回はインストール・実装を見送る**。通常TensorRTもRTX版も配布そのものが禁止という意味ではない。RTx限定だからライセンス製品名もTensorRT for RTXにしなければならない、という関係でもない。

- [通常TensorRT契約](https://docs.nvidia.com/deeplearning/tensorrt/latest/reference/sla.html)：§1.2でアプリ付随の配布条件、条件に整合するユーザー契約、違反を知った／疑った場合の通知・契約執行等。補足§2はランタイム`.dll`/`.so`を配布対象としている。アプリ全体のソース公開を要求する契約ではない。
- [TensorRT for RTX契約](https://docs.nvidia.com/deeplearning/tensorrt-rtx/latest/reference/sla.html)：§2.13にベンチマーク・性能情報等の第三者開示への事前許可、§2.9に競合開発制限。性能比較と将来UIの実測負荷表示に使う本件では無視できない追加条件。通常TensorRTにこのRTX版の条文をそのまま当てはめない。
- **通常TensorRTの主要な配布義務は、既に使っているCUDA SDKにも同種のものがある。** 現行CUDAが無条件配布なのにTensorRTだけ厳しいという結論ではない。今回は製品EULA・DLL同梱方針を未確定のまま契約依存を増やさない判断とした。通常TensorRTを許容する方針になれば技術実装候補に戻せる。
- [ORTのTensorRT経路](https://onnxruntime.ai/docs/execution-providers/TensorRT-ExecutionProvider.html)はCUDA EPと別。公開互換表は現環境ORT1.30/CUDA13との組合せを確定する資料として不十分だった。将来は実wheel依存と対象SDK版を照合し、エンジンの環境依存と初回構築を評価する。今回、速度や品質は計測していない。

GPU推論の既存構成は継続する。今回の調査を理由に環境からCUDAや既存モデルを削除したり、CPU推論へ切り替えたりしない。FP16・部位間引きも追加しない。

## 保存した棚卸しと更新方法

```powershell
.\.venv\Scripts\python.exe tools/audit_distribution.py --output results/distribution-audit-20260913
```

上記保存先は作成済み。再実行は新しい保存先にする。22パッケージ、48個のライセンス/通知実体、ローカル16 ONNXのSHAを収集済み。原本は変更しない。`inventory.json`の宣言は自動収集したメタデータであり法的な許諾判定ではない。結果には派生キャッシュ・比較モデルも含むので同梱リストとして使わない。

今後、依存・モデル・Unityプラグインを変更したコミットで、この表とinventoryを更新する。リリース単位では、実際に同梱するファイルの一覧とSHA、ライセンス本文、著作権通知、派生物の変更通知を`ThirdPartyNotices`へ集約する。コードのOSSライセンスだけを並べた一覧を配布完了条件にしない。

## 配布までに残る具体作業

1. 独自コードのライセンスと製品EULAを決める。NVIDIA/Unity/素材の条件を独自部分へ不必要に広げず、第三者部分の例外を明示する。
2. 通常モデルの取得物単位で重みの許諾・学習由来の未確定点を閉じる。頭専用の重み、SAM/HaMeR比較環境を製品へ自動的に含めない。
3. 実出荷フォルダーでDLL/フォント/シェーダー/ONNX/アバターの全ファイルを照合する。NumPy/OpenCV/Spout/Unityなどの内部同梱物も対象。
4. 必要な通知の同梱・NVIDIA DLL再配布リスト照合・利用条件表示を実装し、クリーンPCの導入試験で検証する。現在の全開発環境コピーは出荷方式にしない。

一般配布は未実施。今回の成果は配布可否の論点・除外対象・根拠の整理であり、フェーズ5全体の完了ではない。
