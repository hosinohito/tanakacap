# 開発用素材・依存の記録

## HAOLAN

クレジット：**かなリぁ**

- 公式配布元：https://booth.pm/ja/items/3818504
- ユーザーが配置したBOOTH原本：HAOLAN_Ver1.6.zip
- SHA256：c37750cc2c6edcfafd70459e5c658d5cb78f3ab0483705b063bb3277c8140f4c
- 作者指定の利用規約：https://drive.google.com/drive/folders/1YUDZYWJyZPLCqWOkAFrlyIGkYGs4dVMV
- 取得した日本語規約：assets-source/haolan-license-ja.pdf。2026-09-11確認、規約版1.00。
- 個別条件I/Jに調整・形式変換・改変、Oに配信、Rにソフトウェアへの組み込み、Vにクレジット必須の記載を確認。全文を原本PDFで保持する。本メモは規約全文の代替ではない。
- 今回はローカル開発用。配布アプリへの標準同梱を決定したわけではない。

## lilToon

- 作者：lilxyzw、版2.3.4、MIT。
- https://github.com/lilxyzw/lilToon/releases/tag/2.3.4
- 公式配布ZIPをPackages/jp.lilxyzw.liltoonへ展開。LICENSEも保持。
- 元のマテリアルをこの版でインポートした。旧版と同一の見た目は未保証。

## 推論系

モデルURLとハッシュはmodels/catalog.jsonおよび各model.receipt.json、Python依存はrequirements-lab.lock.txtに記録。RTMW・DWPose・YOLOXは比較用であり、製品同梱時の重み・学習データ・ランタイムの条件確認は未完了。

規約の読み出しだけにpypdf 6.18.0を追加導入した。アプリ・キャプチャ実行には不要。

## Iris Landmark ONNX（2026-09-12試行導入）

- [PINTO変換配布](https://github.com/PINTO0309/PINTO_model_zoo/tree/main/049_iris_landmark)のdownload.shが示すresources.tar.gz内、20_new_20211209/resources.tar.gz → saved_model_64x64/model_float32.onnxを抽出。元はGoogle MediaPipe Iris。配布元のApache-2.0表記をmodels/iris-landmark.LICENSEへ保存。製品同梱の最終レビューは未完了。
- models/iris-landmark.onnx SHA256 `e3c8ae73a21415e396688d655d5f1d9e1cb5a01b7ed19962de76c06458bfddcb`。起動時照合。取得元URLは `https://s3.ap-northeast-2.wasabisys.com/pinto-model-zoo/049_iris_landmark/resources.tar.gz`、取得物はresults/iris-resources.tar.gz。モデル変換は無改変、ONNX Runtime CUDAで実行。
- 調査・入力仕様・限界は[目線試行](GAZE_TRIAL.md)。注視点の正確な推定を保証しない。

## KlakSpout 2.0.6（2026-09-12導入）

- [公式リポジトリ](https://github.com/keijiro/KlakSpout)、[公式npm配布](https://registry.npmjs.org/jp.keijiro.klak.spout/-/jp.keijiro.klak.spout-2.0.6.tgz)。Unity2022.3以降・Windows D3D11/12対応。現在のBuilt-in/D3D11でTexture送信を採用。
- 配布物のUnlicenseをembedded package内LICENSEに保持。ネイティブDLLを含む公式パッケージを無改変展開。ライブラリ版と依存はpackage.json/packages-lock.jsonに固定。
- npm integrity SHA512（base64）`mMwYPZalcNYaZWrJStiIqqIA4/8Ha6JgHP2YuyUyWmwXxC0r4a+0KjnCaMqTs2VuYtg3uG1/ys+9DqfxkyVCCA==` を取得物と照合済み。保存先results/klak-spout-2.0.6.tgz。
- OBS側 [Off World Live Spout2](https://github.com/Off-World-Live/obs-spout2-plugin)は別プラグイン（GPL-2.0）。今回導入/同梱していない。OBS受信は未検証。

## RTMW3D-X（身体奥行きの比較用）


- 原モデル・学習設定：https://github.com/open-mmlab/mmpose/tree/main/projects/rtmpose3d
- RTMlibが案内するコミュニティONNX変換：https://huggingface.co/Soykaf/RTMW3D-x
- ONNXのSHA256：4a289c0e99d47eb595e99679d9d4a2d1def1b4241f9adcbafba44b9ff585ebcd
- カード表記Apache-2.0。原モデル・学習データを含めた製品への同梱判断は未完了。公式ONNX配布物と混同しない。
- 深度復元の根拠はMMPoseのSimCC3DLabelとrtmw3d-x_8xb32_cocktail14-384x288.py。入力の深度軸は288、z_range=2.1744869。深度は相対メートル、画像XYはピクセル。

## 標準顔幾何点（2026-09-12）

Google MediaPipe canonical_face_model.objの29点を抽出、Apache-2.0。capture_lab/data/face_template.jsonに出典URL/SHA256と近似対応の注記、face_template.LICENSEにライセンス全文。頭ピッチと口角投影補正の幾何テンプレートで学習済み推論モデルではない。詳細docs/HEAD_PITCH_MOUTH.md。


## 2026-09-12 RTMW-X 2D比較候補

公式OpenMMLab ONNX SDK配布のrtmw-x_simcc-cocktail13_pt-ucoco_270e-384x288-0949e3a9_20230925.zipを取得。ONNX SHA256 b2dd00cce207d3c1503e35cc77a82ecd7092dcbdfe4a3c692ec4cdc3cf40c804、アーカイブSHA256 e2635599f6d14152af4bb3e97f90881a782b003857514c76cc341794364ffbdd。models/rtmw-x-384/model.receipt.json。ローカル測定ハッシュで署名検証ではない。出典は[RTMlib公式モデル一覧](https://github.com/Tau-J/rtmlib)とmodels/catalog.json。配布可否の最終判断は既存モデルと同様に別途行う。新たなSAM/HaMeR/MANO素材は今回取得していない。

## 2026-09-12 — フェーズ3追加

- Unity標準AssetBundle module1.0.0（Unity2022.3.22f1付属）を有効化。既存Unityの標準機能であり新推論依存なし。
- OBS Spout plugin1.12.0を公式releaseから取得し、OBS32.2.2で実受信検証。https://github.com/Off-World-Live/obs-spout2-plugin/releases/tag/1.12.0 。DLL SHA256 B998DF1C4C609D1EF27CA0561203FD1E196D7ED6FBCA7EDA45A4B0DD13D3DADD。導入済みOBSのコピーはローカル検証用、当プロジェクトの配布物へ同梱したと扱わない。再配布時は元ライセンスと依存DLLを再監査する。

## 自作の繰り返しモーション

ProceduralMotion.csは外部クリップ/実写記録を使わない独自の数式モーション。ソースと生成データは0BSD、docs/PROCEDURAL_MOTION_LICENSE.txt。アバター本体の配布条件は別。PhysBoneのSDKコード/DLLは同梱せず、docs/SECONDARY_MOTION.mdの独立互換変換を使う。
