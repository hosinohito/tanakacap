# フェーズ3：外部アバターファイルとOBS透過出力

2026-09-12。HAOLAN向けの最小経路を実装。モデル・肩face_ratio・腕front_projectionは維持する。汎用改変対応/自然な髪服揺れ/配布環境同梱まで完成した意味ではない。

## 使い方

1. 通常はデスクトップtanakacap-test.batで起動。アプリは組込みアバターではなくbuilds/lab/avatars/haolan.tcapを読む。
2. 別ファイルはアプリでF5→パス入力→Load avatar。起動時はrun-avatar-lab.ps1 -Avatar ファイル、Player単体は--avatar ファイルでも選択可能。
3. OBSを次回起動するとSpout2 Captureが使える。送信元TanakaCap、Composite modeはPremultiplied Alphaを選ぶ。背景ソースを下へ置く。必要ならソースを画面へ合わせる。
4. Unity側はbuilds/lab/TanakaCapExporter.unitypackageを導入し、アバタールートを選択→TanakaCap/Export selected avatar (HAOLAN profile)。現行はHAOLAN用表情プロファイルのみ。出力先には新しいファイル名を選ぶ。出力と同名の.report.jsonに省略機能と対象を記録する。

書き出しと再生のUnityは2022.3.22f1/Windows64/Built-inを一致させる。VRCプロジェクト一般への導入互換性は別途検証が必要。Modular Avatar等のビルド時処理は未対応で、ロードできる未知スクリプトはエラーにする。VRC/欠損スクリプトはパス付き警告で省略する。PhysBoneは後続実装で設定の互換変換を追加済み。本家の動作一致は未確認で、範囲は[揺れ物の現仕様](SECONDARY_MOTION.md)を参照。

## パッケージ

.tcapはmanifest.jsonとavatar.bundleの2要素を持つZIP。形式version=1、Unity版、対象platform、profile、prefab名、表示名、SHA256、省略警告を持つ。読込時は要素数/名称、形式版、Unity版、platform、profile、SHA256を検査する。metadata上限1MB/bundle上限1GB。ローカルの信頼できる書き出し結果向けであり、任意の未信頼AssetBundleを安全に実行するsandboxではない。

Exporterは元のコピーだけを加工し、元Prefabや共有メッシュ/マテリアルを書き換えない。メッシュ・材質・BlendShape・Humanoid・Unity標準Constraintを保持。標準Constraintの汎用精度は別評価。ビルド時は原本依存hashの前後一致を検査する。生成物は新しいファイルで成功してから既存出力を.bakへ退避して置換する。失敗で有効な旧パッケージを先に消さない。

BuildLabは書き出し後にシーンのアバターを削除し、Loaderだけを置く。カメラ構図/照明はHAOLANで準備した値を保持。Playerのシーンにアバターを直接組み込まない。カメラ/表情の他アバターへの一般化、UI整備は残件。

## 検証結果

- results/unity-build.log：TANAKACAP_EXPORT_OK、TANAKACAP_SOURCE_UNCHANGED、TANAKACAP_BUILD_OK。外部.tcap約26MB、Exporter.unitypackage生成。
- results/phase3/package-verified.pngと付随log：外部読込→UDP受信→実骨/掌/指/表情と透明描画のsmoke成功。
- tools/test_avatar_package.py、results/phase3/invalid-final/report.json：形式version不正、Unity版不一致、checksum不一致を実Playerで拒否、終了code2。初回はAlphaOutputの終了待ちがcodeを0へ上書きしていたが修正済み。
- tools/verify_obs_phase3.py、results/phase3/obs-report.json：OBS32.2.2/Spout1.12.0で実受信、透明・不透明・中間アルファを確認、背景合成、2秒後の画像変化を検証。画像はobs-source-final.png/obs-composite-final.png/obs-source-next.png。
- OBS検証はデモ動作。実カメラの遅延、顔や指の精度、OBS併用30分性能の証明ではない。配信・録画開始はしていない。

初回OBS画像は透明一色だった。Spout登録だけでは描画成功を保証しなかったため、AlphaOutputはDefaultExecutionOrder(1000)のLateUpdateから透明カメラを明示Renderし、自動描画を止めた。通常送信はGPU上のままでCPU ReadPixelsを使わない。複数の検証Playerが同じSpout名を使うと受信を妨げるため、smoke終了後に送信Playerを起動する順序で検証した。

## OBS導入と既存環境

実受信はresults/phase3-obs/appの隔離OBSコピーで行い、通常ユーザーのシーン/配信設定を変更していない。検証用WebSocketはport4456・認証あり、資格情報はignored configだけに保存する。

通常OBSにも公式推奨C:/ProgramData/obs-studio/plugins/win-spoutへSpout1.12.0を配置した。Program Filesへの最初のコピーはOSアクセス権で失敗し、推奨配置へ切り替えた。通常OBSの再起動・既存シーンのソース追加は自動実施していない。次回起動後のユーザーの通常シーンでの見た目は未確認。

## 再開と残件

最小の書出し→外部読込→OBS実受信は検証済み。次は通常OBSでの利用確認とフェーズ4の髪/服揺れ、衝突/更新順、OBS併用性能と継続実行。フェーズ5の汎用非破壊変換、改変ビルド処理、対応表、一般向け導入UIも残る。原本アバター、.tcap、録画と結果はGitへ入れない。

## 参照・採用理由

- Unity標準AssetBundleを使用。既存Unity2022.3.22f1/Built-in/lilToonと同じ版で作り、別エンジンへの変換を避ける。新しいUnity版への移行はしていない。標準com.unity.modules.assetbundle=1.0.0を有効化。
  https://docs.unity3d.com/2022.3/Documentation/Manual/AssetBundles-Workflow.html
- Spout1.12.0の公式Windows64 portable配布物をOBS32.2.2で実検証。一般互換性保証ではない。
  https://github.com/Off-World-Live/obs-spout2-plugin/releases/tag/1.12.0
- OBS公式プラグイン配置手順：
  https://obsproject.com/kb/plugins-guide
