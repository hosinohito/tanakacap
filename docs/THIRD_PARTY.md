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
