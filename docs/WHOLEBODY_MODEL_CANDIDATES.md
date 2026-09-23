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
