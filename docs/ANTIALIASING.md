# 軽量アンチエイリアス

2026-09-12。ユーザー追加要件：軽いAA。既存ライブラリは配布要件を妨げなければ可。

## 採用方式

既存透過RenderTextureの4倍MSAAを維持し、その後に自作の単一パス輪郭フィルターを追加した。FXAA製品/実装を移植したものではない。画面中央＋上下左右の5サンプルでコントラストと輪郭方向を判定し、斜め輪郭に沿う2サンプルを弱く混ぜる。均一領域と軸に平行な線は処理を抑制する。計7サンプル、深度・モーションベクトル・過去フレーム・超解像を使わない。追跡待ち時間を増やさない。

黒背景と白背景へ合成した場合の両方の輝度差から輪郭を選び、黒い髪などの透過境界も判定する。premultiplied RGBとalphaへ同じ線形重みを使う。alphaを輝度の保管場所に流用せず、alphaで割らない。背景の色は混入させない。プレビューと明示Renderする透過カメラ双方へ適用する。通常経路のCPU画像読み戻しはない。

- EdgeAntialiasing.cs / EdgeAntialiasing.shader：フィルター。
- AlphaOutput.cs：カメラ接続、F7切替、--no-edge-aa、同一姿勢比較用--aa-check。
- BuildPlayer：shaderをシーンへ明示参照し、Playerビルドでの除去を防ぐ。
- --output-height 720/1080：Spout出力の高さ。横は16:9。既定720。

F7または-NoEdgeAAで追加分だけOFFにする。従来MSAAまでOFFにする機能ではない。髪の細線や微小な模様はわずかに柔らかくなる可能性がある。MSAA/画像AAはモデル誤検出や関節の震えを直さない。

## 初回実画像確認

results/phase4/aa.off.alpha.png と aa.on.alpha.png は、同一Player・同一姿勢・同一揺れ状態で連続して描画し比較した。720pでRGBA差が1を超える画素28,028、平均絶対差0.225/255。中間alphaは3,877→9,238画素、ONでも完全透明647,877、不透明264,485画素。完全透明画素のRGB最大0。aa-head.jpgで髪/耳の輪郭の軟化を目視した。ユーザーの好み・全素材の品質合格とは別。

性能と実OBSの確認結果はPHASE4_VALIDATION.mdへまとめる。720p/OBS60fps/自作モーションでON/OFFとも約60fpsを維持し、GPUカウンターはともに約3ms台。追加分だけのGPU時間は測定ばらつきから厳密に分離できていない。描画投入のCPU時間をAAのGPU時間と呼ばない。GPU専用診断には測定負荷があり、同条件のON/OFFで比較する。

## 配布・根拠

追加の外部パッケージ/SDK/ネイティブDLLはない。フィルターは本プロジェクトで記述したもの。既存Unity/lilToon/Spout/アバター/モデルの条件は引き続き別に適用される。

Unity Built-inのOnRenderImageとGPU上のGraphics.Blitを用いる。
- https://docs.unity3d.com/2022.3/Documentation/ScriptReference/MonoBehaviour.OnRenderImage.html
- https://docs.unity3d.com/ja/2022.3/ScriptReference/Graphics.Blit.html

Unityの既成AAにもalpha保護の設定があることを確認したが、今回は依存を増やさずRGBAを明示的に同時処理する小さい実装を選んだ。
- https://github.com/Unity-Technologies/Graphics/blob/master/com.unity.postprocessing/Documentation~/Anti-aliasing.md
