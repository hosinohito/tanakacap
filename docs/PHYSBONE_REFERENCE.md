# 開発Editorでの本家PhysBone比較

2026-09-12。公式SDK 3.10.5、Unity 2022.3.22f1、HAOLAN無改変Prefabのコピー。通常プロジェクトとは別のresults/physbone-reference/projectに配置。SDKのDLL・ソース・アバター原本・結果はGit/Player/Exporterに含めない。

公式取得元：https://vrchat.github.io/packages/index.json
SDKの条件：https://hello.vrchat.com/legal/sdk
公開挙動仕様：https://creators.vrchat.com/common-components/physbones/

ライセンスファイルも上記SDK規約を参照している。SDKを独自Playerへ移植せず、ローカルのVRCアバターEditor比較に限定した。SDKの逆コンパイル・改変・ソルバーソースのコピーは行わない。独自実装は既存の公開パラメーター近似を継続する。一般配布可能性の確認と、ローカルEditorでの比較は区別する。

## 再現

1. 通常UnityプロジェクトのHAOLAN/lilToonが準備済みの状態で、Pythonのtools/prepare_physbone_reference.pyを実行する。公式ZIPをSHA256照合し、コピーだけを使う。
2. tools/tune_secondary_reference.py --values 1 1.5を実行する。隔離Editorで同一動作・60Hzを与え、両ソルバーが動いたことを確認して回転差を保存する。通常ソルバーのファイルは変更しない。
3. 結果はresults/physbone-reference/sweep-*/summary.json。SDKの初回importには時間がかかる。Unityパス変更時はツール内の実行ファイル指定を合わせる。

準備時、標準Physics2D/AndroidJNI/Test Framework不足を追加して解決。SDK本体は変更していない。Unityパッケージの解決結果は隔離project/Packages/packages-lock.json。

## 比較の条件

元Prefabから本家36コンポーネントと独自35系統73区間を作る。作者の左zipper重複は独自側では以前通り1件を警告して省略し、この差を隠さない。Animatorを停止し、頭/胸へ自作の同じ回転を与える。描画Rendererは無効。ローカル骨回転のQuaternion.Angleを測る。頭0.7Hz/25度、続けて胸0.45Hz/ピッチ15度＋ロール10度、最後に静止。1260フレーム/論理21秒。SDKのPlay mode実行が必要。

初回の独自側初期化漏れと、Time.deltaTime対unscaledDeltaTimeの時間刻み不一致は比較ハーネスの不備であり、修正前の値は評価に使わない。同じ1/60秒で独自Stepを外部駆動して測り直した。SDK内部の更新タイミング・1フレーム単位の位相差までは一致保証していない。

## 結果と採用

復元周波数の係数4/12/16を試したが、元8より頭振りの平均差が悪化したため採用しない。減衰係数倍率0.5/1.5/2.5を比較し、1.5で改善。別動作の胸を加えて再検証した。

| 条件 | 元の減衰 | 1.5倍 |
|---|---:|---:|
| 頭振り中の全対象骨平均回転差 | 1.740度 | 1.266度 |
| 頭振り中の最大差 | 16.966度 | 10.687度 |
| 胸動作中の平均差 | 2.523度 | 2.188度 |
| 全1260フレームの平均差 | 2.007度 | 1.740度 |
| 最終60フレームの平均差 | 1.847度 | 1.847度 |

結果：same-clock-baseline、frequency-sweep.json、damping-sweep.json、damping-validation.json、validation-damping-1.0/1.5のframes.jsonl。平均は動いていない骨も含み、動いた骨だけの精度や見た目の合格率ではない。開始時の服の衝突による過渡・停止直後の急変には大きな差があり、最大差を隠さない。

通常独自ソルバーの減衰項へ1.5倍を適用。元PhysBoneの値/カーブ/ファイル形式は変えない。Playerの--legacy-secondary-response、起動ps1の-LegacySecondaryResponseで旧減衰へ戻る。髪・服の実人物での自然さ、別アバター、非一様scale、全てのPhysBoneバージョン/モード/衝突の一致は未確認。SDKをそのまま実行する機能を製品へ加えたものではない。

## 2026-09-13 比較動画

本家SDKを動かした同じEditorシーンから、左をPhysBone/右を現在の独自実装として同時撮影した。独自側は採用済み減衰1.5倍。通常アプリ/ソルバーの変更はない。

保存先：results/avatar-videos/physbone-vs-independent。

| 動画 | 内容 |
|---|---|
| front.mp4 | 正面・服を含む全体、21秒 |
| hair-closeup.mp4 | 髪の拡大・斜め25度の共通カメラ、21秒 |
| front-half-speed.mp4 | 正面の半速、約42秒 |
| hair-closeup-half-speed.mp4 | 髪の拡大の半速、約42秒 |

全て1920x1080/60fps/H.264、音声なし。字幕で本家/独自と動作区間を明示。0〜3秒は静止、3〜9秒は頭振り、9〜15秒は胸pitch/roll、15〜21秒は停止後の収束。原Prefabの腕Tポーズを共通使用。カメラ実写や認識モデルを使う動画ではなく、揺れ物の同一入力比較。初期化の最初のdtだけ20ms、その後は双方1/60秒。半速は同じ撮影フレームの再生時間を延ばしたもの（物理の時間刻みを変更しない）。

再現：tools/prepare_physbone_reference.pyで同期し、tools/render_physbone_comparison.py。既存出力がある場合は意図しない上書きを避けて停止する。--encode-existingは撮影を再実行せず、ラベル付き動画/半速版を再生成する。元raw動画と当該撮影の計測JSONLは保持する。

両ソルバーの骨変化、通常版1260フレーム、半速2519フレーム（末尾端数1フレーム）、全編ffmpegデコード、ラベル/構図の目視を検証。report.jsonのstatus=complete。数値比較の平均差は前回と同じ1.7395865度。動画の見た目をユーザーが評価したことにはしない。SDK/アバター/動画はGitへ入れない。デスクトップtanakacap-compare-physbone.batで正面動画の場所を開ける。
