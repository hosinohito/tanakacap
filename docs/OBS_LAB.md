# 開発版のOBS透過出力

前回のマゼンタ背景・クロマキー案は撤回。現在はアルファ付き画像をSpoutで送る。汎用変換・ファイル読み込み・OBS実合成は未完了。

1. デスクトップの `tanakacap-test.bat` で起動する。Spout送信元 `TanakaCap` が自動的に公開される。
2. OBSへ [Spout2プラグイン](https://github.com/Off-World-Live/obs-spout2-plugin/releases)を導入する。OBS側の導入は今回未実施。
3. OBSで `Spout2 Capture` ソースを追加し、送信元 `TanakaCap` を選ぶ。
4. Composite modeは `Premultiplied Alpha` から確認する。下に背景を置き、髪・輪郭・瞳の色と透過を確認する。実合成時の設定確定は未実施。[プラグイン公式手順](https://knowledge.offworld.live/articles/5059810-spout-plugin-for-obs-studio)

プレビュー背景はそのままだが送信背景は透明。ステータスは送信に含まれない。F3/`--obs` はプレビューGUIを隠すだけで送信開始には不要。

専用カメラ→1280×720 ARGB32 RenderTexture（4xMSAA）→KlakSpout Texture/KeepAlpha。Built-in RendererのためCamera captureモードは使わない。通常送信にCPU画像読み戻しはない。プレビューとの二重描画負荷は今後計測する。[KlakSpout公式仕様](https://github.com/keijiro/KlakSpout)

実Playerの透明/不透明/中間アルファ、Spout送信元登録、正常終了を検証済み（results/gamma-alpha/spout-msaa.log）。OBS受信・合成品質の確認を代替しない。

表示カメラはおなか付近からケモミミの先までを含む固定構図。実カメラの撮影範囲や推論解像度は変えていない。腕を広げると表示の左右から出る場合がある。

腕の推定の暴れは既知の未解決課題として残し、ユーザーの指示により細かな補正の追加をひとまず止める。次は最小の書き出し・読み込み経路とOBS実取り込みを接続する。フェーズ2の品質合格やフェーズ3の完了を意味しない。
