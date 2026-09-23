# 全身3Dモデルの交換候補

調査日：2026-09-23。候補調査であり、導入・採用・公開はしていない。

## 結論と範囲

RTMW3D-Xの公式PyTorch・公開ONNX・自前ONNXで問題区間のZ出力が一致したため、全身モデル交換の候補を調査した。[切り分け](HAND_SIDE_AUDIT.md#元pytorchと自前onnxの比較)。対象は単眼RGBから体と両手・指を3D推定する系統。手専用モデルの別途探索はユーザー指定により行わない。

今回確認した範囲では、現モデルより新しく、商用利用・重みの再配布・リアルタイム性をすべて明確に満たす新候補は見つかっていない。SAM 3D Body系は条件付き候補に残るが、以前評価した系統であり、新発見や即採用として扱わない。通常のRTMW3D-X FP16を維持する。

## 候補と除外理由

| 候補・時期 | 機能と公開状態 | 配布の評価 | 今回の判断 |
| --- | --- | --- | --- |
| SAM 3D Body（2025年11月、論文2026年） | 体と手の3D復元。公式コード・重みあり | コードと重みは独自SAM License。非商用限定ではなく再配布許諾あり。ただし契約同梱・派生物への条件継承等が必要 | 条件付き候補。以前のViT-H full実測約0.5〜0.6秒/フレームで、ライブ用途には重い |
| Fast SAM 3D Body（2026年3月） | SAMの学習不要の高速化実装。新しい学習済みモデルではない | 追加コードのMITだけで元SAMや同梱依存の条件は消えない。公開構成はYOLO・MoGe等も使う | CUDAのみ・既存人物切り出しを用いる構成の検討余地。採用や速度達成は未確認 |
| Multi-HMR 2（2026年6月） | 全身メッシュ・追跡、Annyベース。公式重み公開 | 公式LICENSEはコード・チェックポイント等を含め非商用限定 | 今回の一般配布方針では除外 |
| Multi-HMR Anny版（2026年2月追加） | Annyを使う新チェックポイント | Anny自体はApache-2.0だが、推論モデルMulti-HMRは非商用限定 | 同上。人体モデルの許諾を推論重みへ流用しない |
| Hand4Whole++（CVPR 2026） | 全身推定で手の精度改善を狙う。コード・重み公開 | 本体コードMIT。ただし公式手順にSMPL-X・MANO・FLAME等の別資産が必要。SMPL-Xの標準モデル契約は非商用・再配布不可 | そのまま配布可能な候補から除外。外部配布重みまでMITと断定しない |
| SMPLest-X（2025年） | 表現力を重視する全身3D復元 | S-Lab Licenseの非商用限定。商用は別途連絡が必要 | 今回の一般配布方針では除外 |

時期は論文または提供者の公開告知に基づく。新しいリポジトリ更新日と新しい学習済み重みを混同しない。未実測候補の速度や左手の改善は保証しない。

## SAM系を検討する場合の制約

SAM License（2025-11-19版）はコード・学習済み重みを対象に、利用・改変・再配布を許諾する。一方で再配布/派生物への同条件適用と契約同梱、逆解析等の禁止、用途制限、第三者請求への補償、契約変更と継続利用による受諾などがあり、MIT/Apache相当の簡潔な条件ではない。MHR自体はApache-2.0。MHRからSMPLへ変換する必要は本アプリにはなく、SMPL資産を追加する前提にしない。

Fast版の現行READMEはRTX 5090で約65ms/フレームを報告する。約15fps相当であり、4090で30fpsの根拠ではない。標準デモはtorch.compileとTensorRTを使う。**TensorRTはユーザーが不採用としており復活させない。** TensorRTを除外した速度は別検証が必要。処理削減は肩・肘・掌・指の品質が同等とは限らない。

過去の測定・品質評価は[SAM実時間化調査](VITH_REALTIME_DISTRIBUTION.md)・[測定記録](SAM_PERFORMANCE.md)。同文書のTensorRT提案は現在の不採用方針で上書きされる。SAM3DBody-cpp等も別の学習済みモデルではなく実行実装であり、C++というだけで速度やライセンス問題の解決とはしない。

## 判断上の注意と次の作業

自動ダウンロードに変えても非商用限定は解消しない。SMPL-Xの生成済みBody向けCC-BYと、推論に必要なModelの契約は別物。コードMIT、人体モデルApacheという表示だけでは必要な全資産を配布可能とは判断しない。

次に試すならSAM系のCUDA経路が技術的な候補。ただし今回は候補提示まで。追加条件を嫌う方針なら、調査済み候補から無理に採用せず現行維持となる。採用前には採用版の全依存/モデル資産の条件、Windows RTX実行、問題録画の6秒・7秒台・15秒を含む両手品質、遅延・GPU負荷を確認する。最新録画とアバターの場所はHANDOFF参照。

## 一次資料

- [SAM 3D Body](https://github.com/facebookresearch/sam-3d-body)、[コード・重みを含むSAM License](https://github.com/facebookresearch/sam-3d-body/blob/main/LICENSE)
- [MHR公式説明とライセンス](https://github.com/facebookresearch/MHR)
- [Fast SAM 3D Bodyの構成・速度](https://github.com/yangtiming/Fast-SAM-3D-Body)、[論文](https://arxiv.org/abs/2603.15603)
- [Multi-HMR 2](https://github.com/naver/multi-hmr2)、[重みを含む契約](https://github.com/naver/multi-hmr2/blob/main/LICENSE.txt)
- [Multi-HMRのAnny重み追加](https://github.com/naver/multi-hmr)、[契約](https://github.com/naver/multi-hmr/blob/master/LICENSE.txt)、[Anny](https://github.com/naver/anny)
- [Hand4Whole++の必要資産](https://github.com/mks0601/Hand4Whole-plus-plus_RELEASE)、[本体コードMIT](https://github.com/mks0601/Hand4Whole-plus-plus_RELEASE/blob/main/LICENSE)
- [SMPL-X Modelの契約](https://smpl-x.is.tue.mpg.de/modellicense.html)、[生成Body向けの別契約](https://smpl-x.is.tue.mpg.de/bodylicense.html)
- [SMPLest-Xの契約](https://github.com/MotrixLab/SMPLest-X/blob/main/LICENSE.txt)

重み・依存のダウンロード、実機推論、ビルドは今回実施していない。SMPL-Xの拡張子なしURLは取得失敗し、公式modellicense.htmlで確認した。

## 他のキャプチャソフトの採用技術（2026-09-23）

使用モデルを公開している製品と、サービスとしてのみ提供する製品を分けて調査。以下の「未確認」は調べた公式資料内での状態であり、世界中の全資料を確認した意味ではない。各ソフトの最新重みの版・ハッシュは今回取得していない。

| 製品 | 公開情報から確認できた系統 | 一次資料・限界 |
| --- | --- | --- |
| Warudo | 内蔵MediaPipeで顔・手首・指。外部トラッカー併用可 | [公式マニュアル](https://docs.warudo.app/docs/mocap/mediapipe)。内部の厳密な重み版は未確認 |
| VNyan | WebカメラのMediaPipe系統、顔と実験的な手追跡 | [公式リポジトリWiki](https://github.com/Suvidriel/VNyanDoc/wiki/Tracking-Layers)。2025年の記述のため最新バイナリのモデル版まで断定しない |
| XR Animator | Google MediaPipe。顔・体・手を選択して全身追跡 | [作者README](https://github.com/ButzYung/SystemAnimatorOnline)。モデル単体でなく出力をアバターへ変換するアプリ |
| Dollars MONO SDK | MediaPipeUnityPluginベース、MediaPipe出力から骨格を計算 | [公式SDKガイド](https://docs.dollarsmocap.com/sdk-guide/)。SDKの確認であり全製品・全版への一般化はしない |
| VSeeFace / VTube StudioのWebカメラ顔追跡 | OpenSeeFace、MobileNetV3ベースの顔ランドマーク、ONNX Runtime | [OpenSeeFace作者](https://github.com/emilianavt/OpenSeeFace)。VSeeFace標準の手追跡は[Leap Motion](https://www.vseeface.icu/)でありWebカメラ全身モデルではない |
| Webcam Motion Capture | AIによる手・指追跡。具体的な公開モデル名は未確認 | [公式サイト](https://www.webcammotioncapture.info/index.php)。商用コンテンツ制作は可だがアプリ再配布・他製品への組込は不可と明記。MediaPipeと推測で断定しない |
| Move AI | 単眼s2・複眼m2、Dex手追跡。リアルタイムrt系列は複眼 | [公式モデル一覧](https://developers.move.ai/docs/models/)。製品モデル名は公開、ネットワーク構造と自由に配布できる重みは確認できず |
| Rokoko Vision / DeepMotion Animate 3D | 動画からのAIモーション生成。具体的な公開重みは未確認 | [Rokoko](https://www.rokoko.com/products/vision)・[DeepMotion](https://www.deepmotion.com/about)。Rokokoは[2026年に動画アップロード中心へ移行](https://support.rokoko.com/hc/en-us/articles/48823033216017-Rokoko-Vision-and-Rokoko-Create-What-you-need-to-know)。単眼ライブと同条件の速度比較ではない |

今回の発見は、新しい全身モデルよりもMediaPipeによる部位別モデル構成の採用例が多いこと。Googleの[Holistic公式](https://developers.google.com/edge/mediapipe/solutions/vision/holistic_landmarker)は体33点、両手21点ずつ、顔478点のモデルを組み合わせ、体と手のworld座標も返す。MediaPipeという名称だけで各製品が同じ版・同じ補正を使うとは言えない。

OpenSeeFaceは作者がコードとモデルをBSD-2-Clauseと明記するが顔用であり、今回の左手Z問題の直接の交換先ではない。MediaPipe系は別の比較対象になり得るものの、今回の調査は採用実績の確認まで。候補資産の配布監査、Windows RTX実行方法、品質・速度の比較は未実施。先の「より新しい全身モデルを探して見つからない」は、この既存系統まで使えないという結論ではない。ユーザーが保留した手専用追加モデルの実装を再開する指示とも扱わない。

## MediaPipeの精度・速度・ライセンス・時期（2026-09-23）

- 体はBlazePose GHUM（Lite/Full/Heavy）、手はHandPose GHUM（Lite/Full）。顔・体・手の複数モデルをまとめるHolisticと単体モデルを区別する。
- 公式旧Pose評価は2〜4mの人物1人、Yoga/Dance/HIIT、COCO相当17点。FullのPCK@0.2は95.5/96.3/95.7%、Heavyは96.4/97.2/97.5%。許容誤差以内の2D点の割合であり、3D・指・着席近接の正解率ではない。[公式表](https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/pose.md)
- 手Fullの公式2021年評価は2D mAP83.8%、平均3D誤差1.3cm（Liteは79.2%、1.4cm）。今回のRTMW3Dとの同条件比較ではない。[Google記事](https://blog.tensorflow.org/2021/11/3D-handpose.html)。遮蔽・手袋・物を握る場合などには制約があり、掌Z/指の改善は実録画で未確認。
- 手の現行Task公式平均遅延はPixel 6 CPU17.12ms/GPU12.27ms、処理パイプライン全体。[公式](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker)。旧体FullはPixel 3 GPU25ms、Heavy53ms、Lite20ms。別機器・別世代なので合算しない。2021年ブラウザー両手Fullはi9-10900K/GTX1070、MediaPipe WASM+GPUで120fps（TF.js WebGLでは35fps）。Windows Python CUDAや全身の速度を意味しない。
- 公開系統の時期：Hands初公開2019-08-19、BlazePose2020-08-13、Holistic2020-12-10。手のメートル単位3D対応改良は2021-11-15。Face Mesh V2のモデルカード日付2022-09-15。旧Solutionsから新Tasksへの移行告知2023-05-10。2026年のドキュメント更新日を重みの刷新と扱わない。[Hands初公開](https://research.google/blog/on-device-real-time-hand-tracking-with-mediapipe/)・[Pose](https://research.google/blog/on-device-real-time-body-pose-tracking-with-mediapipe-blazepose/)・[Holistic](https://research.google/blog/mediapipe-holistic-simultaneous-face-hand-and-pose-prediction-on-device/)
- コードだけでなく、[体モデルカード](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf)、[手モデルカード](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20Hand%20Tracking%20%28Lite_Full%29%20with%20Fairness%20Oct%202021.pdf)、[Face Mesh V2モデルカード](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20MediaPipe%20Face%20Mesh%20V2.pdf)にもApache-2.0明記。これらは商用利用・再配布可の根拠あり。本文/NOTICE/変更通知を保持する。GHUMを教師にした推論モデルと別途GHUM人体モデル資産の配布を混同せず、採用時は検出器・表情モデル等も含め実物の全資産・版・ハッシュを監査する。今回配布物の監査完了ではない。
- Windows GPU実装は別課題。[公式Windowsビルド手順](https://developers.google.com/edge/mediapipe/framework/getting_started/install)はGPU無効の例、[Python GPUのIssue](https://github.com/google-ai-edge/mediapipe/issues/5385)も存在。ブラウザーGPUの実績をPython CUDA対応と読み替えない。今回インストール・ベンチマークなし。
