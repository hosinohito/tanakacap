# 引き継ぎ：現在の状態

最新：2026-09-13：雪ぱーちくるのUnsupported component: UnityEngine.ParticleSystemに対応。ParticleSystem/ParticleSystemRendererを削除せず標準コンポーネントとして書き出し許可。既存の全Rendererのマテリアル/シェーダー検査は維持。playOnAwake設定を保持し、Animator/VRChatメニュー/スクリプト起動は再現しない旨をreportへ記録。Unityコンパイル/既存回帰検査/梱包ソース照合成功、既存Player内ParticleSystemModule DLLを確認。実エフェクトの描画・透過・起動は未検証。修正プラグインはbuilds/fixes/parent-constraint/TanakaCapExporter.unitypackage（過去2修正も含む）。Player/公開ZIPは変更なし。results/unity-exporter-particles-fix.log。

最新：2026-09-13：続くOverlapping PhysBone chains（イヤリングBone）に対応。全有効PhysBoneルートを事前収集し、親からの走査は別の子ルートで停止。子の専用設定を優先し、親のtailは子ルート位置を参照する。親→子の順でデータを作成、同一rootの既存first-wins警告は維持。二重登録の最終検査は残す。元のPhysBone/ignore設定は変更せず、境界変更をreport警告へ記録。Unityで実際のCollectSegmentsの親/子領域、子PBなし、ignoreを回帰検査し成功。results/unity-exporter-nested-physbone-fix.log。builds/fixes/parent-constraint/TanakaCapExporter.unitypackageを両修正入りに更新。PlayerとGitHub公開ZIPは未変更、実アバター再書出しは未確認。

最新：2026-09-13：公開版の書出しエラーPhysBone/Constraint overlap（FakeBonePositionsForOrnamentsPB/Fake_Furry_Hair_R.001、ユーザー確認Parent Constraint）を修正。競合するボーンはUnity Constraintに任せ、PhysBoneの回転対象だけから外す。子の走査は継続、競合しない子は揺れ対象として維持。末端でtail=0の偽重複は報告しない。原本とConstraintを削除・無効化しない。失う揺れはパス/型とともにreport警告へ明記。ソルバー/本体は変更なし。修正プラグイン：builds/fixes/parent-constraint/TanakaCapExporter.unitypackage。公開v0.1.0 ZIPは未更新。Unityコンパイル、親/位置/回転Constraintの除外・末端判定・子の適格性・複製内参照と原本維持の検査、梱包ソース確認成功。results/unity-exporter-constraint-fix.log。実アバターの書出し/見た目は未確認。

最新（2026-09-13）：TanakaCap v0.1.0をGitHubへ公開完了。
- リリース：https://github.com/hosinohito/tanakacap/releases/tag/v0.1.0
- origin=https://github.com/hosinohito/tanakacap.git、ローカルmasterをremote mainへpush、v0.1.0タグ=0217817。以後の公開記録は文書のみの追加コミット。
- Unityソースから再ビルド、最新USER_GUIDEを同梱。builds/releases/0.1.0のpart01/part02とSHA256SUMS.txtを公開。全3資産のGitHub size/digest照合成功、draft=falseをAPIで確認。
- part01=2,084,961,325 bytes / part02=162,029,922 bytes。12,918ファイル、双方2 GiB未満、CRC/ライセンス監査合格。大きいoversize-local-only.zipは公開していない。
- publication_approved=true、ライセンス残件は解消済み。GitHub公開のユーザー許可あり。実カメラ未使用、新規PC/全アバターの品質合格を意味しない。
- 認証は個人tanakacap限定fine-grained PAT（Contents/Workflows write、Metadata read）。results/github-auth/token.dpapiはWindows DPAPI暗号化・Git除外。同一Windowsユーザーで復号しGH_TOKENを実行プロセスだけへ渡す。秘密を出力しない。通常OAuth/Organization accessは使用しない。
- Git pushはsandbox schannel SEC_E_NO_CREDENTIALSで失敗したが、通常権限で成功。gh.exeはtools/bin/github-cli。公開説明はrelease/RELEASE_NOTES_0.1.0.md。
- 次の変更時は既存タグ/ZIPを上書きせず新バージョンでビルド・公開する。


2026-09-13：使い方にMA/VRCFury/キセテネ/AvatarTools別の書き出し準備とAAO併用設定を追加。ユーザー指定で全手順を複製プロジェクト内の処理とし、生成コピーを選択、原本へApplyしない。VRCFuryのSDK前処理/Test Copy置換、AAOの表情除去を公式資料・作者ソースで確認。EXPORT_TOOL_RESEARCH.mdに根拠と未検証を分離。実改変アバターの組合せ試験は未実施。review8は作成途中に追加されたこの説明書変更を含まず、次の.batビルドから自動同梱。


最新：build-release.batを追加。日時版名、原本/モデル/通知/NVIDIA/依存版チェック、UnityソースからPlayer/Exporter再ビルド、梱包とCRCまで一括。CheckOnlyは.bat経由で成功。通常権限でソースからUnity/Exporter再ビルド・review8 ZIP/CRC/監査成功（sandbox IPCは失敗後に通常権限で復旧）。原本は現フォルダーに揃い、AI生成不要。models/埋め込みPackages/対応ソースはGit外、外部Unity/Python環境は別途必要。docs/RELEASE_BUILD.mdとREADMEに保管対象を記載。


2026-09-13最新：NVIDIA・FFmpeg・Unity Personalの配布条件を確認。詳細はdocs/RUNTIME_LICENSE_DECISIONS.md。cuDNN9/nvJitLinkは公式同版ZIPのLICENSEと現行11 DLLのSHA一致で解消。FFmpegは実DLL対応source commitを固定し、不足していたOpenCV/OpenH264ソースを補った約161 MBの対応ソースZIPをビルド同梱。UnityはPersonal申告、現行§2.2とWindows Mono Player専用TPNで確認、スプラッシュ維持。通知20件・DLL/ソースSHA監査を追加。open_license_itemsは空、publication_approved=falseは最終出荷ゲートとして維持。モデル・追跡・DLLの挙動は変更なし。
検証完了：review7を既存release-playerから再梱包（Unity再ビルドなし）。part01=2,084,961,237 bytes、part02=162,028,059 bytes、計12,918ファイル。双方2 GiB未満・CRC合格。通知20/NVIDIA DLL20/全binary194、Unity runtime3のSHA、FFmpeg/source lock照合エラー0。同梱Python起動成功、FFmpeg不一致を模擬した拒否検査成功。resultsではなくbuilds/releases/0.1.0-review7/{release-report,license-audit}.jsonが検査結果。Playerの新規動作品質を今回確認したものではない。oversize-local-only.zipは公開対象外。


2026-09-13最新：モデル3残件を解消。HumanArt版YOLOX-MとRTMW-LはRTMW作者Tau-JのHugging Face保管庫でApache-2.0、ZIPのSHAがOpenMMLab取得receiptと一致。頭MobileNetV3 smallは作者の重み別MIT宣言と原本SHA一致。公開条件に基づき商用利用・再配布可へ更新、ライセンス理由のモデル移行は不要。docs/MODEL_LICENSE_DECISIONS.mdに3モード表、release/model-license-evidence.jsonに固定版/原文SHA/モデル対応、results/model-license-evidenceに原文。collectorで6資料/3モデル照合成功。release/config.jsonのモデル2項目を閉じ、NVIDIA/FFmpeg/Unityの3残件とpublication_approved=falseは維持。実行モデル・配布方式・ZIPは変更なし。次はモデル比較の必須化でなく、残るランタイム監査。外部問い合わせ/公開なし。

2026-09-13：自動取得方式と頭・顔の代替を調査、docs/MODEL_DOWNLOAD_OPTIONS.md。初回に提供元から版/SHA固定で取得する案は未採用・未実装。利用制限は別取得でも残る。現行頭専用は作者の重み一覧にMITの追加根拠を発見（現行実物とのSHA照合は未完）。Face Landmarker/Face MeshのApache表記付きONNX移植が顔専用RTMW-L代替候補。全部ONのRTMW3D顔点共有とは区別し、別推論追加で軽くなるとは扱わない。モデル交換・公開判定変更なし。

2026-09-13：モデル条件の導入前確認と代替候補を調査。頭専用は当初から重みの配布監査未完と記録されていた。人物検出代替はモデル許諾を明示するRT-DETR R18（PekingU）とRF-DETR Nano/Small（Apache指定版）。詳細RELEASE_LICENSE_AUDIT冒頭。提案のみで未取得・未比較・未採用、既存推論は変更なし。

最新（2026-09-13）：Python UIの各タブ内でラベル/入力欄/閉じたプルダウン/スクロールバー上のホイールをタブの縦スクロールへ転送。ウィジェット標準処理より前の専用bindtagで、閉じたプルダウンの誤選択を防ぐ。展開したプルダウンは標準操作を維持。実Tkを770x730で動かし、子ウィジェット上のスクロールと選択値不変を検査済み。Unity再ビルド不要。

最新（2026-09-13）：自由入力の表示は「自由入力（推論上限をつけて負荷を軽減できます）」、ウインドウ表示は「アバターのウインドウを表示（オフにすると負荷軽減になります）」。Python UI右下に終了ボタン、既存の停止完了待ちで推論/Playerとともに閉じる。Unity構図ボタンを撤去、パネル既定表示・Escで開閉（F9撤去）、FOV 15〜80度のスライダー追加。起動時のウインドウ解像度を出力解像度に合わせる。通常Player更新済み、構図保存/reset/FOV・デモ描画・実ウインドウ960x540・実Tk終了ボタン検査成功。Escの実キー操作は未検証。results/framing-panel-v2。既存review6 ZIPは今回の変更前で再作成していない。

## 2026-09-13 — ライセンス実物監査と推論同期UI修正

監査を実施しdocs/RELEASE_LICENSE_AUDIT.mdへ根拠・判断・残件を記録。本文14件をrelease/noticesに出所/SHA付きで追加、THIRD_PARTY/TERMSを同梱。build_release.pyにaudit_release_licenses.pyの検査を接続。NVIDIA .h122/.hpp14/.lib5を製品から除外、DLL20は不変。review5は2,085,247,898 bytes/CRC成功、合成虹彩CUDA381/CPU0確認。5残件はconfig.json：cuDNN9と旧wheel本文/nvJitLink、HumanArt YOLOX-M #3271未回答、RTMW-L/頭モデル適用範囲、OpenCV内部FFmpeg対応ソース、Unity適用契約/プラン/内部由来。禁止と未確認を混同しない。問い合わせ未送信。公開可ゲートは解除しない。

追加UI要求：同期時はFPS入力なし、固定/自由fpsの残値を推論上限に使わない。入力欄はcustom時だけ。ラベル列/Combobox幅を固定。18 tests/実Tkモック合格。通常Player再ビルド済み、合成packet15/35Hz→14.93/34.00fps（results/render-sync-ui）。イベントループは上限240で、出力だけpacket同期。停止時10Hz維持は従来どおり。実カメラは開いていない。release6は最初sandbox licensing IPC失敗、通常権限の再実行でUnityビルド成功、review6梱包も成功：2,085,247,952 bytes/12,911 files、CRC/同梱Python/通知SHA成功。最新UI/Playerを含むローカルレビューZIP。公開許諾は保留。

次：5残件の個別解消。NVIDIAは採用実配布版の正しい契約取得・整合確認、MMPose/頭重みの条件確認、OpenCV同梱DLLの対応ソースとビルド手順固定、Unity契約プランと内部通知の照合。モデル変更/外部連絡が必要になったら具体案を示す。既存UI/カメラ/追跡の実装は維持。

2026-09-13 認証復旧：ユーザーのUnity Hubログイン後、製品Playerと通常lab Playerのビルド成功。製品Player＋保存デモで外部アバター読込、構図上下/距離/FOV変更・保存・リセット、デモ描画の自動検査成功（results/release-framing-check/player.log）。実マウス操作/最新背景のSpout確認、新規PC導入は未検証。認証の追加操作は不要。ZIP作成はUTF-8 BOM対応と調査用pypdf除外を修正しreview4成功。builds/releases/0.1.0-review4、2,088,360,246 bytes、13,035 files、CRCと同梱Python読込成功。公開許諾監査は残りlocal-review-only。透過画像のalpha検査成功（OBS実受信ではない）、デスクトップbat更新済み。


## 2026-09-13 — 配布ビルド/UI刷新、Unity認証待ち

最新依頼：Exporter、本体、UI、実行ライブラリ/モデル、簡潔な利用説明書、ライセンスをGitHub Release ZIPへ。MIT承認済み。口寄せ通常4mm復帰、8mmは実験。ユーザーが逐次指定したUIをcontrol_panel/ui_experimentsへ実装。実写非表示の機構は残し文言だけ削除。カメラはDirectShowのメタデータ列挙のみ（8機種、HD webcam-CMS-V43BKを確認）。実験タブのFP16/FP32は子プロセス環境変数で切替。部位負荷4/1/4割はFP32時代の同条件stage mean比率で、現在のFP16削減率ではない。

描画UI最新：60/30時は自由入力非表示、説明は選択肢内。ウインドウON時だけ背景ラジオ「指定しない=黒、緑、青、マゼンタ」。Spout用カメラはclear維持。開始/適用は保存して開始へ統合。273 Python testsと実Tkモック起動/設定/条件表示テスト成功。利用者手順docs/USER_GUIDE.md、開発docs/RELEASE_BUILD.md。ControlPanelから実カメラを開く検証はしていない。

Unity新コード：AvatarFraming（アバターpath別の上下/距離/FOV保存、reset、Esc閉じ、右ドラッグ上下、ホイール距離、CtrlホイールFOV）、AvatarWindow（タイトルバーなし/左ドラッグ移動）、統計初期OFFかつF1トグル撤去。構図ボタンから保存/リセット、F9でも開閉。AlphaOutputは背景色をpreviewだけへ、FOVはoutputへ同期、構図変更時は同期描画を更新。--framing-check <新規JSONパス>で位置/FOV/保存/リセットの自動チェックコード追加。ただし最新コードはUnity再ビルド未達成・実ウインドウ未検証。

重大な停止点：build-release.ps1のUnity起動が最初ライセンスIPC失敗、その後通常権限でもNo valid Unity Editor license / Machine bindings don't match, Token not found in cache。ユーザーに現在ユーザーのHubライセンス確認を依頼済み。ユーザーから「Unity自体をビルドしているのか」と質問あり、TanakaCap.exeをUnity Editorで作るためEditor認証が必要、Personal条件内なら有料契約不要と説明した。認証情報の変更や回避はしていない。再試行連打せず復旧報告待ち。

配布環境：build-release.ps1→新BuildRelease.Build（HAOLAN原本不要の空シーン、外部AvatarLoader）→tools/build_release.py（runtime再配置、lock一致依存、モデルSHA lock、通知/manifest、ZIP CRC、2GiB未満なら一つ）。手動Actions workflowも追加、実行未確認。現行builds/releases/0.1.0-review1は旧lab Playerでの**途中梱包試験**であり最新UI/Unity変更を全て含まない。13,101files/ZIP2,088,759,516bytes、CRC成功、単独ZIP可能。同梱Python/Tk/主要ライブラリ読込成功、別途results/portable-runtime-gazeで合成入力の虹彩CUDA1536node/CPU0を確認。頭/全体モデルや新規PCの全機能成功ではない。SDK/原本/録画/SAM/HaMeRは梱包しない。モデル/CUDA/Unity/Spoutの公開監査残件はrelease/config.json、Publishableビルドは未承認なら停止。公開/アップロード未実施。

次：認証復旧後 .\build-release.ps1 -Version 0.1.0-review2（未作成なので使用可）、必要なら .\build-unity-lab.ps1 で普段のPlayerも更新。最新デモtcap+--framing-checkの保存/リセット、背景各色のpreviewとSpout alpha不変、枠なしドラッグ/Esc、UIからFP16/FP32録画経路を実検証。最終ZIPを同梱Python/Playerで録画起動して検査し、初回review1を完成品扱いしない。モデル/通知の公開監査は別残件。ログresults/unity-release-build.log。

## 2026-09-13 — 口寄せ8mmとフェーズ整理

ユーザーが目線の改善を確認。生成口寄せキーを4→8mmへ倍増、入力1.7倍/唇14mm帯は維持。--legacy-mouth-shift-rangeで生成を4mmへ。デモ/auto-customの不足キーが対象で既存キーと凍結原本は維持。比較results/avatar-videos/mouth-shift-range-final/face-closeup.mp4、左4mm/右8mm、全強調/校正済み目線/同853packet。両方向のBakeで4mm/8mmと唇外・顎首不変を確認。初回mouth-shift-rangeはフラグ適用順の誤りで両側8mmになった無効比較。適用を生成前へ修正し、比較ツールに期待ログ検査を追加。口寄せの見た目は未評価。フェーズ一覧をdocs/IMPLEMENTATION_PHASES先頭で更新。

最新比較（2026-09-13）：results/avatar-videos/gaze-range/face-closeup.mp4、左range-off（範囲校正なし）/右range-on（あり）。同853虹彩観測・PnPゲート・強調最大デモ・soft応答を固定し、校正だけ比較。保存診断から再構成した校正ありpacketが前回推論と完全一致。各901描画frame/30.033秒、全デコード成功、目視未実施。tools/prepare_gaze_range_comparison.pyで再現。口寄せが弱いという追加質問へ、直近の変更なし・入力強調1.7倍/最大4mm維持と説明。今回は口の変更なし。

## 2026-09-13 — 目線範囲中心の常時校正

ユーザー指定でかつての腕長と同じ5秒10支持で横/縦の観測範囲を拡張し、その中点を中立へ。capture_lab/gaze_range.py、IrisGazeの角度化/4フレーム前に接続。両目有効時だけ学習、片目は保存中心適用、欠測保持、起動ごと初期化、範囲縮小なし。倍率は範囲で割らない。Python --no-gaze-range-calibrationでOFF。272 tests、最新録画853frameのCUDA FP16再推論成功（595目線有効）、結果results/gaze-range。表示改善/動画確認は未実施。docs/GAZE_RESPONSE.md先頭参照。旧提案「正面注視校正」は本指定へ置換。

## 2026-09-13 — 上下目線の飽和を修正

縦が動かない申告。保存録画589有効目線のうちデモgain6で旧目標の縦74.2%/横33.6%がクリップ。横/縦を眼幅変位で同じ正規化感度に揃え、共通soft boundへ通常変更。表示最大範囲/キー形状/検出モデル/4フレーム法/欠測カメラ復帰は維持。--legacy-gaze-responseで旧方式。docs/GAZE_RESPONSE.mdに式・録画のゲート由来・検出残件を記録。比較results/avatar-videos/gaze-response、左旧/右新、全強調デモ。Unity応答チェックとビルド成功、見た目は未確認。

## 2026-09-13 — 部位別強調UIとデモ強調固定

ユーザー指定でUI表情タブに眉/目線/まぶた閉じ/口の4独立スライダーを実装。0〜1、0は追加作用なし。保存/適用で再起動。Player引数--brow-exaggeration/--eye-exaggeration/--eyelid-exaggeration/--mouth-exaggeration。表示倍率は眉1→1.75、目線基準感度に1→1.5、閉眼1→1.8、口各形状1→1.7と口角既存強調max。各上限/左右/ロスト保持を維持。眉gain2やgaze_gain4は基準として残る。目閉じのモデル/閾値/4フレーム処理は未変更、今回追加したのは表示感度。

デモflag --use-demo-shape-keysでは全項目1固定。UIでも保存デモを選ぶと1表示でスライダーを無効化。旧デモmotion batを最新Player＋保存demo.tcapへ更新、凍結原本は維持。デモの不足口寄せ/目線キーを既存の唇/虹彩レシピで実行時補完し、既にあるTCキーは再生成せず保持。shiftL未マップの旧制限は解消。通常existingでは生成なし。

比較はresults/avatar-videos/facial-exaggeration/face-closeup.mp4、左normal=追加強調0、右exaggerated=全1。最新版の同アバター/補完済みキー/同853packet。旧Player比較ではない。比較専用の--comparison-neutral-exaggerationは--render-replayのみ許可。元映像/推論は変更なし。269 tests/Tk操作/Unity強調独立テスト成功。初回新スクリプトimport途中の一時CS0246後、最終ビルド成功。実カメラ/実写表示/エージェント目視なし。詳細docs/FACIAL_EXAGGERATION.md。

最新比較（2026-09-13）：眉の振動対策なし/ありの比較はresults/avatar-videos/brow-follow/face-closeup.mp4（左brow-direct/右brow-adaptive）。同じ新30秒録画の853packet、PnP/gain2/4フレーム法/左右分割デモアバターを固定し、--no-adaptive-brow-followの有無だけ変更。準備はtools/prepare_brow_follow_comparison.py、入力reportはresults/comparisons/brow-follow。頭や目閉じは変更せず、オフライン30fps比較。既存の眉倍率比較とは別。

## 2026-09-13 — 眉にも可変速度の振動対策

ユーザー指定で眉の表示補間を追加。既存4フレーム法/gain2の後、表示値と目標の絶対差0〜0.3でrate6〜45をsmoothstep、係数1-exp(-dt*rate)。眉の左内/左外/右内/右外を個別更新、片側の大きい動きが反対側の補間を速めない。無効観測は既存の保持分岐。新しいデッドゾーン/観測待ちは追加しない。既定ON、--no-adaptive-brow-followで旧直接反映へ。頭の可変追従設定・口・目閉じ・揺れ物は変更なし。

Editor検査で微小交互入力の低減、大入力の速い追従、微小目標への収束、dt=0、逆戻し、片側不変を検査。実録画デモ再生はresults/brow-follow/demo.mp4。最新test batは同じ入口で新Playerを使う。実カメラ/実写表示/エージェント目視なし。見た目の改善はユーザー評価待ち。

## 2026-09-13 — デモ・独自モードの眉を左右独立へ

ユーザー指定でBrowShapeSplit追加。眼骨の解剖学的左右軸/中点を基準に、既知の両側眉モーフの頂点・法線・接線差分を左右へ分配。元のフレーム重みを保持、左右和は元の差分、眼間隔20%の中央帯でsmoothstep。デモ/auto-customの実行時コピーに生成し保存原本は不変。MMD上/下/困る/怒り、共有browInnerUpを材料にする。眼骨/読取/既知材料がない場合は分割できない。左右独立は眉内外の4領域独立ではなく、各側上下と困る/怒りで表す。

FaceExpressionsは既存左右キーを標準名と上左/左上/上_L/眉上げ左等で探索、保存profile後に共通fallbackを置換。既存片側キーを生成キーで上書きしない。共有browInnerUpは独自モードで左右分割を使用可能。既存モードは生成せず、共通キーのみでは共通表示を維持。左右別キーがあるときに共通の困る/怒りを重ねない。demo flagは既存TCキー利用＋今回の眉生成、口寄せ未マップは別残件。眉gain2、PnP、目閉じ、揺れ物は維持。

Editorで片眉上下の反対側weightゼロ、合成メッシュの反対側変位ゼロ、原本不変、既存モードでキー数不変を検査。--check-brow-sidesで実デモでもマッピング検査可能。最新test batはそのまま新Playerで左右分割を使用。旧比較動画は共通眉の時点のもの。今回の再生動画はresults/brow-independent/demo.mp4へ保存。実写表示/実カメラ/エージェント目視なし、実人物の見た目は未評価。

最新（2026-09-13）：眉の比較動画はresults/avatar-videos/brow-gain/face-closeup.mp4（左brow-1x/右brow-2x）。保存済みデモtcap＋最新Player、PnP/同一853packet時刻、眉4値以外が一致することを検査。各約30秒。眉の左右独立について質問あり：検出は左右内外4値で独立だが、デモの表示は左右共通MMDキー「上/下/困る/怒り」へまとめているため独立ではない。左右分割モーフは未実装。ユーザーへ説明、今回追加していない。

最新成果物（2026-09-13）：ユーザーの動画化指定で、眉gain2のデモアバター再生から顔アップ版results/brow-demo/face-closeup.mp4を作成。約30秒、全デコード成功。全体版はdemo.mp4。目の閉じ処理は変更なし。眉評価用で、下記の口寄せ未マップ制限は残る。

## 2026-09-13 — 眉を2倍へ、検証アバターを保存デモへ統一

ユーザー指定：眉の強調は実装、閉眼は案だけ、今後の検証はデモ用シェイプキーアバター。BrowFilterの既存4フレームゲート後にgainを掛けて±1へ制限。brow_gain=2、1で旧。検出/基準/ゲートの閾値は維持。CLI --brow-gain、通常bat/UI/比較共通経路へ接続。UIの新スライダーは今回なし。

検証testは-DemoAvatar、最新Player＋builds/demos/haolan-custom-brows/avatars/haolan.tcap＋--use-demo-shape-keys。auto-customの生成は行わず、保存済みTCキーをマッピングする。固定デモ一式のハッシュ一致確認。通常アプリの既存キー優先既定は変えない。今後の比較器もこのavatar/flagを明示すること。

30秒録画の保存XYをPnP/眉gain2で再処理（tools/prepare_brow_demo.py、results/brow-demo）。853観測/眉有効789。閉眼コードは変更なし、左/右ともraw/filtered最大1。0.9超はraw24/20、filtered24/22だが正解ラベルなしで成功率とはしない。案：個人別の開眼/閉眼比率で閾値を校正、短い閉眼を弱めない閉じ/開き別の時間処理、表示側で1.0入力が完全閉眼するか切り分け。目の新モデル導入や4フレームルール変更は未実装。

264 tests成功、Unityビルド成功。デモアバター録画再生をresults/brow-demo/demo.mp4へ保存、901frame/30.033秒、全デコード成功。原映像表示・実カメラ起動・エージェント目視なし。眉の見た目のユーザー評価は未確認。既知の制限：保存tcapではshiftLが未マップ（player.log）。旧デモPlayerは口寄せキーを実行時生成していたため、この既存キーのみの経路は旧デモ表示の完全再現ではない。今回は眉検証に使い、口寄せの比較には使わない。将来口寄せ検証時は旧デモの生成処理も合わせる必要がある。

## 2026-09-13 — デスクトップbatを整理

ユーザーの整理指定で直下29本を5本へ：tanakacap.bat/test/face-capture/live/motion。補助24本はdesktop/tanakacap-toolsへ移動。削除はせず比較・デモ・過去試行を同フォルダーから利用できる。更新スクリプトも生成先を分け、次回更新で直下に復活させない。過去文書の補助batの「desktop」はこのサブフォルダーへ読み替える。アバター・録画・結果・推論設定は変更なし。今後は個別batを直下へ増やさず、通常検証batを更新するか補助フォルダーへ置く。

## 2026-09-13 — 頭角度の既定をpnpへ復帰

ユーザー指定でtracking-settings、UIの初期値、通常検証batをpnpへ戻した。保存済みui-settingsもpnpであることを確認。size2dは任意選択として維持。可変追従は別機能で、通常は引き続き固定速度。既存のhead-follow比較動画はsize2d入力でありpnp比較とは扱わない。今回カメラ起動なし。

## 2026-09-13 — 頭の可変追従を試行・比較動画

頭の震えについてユーザーが「4フレーム法後、小さい動きはゆっくり、大きい動きは速く」を提案し比較動画を指定。Player --adaptive-head-followで試行。表示頭と目標の最短角度差0〜12度でrate6〜45へsmoothstep、既存固定45のSlerpを置換。4フレームゲート/size2d/他部位/欠測保持は維持。通常は引数なしの固定追従、採用待ち。docs/HEAD_FOLLOW_COMPARISON.md。

新30秒録画から全部ON FP16で853観測を再推論、顔有効849。results/comparisons/head-follow-input。制御値をバイト一致で複製しresults/comparisons/head-follow。動画results/avatar-videos/head-follow/face-closeup.mp4（左fixed/右adaptive）、desktop tanakacap-compare-head-follow.bat。比較は30fpsのオフライン・auto-custom表情、実時間遅延測定ではない。Unityビルド/可変係数と微小収束/既存関節・表情・受信回帰成功、results/head-follow-smoke。実カメラと実写表示/動画目視なし。次はユーザーの比較評価に応じ採用か感度調整。

## 2026-09-13 — 30秒の顔・頭・表情録画を受領・検証

ユーザー撮影完了。results/comparison-takes/20260912T230559-718866Z、face-head/free、1280×720、29.999秒、853保存フレーム。全編デコード/メタデータと時刻行数一致/単調時刻/映像と時刻のSHA256一致を確認、validation.jsonへ保存。カメラ読取から保存まで48フレームの欠落あり（skipped_camera_frames）、連続30fpsの記録とは扱わず実観測時刻で評価する。完了状態で、破損は検出されなかった。映像の目視や表情の網羅性・推論品質は未評価。実カメラをエージェントが開いたり実写を画面表示したりしていない。

今後の顔・頭・表情修正にはこの録画を使用。次は必要な修正対象に合わせ同一入力でpnp/size2dや表情値を比較する。自由撮影のため動作ラベルはfreeのみで、旧ガイドの区間を流用しない。今回、推論やアバター制御の変更なし。実写本体はGit除外を維持。

## 2026-09-13 — 撮影は30秒・動作案内なしへ訂正

ユーザー指定でface-headを30秒自由撮影に変更。下記の235秒15区間案は撤回。動作はユーザーが決め、区間ラベルはfreeのみ。開始前3秒カウント、録画残り時間、完了表示は維持。desktop tanakacap-face-capture.batは同じ入口で新方式を使用。実写非表示/音声なし、撮影はユーザー待ち。13 tests成功、実カメラは開いていない。

## 2026-09-13 — 顔・頭・表情の新規録画をユーザー待ち

tanakacap-face-capture.batをdesktopへ追加。run-comparison-lab.ps1 -Mode capture -Profile face-head。既存HuffYUV録画にface-headプロファイル追加、235秒・15区間。正面静止/上下/左右/roll/素早い頭運動/距離/まばたきと目線/眉/母音形/口角強弱/口寄せと非対称/上下向きで開口/遮蔽復帰/終端静止。ユーザー「表情も」「詳細な案内不要」に従い、撮影中は短い動作名のみ。音声/実写表示なし、推論なし。実カメラはエージェントが開いていない。

保存先results/comparison-takes/<日時>/camera.avi,frames.jsonl,take.json。profileと各区間を保存、元のbody撮影は維持。次はユーザーが撮影後、complete/profile=face-headの記録を確認し、頭と表情の修正に使用。新しい撮影が完了したとは扱わない。13 tests成功（録画は合成画像のみ）、CLI引数確認。頭角度・表情制御自体は今回変更なし。

## 2026-09-13 — 頭角度を2D比率にする可逆試行

ユーザーの頭のガタつき申告でsize2dを試行既定へ。直前pnpもモデル推定Zは使わず、ピッチは固定3D顔型へのXY当てはめだった。新方式は眼間距離で正規化した鼻位置からpitch/yaw、眼軸からroll。初期10安定観測、既存3平均/stride1、欠測保持。口・眉のPnP補正は独立して残し、一致をテスト。頭のみモデル/腕/肩/距離/揺れ物は変更なし。

UI「入力・推論」頭角度にsize2d/pnp等を追加、pnpへ戻して適用で復帰。tracking-settingsと通常testをsize2dへ。既存UI設定に頭方式がない場合はtrackingから継承。docs/HEAD_SIZE_TRIAL.md参照。起動後に正面で短く静止。頭のみでは選択無効。

既存FP16録画5,187観測、頭以外の制御を固定して全編比較。results/comparisons/head-size2d。pitchの95%観測差1.69→2.10度、最大18.69→22.28度で改善と断言できない。欠測保持で集計し直すとyaw/roll最大差も12.13/4.42→13.17/4.71度で改善なし。実動作とノイズの区別はない。アバター比較results/avatar-videos/head-size2d（左pnp/右size2d）。ユーザー目視は未実施。次は試行方式の感度/ガタつきの評価、悪ければUIでpnp復帰。262 tests、Tk操作検査成功、実カメラ/実写表示なし。Unityソース変更なし。

## 2026-09-13 — 操作用UIを実装

desktop tanakacap.bat / run-ui.ps1でTk操作画面を開く。起動だけではカメラもPlayerも起動しない。開始時に選んだカメラ/保存録画/自作モーションと.tcapを使う。全機能/顔・頭/頭のみ、全機能時の部位OFF、60/推論同期/30/自由1〜240fps、幅高さ64〜4096（既定Full HD）、AA/アバタープレビュー、既存/自動表情と口角3調整/目線感度を実装。保存先ui-settings.jsonはGit除外。実行中の適用は停止・再起動、ホットリロードではない。

実写画面はUIにも録画選択にもない。UIから長い表示許可引数を渡す経路なし。アバター用previewとは区別。UiStatusFeedbackとlive_status.pyで数字だけloopback UDP通知、推論Hz/実RGBA描画fps/受信Hzを別表示、2秒無更新で消去。上限制御は入力取得前・推論開始前に待機、カメラはその後最新を読む。同期は新packet時にRGBA描画、100ms以上空くと10Hz以下で更新、ウインドウ/同じSpout画像再送は上限fpsで継続。モーションは同期でも上限fps。

検証は既存録画のみ。results/ui-validation/report.json complete、5構成（全機能60、顔頭60、頭のみ60、全機能23、同期60）で推論/実Player受信/描画/終了を検査。全部ON47.54Hz/60fps、顔頭49.18Hz/受信49.11、頭のみ58.65Hz、23指定22.84Hz/23fps、同期47.94Hz/描画44.09。ms/観測は16.97/14.26/8.46でUIの倍率2/2/1（頭のみ基準）、docs/ui-costs.json。個別OFFや描画負荷はこの倍率で保証しない。今回OBSアプリ合成は含まない。Player回帰/透過Spout検査はplayer-regression.logで別途成功。

GUI検証：実Tk入力/開始/適用/再起動/保存/終了（プロセスmock）、257 tests成功。実写/実カメラは使用せず。UIスクロール対応、閉じると子プロセス終了。カメラ・停止ハング・新規PC・任意アバター・長時間品質は未確認。

UI検証で見つけた既存不具合も修正：(1) RTMW-L FP16 Graph起動失敗→このモデルだけFP32 CUDA Graphを明示使用。CPUへのfallbackは不可、全部ON RTMW3D/人物/虹彩はFP16維持、UIに精度選択は追加しない。(2) body OFFでfingerTrackedだけ送ってflex配列が欠け、Unityが全packet拒否→無効フラグとゼロ15角を揃える。顔頭の受信まで確認済み。

README/SPEC0.72/CONTROL_PANEL/フェーズ表を更新。次はユーザーがtanakacap.batから操作確認。UIは実装済みだが、一般向け配布インストーラー/別PC/個別オプション全組合せ倍率/設定ライブ反映/カメラ名の自動列挙は未実装。過去のUI未実装記述は旧状態。

## 2026-09-13 — 実写の画面表示を長い専用起動引数だけに制限

ユーザー指定：カメラ映像は特別に長い起動オプションがない限り画面へ出さず、今後の実装でも一貫して守る。完全一致の --explicitly-allow-displaying-raw-camera-images-on-screen-for-this-session-only のみ許可。旧--previewを削除、argparse省略形拒否。capture_lab/camera_display.pyで実プロセスsys.argvを毎回確認してOpenCV表示/ROI選択/Tk画像生成を守る。診断・設定値・UI・ホットキー・環境変数による許可は作らない。録画映像や重畳画像も対象。標準ランチャーへ長い引数を自動追加しない。

全機能/頭専用の表示、頭の手動ROI、比較撮影の実写を共通ガードへ移した。通常batの常時--previewを撤去。比較撮影は映像なしで文字ガイド/開始/中断/録画を利用可能。固定頭ROIは通常数値指定必須、画面上の選択は専用引数が必要。アバター表示とOBS/録画保存は別、停止手段はアバター終了または端末Ctrl+C。通常検証版も--parent-pidでPlayer終了に追従する。

245 tests成功（results/pytest-camera-display-complete）。短縮/旧フラグ拒否、完全一致受理、無許可のimshow/selectROI/Tk変換不達、設定preview=Trueによる頭選択迂回拒否、許可非永続、capture_lab/tools内の表示API集中を検査。実カメラ/実写の画面表示なし、Unity変更なし。PowerShell構文検査とdesktop bat更新済み。README/SPEC0.71/HEAD_ONLY/LAUNCH_MODES/AGENTS更新。今後表示手段を増やす際はガードと構造検査を必ず拡張する。

次はユーザーの指定作業。映像表示をしなくても実カメラをエージェントが勝手に試験してよい意味ではない。比較用実写のローカル保存やアバター動画は維持。

## 2026-09-13 — 通常口角の無作用既定・任意調整とARKit非対称確認

ユーザー指定で通常existingのガンマ/開口時上げ抑制/強調は既定1/0/0（追加調整による影響なし）。以前は通常版にも2/.9が固定適用されていたが、今回外して任意設定へ変更。auto-customのモード既定は2/.9/0のまま。tracking-settings.jsonのmouth_corner_gamma/mouth_open_smile_suppressionはnullでモード既定、数値で共通上書き。PowerShell -MouthCornerGamma（.25〜4）/-MouthOpenSmileSuppression（0〜1）、既存-MouthCornerEmphasis（0〜1）を優先。Playerにも同名kebab引数。Driverプロパティは将来UI接続用、UI画面はまだない。

追加質問：通常版もPerfect Sync/ARKit mouthLeft/Right、mouthSmileLeft/Right、mouthFrownLeft/Rightで横寄せ/非対称を既に駆動する。合成メッシュで横寄せ±70%、笑顔左80%/への字右60%と反転、前の重みの消去を検査し成功。実Perfect Syncアバターの見た目検証とは区別。HAOLAN通常版のキー不足を全体の未実装としない。

検証：Unity Editorの無作用/調整/への字非抑制/追加強調/ARKit左右検査と最終ビルド成功。実Playerの通常既定/auto既定/通常調整2/.9/.5が全てmotion-check成功（results/corner-options/{normal,auto,adjusted}.log）。カメラなし、口/目/腕/手首回帰あり。PowerShellは起動をmockして既定時省略と明示値受け渡しを検査、カメラ起動せず。デスクトップbat更新、保存デモは不変。

既存比較動画は変更前の通常ガンマ2/.9であり、新しい無作用既定の動画ではない。再生成要求はなく今回動画生成なし。README/SPEC0.70/EXPRESSION_PORTABILITYを更新。次はユーザーの見た目評価/指定作業。その他の残件は下記。

## 2026-09-13 — 眉追加・保存デモ・表情モードの汎用化

現在のユーザー指定：眉を追加した従来版をデモ保存。その後、通常は機能別ARKit/Perfect Sync→MMD→VRCの既存キーだけで口/眉/まばたき/目線を動かす。Perfect Sync推論そのものは作らない。追加のauto-customは過去の実験（左右口角、唇帯のみ横4mm、瞳限定移動、ガンマ2、開口上げ抑制、強調0）を踏襲する任意モード。眉専用動画は不要。

眉のソースチェックポイント6806913。builds/demos/haolan-custom-browsへ旧Player一式と旧.tcapを別保存済み、通常ビルドで上書き禁止。desktop tanakacap-demo-custom-brows.batでカメラなし/非記録/無期限の自作モーション。眉は追加モデルなし、眼端基準/PnP固定平面/安定10観測中立/3平均stride1/欠測保持。既存録画5,071/5,187で有効、正解率とは扱わない。

通常Playerはexisting既定、run-avatar-lab.ps1/run-motion-lab.ps1 -ExpressionMode auto-customで実験方式。新規.tcapはexisting-expressions-1と対応表を保存、旧haolan-1.6も新Playerで読める。通常ではメッシュ生成なし。auto-customだけ実行中コピーへ生成。HAOLAN既存方式はMMD口、左右独立の口角/横寄せは未対応、目線は弱い眼ボーンとなる。自動モードが任意モデルに適用できる保証はない。揺れ物/推論モデル/人体補正は変更なし。

237 tests、Editor優先順位/空キー/Descriptor名優先/両側平均/目線軸代替/既存メッシュ不変の検査、両モードの実Player回帰成功。results/expression-mapping/{existing-final,auto-custom-final}.log。autoの唇外不変/両方向4mm、瞳2,178頂点の方向/範囲外不変、強調連続を確認。通常実アバターはHAOLANのみ。SDK設定はローカル3.10.5公式Editorソースで確認したが、全Descriptor型の実SDK書出し検証は未実施。

比較完成：results/avatar-videos/expression-mapping、左からcustom-demo/existing/auto-custom。5,187の同一packet/時計、各185.033秒/30fps/5,551描画。単独3本＋side-by-side/face-closeupの計5本、全編decode検査成功、report.json status=complete。再生入力3本のSHA256一致。保存デモ6806913、通常/自動の比較ビルドは2504820。実カメラ/エージェント動画目視なし。desktop tanakacap-compare-expressions.bat、test-auto-expressions、motion-auto-expressions追加済み。README/SPEC0.69とdocs/EXPRESSION_PORTABILITY.mdに方式/限界を記載。映像の品質判断はユーザー。汎用アバター対応やフェーズ5全体の完成とは扱わない。

最後にCPU頂点Read/Write無効のメッシュでも既存キー方式を起動できるようガード追加。自動生成は省略して警告/既存方式へ戻す。合成Read/Write無効メッシュ検査と再ビルド、両モードの実Player回帰成功（results/expression-mapping/*-readability.log）。HAOLANはRead/Write有効なので比較動画の分岐には影響せず、両モードの対応表も完全一致。動画は上記比較ビルドのまま保持、最終DLLと動画のDLLのSHAは異なる。

次：ユーザーが比較動画の見た目を評価。今回の実装・保存デモ・比較生成は完了。残件は未知の形状名/分割renderer、実SDK各Descriptor種、別アバターでの表情・骨/構図/改変対応、将来UI等。外部push、実写/素材/resultsのGit追加なし。

## 2026-09-13 — FP16通常採用、FP32起動選択の撤去

ユーザーがFP16採用と、FP32は起動オプションから消して将来UIに追加する可能性に備えた口だけ保持するよう指定。通常test/live/Python CLI/soakは精度指定なしでgraph-fp16。launcherの-InferenceMode、CLI/soakの--inference-mode、tracking-settings.jsonのinference_modeを削除。古い設定値でFP32に戻る経路はない。DEFAULT_INFERENCE_MODEとmain(argv, inference_mode=...)・既存モデルAPIを内部接続として保持。UIへの追加は未確定で、勝手に実装予定へ格上げしない。過去のオフライン比較ツールは内部APIでFP32回帰が可能、通常起動の選択肢ではない。

既存録画60観測を精度引数なしで全機能実行し、FP16/CUDA実行成功（results/fp16-default-smoke.log）。234 tests成功。通常bat更新、test-fp16は通常testと同じ内容の互換ショートカット、比較動画は保持。頭専用モデル/口の補正/揺れ物/TensorRT不採用は変更なし。下記のFP32通常/評価待ちは以前の状態。


## 2026-09-13 — TensorRT不採用（ユーザー確定）

契約条件の質問へユーザーが「使わない」と回答。TensorRTの接続モジュール、trt-fp32/trt-fp16選択肢、requirements-tensorrt.txtを削除し、開発venvのtensorrt-cu13/bindings/libsをアンインストールした。確認待ちではない。ユーザーが改めて指定しない限りTensorRTを再導入しない。既存ORT wheelに付属する未使用provider DLLはパッケージの一部として残るが、アプリから選択/実行しない。CUDA/FP16/Fと比較動画は維持、通常はF有効・graph/FP32。次はFP16動画のユーザー評価。下記のTensorRT確認待ちは不採用決定前の経緯。


削除後の検証：232 tests成功、既存録画60観測の全機能CUDA FP16試験も完了・GPU実行確認（results/no-tensorrt-smoke.log、results/20260912T203105-605551Z-rtmw3d-x-384）。新しい棚卸しはresults/distribution-audit-no-tensorrt-20260913。実カメラは使用していない。

## 前回の記録：2026-09-13 — F通常採用、CUDA FP16比較、TensorRT条件確認待ち

ユーザーがF採用を指定し`detector_graph=true`へ変更。コミットdf63f74。`-NoDetectorGraph`で戻せる。G/I・全部ON・body3d/pnp・3/1・口角0・揺れ物は維持。通常精度はgraph/FP32のまま。

CUDA混合FP16を`-InferenceMode graph-fp16`で可逆実装。YOLOX固定部分/RTMW3D-X/batch2虹彩が対象、入出力・Softmax/一部集約・NMS後段はFP32。元ONNXを保持、既存ORT同梱変換器で派生モデルを作成。`graph`で復帰、頭専用は対象外。通常採用/見た目同等の判断はまだしていない。

全5,187観測を2方式の独立ROI/推論/補正で処理、results/comparisons/cuda-precisionにreplay/frames/report/difference。主要計算CUDA確認、32/16で推論＋CPU補正の参考平均17.794/16.267ms。Full HD60/全機能/隔離OBS透過合成の各90秒試験は受信46.170/49.396Hz（約7%向上）、描画59.976/59.998fps。透過/背景合成/動き/正常終了成功。results/precision-{fp32,fp16}-fullhd。results/avatar-videos/cuda-precisionの動画4本（単独2/左右/顔拡大）は完成・全編decode検査成功。各185.03秒/30fps/5551描画、左FP32/右FP16。詳細docs/PRECISION_COMPARISON.md。実カメラ・エージェントの映像目視は行わない。

FP16のXY差p95約1.65pxだが大きな外れもあり、補正後の胴体yaw差p95約29度、口角にも差がある。精度改善/劣化を正解付きで判定した結果ではない。ユーザーが比較動画で評価する。desktop tanakacap-compare-fp16.bat（比較動画の場所）/tanakacap-test-fp16.bat（ユーザー用実カメラ試験）追加、通常test/liveも更新。検証232 tests成功。

重大な保留：ユーザーはTensorRTを「CUDAと同条件なら」実装と指定。通常版10.16.1.11/cu13はORT実DLLのnvinfer_10/CUDA13と一致するため開発venvへ導入し版/契約を確認した。しかし実wheel契約は最新Web SDK SLAと異なり、1年自動更新/更新終了・競合技術制限・狭い再配布対象記述がある。同条件と確定できないためasyncで確認中。返信があるまではTensorRTのモデル実行/engine構築を行わない。これまでTRT推論は一切未実行。`trt-fp32/trt-fp16`接続とrequirements-tensorrt.txtは未検証の準備段階、通常依存ではない。TensorRT for RTXではない。CUDA FP16はTensorRTを呼ばない。

次の作業：ユーザーのFP16動画評価とTensorRT条件への回答を受ける。許容回答があればTRT EP実行/ビルド時間/キャッシュ/CPUフォールバック検査/同録画速度と動画比較を実施。CUDA FP16の通常採用を勝手に決めない。TensorRT Web契約だけで実wheel再配布条件を解決済みにしない。棚卸しはresults/distribution-audit-precision-20260913（25packages/51通知/19ONNX）、docs/DISTRIBUTION_LICENSES.md。README/SPEC0.66も更新。動画・重み・実写はGitへ追加しない。

## 2026-09-13 — FのOFF/ON全編比較動画完成

Fの通常OFFはユーザー指定ではなく、初回実装b3d583fで改善幅が小さいためエージェントが決めたと履歴確認。ユーザーはF〜I実装、Hのみ独立コミット/遅ければrevertを指定していた。OFF指定の発言があったと扱わない。

ユーザーの動画要求を受け、既存F動画はなかったため新規作成。tools/compare_detector_graph.pyで既存録画全5,187観測をF-OFF/ONそれぞれ独立ROI追跡・推論・補正へ通した。通常設定body3d/pnp・3/1・G/I・口角0を共通使用。全観測でROI/送信packet完全一致。有効観測は両側顔5145、目線4951、胴体5183、左腕4571、右腕4558。無追跡だけの一致ではない。results/comparisons/detector-graph-f/report.json、各replay/framesを保持。

同一PlayerでF-OFF.mp4 / F-ON.mp4 / side-by-side.mp4をresults/avatar-videos/detector-graph-fへ生成。各185.03秒・30fps・5551frame、全3本decode成功。左右比較は左OFF/右ON、デスクトップtanakacap-compare-f.batで保存先を開く。これは表示品質の同期再生で、推論速度・実遅延の比較ではない。目視はユーザー。実カメラ/目視/Unity変更なし、通常Fの設定はまだ変更していない。詳細docs/FURTHER_OPTIMIZATION.md。次は比較評価・F通常採用の判断。口の推定Zなし試行等は下記を維持。

## 2026-09-13 — 口の推定Zなし試行・比較動画、配布ライセンス整理

通常設定をbody3d/pnpへ変更。現行は口角もZを使用していたため、既存HeadPoseの固定テンプレート/PnP正面化を再利用して推定Zを口輪郭から外す。頭ピッチは維持、全身のモデルZは引き続き使用。pnp_depthmouthで直前のZ口輪郭へ可逆。時間処理3/1、口角追加強調0、他部位・揺れ物は不変。実装コードを重ねず設定で既存経路を選択した。

既存face-depth-trialの保存済み5,187観測から口4制御/有効フラグだけを再計算し、頭・目・開口・体・腕・指の保存済み制御を固定して動画4本を作成。results/avatar-videos/mouth-no-z/{face-closeup,side-by-side,mouth-z,mouth-no-z}.mp4。各185.03秒/30fps/5551描画、全4本decode成功。左Z/右Zなし。口有効3588→5104、口角/横寄せの隣接変化p95縮小だが対象集合が違い実表情も含むため精度証明ではない。ピッチ差0。CPU姿勢/口平均0.383→0.456msと微増、GPU高速化ではない。見た目はユーザー未確認、実カメラ/目視なし。関連38 tests。詳細docs/MOUTH_NO_Z_TRIAL.md、生成tools/compare_mouth_depth.py。

test/liveはZなし、desktop tanakacap-compare-face.batは新顔拡大動画、tanakacap-test-mouth-z.batは直前方式。通常testの明示HeadPoseModeもpnpへ更新済み。Unity変更/ビルドなし、現在Playerを使用。新撮影は不要。次はユーザーの比較評価を受けて口試行を判断し、既存品質・UI等の指定作業へ。

docs/DISTRIBUTION_LICENSES.mdに製品/モデル/SDK/素材/比較ツールの条件と残件を整理。tools/audit_distribution.pyで22packages/48license files/16local ONNX SHAをresults/distribution-audit-20260913へ収集。配布承認や完全SBOMではない。HAOLANは条件付き再配布許諾があり一律禁止と扱わない。頭専用重み等は未確定、MANOは用途/再配布制限、FFmpeg実体GPLv3は開発用途、SDK本体は製品から除外する方針。製品EULA/全DLL照合/モデル通知同梱・新PCは残件。

TensorRTは今回見送り。通常版はランタイム再配布可能だが条件継承・通知/執行等の義務、RTX版はさらに性能情報の第三者開示制限。ユーザーの追加制約回避を優先して依存を増やさない判断。通常版の主な配布条件は既存CUDAにも同種のものがあり、TensorRTだけ特別厳しいとは断言しない。ユーザーが通常版の条件を許容すれば再検討可能。今回は未導入/未実装/未計測。A/FP16/Eの高速化は現状維持、H/J/K/L復活なし。

以下は過去の状態。最新の通常pnpを、以前のpnp_depthmouth採用記述より優先する。

## 2026-09-13 — 口角強調度完了、J/K/Lは比較後すべてrevert

口角強調度0〜1、既定0（追跡OFFではなく追加モーフ増幅なし）、1は従来。5085cb5、mouth_corner_emphasis/両launcher -MouthCornerEmphasis/Player --mouth-corner-emphasis/将来UI用プロパティを追加。実モーフ0/0.5/1・左右/腕/透過回帰成功。ガンマ・口閉じ校正・開口時上げ抑制・横寄せは維持。実人物の新しい口角の見た目は未確認。

J/K/Lを各独立実装・Full HD60＋OBSで比較し全部revert。基準2回45.419/45.199Hz、J45.395（座標差0だが改善確認できずbacbc07でrevert）、K48.395（80録画観測で高信頼XY最大差38.49px/Z0.8834mのため96af046でrevert）、L45.162（5,187観測の制御完全一致だが両基準より僅かに遅くfc9a905でrevert）。Jは明確な遅化と断言せず、利点が確認できないため撤回。モデルの推定差を人体の実距離誤差と呼ばない。全て約60fps、透過/合成/変化/正常終了成功。実カメラ/映像目視なし。推論コードは5085cb5と同じ、G+Iを維持、試行フラグは残さない。

詳細docs/MOUTH_EMPHASIS_AND_OPTIMIZATION_JKL.md、結果results/optimization-{jkl-baseline,J-fullhd,K-fullhd,L-fullhd,jkl-baseline-repeat}、compact-simcc-audit/gpu-preprocess-audit/reuse-buffers-audit.json。試行J2713bfe/K482c79c/L69f1b4a。最終228 tests、Unity実Player検証済み。フェーズ残件表はIMPLEMENTATION_PHASES先頭へ更新。今回の高速化は終了、次は既存品質/長時間/配布UI等の残件をユーザー優先で進める。UIの推論Hz・描画4択・上限待機・口角強調度は予定、UI自体は未実装。A/E保留、H復活なし、揺れ物終了、録画検証を維持。

## 2026-09-13 — UIの推論速度表示を追加予定

ユーザー指定で将来の推論切替UIに実測推論速度表示を追加。描画fps/Player受信Hzと区別する。SPEC0.63/SHARED_PREVIEW/AGENTSへ記録、UIは未実装。次の高速化候補はRTMW3D出力の点への復号をGPU上で済ませCPU転送を小さくする案、切り出し/正規化のGPU化、CPU補正の割り当て削減。いずれも提案のみ、効果未測定。前回H並行は復活させず、A/Eは保留、モデル/補正・揺れ物は変更しない。

## 2026-09-13 — 描画共有・自由解像度・プレビュー非表示を実装

- ユーザー指定の3案を実装。通常はOBS用RGBAをプレビューへGPU合成して二重アバター描画を省く。MainCameraは姿勢参照用に有効のままcullingMask=0。出力AAのみ1回、UIはOBSへ入らない。--legacy-preview / -LegacyPreviewで旧方式へ戻せる。
- Full HD（1920×1080）を既定化。--output-width/height、両launcherの-OutputWidth/-OutputHeightで各64〜4096、幅省略は16:9。異なる比率は横FOVが変わる、プレビューは余白付き。--no-preview/-NoPreview/F8でプレビュー画像だけ省略、出力/追跡は維持。desktop test-no-preview追加、通常test/live/motionは表示あり、非記録無期限は維持。
- 同じ既存録画・全部ON G+I/body3d/pnp_depthmouth/OBS60・各60秒。旧Full HD受信44.04Hz→共有44.93→非表示45.49、描画59.83〜59.99fps。共有960×960も44.91Hz/60fps。4条件とも透過合成/画像変化/正常終了成功。GPU使用率は下がらず、小差を確実な省電力改善と断言しない。短期3標本の全体GPU値。結果results/shared-preview-*、docs/SHARED_PREVIEW.md。
- 実Player合成入力3条件と画像数値照合に成功。上下/色/余白のRGB平均差0.17階調未満、非表示は背景のみでSpoutのアバター維持。tools/check_preview_pixels.py。Unityビルド・構文確認・desktop更新済み。実カメラ/映像目視なし、F8実キー・長時間見た目未評価。揺れ物ソルバーは変更なし。
- 将来UI：推論切替と同じ場所へ60/推論同期/30/自由入力。推論が指定描画数値を超える場合は開始前に待機して推論を同じ上限まで抑える予定。現行へ上限制御を追加したわけではない。同期モードの上限表示/欠測時更新等はUI設計時に具体化。部位間引きEとは別。UIの約N倍表示要件も維持。
- 次はユーザーの優先指示または既存フェーズ残件。A/E保留、H再導入禁止、揺れ物調整終了、録画検証を維持。README/SPEC0.62/LAUNCH_MODES/INFERENCE_BREAKDOWNに反映。

## 2026-09-13 — 描画30固定対60固定の比較完了

- Player --render-fps 30|60、run-avatar-lab.ps1 -RenderFps、既定60。デスクトップtanakacap-test-30fps.bat追加、通常test/live/motion維持。Unity再ビルド・構文確認済み。
- 同じ既存録画/全機能G+I/body3d/pnp_depthmouth/720p/AA/隔離OBS60で各60秒。描画60.00→29.98fps、受信44.47→46.14Hz、GPU使用率53.0→47.7%、GPU電力145.7→142.5W。GPUは安定区間3標本の全体値、描画単独ではない。送信→描画投入p50中央値6.54→10.32ms。実カメラHz/実表示遅延ではない。
- 透過・合成・画像変化・正常終了を両方確認。実カメラ/映像目視はなし。Unityループ全体の上限なので表示/揺れ物呼び出し間隔も変わるがソルバーは変更なし。30の見た目は未評価、通常60を維持。
- 詳細docs/RENDER_RATE_COMPARISON.md、結果results/render-rate-60とrender-rate-30。追加案はOBS出力テクスチャをプレビューへ再利用して二重描画を省く案が最優先、次に小さな配信表示向け解像度、プレビュー省略。未実装。受信同期可変描画も未実装。ユーザーの優先判断を待つ。A/E保留・H復活禁止・揺れ物調整終了を維持。

## 2026-09-13 — F〜I高速化完了、G＋Iを通常採用

- ユーザー指定通りF→G→H→Iを実装・計測。追加で高優先だった全画像RGB変換の無駄はGで対応し、低優先の別施策は追加しない。顔はRTMW3D共有・PnPピッチ/Z口角を維持。A/E保留、揺れ物は変更なし。
- F b3d583f：同じYOLOX固定390/NMS25ノード分割、GPU上直接受け渡し。空画像/録画80入力でROI・信頼度差0、主要計算CUDA。900観測平均22.248→22.028msと小幅なので任意（既定OFF）。-DetectorGraph/-NoDetectorGraph。
- G 9aed8d0：RGB化を全画像からcrop後へ移動、モデル入力完全一致。900観測平均22.387→20.323ms、前処理3.966→1.756ms。通常preprocess_mode=crop、-PreprocessMode legacyで復帰。
- H 53772c7：同一観測内の虹彩GPUとCPU補正を並行化、229 tests。前後基準20.128/20.263msに対しH20.413msで遅く、指示通りcee5557でrevert。並行worker/オプションは現行に残さない。
- I e925743：既存虹彩重みのbatch2派生、片眼はダミー枠を無視し両眼欠測は呼ばない。80入力/73観測眼の虹彩座標差0・視線有効一致、GPU主要計算確認。900観測平均は前後基準20.101/20.345→19.625ms、目線2.159/2.152→1.472ms。通常batch_eyes=true、-NoBatchEyesで復帰。
- 最終実Player＋隔離OBS/720p60/AA/各60秒/既存録画最大速度：基準39.317Hz→G＋I44.833Hz、両方描画59.997fps。透過合成・画像変化・正常終了成功。results/optimization-fgi-obs-baseline-retry と optimization-fgi-obs-final。カメラの新規観測Hz・実センサー表示遅延・長時間品質の保証ではない。配信/録画なし、映像目視はしない。
- 最初のOBS基準はAPI207（WebSocket接続後の出力系未準備）で失敗。検証スクリプトへ準備待ちを追加し再試験成功。失敗結果optimization-fgi-obs-baselineを保持。実カメラ未使用、モデル/実写/アバター/結果はGit除外。原本ONNXは変更せずSHA別の派生キャッシュ、既存ONNX1.22.0を利用。
- 現行228 tests、PowerShell構文確認、desktop bat更新済み。通常live/testは採用設定を使用、head-only/motionは維持。全高速化を戻す場合-PreprocessMode legacy -NoBatchEyes -NoDetectorGraph。顔の採用設定とは独立。
- 詳細・単独条件・再現はdocs/FURTHER_OPTIMIZATION.md。次は必要な録画品質/長時間評価と既存フェーズ残件。Hを再追加しない。ユーザー明示まで実カメラを開かない。揺れ物・A/Eへ勝手に戻らない。


最新高速化（2026-09-13）：Fは実装済み任意（既定OFF）、G=crop前処理とI=batch_eyesを通常採用。Hは53772c7で実装、計測で遅くcee5557でrevert。顔はbody3d/pnp_depthmouthのまま。既存録画＋Player/OBSの最終比較を進行中。docs/FURTHER_OPTIMIZATION.md参照。

最新指定（2026-09-13）：全部ONのF〜I高速化を実装。Hは独立コミット、遅ければrevert。Fは分割Graph実装/録画一致/GPU/900観測比較済み、効果小で任意。Gはcrop後RGB化を通常採用（入力一致/228 tests/900観測比較）。H→Iが進行中。docs/FURTHER_OPTIMIZATION.md参照。

## 2026-09-13 — ピッチPnP・口角Zを通常採用

ユーザーは顔Zのピッチが大きくがたつくと評価し従来方式を選択、口角はZ方式でよいと明示。通常設定をface_source=body3d / head_pose_mode=pnp_depthmouthへ変更。PnPでピッチを求め、口角・口輪郭は前回と同じ推定Z方式を維持する。PnPの口正面化は省略し二重処理を避ける。頭以外の推論・揺れ物は維持。

既存5187観測の生データで従来PnPとのピッチ差0、顔Z方式との口角/横寄せ/弓形差0・口輪郭有効フラグ一致を確認。results/face-pnp-depthmouth-audit.json。CPU単独の再計算平均はPnP全処理0.476ms/混合0.346ms、前回GPU併用計測とは別条件。225 tests成功。実カメラ・動画目視・追加動画作成は行っていない。口角Zの欠測は既存通り保持し、PnPピッチを止めない。

デスクトップtest/liveは採用構成、test-face-pnpは同じRTMW3Dでピッチ/口ともPnPへ復帰、test-face-originalはRTMW-L/pnp。depth3dは過去比較の再現用に残すが通常へ戻さない。頭専用は維持。既存のface-depth-trial動画は混合採用前の比較である。次は採用構成で必要があれば録画検証、顔Z口輪郭欠測など既知残件を扱う。


## 2026-09-13 — 顔Zからピッチ・口角を同時に求める試行と動画完成

- ユーザー指定でHeadPose3Dとhead_pose_mode=depth3dを実装。RTMW3Dの同じ推論のXY/Zからカメラ距離を近似し、鼻/眼端9点の剛体回転でピッチと口輪郭の正面座標を計算。PnP/LM、標準唇の仮の奥行き・1.5倍補正は新経路で使わない。標準の鼻/眼形状と近似カメラは残る。既存gain1.8・10観測校正・時間ゲート・モーフ・揺れ物は維持。
- 通常はseparate/pnpのまま。-FaceSource body3d -HeadPoseMode depth3dで試行、-HeadPoseMode pnpで今回の対照へ戻す。-FaceSource separate -HeadPoseMode pnpでRTMW-Lへも戻せる。depth3dはbody3d顔が必須。頭専用・通常live/motionは維持。
- 比較は両側とも同じRTMW3DのXY/Z・ROI・撮影時刻・5187観測、ピッチ/口輪郭処理のみ変更。左body3d=旧PnP、右depth3d=顔Z。results/comparisons/face-depth-trial。前回のRTMW-L対RTMW3D比較とは区別する。
- 動画はresults/avatar-videos/face-depth-trialのbody3d.mp4/depth3d.mp4/side-by-side.mp4/face-closeup.mp4。各185.03秒/30fps/5551フレーム。4本全編デコード成功・時刻/フレーム整合確認。ユーザー指定で映像抽出や目視確認はせず、見た目の判断はユーザー担当。
- 対象計算の平均0.589→0.220ms、両方頭fit有効の3841観測だけでも0.594→0.236ms。全体fpsやOBS併用速度ではない。頭fit5118→3898/口輪郭5104→3588、顔Zのpitch p95が40度上限。既存姿勢ゲートへの波及で視線4951→3266/顔距離4911→3380。軽いことを品質改善と扱わない。追加補正で隠さず比較動画に残す。通常採用は保留。
- 224 tests、PowerShell構文確認成功。別の録画300観測で実benchmark経路の共有1セッション/GPU主要演算を監査、CPU主要計算なし。results/20260912T174517-019568Z-rtmw3d-x-384。実カメラ未使用、Unity変更/再ビルドなし。
- desktop test.batは顔Z、test-face-pnp.batは今回の対照、test-face-original.batはRTMW-L、compare-face.batは新比較の保存先へ更新。README/SPEC/AGENTS/関連文書更新。動画・実写・重み・アバターはGitへ入れない。
- 次：ユーザーが動画を確認。顔Z方式の有効率低下・ピッチ上限・表情差を含めて採用判断する。勝手な補正追加/通常採用をしない。今回の映像目視確認はユーザー担当。A/E保留、揺れ物調整終了、録画検証方針を維持。詳細・公式座標根拠・再現はdocs/FACE_DEPTH_TRIAL.md。


## 2026-09-13 — RTMW3D-X顔共有の可逆実装・比較動画完成

- ユーザー指定でface_source=separate/body3dを追加。共有はRTMW3Dを顔/体で1回だけ実行しRTMW-Lを生成しない。XYと信頼度を共有、顔Zの新規利用なし。頭/口/虹彩/距離/体補正・揺れ物は維持。通常tracking-settingsはseparate、頭専用も維持。
- 全5187録画観測を共通ROI/生体出力/実撮影時刻で比較。顔に加え眼crop・顔距離・体の整合参照も変わる。顔有効5142→5145は正解率ではない。共有で開口が増え、瞬き出力が小さく、頭ピッチ基準も変わるため通常採用は保留。録画は主に体/手用で顔の全可動域を網羅していない。
- results/avatar-videos/face-source-trial：separate.mp4 / body3d.mp4 / side-by-side.mp4 / face-closeup.mp4完成。各185.03秒/30fps/5551フレーム、左従来・右共有。全編デコード成功、30/85/150秒の顔構図・左右ラベルを確認。推論結果results/comparisons/face-source-trial。Unityソース/ビルド変更なし。
- RTX4090/録画900観測/全部ON/graph/M/3間隔/Player・OBSなし：ループ平均27.53→22.54ms（約18%減）、中央値22.64→17.70ms。results/full-optimization-face-1789233552678811500。描画併用Hzやセンサー表示遅延の測定ではない。
- 216 tests成功、PowerShell構文確認。別の録画30観測で共有RTMW3D/虹彩/人物検出のCUDA主要演算を監査、CPU主要計算なし。results/20260912T172632-336891Z-rtmw3d-x-384。実カメラは開いていない。
- デスクトップtest.batを共有試行へ更新、test-face-original.batで従来、compare-face.batで拡大動画の保存先。直接-FaceSource separateで戻せる。live非記録無期限は従来既定、head-only/motion維持。
- 次：比較動画のユーザー評価を受けて採用/調整を判断。共有側の口/瞬き、顔距離による表示サイズ差、独立2D整合参照を失う影響が評価残件。新構成OBS性能・実カメラ品質は未確認。A/E保留、揺れ物は触らない。詳細と再現はdocs/FACE_SOURCE_TRIAL.md。


最新検証方針（2026-09-13）：検証は既存録画を基本とする。ユーザーが明示的に指示するまで、エージェントは実カメラを開いて試験しない。録画では確認できず実カメラが不可欠と考える場合は、目的・録画で代替できない理由を説明して事前に相談する。一般的な自走許可を実カメラ試験の許可と解釈しない。ユーザー自身が起動するカメラ用batは維持する。

## 2026-09-13 — 全部ON高速化B→C→Dを実装・比較

- 最新ユーザー指定：全部ONでB→C→D、A（TensorRT/FP16）/E（部位更新間隔）は保留。揺れ物は触らない。RTMW3Dは体/手が共同推論なので、手に影響する胴体停止案は採用しない。
- 通常設定はB+C：inference_mode=graph / detector_interval=3 / detector_model=yolox-m-human。run-avatar-lab.ps1の同名引数で戻せる。Python CLI既定はrun/1/Mを維持。デスクトップtestは全部ON診断に戻して更新済み。liveの非記録無期限、head-only/motionは維持。Unity再ビルド不要（今回Unityコード変更なし）。
- B：GPU固定入出力/Graph、検出可変長出力はbindingを毎回再設定。空画像/復帰を含む5モデルの旧runとの差0、GPU主要演算確認。結果results/gpu-runner-audit-1789231210724547400。顔/体/目/部位別補正は維持。
- C：3回の実検出で確定後、最大2観測を上半身点の往復LK flowでROI移動。不良/端/120msで即再検出。キャッシュで初期確定しない。ロストと復帰は既存保持契約。4件の新規テスト含む214 tests成功。
- D：公式YOLOX-tiny HumanArt416を取得・GPU比較・選択実装済み。モデル別のROI差が相対Zへ大きく影響したため通常採用しない。-DetectorModel yolox-tiny-humanで任意選択。原本重み・実写・結果はGit除外。
- 単独900観測中央値：従来B基準40.90ms→graph37.39ms、C比較37.11→22.20ms。6×150観測の同一区間比較でCの顔XY差平均0.37px、左右手0.58/0.72px、体Z差平均0.0076m。Dの体Z差平均0.0435m/p95 0.2544m。正解率ではない。results/person-optimization-audit-1789231118191184300。
- 実Player+隔離OBS/720p60/AAあり/各60秒/既存録画最大速度：従来20.24Hz→B+C32.63Hz、任意D35.60Hz、描画全て約60fps。透過合成/画像変化/正常終了成功。results/optimization-obs-{baseline,bc,bcd}。実カメラの新規観測Hz・センサー表示遅延と混同しない。
- 実カメラ1/MSMF1280x720/30fpsは取得成功、120観測で人物確定0。results/20260912T164948-822875Z-rtmw-l-384。人物不在とは断定せず、この試験を追従品質・全部ON実カメラ性能の成功に数えない。
- README、SPEC、PROGRESS、PHASE4_VALIDATION、IMPLEMENTATION_PHASES、THIRD_PARTY、PERFORMANCE_OPTIONS更新。ユーザーの部位別経路の質問へINFERENCE_PIPELINE.md追加。詳細・条件・再現はFULL_MODE_OPTIMIZATION.md。
- 次：既存録画でC有無（-DetectorInterval 1）や長時間安定性を確認。実カメラ試験はユーザーの指示待ち。新構成の実カメラ+OBS30分、露光〜表示遅延、腕/肩/左指・遮蔽品質、フェーズ5UI/配布環境/汎用アバター/許諾監査が残る。A/Eや揺れ物を勝手に再開しない。
- 追加高速化はPERFORMANCE_OPTIONS.md末尾のF〜Iを提案。未実装・効果未測定。現行B+C設定は維持、A/E保留。
- pytestは通常sandboxの`.venv/Scripts/python.exe -m pytest -q`で実行可能。tests/conftest.pyのWindows tmp_pathがworkspace ACLを継承、OS権限変更なし。


最新指定（2026-09-13）：スポーン時を含む揺れ物は今後調整しない。頭専用モードを先に仕上げ、次は高速化案だけを提示し、ユーザーが優先順位を指示するまで高速化の実装に着手しない。音声口パクは引き続き後日。

## 2026-09-13 — 頭専用autoの実装完了（実人物品質は未確認）

- HeadRegionDetector（YuNet/ORT CUDA）＋HeadRegionTrackerを追加。頭の存在・移動・距離変化に応じてcrop更新、未検出で保持、2検出で再取得。P停止/R初期化/S対象選択、複数人の即切替を抑止。表情/目線/体/従来人物モデルは生成しない。-HeadRoiMode fixedで旧方式。loop-videoも対応。
- 900測定全て追跡有効、単独録画ループp50 8.601ms。人工遮蔽/移動/回転と2モデルCUDA実行、実Player頭/ロスト保持、実カメラ起動成功。210 tests。詳細・結果・再現・ライセンスはHEAD_ONLY.md。実人物品質/頭重み一般配布は未達。
- tanakacap-test.batを頭専用診断へ更新。head-only.batは自動取得の非記録無期限。通常tracking-settings.jsonはfullのまま。Unity/揺れ物は未変更。
- 次：高速化候補はPERFORMANCE_OPTIONS.md。ユーザー指定の優先順位待ち。上記より古い揺れ物の調整候補・頭専用自動取得未実装の記述は旧状態。


最新追加要件（2026-09-13）：将来のUIでオプション/構成の重さを「約N倍」の整数倍率表示にする。SPEC/フェーズ5/AGENTSへ記録済み。倍率の基準・測定範囲はUI設計時に決定、今はUI実装しない。

## 2026-09-13 — 本家PhysBoneと独自揺れ物の比較動画

- ユーザー指定で、本家SDK3.10.5と現在の独自ソルバー（減衰1.5倍）を同じEditor/同じHAOLANコピー/同じモーションで同時撮影。左本家・右独自、日本語ラベルと動作区間付き。
- results/avatar-videos/physbone-vs-independentにfront.mp4、hair-closeup.mp4各21秒、各-half-speed.mp4約42秒、全て1080p60/H.264。正面は服込み、拡大は髪を斜め25度から。原Prefabの共通Tポーズ、頭振り/胸pitch-roll/停止後を比較。SDKは隔離Editor内のみ。通常アプリ・追跡・揺れの設定/実装は変更しない。
- 検証：両側の実骨変化、1260撮影フレーム、半速2519フレーム、4本の全編デコード、ラベル/構図を確認。最初のdtのみ20ms、以降1/60秒。半速は撮影結果の再生時間だけ変更。試写でエンコーダーパス不一致を修正、初期化失敗時の自動終了を追加。平均骨回転差1.7395865度は前回と一致。実人物/本家完全一致/ユーザー見た目評価の合格とは扱わない。
- 再現はtools/prepare_physbone_reference.py→tools/render_physbone_comparison.py。--encode-existingで撮影データを保持して字幕・半速を再生成。デスクトップtanakacap-compare-physbone.batを追加し既存batも更新。docs/PHYSBONE_REFERENCE.md、READMEを更新。SDK/アバター/動画/結果はGit除外。
- 次は完成動画で揺れの差を確認し、必要なら残る衝突・初期過渡・停止後の差へ対応。その他の現状・未達は下記引き継ぎを継続。

## 2026-09-12 — 推論内訳・統合OFF設定・頭専用試行・本家PhysBone比較

- ユーザー指定：目/顔頭/体/その他の時間を測り、頭以外を個別OFF（既定ON）。最軽量は頭姿勢のみ＋将来の音声口パク、顔ランドマークも省略。音声口パクは今回未実装。追加質問を受け、同じアプリ/起動スクリプトの構成オプションへ統合。tracking_mode=full（既定）/face_head/head_only、-TrackingModeと-HeadOnly別名。頭専用batは別製品ではなく非記録・無期限ショートカット。
- 計測追加：モデル毎、人物検出の前/推論/後、PnP、顔フィルター、距離、体補正、UDP、read/その他。--no-ort-profileでJSON記録とORT詳細traceを分離。RTX4090/同じ録画900観測/専用Player・隔離OBS・previewなし：全体41.145ms、体OFF29.352ms、顔頭のみ24.579ms、人物検出もOFF9.719ms、頭専用3.177ms（ループ中央値）。全構成の人物検出推論14.968msが最大、RTMW-L5.683/体10.228/目4.106ms。測定条件の違う旧OBS併用20Hzや表示遅延と混同しない。docs/INFERENCE_BREAKDOWN.md、results/inference-stages-1789224490331791700。
- 頭専用はMobileNet V3 smallの直接頭姿勢ONNX、CUDA必須、SHA256固定。顔/体/虹彩/人物検出モデルを読み込まない。手動固定ROI、P停止/R再選択。空画像の自動ロスト/再取得は未達。矩形が合っている前提の試行であり通常品質を置き換えない。画像既知回転から当初の符号反転を修正。headTrackedをfaceTrackedから分離、実Playerで表情OFF/頭pitch22度反映を確認。CUDA node5643/CPU0。コードMIT表記を保持、重み/学習元の一般配布監査は残し同梱しない。docs/HEAD_ONLY.md。
- PhysBone公式SDK3.10.5をSHA照合し隔離Editorへ。原本コピー36SDKコンポーネントと独自35系統73区間を同じ60Hz/頭振り・胸pitch/rollで比較。初回初期化漏れ/時間刻み不一致の無効な比較は修正して除外。復元周波数候補は悪化で維持、減衰1.5倍は別動作でも改善し採用。平均回転差（全骨1260frame）2.007→1.740度、頭振り1.740→1.266度、胸2.523→2.188度。静止残差1.847度/服の衝突過渡/急停止差は残る。--legacy-secondary-response/-LegacySecondaryResponseで旧減衰。SDKはPlayer/Exporter/Gitに入れず、逆コンパイル・ソルバーコピーなし。docs/PHYSBONE_REFERENCE.md、results/physbone-reference。
- 検証：205 Python tests、PowerShell3本構文、最終Unity build、実Playerの既存骨/表情/掌/指/ロスト/透過と頭単独smoke成功。揺れ960stepで73区間、本体/位置誤差0、OFF復元、静止速度0.0000143m/s。結果results/model-switches-final。実カメラ品質・最終30分・本家全機能一致の合格とは扱わない。bat更新済み、実写/SDK/資産/結果はGit除外。
- 次：統合設定を実カメラで確認、頭専用の範囲追跡/再検出と角度品質、肩/腕/左指の既存品質課題、PhysBone衝突/初期過渡/静止差、フェーズ4の最終OBS併用と実遅延。音声口パクは後日。通常アバター/追跡補正は維持。SDK比較再現はtools/prepare_physbone_reference.py→tools/tune_secondary_reference.py。

## 2026-09-12 — 軽量AAとフェーズ4の継続・性能検証

- ユーザー追加の軽量AAを、自作7サンプル/単一パスのGPU輪郭フィルターで実装。元4xMSAA、明示Render、premultiplied alphaを維持。F7/--no-edge-aa/-NoEdgeAAで追加分だけ復帰。追加ライブラリなし。既定720p、-OutputHeight 1080でフルHD。docs/ANTIALIASING.md。
- 30分の既存録画GPU推論＋Player＋隔離OBS試験：720p、OBS30fps。Player59.990fps/受信20.168Hz、メモリ大幅な継続増加なし、OBS取りこぼし増分0。初回のソース倍率2/3残留を発見し、検証ツールの寸法補正/背景四隅検査を追加。初回は全面表示検証と分ける。小さいPythonランチャーだけのメモリ値を使わず、実子を補足1671秒計測。
- 初回最大間隔435ms/209msの2件を記録。後者は管理メモリ回収と同時、因果断定しない。LoaderのMemoryStream＋ToArrayを正確な長さの単一バッファへ整理し、過剰な一時配列を削減。読み取り長/ハッシュ/形式検査を維持。最終変更後の30分再実行は未実施。
- AA ON/OFF各90秒・720p自作モーション・OBS60fps：両方約60fps、GPU約3ms台。ON3.182/OFF3.382msと測定差は逆転しており、追加分の厳密なGPUコストは未分離。AAで高速化したとは書かない。RGBAと背景四隅一致を確認。
- 最終1080p/全モデル録画入力/OBS60fpsの120秒：Player59.992fps/受信20.101Hz。最新画像read完了→描画投入の窓中央値の中央値56.284ms、窓p95の中央値65.438ms、送信→描画投入8.635ms。露光/時間フィルター位相/GPU完了/OBS/表示走査は含まず、100/150ms体感遅延目標の達成とは扱わない。
- 検証76件、実Playerの骨/表情/掌/指/ロスト保持/alpha smoke、揺れ73区間960stepの収束/本体非干渉/OFF復元、不正パッケージ4種code2拒否成功。原本依存hash不変。非記録motion4秒でPlayer.log不変/新規resultsなし。
- 検証batの-Diagnoseはresults/player-performanceへPlayer統計も記録。live/motion版は非記録・無期限を維持。デスクトップbat更新済み。README/SPEC/LAUNCH_MODES/THIRD_PARTYとIMPLEMENTATION_PHASESの最新表を更新。通常OBSは変更も終了もせず、試験Player/隔離OBSは終了。
- フェーズ4全体は未達：実カメラ/最終構成30分、実動作→表示遅延、認識30Hz、腕/肩/左指と遮蔽復帰の実用品質、本家PhysBoneとの動作比較。既存録画の品質監査では終盤静止yaw約16度と顔付近左腕の跳びが残る。今回、採用済み補正やモデルは変更しない。結果と再現手順はdocs/PHASE4_VALIDATION.md、results/phase4。実写/資産/結果はGit除外、外部pushなし。

## 2026-09-12 — READMEをセットアップ・ビルドの入口として整備

- ユーザー指定でREADMEを現在のセットアップ、Unityビルド、成果物、通常/非記録/モーション起動、Exporter、OBS、検証、トラブル対応まで整理。プロジェクトの趣旨・制約・素材クレジット・引き継ぎへの導線は維持。古い進捗の重複は整理し、過去の内容はGit履歴と既存PROGRESSに残る。
- setup-lab.ps1に虹彩モデル取得が含まれない点、prepare_unity.pyが要求する正確なZIP名、BuildLabが規約PDFを必須コピーする点を実ソースで確認し明記。虹彩の追加取得/安全な抽出/SHA256照合、results作成、Unityパス指定、bat再生成を案内。SAM/HaMeRは通常導入の必須ではない。
- AGENTSのREADME役割に継続メンテナンスを明文化。依存版・素材・ビルド/起動引数・成果物・設定・OBS連携変更時は同じ変更でREADMEを更新する。READMEは現在手順、PROGRESSは履歴、HANDOFFは再開地点に分ける。リンク先PHASE3_PACKAGE_OBSの旧「PhysBone未変換」を現行の互換変換へ訂正。
- 検証：READMEのローカルリンク22件が実在、PowerShellコード例14件の構文解析成功。虹彩の入れ子archive選択・SHA256・既存モデルとの一致を、取得済みファイルで読み取り検証。新規PCの一括導入/再ダウンロード/Unity再ビルドは今回未実施（文書のみの変更）。新しい依存導入・追跡/揺れ実装変更はない。
- 次の実装・品質残件は下記のPhysBone互換変換とフェーズ4の引き継ぎを継続する。


## 2026-09-12 — PhysBone設定の互換変換と非記録起動を実装

- ユーザー要求：髪/服の揺れ、既存検証batの更新とは別の非記録/無期限カメラ版、カメラなしで再配布制限のないモーション版。さらに元PhysBoneのパラメーターを保ち本家に似せる方針へ指定。最初の固定ばねプロファイルは撤回済み。
- SecondaryMotionExporterはSDK存在時SerializedObject、現在のSDK欠損HAOLANでは原本テキストPrefabの作者設定を読む。35系統/73区間/15明示コライダー、力/制限/カーブ/半径/内包Capsule等をmanifest.secondaryPhysics v1へ。左zipperの重複1件は先頭採用/警告。原本依存hash前後不変。SDK本体/DLL/ソルバーを同梱せず、公式公開仕様から独立した近似実装。docs/SECONDARY_MOTION.md。
- SecondaryMotionは追跡後・透過描画前に更新し、F6でOFF復元、--no-secondary-motionで起動OFF。Humanoid骨/同一骨Constraintは駆動しない。骨長を変えない。内包Colliderで固定支点まで投影して裾が81.9度へ折れる不良を検証で発見、動かせる末端の衝突へ修正。静止時形状差は最大12.63度残り、本家一致とは扱わない。
- 検証：results/secondary-motion/source-audit.jsonで530数値/カーブ値/個数/参照一致。check.jsonの実Player960ステップで本体回転/ローカル位置変化0、OFF復元、静止速度約0.0000142m/s。単独CPUステップ最大約0.80ms。transport.*既存顔/腕/指/掌/ロスト/アルファsmoke成功。motion-final.pngは自作モーションの実描画、デモ専用snapshotが不適切にロストテストへ入る不良も修正し終了code0。頭や腕の採用追跡設定は変更していない。
- デスクトップ：tanakacap-test.bat=従来診断1800frame、tanakacap-live.bat=カメラ非記録無期限、tanakacap-motion.bat=カメラなし自作モーション非記録無期限。tools/update-desktop-launcher.ps1更新済み。F6で揺れON/OFF。run-avatar-lab.ps1 -NoLog、run-motion-lab.ps1、各-Avatar可。docs/LAUNCH_MODES.md。
- 非記録は結果JSON/JSONL/校正/スナップショット/ORT profilingをOFF、履歴は1件。Unity -nolog。無期限は--frames 0かつ--no-log限定、Player終了でカメラ推論も終了。tests/test_no_log.py 3合格、実synthetic GPU構成3frame終了成功、カメラなしPlayer4秒で既定Player.logと結果フォルダー不変(no-log-smoke.json)。長時間メモリ実測は未実施。
- モーションは外部素材/実人物録画を使わないProceduralMotion.csの24秒周期。モーション専用0BSD許諾をdocs/PROCEDURAL_MOTION_LICENSE.txtとbuilds/lab同名ファイルに配置。HAOLAN等を再配布できる意味ではない。
- 未確認：本家VRChatとの同一軌跡比較/減衰時間校正、実人物での自然さ、SDKありの実改変プロジェクト、Simplified/Polar/Plane/版1.1の実素材、非一様scale、標準/他人Collider、Stretch/Squish/Grab/Animator挙動、30分とOBS併用性能。初期段階の独立互換変換であり完全一致とは書かない。次は通常batでの見た目評価と合法的なVRChat実行結果との比較、フェーズ4の品質/性能評価。
- 検証用Playerは終了済み。実写動画/アバター/結果はGit除外のまま。外部pushなし。


## 2026-09-12 — フェーズ3最小経路を実装・検証

- HAOLAN限定Exporter、.tcap（manifest＋AssetBundle）、外部ファイルLoader、OBS実受信/背景合成まで成功。docs/PHASE3_PACKAGE_OBS.md。通常tanakacap-test.batは外部builds/lab/avatars/haolan.tcapを読み込む。F5/--avatar/-Avatarでファイル指定。Exporterはbuilds/lab/TanakaCapExporter.unitypackage。
- ビルド済みシーンから組込みavatarを除去。原本依存hash前後一致25babac2d68f0ee4c5323cd154f54b98、骨/表情/掌等の実Player smoke成功（results/phase3/package-verified）。不正形式/Unity版/shaをcode2で拒否（invalid-final/report.json）。単体ソフトの一般配布用依存同梱はフェーズ5のまま。
- AlphaOutputの通常自動描画ではOBS画像が透明一色になる問題を実受信で発見。LateUpdate明示Renderへ変更し、GPU送信を維持。最終OBS32.2.2/Spout1.12.0の透明677443/不透明240913/中間3244画素、2秒変化69033画素、背景合成を確認（results/phase3/obs-report.json、obs-composite-final.png）。デモでの検査、実人物/30分/遅延合格ではない。
- 通常OBSへC:/ProgramData/obs-studio/plugins/win-spoutを配置済み。次回起動後Spout2 Capture→TanakaCap→Premultiplied Alpha。通常ユーザーのシーン/配信設定は変更せず、実受信は隔離コピーで検証。通常シーンでのユーザー確認は残る。Program Files配置はOS権限で失敗し、公式推奨ProgramDataに成功した。
- 検証用Player/隔離OBSは終了済み。ユーザーの別OBSは停止していない。配信/録画は開始していない。次は通常OBSでの利用確認、フェーズ4の自然な髪服揺れとOBS併用品質/性能。汎用MA/PhysBone変換・一般向け導入は未完了。肩face_ratio/腕front_projection維持。

## 2026-09-12 — フェーズ3進行中：外部アバター成功、OBS実受信を検証中

- ユーザーはフェーズ3開始を指定し、Astra使用量への配慮を要求。モデル交換や多重エージェントは使っていない。
- AvatarExporter.cs/AvatarPackage.cs/AvatarPackageLoader.cs追加。HAOLANプロファイル限定の.tcap（manifest+AssetBundle ZIP）、Unity2022.3.22f1/Windows64一致・SHA256照合。原本コピーだけ加工、未対応scriptはエラー、欠損VRC挙動は対象パス付き報告、標準RotationConstraintは保持。汎用MA/PhysBoneは未対応。
- BuildLabは書き出し後に組込みavatarを除去しLoaderのみのPlayerへ。builds/lab/avatars/haolan.tcap（約26MB）、TanakaCapExporter.unitypackage。--avatarパス/F5読み込み。通常デフォルトはexe隣のavatars/haolan.tcap。
- results/phase3/package-smoke.png/log：外部パッケージの骨/表情/掌/透明画素/Spout登録のsmoke成功。com.unity.modules.assetbundle=1.0.0追加。初期module不足/CompressionLevel衝突/標準RotationConstraint拒否は修正済み。
- OBS32.2.2をresults/phase3-obs/appへ隔離コピー、公式Spout1.12.0 portableを導入。ユーザーの通常OBS設定は変更なし。検証OBS PID24940、認証設定はignored config内でチャットへ出さない。tools/obs_phase3.pyで127.0.0.1:4456へ接続。配信/録画開始はしていない。
- OBSはsenderを検出するが初回の実受信画像は透明一色。合格扱いしない。AlphaOutputをLateUpdate明示Renderへ変更してビルド中（session56015）。build後に--demo --obsで送信を再起動し、実OBS source/合成画像を再検査する。検証Player PIDはresults/phase3/obs-player.pid、停止はそのpid/commandlineだけ。ユーザーの別OBSは停止しない。
- 未完了：OBS実画素検証、パッケージ不良入力検査、完成文書・Gitコミット。通常肩face_ratio/腕front_projectionは維持。実写動画はGit除外のまま。

## 2026-09-12 — 新肩ヨー・腕奥行きを通常採用、フェーズ3へ

- ユーザーが新方式の肩ヨーと肘前後位置を採用し、次へ進むよう明示。tracking-settings.jsonはshoulder_yaw_mode=face_ratio、arm_depth_mode=front_projection。通常tanakacap-test.batを更新。各legacyで個別に戻せる。CLI省略既定legacyと設定ファイル経由の通常起動を区別する。
- 採用は全品質合格の意味ではない。終盤静止ヨー/腕の大きな跳び/左指等の未確認課題は残件として維持し、これらの微調整でフェーズ3への進行を止めない。前傾判定へモデル首/肩/胴体Zを使わない方針も維持。
- docs/IMPLEMENTATION_PHASES.mdへ6フェーズの現状を追加。1は主要比較/候補選択済み、カメラ要因の分離など残り。2は駆動実装・反復評価済み、部位の品質残件あり。3はSpout送信のみ先行、最小Exporter/ファイル形式/Runtime読込/OBS実受信が未完了。4は揺れ物・OBS併用性能/30分・実遅延未確認。5は配布UI/依存導入/非破壊汎用変換/ライセンス全体監査未完了。6は追加表情・指・視線を一部先行、仮想カメラ/コラボ/全身/軽量化は後日。
- 次の具体作業：haolanの書き出しコピー→最小バージョン付きパッケージ→外部ファイル読込の経路を作り、OBS Spout実受信を確認する。髪/服は現検証シーンにPhysBone互換を主張できる実装なし、自然な揺れはフェーズ4の主要残件。SPEC本文の旧ロスト待機姿勢/ローカルクロマキー案も最新指示へ整合した。

## 2026-09-12 — 画像の顔肩距離比によるヨー試行

- ユーザーはモデル首/肩/胴体深度を前傾判定へ使う案を拒否し、顔中心と肩中点の距離/顔サイズを指定。新方式は上顔面と肩の画像座標のみで量と保護を計算。方向の旧モデル肘深度補助は維持。docs/SHOULDER_FACE_RATIO_TRIAL.md。
- shoulder_yaw_mode=legacy（通常既定）、width_only（支持最大基準＋旧深度ゼロ化なし）、face_ratio（加えて顔肩比/顔姿勢が曖昧なら符号付き保持）。最大基準は5秒10支持・短縮禁止。旧基準更新を新経路へ重ねていない。
- results/comparisons/shoulder-projection-final完了。5187観測×3方式、旧全パケット差0、新方式はtorsoYaw以外差0。196テスト成功。顔肩比で接近/頭だけ区間のヨーを抑え、ひねり反応は増えたが、終盤静止案内に中央値16度が残る。成功/通常採用とは扱わない。基準最大は9.595→9.912、短縮なしを監査。
- 動画先results/avatar-videos/shoulder-projection-final。全編4本は185.033秒/5551frame、接近15秒/ひねり15秒/終盤静止10秒の抜粋3本も完成、全編復号成功。40/131/132.912/180秒の実描画を確認。report.json/excerpts.jsonはcomplete。tanakacap-compare-shoulder.batで開く。tanakacap-test-shoulder.batは設定不変の専用face_ratio試行、通常tanakacap-test.batは従来肩を維持し更新済み。
- 次：動画で終盤ヨーと左右方向を評価。顔肩比だけで姿勢と距離差が完全に分離できたと扱わない。未知の深度や単純な正面再校正を追加せず、基準不確かさ/肩点変動を切り分ける。実人物未確認。

## 2026-09-12 — 肩ヨーにも投影短縮の抑制があるか監査

- ユーザーは今回の腕と同じ問題が肩幅にもあるのではと相談。今回はコード/既存録画の調査のみ、動作変更なし。
- torso_yaw.pyは顔尺度補正した肩幅比からacosで角度を復元済み。腕のような方向正規化時の短縮消失と同一経路ではない。しかしbody3d.pyは最後にモデル肩深度差が25mm未満ならヨーを0にし、画像短縮の根拠をモデルZで棄却する点は共通。
- 基準肩幅もモデル肩深度差20mm以下・2D/3D肘整合・10安定観測で再取得する。モデルが回転を見落とすと回った幅を正面基準へ吸収する可能性がある（コード上の仮説、各更新の実姿勢は未ラベル）。ヨー方向は今回復元した肘ではなくモデル元XYZの肘差のまま。
- results/shoulder-yaw-width-audit.json。front-projection-trial-4/currentの5187観測を読取集計。torso_yaw案内区間の処理有効412中、幅由来15度超80、そのうち深度ゲートで0となるもの71。正解角度や全抑制が誤りである証明ではない。head_only区間でも幅由来15度超178/419があり、ゲート単純撤去で誤ヨーを増やす懸念がある。
- 次の案：肩幅の基準更新と角度採用を切り分け、モデルZを絶対の拒否条件にしない可逆比較。顔尺度補正は維持。正面付近の幅ノイズを角度へ大きく変換するacosの性質を考慮する。左右方向は幅だけでは決まらず、肘は符号の補助に限定し、新たな前方復元肘をそのまま肩の真値にしない。未実装/未採用。

## 2026-09-12 — 実写録画のGit混入監査

- ユーザーは実写動画がコミットされていた場合の履歴除去と、ローカル実体の継続利用を指定。
- 変更前20コミット/489オブジェクト/370blobを、到達不能分も含め検査。動画/画像/resultsパス、動画コンテナ署名、LFSポインターはいずれも0。非UTF8の2blobはKlakSpout.dllとパッケージ署名で、録画ではない。remote登録なし。履歴削除対象はなく、書換えは実施していない。
- results/git-media-audit.jsonに監査要約。camera.avi（5,791,849,388bytes）はresults/除外が適用され、実体は不変。一般的な動画拡張子も.gitignoreへ追加し、今後の管理対象外方針をAGENTS.mdへ記録。

## 最新：2026-09-12 — 前方作業域の投影短縮復元を可逆に実装

- ユーザー指定で既存録画の該当姿勢を使用。新方式はモデルを変更せず、画像上の短縮と常時校正長から奥行きを復元する。手首は肩よりカメラ側、肘/前腕を一律前方へ反転しない。詳細はdocs/ARM_FRONT_PROJECTION_TRIAL.md。
- tracking-settings.jsonのarm_depth_mode=front_projectionが最新試行、legacyで旧方式へ戻せる。顔/口/目/胴体出力は同一。掌/指アルゴリズムは維持するが腕の有効性によるゲート状態は変わる。
- results/comparisons/front-projection-trial-4が最終比較。5187観測で旧パケット差0、188テスト成功。results/front-projection-unity-v4の実Unity4場面成功。frame4246の肩相対手首Zは旧-24mm→新+297mm。正解精度の証明ではない。
- 新方式の顔尺度不足による保持243観測/側、肘変位p95は減るが最大跳びは少し増えた。逆肘/誤深度/震えの完全解消とは扱わない。SAM ViT-Hは既存オフライン品質参考であり正解ではない。
- 動画の最終出力先results/avatar-videos/front-projection-final。全編4本（185.033秒/5551frame）と25秒/30秒抜粋が完成、全編復号成功。85秒/142.95秒/151.71秒の描画を確認。report.json/excerpts.jsonはcomplete。旧front-projection-trial動画は中止/差し替え済み、配布しない。デスクトップtanakacap-compare-arm-depth.batは最終フォルダーを開く。通常tanakacap-test.batも更新する。

## 最新：2026-09-12 — 投影短縮が横曲げへ伸ばされる経路を確認

- ユーザーは腕前後運動が「真横で肘を曲げて顔付近へ手を持つ姿勢」になり、骨長適用で肘が前に折れると報告。後方検出を捨てる案を質問。今回は調査のみ、動作変更なし。
- docs/ARM_FORESHORTENING_AUDIT.md。Unityは骨ベクトルを正規化してアバター長へ戻すため、入力でZを復元しないと平面内に伸び得る。外側手でモデルZ35mm未満の時など、既存DepthAssistが短縮を復元しない経路がある。
- 読取監査tools/audit_arm_foreshortening.py成功。arm_depth案内区間2218骨観測中186が投影75%未満＋Z35mm未満。frame4246は右前腕の校正31.3cm/投影13.0cm/Z6mm、送信後も長さ12.9cm/Z7mm相当。人体実寸ではない。画像確認は行ったが、申告の横曲げ姿勢そのものの正解ラベルではない。
- 提案：投影短縮と骨長が整合するZを方向正規化前に復元し、曖昧な前後を前方へ制限。横曲げ姿勢自体の一律禁止や両骨Zの一律正値化はしない。校正/袖誤認/透視投影/後段IKも検証。後方動作を前へ反転するか境界停止かは未決定、前方専用モード未実装。


## 最新：2026-09-12 — 先行例を超える見通しと現行奥行き補正の再点検

- ユーザーは5090の10〜20fps事例を4090で超えられる見込みを疑問視し、モデルの奥行き出力と現行補正で改善しない理由を質問。回答方針：同じ品質/処理範囲のまま先行例を超える根拠はなく、達成を前提にしない。現実装の高速化余地と研究実装を超えることを区別する。
- 現行RTMW3Dも相対Zを返し、decode_simcc3d→BodyRetarget→DepthAssistで使用済み。SAM両方式はネイティブXYZを使用。どれも単眼学習推定であり深度センサーの実測ではない。
- コード確認：RTMW3DはZ分布576binから最大付近を選択（肩/肘/腰は局所補間）。Zピーク値を保持するが、多峰性/幅を候補評価へ使っていない。可視性は主にXYスコア、Zは有限性の確認であり、Z確信度の校正は未実装。
- 具体的な候補：body_geometry.py DepthAssistのfront_length_fitは上腕Z絶対値35mm以上なら逆符号候補を除外。過去の逆肘防止に寄与し得るが、モデルの誤った前後も保持し得る。今それが各不良frameの主因だと実証したわけではない。単純撤去して逆肘を再発させない。
- RTMW経路はXYに顔尺度の弱透視近似、Zにモデル相対深度を使う。手だけ接近した場合の投影整合、骨長の不確かさ、点の袖誤認、符号選択、Unity IKも切り分け対象。現記録の補正前相対肘Zは静止距離案内410ペアで現行左p95約279mm、SAM約3mm。正解誤差ではないが入力段にも大きな変動がある。
- 次の提案：同じ撮影でRTMWの復号/単位/軸/深度候補分布を監査し、補正の各段とUnity最終骨を比較。モデルZを絶対の符号制約にせず、2D再投影/骨長/肘関節/前姿勢を一貫した評価に使う案。SAMはオフライン参考、正解扱いしない。今回は調査と説明のみ、補正/モデル/要件は変更なし。
- 一次資料： https://raw.githubusercontent.com/open-mmlab/mmpose/main/projects/rtmpose3d/rtmpose3d/simcc_3d_label.py 、 https://raw.githubusercontent.com/open-mmlab/mmpose/main/projects/rtmpose3d/README.md 、 https://arxiv.org/html/2603.15603v1 。調査時projects/rtmw3dは404、正しいrtmpose3dへ訂正して確認した。


## 最新：2026-09-12 — ユーザーはViT-Hの品質を優先、実時間化/配布条件を調査

- ユーザー評価：SAM両モデルの肘は非常に安定、最後のViT-Hは肩もよく、質ならViT-H。今回の比較動画での評価。通常ライブの採用確定ではない。
- docs/VITH_REALTIME_DISTRIBUTION.mdに一次資料を確認した検討を記録。SAM Licenseは利用/改変/再配布の許諾あり、研究限定ではないが条件付き。MHRはApache-2.0。製品全依存の配布監査は未完了。
- Fast SAM研究は参考になるが公開手順DINO中心、5090実演65ms。4090/ViT-H/同じ肩品質で30Hzの証拠ではない。MHR→SMPL変換の倍率は本件に適用しない。
- 提案：ViT-H fullを品質基準に演算内容を保つ最適化→エンジン/演算統合→可逆な処理削減→ライブ＋Unity＋OBS評価。15Hz級の初期到達点案と30Hz検証は保証/確定要件でない。モデルパック分離案。顔/補正/通常実装は今回変更なし、実験も未実施。


## 最新：2026-09-12 — 3方式の全編動画完成、CPU/CUDA負荷を計測

- ユーザー指定の現行RTMW3D-X / SAM DINOv3 / SAM ViT-Hを全5187フレームで完了。results/comparisons/body-three-models、results/avatar-videos/body-three-models。個別3本とside-by-side.mp4、各5551frame/185.033秒、全編復号成功。横並び左から現行/DINO/ViT-H。85秒/148秒の実画像確認済み。人物品質合格やリアルタイム動画と扱わない。
- 基準全パケット差0、顔/口/目/距離と補正固定。SAM各5185予測/2欠測、投影最大差0.00022px未満。共通可視性の時間集計完了、SAMで左肘の大きな深度変動と指の棄却が減る。正解姿勢との誤差は未評価。docs/BODY_MODEL_COMPARISON.md。
- 全編推論/自動動画化/単独profilerの各セッションは正常終了。待機ジョブや追加ダウンロードは不要。重複実行しない。デスクトップtanakacap-compare-body.batで完成フォルダーを開ける。
- 最新質問はGPU低負荷・CPU2コア。CPU各ワーカー約1コア、CUDA実行あり。動画後の単独プロファイルで1frame約2.8〜3万kernel/2425同期、同期132〜147ms。MHR26回/314〜339ms。計測器負荷あり、GPU注釈と実演算を区別。4090演算能力の限界とは言わない。docs/SAM_PERFORMANCE.md。
- tools/profile_sam_runtime.py、tools/audit_sam_profile.py、results/sam-setup/runtime-profile/trace-audit.jsonで再現。初期summaryのCPU/GPU同名区間混同を訂正し旧版保持、元traceは不変。実4trace集計と新規3テスト成功。本体177テスト成功済み、通常追跡や補正を変更していない。
- 次：完成動画のユーザー評価を受け、MHR/動的処理/同期の実行経路を出力同等性を守って最適化検証。TensorRT・ネイティブMHR・低頻度併用は候補のみ、採用/30fpsは未決定。通常モデルは現行のまま。OBS実取り込み等の既存未確認事項も残る。


## 最新：2026-09-12 — ViT-H受領、2モデル全編推論と自動動画化を開始

- 追記：DINO全5187frame完了、5185推論/15555 CUDA backbone calls。ViT-Hは継続中。追加要求「GPU低負荷・CPU2コア」の観測はresults/sam-setup/observed-load.json（CPU約0.99/0.85コア、別5標本GPU平均74%/165.5W）。使用率だけでCPU演算律速かGPU待ちか断定しない。動画後に単独プロファイルを行うと回答。
- tools/profile_sam_runtime.py --output results/sam-setup/runtime-profile --wait-for-videos をSAM venvでセッション89447に起動済み。動画完成後にDINO/ViT-H各12frame、3warmup後2frameのCPU/CUDAトレースを取る。ログresults/sam-setup/runtime-profile.log。この結果の分析と文書更新も終了前に必要。診断計測は通常スループットと区別。

- 追記：ユーザーはリアルタイム処理の可否を質問。現在のSAM fullはDINO単独約530ms/フレーム（約1.9Hz）で、そのまま滑らかな実時間駆動は厳しいと回答。30fps動画はオフライン再生。エンジン最適化/身体only/高速モデルとの低頻度併用は提案のみ、未採用。動画作成の中止指示はない。
- 追記：全177pytest成功。共通の連続可視ペアだけで生肘深度/補正後/ヨーを集計するtools/summarize_body_comparison.pyを追加。欠測・案内区間をまたいだ差を除外するテスト成功。基準5187frameで実行検証済み。

- ViT-H重みはC:/Users/LLMTEST/Downloads/model (1).ckptに存在。原本を残しassets-source/sam-3d-body-vith/model.ckptへコピー。設定も受領済み。追加ダウンロード待ちではない。
- ViT-Hの20フレームCUDA推論成功（60backbone calls）、投影最大差0.000133px未満。共通MHR資産はDINOv3受領済みassets/mhr_model.ptを明示使用。docs/BODY_MODEL_COMPARISON.md。
- DINO全編セッション27698、ViT-H全編8766で処理中。出力はresults/comparisons/first-take-sam-dinov3 と first-take-sam-vith。ログresults/sam-setup/dinov3-full.log、vith-full.log。両モデル同時のため時間分布を単独性能にしない。
- tools/finish_body_comparison.pyをセッション97716で起動。両方全5187frame成功後、自動でresults/comparisons/body-three-modelsへ共通補正、results/avatar-videos/body-three-modelsへ個別3本と横並びを生成。ログresults/sam-setup/finish-body.log。完了後に実画像の目視確認、tools/summarize_body_comparison.py results/comparisons/body-three-models で共通可視性の集計、文書更新が必要。今は全編動画完成ではない。
- 状況確認：.venv/Scripts/python.exe tools/body_comparison_status.py。セッションが引き継がれない時は既存プロセスとログを調べ、重複推論を起動しない。
- デスクトップtanakacap-compare-body.batからrun-body-comparison.ps1を実行可能。実行中のrawがあれば重複開始せず表示。完成済みrawを再利用し、最終的に動画フォルダーを開く。既存test/capture/analyze/hamer batも更新済み。


## 最新：2026-09-12 — 3方式身体比較の接続完了、全編推論中

- ユーザー指定は現行RTMW3D-X / SAM DINOv3 / SAM ViT-Hを完了し動画化。通常追跡の採用モデルは変更しない。docs/BODY_MODEL_COMPARISON.md。
- SAMネイティブXYZ用の省略可能な入力口、MHR70対応、共通RTMW可視性条件を実装。既存基準全5187パケット最大差0、176pytest成功。顔/口/目線/距離と補正は固定。
- 先頭600フレームでSAM接続と実Unity動画検証成功、results/avatar-videos/body-smoke-600。全編完成とは扱わない。
- DINO全編はresults/comparisons/first-take-sam-dinov3へ処理中、ログresults/sam-setup/dinov3-full.log。開始10:32頃、約0.53秒/フレーム見込み。実行セッション27698（次の会話ではPID/ログで実行継続を確認）。途中のGPU動画検証との負荷重複あり。
- ViT-Hはassets-source/sam-3d-body-vithに設定のみ到着、重み待ち。PythonHFトークンなし。直接URLをユーザー案内済み。受領後チェックポイント監査→推論→共通補正→3方式全編動画へ進む。


## 最新：2026-09-12 — 2方式アバター動画完成、SAM資産受領・GPU初検証

- 依頼された現行対HaMeR指の動画3本をresults/avatar-videos/rtmw-vs-hamerへ作成。current.mp4、hamer-fingers.mp4、side-by-side.mp4、全5551frame/30fps/185.033秒。実Unity/lilToon描画、dt基準で時刻一致。docs/AVATAR_COMPARISON_VIDEOS.md。
- 初回の一括描画はスキニングが更新されず不適切だった。目視で発見・ユーザーへ訂正し、各描画前にUnityのフレーム更新を挟んで全編再生成。旧版はinvalid-stale-skinningへ隔離。最終版の腕・指を実画像確認し、全編復号成功。通常Unity受信の回帰成功、171pytest成功。通常追跡/補正は不変。
- SAMは承認・3ファイル受領済み、assets-source/sam-3d-body-dinov3へ配置。独立CUDA環境で生3D推論成功。全撮影35標本と単独20連続frameを実行。単独中央値約716msで重い。既定FOV・公式full設定。docs/SAM_INITIAL_VALIDATION.md。
- SAMを既存補正へ接続する身体アダプターと負荷分析は未完了。現行対HaMeRの動画にSAMは含まない。次はSAMの関節/左右/単位・速度内訳を監査し、身体比較へ進む。モデル・結果・環境はGit管理外。デスクトップbat更新。


## 最新：2026-09-12 — SAM待機中にHaMeR実推論・指だけの比較を完了

- docs/HAMER_COMPARISON.md参照。独立assets-source/hamer/venv（torch 2.11.0+cu128）で公式HaMeR重み/取得済みMANOを実行。原本は保持、ChumpyをNumPyへ同値コピー。Windows EGL importはワーカー内win32指定で解消。上流ソース/本体環境/補正は維持。
- results/comparisons/first-take-hamer：全5187 frame / 10370手出力、両手中央値38.02ms・p95 44.34ms、最大torch allocated約2.80GB。他モデル/Unity/OBS込み速度ではない。SAMは承認待ち。
- tools/compare_hamer_fingers.pyで3D指形状だけ交換。信頼度/境界/指補正は既存共通。基準の指再計算は全frame不一致0、指以外のpacket一致。right_fingers_faceの有効判定は左1947→2085、右2025→2085（各417×5）。有効率は正解率ではない。ライブ切替は未実装、既定モデルを変更していない。
- 実Unityで600packet処理、600監査行を確認。指骨の品質合格とはしない。171pytest成功。デスクトップにtanakacap-compare-hamer.bat追加、既存bat更新。追加撮影不要。次は開閉/欠測のアバター比較と可逆なライブ接続、身体はSAM取得後。
- first-takeの2D対照は最終packet全5187frame一致。距離stableは静止案内2区間の隣接変化p95約77%/74%減、緩やかな揺れは残る。左肘生深度の大きな飛びを確認。tools/audit_comparison_input.pyで再現、補正追加はしていない。


## 最新：2026-09-12 — MANO受領、SAM承認待ち

- ユーザーがプロジェクト直下へ保存したMANO_RIGHT.pkl（3,821,356 bytes）をassets-source/mano/MANO_RIGHT.pklへ移動。SHA256: 45d60aa3b27ef9107a7afd4e00808f307fd91111e1cfa35afd5c4a62de264767。pickleを実行せず命令列からMANOの主要キー7種を確認。HaMeRでの読み込み・推論成功はまだ未確認。モデル原本はGit管理対象外。
- SAMはユーザー申告でアクセス申請済み・著者の審査待ち。取得済みとは扱わない。HaMeR公開重み・独立CUDA環境・共通補正への接続が次の作業。
- 撮影済みresults/comparison-takes/20260911T235327-031115Zに対するresults/comparisons/first-take/report.jsonはcompleteを確認。現行と2D対照の処理完了であり、3D交換や人物品質合格ではない。詳細監査・結果報告は未完了。実行中にORTプロファイル記録上限の警告があったため、GPU証拠の対象範囲にも注意して監査する。
- 端末ではMarkdownリンクを開けないため、ユーザー向け案内には生URLを添える。不要とされたopen-model-downloads.batは削除済み。



## 最新：2026-09-12 — 撮影前の解析起動を案内へ変更

- 撮影フォルダーがまだない状態で解析用バッチを開き、Get-ChildItemエラーになった。存在確認を追加し、未撮影/完了テイクなしでは撮影用tanakacap-compare-capture.batの案内を出して正常終了する。カメラや録画は自動開始しない。
- 実際の未撮影状態でanalyze起動の案内・正常終了を確認。推論/補正/録画形式は変更なし。デスクトップbat更新。

## 最新：2026-09-12 — 比較用撮影・固定入力ランナー

- ユーザーが一括実装を指示、準備後に自分で撮影する。SAM/MANOは未取得と回答、登録・申請手順を案内。撮影は開始ボタンからで、今回こちらは実カメラ録画を行っていない。
- capture_lab/comparison_capture.py：日本語の約3分ガイド、開始前プレビュー、3秒カウントダウン、中断/エラー、元映像＋実取得時刻＋動作ラベル/設定/ハッシュ保存。保存はHuffYUV AVI可逆、音声なし、プレビューのみ鏡像。開始時30GB空き要求。FFV1は合成720p約20.7fpsで撤回、HuffYUV約150.5fps・全画素一致で採用。容量が大きいことを案内。
- capture_lab/comparison.py：同じ素材/時刻/ROI/顔・目線・口・距離を固定し、既存BodyRetargetへ接続。baseline＋DWPose-l＋新規RTMW-Xの2D対照、指理由/肘/距離/yawを動作別集計。2D対照では3Dは現行のまま、3D交換済みと扱わない。設定と制御コードのハッシュ、素材整合/中断拒否、CUDA実行イベント確認あり。
- tools/compare_external_model.py：SAM/HaMeRの独立CUDA生出力ワーカーを準備。重み/環境不足で実行未検証。共通補正への3Dアダプターは実出力の単位/関節/信頼度を確認してから接続する未完了項目。ViTPose未導入、WiLoR条件確認待ち。全候補の比較完成と誤報しない。
- 171pytest成功、Tk PPM表示（カメラなし）、合成18frameのbaseline/DWPose/RTMW-X CUDA＋虹彩検証とレポート生成、Unityでreplay.jsonl実受信成功。results/comparison-setup/gpu-smoke、unity-replay.png。人物品質/実カメラ録画は未検証。初回の文字コード/試験親dir不足は修正済み。
- 最新既存621frameで左指有効203/168/164/145/141、右324/297/291/299/317。左palm_basis停止1910指判定分。基準不成立が多いが、区間正解なしで原因確定/修正済みとはしない。
- デスクトップtanakacap-compare-capture.batで撮影、tanakacap-compare-analyze.batで最新完了テイクを解析。従来tanakacap-test.batも更新・維持。docs/COMPARISON_CAPTURE.mdに操作/素材/取得待ち/未完了範囲。次は撮影された素材の品質・指/肘の停止段階を監査し、SAM/MANO取得後に独立環境・3D接続を検証する。

## 最新：2026-09-12 — 顔距離安定化とモデル比較計画

- 最新評価：目線/口/掌はおおむね良い。顔距離は静止時ガタつき、胴体yaw不良、腕の暴れ、左指停止、右手を顔横で開閉すると肘が前後へ動く。全追跡合格とはしない。
- 顔距離専用face_distance_filter=stableを追加、legacyで旧処理。相対約2%の方向ゲート＋差に応じた時定数0.22〜0.06秒、欠測保持/復帰連続。FaceScale/腕長校正/頭/口/目線/掌は不変。167pytest、2記録の同条件再処理で観測差p95約67%/36%減。実人物の見た目は未確認。docs/FACE_DISTANCE_STABILITY.md。
- 次はユーザー指定のモデル比較へ。既存補正を固定し、座標/左右/信頼度のアダプターを明示して部位別に差し替える。指はRTMW3D由来なので2Dモデル交換だけを指の比較と扱わない。まず左指の停止段階と右肘の生/補正後を監査する。
- docs/MODEL_COMPARISON_PLAN.mdに候補：現行、DWPose-l、RTMW-x、ViTPose++-H WholeBody、SAM 3D Body、HaMeR、条件付きWiLoR。3D身体/手候補を優先。新モデル導入/比較は未実施。元カメラ画像のないjsonlだけでは再推論不可、共通カメラ素材が必要。無断録画はしない。
- OBS/変換のフェーズ3は未完了のまま、今回の距離とモデル比較を先に進める。デスクトップbat更新、Python変更のみでUnity再ビルド不要。

## 最新：2026-09-12 — ピッチによる口角誤変形の解消を確認

- ユーザーが最新実装を動かし、ピッチで口角がおかしくなる問題の解決を確認した。head_pose_mode=pnp / head_pitch_gain=1.8 / mouth_lip_depth_scale=1.5を維持する。口角の当該症状の確認であり、目・腕・胴体の全品質合格とは扱わない。
- 次はフェーズ3の残作業へ戻る。優先はローカルOBSでSpout透過受信・合成の確認（送信/アルファ生成は実装済み、実受信は未確認）。続いて最小Unity変換プラグインと書き出したアバターファイルのランタイム読み込み。髪服の揺れ物も未完了。仮想カメラ/コラボは後日要件。
- 今回は評価状態の文書更新のみ。コード/設定/ビルドは変更なし。前回162pytest成功を維持、新たな実行試験は行わない。

## 最新：2026-09-12 — 残る口角ピッチ連動

- ユーザーが頭ピッチ改善を確認。下向き口角上昇/上向き下降は残る。頭推定を維持し、唇テンプレートの平均奥行きを固定して奥行き差のみ1.5倍にする試行。mouth_lip_depth_scale=1.0で前回へ、範囲0.5〜2。顔/目モデルと口モーフは不変。
- 223024記録1210frame、正面寄り/閉口935frameで口角とsin(pitch)相関が左0.442/右0.488から−0.109/0.012へ。tools/audit_lip_depth.py、results/lip-depth/comparison.json。正解表情はなく、相関低下は精度保証ではない。162pytest成功、実人物の見た目未確認。


## 最新：2026-09-12 — 頭ピッチと口角の投影分離

- ユーザーが上下向き不足と口角誤上昇を指摘。旧は鼻/両目の単一比でpitch、画像上の唇中央/端の高さ差で口角。鼻/眼端9点の標準顔PnPへpitchを変更、口点の奥行きへ逆投影して正面座標で輪郭判定。yaw/rollとRTMW/目モデルは維持。
- head_pose_mode=pnp（legacyで両方旧処理）、head_pitch_gain=1.8（0.5〜3）。正面寄り安定10観測を基準、出力±40度。個人形状/カメラ未校正の近似。PnP不良はpitch保持/輪郭更新停止、他の顔処理は継続。
- 221714の696frameを同じ開始/観測間隔で新旧再生、口角0.95超は左217→0/右262→88。初回比較の左210は当時の送信基準なので最終再生比較とは違う。pitch新範囲−15.75〜17.05度。残差/成立率/角度範囲で精度を断定しない。
- 154pytest、Unityビルド/既存motion、上下25度の実Head回転到達検査成功。幾何再生中央値0.52ms。results/head-pose/final-audit.json、motion/up/down。実人物未確認。
- docs/HEAD_PITCH_MOUTH.md、標準顔29点+Apacheライセンス、SPEC0.39/進捗/Desktop bat更新。Gitへ保存。sandbox helper障害のため今回も環境の昇格手順を使用。


## 最新：2026-09-12 — Git開始・目線強調/カメラ復帰・顔高さを保つ接近

- ユーザーが適宜Gitコミットを指定、基準a762348作成。今後も検証後ローカルコミット。生成シーンはignore（BuildLab再生成）、原本/models/results/cacheは既存ignore維持。外部pushなし。
- 最新215947は813/1003目線有効、横5〜95%−4.08〜3.54度。感度2→4、上限0.5〜6、最大変形は不変。小入力実画像の水平端間約4.2→8.3px。検出モデル変更なし。
- ロスト時は顔位置/頭向きからカメラ方向を計算しゆっくり復帰、F4 OFFは従来中立。実方向を頭±10度で検証。
- framed既定：距離要求の35%を前傾にし後傾15/前傾35以内、残りを全体移動で補い顔viewport高さを保つ。表示距離比0.5〜2。腰固定ではなく見せ方の試行。seatedで前回へ、translate/OFF維持。「口角」は「広角」の訂正、口角/FOV変更なし。
- Unityビルド/実Player回帰・カメラ方向・顔高さ/距離/保持検査、PNG10枚の感度比較成功。results/framed-gaze/verified.log、results/gaze-render/pixel-check-1789164824135848200。実人物改善/OBS受信は未確認。
- docs/FRAMED_GAZE.md、SPEC0.38、進捗/デスクトップ更新。Git初期化後sandbox helper起動エラー継続、編集ツールも不可のため権限昇格手順で作業。通常権限の所有者差はコマンド単位safe.directory指定、グローバル設定変更なし。


## 最新：2026-09-12 — 接近の横飛び・肘の取り残し

- 最新214959は1284frame、比0.8未満536、右腕無効323/左0、ArmHeld各1。接近中yawは−46.75〜52.96、最大観測差64.45度。正解姿勢なし、全原因断定禁止。
- 着席TorsoRotationをRx(pitch)*Euler(0,yaw,roll)へ。旧Eulerが前傾をyaw方向へ向ける経路を除去。Spine/Chest両方。通常胴体/OFF/translate式は維持。
- 胴体更新の親回転差でlowerUntwistedワールドキャッシュを移送。ArmHeldをpacketで受け、保持時は旧目標を再駆動せずローカル保持で胸と動く。見えている腕のカメラ基準入力に追加前傾はしない。
- 実Player新検査：yaw±45固定の接近で横変位約2.3e-8m、保持肘の胸相対/ローカル回転、欠測前腕cache親相対不変。既存motion/視線/口/腕/着席回帰とビルド成功。results/seated-coupling/verified.log。生yaw急変は未修正、実人物の改善未確認。
- docs/SEATED_COUPLING.md、SPEC0.37/進捗/Desktop bat更新、before-seated-coupling-20260912.zip保存。Python変更なし。

## 最新：2026-09-12 — 全体移動から着席前傾へ

- ユーザー希望は座った腰を固定して前傾接近。既定face_distance_mode=seated。Spineを支点とする頭の軌道からピッチを計算し、既存胴体ピッチへ加算せず置換。Spine/Chestの絶対ピッチを合わせる。頭はカメラ基準、ヨー/ロール/腕は従来どおり。
- 最新214143は634frame中630距離有効、生比最小0.4634、197frameが旧0.75制限。今回の停止主因はロストでなくクリップ。Pythonクリップ撤去。新方式は後傾25/前傾65度の試行限界、GUIでANGLE LIMIT/ロスト保持を区別。腰固定の到達距離には限界が残る。
- translateで旧全体移動、face_distance_enabled=falseでOFF。新snapshotにseatedLeanDegrees/seatedLeanLimited。入力防御比0.34〜2.86。欠測位置保持は前傾保持へ。
- Python146成功、Unityビルド/既存回帰/実骨固定骨盤・頭の前下方軌道・頭向き・欠測成功。比0.8で実頭約0.184m接近。results/seated-lean/final.logが最終。near画像目視、legacy実表示成功。初回は検査の再有効化忘れで失敗し修正。実人物未確認。
- docs/SEATED_DISTANCE.md、SPEC0.36、before-seated-lean-20260912.zip、進捗/Desktop bat更新。目線モデル/設定は今回変更なし。

## 最新：2026-09-12 — 目の輪郭基準・顔距離でアバター前後移動

- ユーザー「続けて」、実カメラへ近づくとavatarも近づく機能を希望。新FaceDistanceがRTMW鼻筋/眼端のFaceScaleを独立使用し、起動後正面寄り10観測の基準から距離比を3/1 gate経由で送信。0.75〜1.5、Unity全体をカメラ軸沿いに平行移動、欠測位置保持。腕尺度や原本倍率は変更なし。
- 視線は同モデル輪郭0/8基準へ。公式グラフのleft/rightは画像側で、旧反転が逆と確認、人体右59〜64は反転なし、人体左65〜70は反転ありへ修正。顔/口/瞬きの対応は不変。旧説明より本項優先。
- settings gaze_reference=contour（legacyで旧基準/旧反転へ）、face_distance_enabled=true（falseでPlayer移動OFF）。感度2/目線ロスト復帰/共通4観測は維持。新旧offset/反転/cornersを診断へ。実人物の改善は未確認。
- Python146成功、CUDA103call/39243events/CPU0、合成5.27ms中央値。Unityビルド/motion、距離接近/離反/欠測/OFF、UDP+実画像near/far/disabled成功。results/gaze-contour、詳細docs/GAZE_CONTOUR_AND_DISTANCE.md。SPEC0.35。before-gaze-contour-distance-20260912.zipから戻せる。Desktop bat更新。

## 最新：2026-09-12 — 目が少し動く状態の入力監査

- ユーザー評価が「少し動く」に変化。最新212310は737frame中610目線送信有効、検出後と送信角度の不一致0。実Player受信はこの記録にない。
- 生/送信の横5〜95%範囲−9.07〜3.14/−8.97〜2.97度。平滑化で振幅全消失ではない。左右眼相関横0.13/縦0.38、頭±10度でも0.26/0.41。片寄りと左右の不一致が調査候補だが、正解視線なしで精度や原因は断定しない。
- 間隔中央値66.71ms、目線処理13.42ms。4観測の窓は約200ms、実測遅延ではない。モデル間のROI/虹彩基準のずれを次に比較。顔の置換はしない。
- tools/audit_gaze_record.pyを最新実記録で実行しresults/gaze-record-audit/212310.jsonを保存。docs/GAZE_INPUT_AUDIT.mdに根拠/候補/限界。runtime/gain/modelは変更なし、SPEC0.34維持。検出改善を実装済みと扱わない。

## 最新：2026-09-12 — 瞳の最終画像比較・表示感度2倍

- 再度「目が動いて見えない」。顔は良好で別系統維持という直前の相談を尊重、顔/目のモデルは交換していない。最新211324の555frame中471有効、yaw−11.03〜9.55/pitch−6.85〜2.43。静止顔+眼だけの合成入力では最終描画の停止は再現しなかった。本人の当時の表示状態や正解視線は未記録、全原因の断定はしない。
- 感度の低さへ試行対処。tracking-settings.json gaze_gain=2.0、1.0で前回。Player --gaze-gain、launcherとsmokeが対応。最大角度/移動範囲（横4mm/縦2.5mm）、ロスト復帰速度は不変。姿勢保持/口も不変。
- tools/check_gaze_pixels.py：固定頭/顔、±10yaw/±6pitchを感度1/2で各5PNG生成し、緑色虹彩の実画素重心を左右別に計測。横端間5.17/5.07→10.34/10.23px、縦3.32/3.14→5.75/5.69px。頂点投影だけの確認から改善したが、検出の正解を示すものではない。
- capture_lab/gaze.py：左右別ROI内iris座標、眼幅、offset、採用後角度を数値診断に追加。非有限値はnull。原画像なし。Unity snapshotにgazeYawApplied/gazePitchApplied、smokeでpacketからの到達を検証。
- 最終142pytest成功、Unityビルド、verified.logの既存回帰/範囲外不変/復帰成功。画素比較reportはresults/gaze-render/pixel-check-1789161541640291200。最初は顔だけfixtureを許さないsmokeが失敗→対応。motionは増幅後の3秒残差を固定0.05度で見る旧試験が失敗→99.7%減衰の仕様で確認するよう修正、runtime速度は同じ。途中失敗は成功扱いしない。
- docs/GAZE_RENDER_AUDIT.md、SPEC0.34/進捗、before-gaze-sensitivity-20260912.zip、Desktop bat更新。次は左右別診断と実表示から検出自体の追従を確認。OBS/変換の残作業も維持。新モデルへ勝手に顔ごと置換しない。

## 最新：2026-09-12 — 目の表示減衰を修正・モデル比較調査

- ユーザーは目が全く動かないと評価し、現モデルの根拠/他モデルの情報を要求。最新205903の453frame中389frameはgazeTracked/faceTracked有効。yaw−12.97〜9.38/pitch−6.08〜1.77、packet最大2124bytes。検出全停止ではない。reportはrunningのまま、終了集計未完了と扱う。
- HAOLAN Bodyの各眼1089頂点の眼骨重み合計38.17855、平均/最大約0.035058。子眼骨.001は影響0。旧±15/±8度の瞳投影移動は最大2.35〜2.44px。前回は実Bakeの非ゼロだけ見ており表示量の検査不足。
- MakeGazeShapes：作者「瞳小」対象と眼骨影響の共通部分だけに横4mm/縦2.5mmの左右上下独立モーフを作る。BodyはMakeMouthShapes後の実行時コピー、原本/骨重み不変。支持を最大眼重みで正規化。iris表示時は眼骨を中立にして二重適用しない。非対応avatarは旧bonesに代替。汎用avatar対応を保証する機能ではない。
- tracking-settings.json gaze_render_mode=irisが既定、bonesで旧方式へ戻る。Player --gaze-bones、smoke --gaze-bones追加。gaze_enabled=false/F4/ロスト時の緩やかな正面復帰は維持。GUIにF4状態/方式/角度追加。元モデル・推論パラメーターは変更していない。
- 同じ合成入力で瞳最大6.38〜6.40px/3.43mmへ。実Bakeの瞳方向/量、対象外1μm以下不変、ロスト/OFF、旧bones方式、既存腕/口回帰成功。results/gaze-audit/verified.log、reversible.log。recorded-look.pngは実記録の視線値を固定し頭等を変更した表示確認。実人物での改善は未確認。
- モデルは最高精度比較ではなく独立追加しやすさで選んでいたことを明記。Face Landmarker V2、L2CS-Net、3DGazeNet、UniGaze、GazeTRを一次資料で調査。推奨比較方針/出典/配布条件と未測定部分はdocs/GAZE_MODEL_REVIEW.md。新モデル導入はしていない。UniGaze/GazeTRの非商用表記、3DGazeNetのライセンス未確認を配布採用済みと扱わない。
- before-gaze-audit-20260912.zip、SPEC0.33、Desktop bat/進捗文書更新。次は実入力の新表示品質とモデル比較。OBS実合成/最小変換の残作業も維持。

## 最新：2026-09-12 — 可逆な虹彩目線試行

- ユーザーは追加要件として目線の調査と可能なら可逆な実装、ロスト時はゆっくり正面へ戻すことを指定。既存の全身保持ルールの例外は目線のみ。
- capture_lab/gaze.py、ONNX虹彩モデル（Google由来/PINTO変換）を追加。64×64眼ROI、CUDA必須、片眼6.54ms中央値/7.06ms p95の合成推論、CUDAイベント39243/CPU0。実人物両眼負荷・精度は未確認。既存モデル/平滑化は置換せず3/1 gateを追加。
- HAOLANはHumanoid eye未登録のため頭配下LeftEye/RightEyeへ接続。頭基準の横±20/縦±12度、眼球中立の相対表現。欠測は時定数0.5秒（約1.5秒で95%復帰）、送信停止時は既存0.3秒タイムアウト後。他の部位は保持。
- tracking-settings.json gaze_enabled=trueでデスクトップから試行有効。falseで推論ごと戻る。F4は反映だけを切替。旧packetも正常、眼原本の編集なし。数値gaze診断/packetとgaze_msを記録、RGB保存なし。
- Python141件成功、Unityビルド/実Player既存回帰、目方向/欠測復帰/OFF、眼の実Bake約1.3mm変位を確認。results/gaze/verified.logとlook-final.png（合成入力）。最初のeye未登録エラー、目も止まる旧テストのエラーは修正済み。目のみ保持テストから除外し別の復帰テストで確認。
- カメラ短時間実行20260911T205223-803057Z-rtmw-l-384は60frame完了したが有効顔なしで虹彩0call。合格と扱わない。カメラのsandbox実行は失敗し権限付き再実行。入力品質/眼鏡/頭動作の実評価が必要。
- docs/GAZE_TRIAL.mdに調査根拠、制限、戻し方。before-gaze-20260912.zip、SPEC0.32、Desktop bat更新。OBS実合成/最小変換は前回の残作業のまま。

## 最新：2026-09-12 — 口角ガンマ・横寄せ4mm・Spout透過送信

- ユーザー指定：弱い口角変形を抑えて強い変形を残すカーブと過大な口横移動の抑制。直前のOBS確認でクロマキー案を撤回しアルファ透過へ進むと回答済み。下記旧OBS準備手順より本項を優先。
- ExpressiveCornerに符号付きガンマ2（x*abs(x)）。±0.2→±0.04、±0.5→±0.25、±1→±1。左右独立、開口時上げ最大90%抑制、中立下げ30%を維持。遅延の追加なし。横寄せ最大10→4mm、作者の口移動対象と唇上下14mmの支持を維持、顎/首を動かさない。
- AlphaOutput：別カメラ→1280x720 ARGB32/4xMSAA/透明黒→KlakSpout Texture+keepAlpha。通常送信のCPU ReadPixelsなし。二重描画の負荷は未計測。F3/--obsはGUI非表示のみ、送信は起動時から有効。マゼンタ処理削除。
- 公式npm KlakSpout 2.0.6をSHA512照合してembedded packageへ導入、Unity2022.3/D3D11対応。docs/THIRD_PARTY.md参照。OBSはPCにあるがSpoutプラグインは通常のインストール先に未検出。OBS側の導入/設定変更は未実施。手順はdocs/OBS_LAB.mdへ訂正。
- 初回全面透明はCopyFrom後のカメラlocal位置/回転/ビュー行列を明示し解消。送信追加後の終了コード3221225477はwantsToQuitで送信停止後2frame待ってから終了するよう修正。失敗画像を合格扱いしない。
- 最終results/gamma-alpha/spout-msaa.png/log：ビルド、実Player motion、口実Bake左右4mm/範囲外不変、非対称口角、既存腕/掌、Spout登録、正常終了が成功。RGBAは透明654952/不透明263252/中間3396pixel、画像目視済み。登録とRGBA検査はOBS実受信の証明ではない。--obs smokeはbatchmodeを外して送信を実行する。
- before-gamma-alpha-20260912.zip、SPEC0.31、進捗/デスクトップbat更新。実人物表現品質は未確認。次はOBS受信導入/実合成/輪郭と色の確認、最小Unity変換/読み込み。腕の暴れは既知課題、追加補正なし。フェーズ3完了ではない。

## 最新：2026-09-12 — 口横寄せを抑制・上半身構図・フェーズ3着手

- ユーザーは口の横寄せが過大で壊れやすいため抑制、表示をおなか〜ケモミミへ寄せるよう要求。腕の暴れは残るが有効な案がなければ次へ進めたいと指示。追加補正は入れず、既知の品質課題として残してフェーズ3へ着手。
- 横寄せ最大16→10mm（約38%減）。唇限定/顎首の範囲外不変、左右独立モーフは維持。実Bake両方向10mm検査成功。
- BuildLab表示カメラ：腹部基準をhips/chest間から、上端をKemomimi実頂点＋35mm余白から取得。FOV35度、画面範囲Y0.713823〜1.312076、距離0.948709。旧距離1.65より寄り、1280×720画像を目視して腹部〜耳先を確認。カメラ映像の取得範囲/推論設定は変更しない。広げた腕は左右に出得る。
- F3/--obsでステータス非表示とマゼンタ背景へ切替。再F3で元の背景/表示設定へ。緑背景の試作はHAOLANの緑の瞳を抜く恐れから不採用。OBS内の取り込み確認・アルファ出力・汎用変換はまだ未実装/未検証。docs/OBS_LAB.md参照。
- Unityビルドとmotion検査、OBS用Player画像を検証。results/upperbody-framingへ保存。腕修正はしていないので今回の成功を腕品質改善と扱わない。
- SPEC0.30、AGENTS/PROGRESS更新、Desktop bat上書き。次はフェーズ3の最小変換プラグイン/ファイル読み込みとOBS実取り込み。フェーズ2の人物品質を合格に書き換えない。仮想カメラ/コラボは後日要件のまま。

## 最新：2026-09-12 — 口だけの横移動・外側後方腕の曲がり面・肩幅証拠の確認

- ユーザーは左肩前方と外側後方手の逆折れ継続を報告。横寄せで顎/首が変形するため「顔の中の口の位置だけ寄せる」「余計な部分を掃除」を要求。前回の全renderer空間変形は撤去した。
- 最新200402の1800frames：外側の左1345frames中、モデル生上腕が前474、補正後前425。右1343中118/105。生が35mm以上後ろ→出力35mm以上前は左0/右3。CrossBody残留は左右0。今回は前回の交差ゲート残留ではなく、推定肘自体の前方化が主な未解決経路。全ての前方肘が誤りという正解ラベルはない。
- Unity外側後方prior：手が同側外方（入力X）、CrossBody=0、WristInFront=false、手首目標が肩より高すぎない（rootY<.12）、胸郭前方への投影が−.025未満なら、骨長と到達可能な手首位置を固定した肘円周上で肘が手首より後ろに来る解を選ぶ。生上腕Zを反転する処理ではない。腕を上げた場合や内側の手には適用しない。人体の全姿勢を網羅しない着席用prior、条件の誤分類/到達不能時の限界は残る。
- 肩：顔相対肩幅由来の量を、独立肩深度差が25mm未満なら採用せずヨー0へ。量は肩幅、方向は肘という分担を維持。初案の肩深度符号と肘符号の一致条件は既存要件/テストと衝突したため撤去。肩深度が平坦に誤推定される場合、実際のひねりも抑える可能性がある。幅の基準再取得は前回の条件付き方式を維持。最新記録で新条件false1206frames（元から中立のframeを含む）、yaw5/50/95%点0/0/18.26度。正解精度の証明ではない。
- 口：作者の口角モーフ領域を全meshへ広げていた処理を削除。作者「口_上」の変形対象・縦変形量を横変位の支持として使い、重み付き唇中心の上下6mmは維持、14mmまで減衰して外は厳密ゼロ。元から口角モーフのあるBodyだけを複製。全身/髪/衣服を複製して横移動させない。対象587頂点、root中心Y1.033992。最大16mmを維持。原本の変更なし、舌制御の復活なし。
- 口モーフはTC_MouthShiftLeft/Rightの左右独立、正の重みへ整理。旧TC_MouthShift単一モーフ/負重み依存は撤去。生成後にrendererへmeshを再設定して形状追加を反映。最初の実Bake検査は負側0mmで失敗し、符号付き複数frameでも解消しなかった。左右分離と再設定後、両側最大16mmを確認。どちらの変更単独が原因かは分離していない。
- 検証：pytestはtestsディレクトリを明示、workspaceの専用basetemp、cacheなしで138件成功0.69秒。途中のpytest全域探索は過去のpytest-tempの権限で収集エラー、製品コードのテスト失敗ではない。Unity Editorの骨長/終点/後方肘/唇マスク、実Player ACTUAL_OUTWARD_BACK_OK、BAKED_LIP_ONLY_OK左右（対象外/帯域外の実頂点変位1μm以下、最大16mm）、既存掌/顔回避/交差腕/口角のmotion検査成功。
- 成果物results/mouth-isolation：baseline.json/comparison.json、reprocessed、motion-isolated.png/logが最終成功、replay.pngは最新1800packetの再生。motion-final/motion-verifiedは途中失敗で合格扱いしない。最新実記録の正しい奥行きや口の表現品質は未確認。
- before-mouth-isolation-20260912.zipから戻せる。SPEC0.29/AGENTS/PROGRESS更新、デスクトップbat更新。次は口横寄せで輪郭が保たれるか、後方外側手の誤分類、肩の過抑制/片寄りを評価。今後はモーフ重みだけで口の成功を主張せず、実Bake頂点検査を維持する。

## 最新：2026-09-12 — 肩の基準復帰・外側への補正残留・口内横寄せ・頭の回避

- ユーザーは全体の改善を確認。左肩が前に残る、外側の手で肘の前方化が再発、顎の貫通、口横寄せの強調、頭に手が埋まる問題を報告。
- 最新195028の1626framesを監査。ヨー中央値20.49度、顔相対肩幅比中央値0.895。後半は肩深度差中央値9mm程度でも比0.909/ヨー22度。正面の基準誤差が残る経路を確認。最初は肩と肘の深度差とも15mm未満が10回続けば方向を解除する案を実装したが、記録で発火0件のため撤去。
- 最終：ShoulderWidthReference.observe_frontalで、肩深度差20mm以内・既存2D/3D肘照合が一致・有効な顔尺度・5秒内10連続候補の補正幅ばらつき5%以内なら顔相対正面幅を再取得。永久最大更新ではない。回転量は引き続き顔相対肩幅から、方向は肘のみ。独立肩深度も誤る場合に誤校正し得る。再計算で11回更新、ヨー5/50/95%点−5.82/0/27.91度。正面正解ラベルはなく、精度合格と扱わない。
- 外側手でもCrossBody>0が元記録左16/右23frames。ゲートのdeadband内に0.0023等が残り得る。現在の有効手首が同側肩より外ならcross_motionをresetし、DepthAssistのfront時間保持も解除する。再計算で外側かつ新規追跡のCrossBody>0は左右0件。モデルの肘点自体が前方なら別問題であり、これだけで逆折れ全例解消とはしない。
- 舌検出/舌駆動のコード・ファイルはcapture_labとUnity実装に残っていない。舌を再実装/原本から削除していない。顎貫通の候補として、旧aaモーフの変形量から作る横寄せが唇/歯/口内で異なる問題を修正。作者口角モーフから口領域を求め、全rendererへ同じroot空間の横移動場を適用。背面は深度で減衰。別メッシュの歯/口内も範囲内なら動く。最大横寄せ8→16mm。原本未変更。貫通物の正体は画像で特定していない。
- ClearFace：目ボーン中点の後方40mmを中心（無ければ頭ボーン上方90mm）、手の厚み込み半径180mmの近似球。目標手首が内部ならXYを保ってカメラ側表面+5mmへ出し、同じ骨長IKで再計算。補間途中の埋まりは解へ戻す。届かない目標や髪/指先等を網羅する厳密衝突ではない。欠測の最後の姿勢保持は継続。
- pytest137件合格1.13秒。初回は既定TEMP/pytest_cacheの権限エラー1件（136成功）、workspace内--basetempとcache無効で全件通過。再試行時は同じbasetempを使い回さず専用名にする。Unityビルド成功、Editor FACE_CLEARANCE_OK、実Player ACTUAL_FACE_CLEARANCE_OK（左右）と既存交差前腕/口/掌検査成功。最終1626packetの実Player再生も成功。
- 成果物results/face-clearance：baseline.json/comparison.json、reprocessed-final、motion-final.png/log、replay-final.png/audit。reprocessedは不採用の最初の正面解除案なので最終と混同しない。tools/audit_face_clearance.pyで再生成。before-face-clearance-20260912.zipから戻せる。
- SPEC0.28/AGENTS/PROGRESS更新、デスクトップbat上書き。次は肩の再校正が実姿勢を消さないか、外側ひじ、口内/顎の貫通、横寄せ量と頭回避の見た目を評価する。口開け時の上げ抑制/への字強調、指、掌最短回転、顔尺度、画面外保持は維持。

## 最新：2026-09-12 — 開口時の口角上げ抑制・口の横寄せ・交差腕の腹部回避

- ユーザー確認：前回の肘の逆折れは解消、手が後ろへ来にくくなった。への字口は現在の誇張量でよい。残課題は開口時の口角上がり（映像には忠実だが表現として抑えたい）、閉口した口の横寄せ、反対側へ手を持ってきたときの前腕の腹部埋まり。
- Unity ExpressiveCornerは正の口角だけ `1−0.9*smoothstep(opening/0.65)` 倍、最大90%抑制。負の口角とCornerDownの既存中立30%は維持。旧fallback笑顔にも同じ抑制。への字の強さを下げない。
- mouthShift追加。左右口角の中点と鼻翼31/35の中点との差を眼軸へ投影、眼間距離で正規化。初期閉口10観測の中央値を引き、1.5倍、±1へ制限。既存3平均stride1ゲートで処理。頭ロール・全体移動には不変だが、強いヨー/遮蔽の影響は残る。Unityは作者aaモーフが動かす領域に最大8mmの横変位を持つTC_MouthShiftを実行時クローンへ生成。正が本人左＝root−X。符号付きweightで両方向、口開閉は変えない。原本未変更。
- CrossBody追加。肩間の横位置で同側肩0/反対肩1とし、0.35→0.65を0→1へ移行。外側0。画面境界マスク後の有効点のみ、3平均stride1ゲート、欠測時は既存保持。肩ヨーの計算には入力しない。
- Unity SolveArmはCrossBody>0時のみ胸郭forward基準で手首を最大10cm前へ補い、骨長と到達可能な手首終点を保つ肘円周上から、肘最大8cm前を満たす最寄りの曲がる側を選ぶ。上腕Zの反転処理は復活させない。幾何的に到達不能な条件は円周上の限界へ制限する。補間途中に再侵入したら解へ戻す。これは各肩を通る胸郭向き平面に対する近似で、衣服/腹部メッシュとの厳密衝突判定ではない。人体可動域全体を保証しない。
- pytest135件合格0.99秒、Unity Editorで旧後方肘姿勢の回帰＋左右/胴体yaw±45度の交差前腕/骨長検査成功。実Player ACTUAL_CROSS_BODY_CLEARANCE_OK、口横寄せ75%伝達、掌往復等のmotion検査成功。初回motionは旧開口笑顔70%を期待する検査で失敗/タイムアウト。新仕様8.061%へ期待値更新後成功。失敗を品質成功として扱わない。
- 最新193501の1800frames再処理と実Player監査をresults/crossbody-mouthへ保存。腕1777/1750、掌1368/1521（元開始状態は未復元）。CrossBodyは左0、右353frames（full196）。口横寄せ5/50/95%点−0.744/0.040/0.637。制御の発生数であり姿勢正解ではない。
- before-crossbody-mouth-20260912.zipで戻せる。SPEC0.27、AGENTS/PROGRESS更新、Desktop bat上書き。次は口開け時の表情、閉口横寄せ左右、交差前腕と服の埋まりを評価する。前回確認済みの後方肘・への字誇張を維持する。

## 最新：2026-09-12 — 後方へ突き出した肘、深い指屈曲、通常時の口角

- ユーザーは左右非対称口を確認済み。通常時の口角上がり、顔前で左手の開閉不良、左肩/腕を後ろ・右肩/腕を前にしたときの左肘の前方化を報告。追加指定は「左手は少し外側、左肘は後ろへ突き出す」。この正当な姿勢を保持する。
- 深い調査と実装根拠は `docs/ELBOW_ANATOMY_REVISION.md`。人体の可動域は姿勢依存で、肘のカメラ前後だけを人体判定にしない。今回、万能な人体priorを実装したとは扱わない。
- 外側の手にまで広がっていた胴体矩形のfront判定を抑止。手首前方から上腕を強制反転するDepthAssist.upper_forwardを撤去し、新規UpperInFront=false。Unityの旧引数互換は残す。モデル上腕深度35mm以上なら長さ候補も符号を反転しない。前方手首の補正は骨長保存、必要時はXYも変更し、後方上腕を正へ反転しない。外側で短縮した前腕は保存済み長さと観測/直前深度符号から復元し、前方prior撤去による追跡停止増加を解消。
- 指：MCPの深い屈曲で近位指骨の掌面投影がゼロ/反転する問題を修正。手首→MCPの参照で軸の向きを固定。左右80/89/90/91/100度でテスト。左手問題全体が解決したとは未確認。次のbody_diagnostics.fingersに指別の停止段階を記録。親指・旧手振り拒否・画面外保持・掌回転は変更しない。
- 口：記録は負の口角もあり、omegaは中央値/95%点ゼロ。omega主因という仮説は棄却。HAOLANの見た目への試行補正としてCornerDownWeightへ中立30%を追加、両端で補正を消して最大の笑顔/への字と左右独立を維持。初期口角基準未取得時は口角ゼロ、bowにも初期閉口基準差分を追加。通常顔がへの字へ寄りすぎないか未確認。原本アバター変更なし。
- 検証：pytest132件合格1.00秒。Unityビルド成功、EditorのPOSTERIOR_ELBOW_AND_NEUTRAL_MOUTH_OK（左右×胴体yaw−45/0/+45、肘の側/手首終点/長さ）、実Player motion検査成功。再計算1800packetのUnity監査も成功。成果物 `results/elbow-face-research/`。
- 同じ2本目の記録・同じ初期状態の旧/新再計算：腕1215/1210、掌1067/1144フレームで一致。旧はreplay-baseline-second、新はreplay-verified-second。replay-second/replay-final-*は中間検証なので最終品質の根拠にしない。元記録のウォームアップ状態は再現しておらず、旧sent_packetとの単純差を今回の退行と扱わない。
- 指比較finger-comparison.jsonは同じ3D点による軸処理比較。顔付近の自動抽出が少なく、実演区間の正解ラベルではない。観測指の角度が変わっただけで精度向上と断言しない。
- チェックポイント `results/checkpoints/before-elbow-face-research-20260912.zip`。デスクトップtanakacap-test.bat更新済み。SPEC0.26。次は通常口角と左手開閉、外側手/後方肘の実評価。人体の不可能姿勢を網羅的に排除できたとは扱わない。既存の肩幅顔相対値、ヨー量/方向分離、4フレームゲート、腕長常時学習、舌撤去を維持。

## 最新：2026-09-12 — 顔相対肩幅の基準肥大化、手の曲げ/ひねり、口の左右変形

- ユーザーは正面ヨーの継続、横に指先を向けた手がカメラ方向に折れる、への字/左右非対称口が出ないと報告。作業中に「肩幅は顔サイズ基準の相対値、固定はよくない」と明示。肩のピクセル幅は固定せず、顔サイズによって画面上の基準幅を毎回変えることを確認。
- 最新184303の1800framesで肩の補正幅基準が0.3414→0.4070へ増加。最大値更新により元の幅へ戻るだけでyawが作られる経路を確認。ShoulderWidthReferenceは初期の安定10観測（5秒内、全幅差中央値5%以内）の中央値へ変更し永久最大更新を撤去。計算は肩pixels×face_scale/初期補正幅、つまり顔サイズで正規化した相対値。画面基準pixels=初期補正幅/face_scaleで毎フレーム変化する。相対比の正面基準は初期取得という仮定が残り、横向き起動/顔尺度自体の誤差は未解決。2%幅の無反応域維持。診断にshoulder_face_relative_ratio/shoulder_reference_pixels追加。
- Unity DriveHand：曲がった手のnormalをそのまま前腕軸へ投影すると曲げがrollに混じる。指先方向を中立へ戻す回転をnormalへ適用してから前腕rollを抽出する。ConstrainHandFrameの曲げ上限60→90度（人体の普遍的可動域ではない試行値）。前腕±160/手首残余±40/速度制限/最短側の経路は維持。横指しが前向きへ削られるEditor検査を追加。
- 同じ旧packet1800件を同じsmoke開始姿勢から旧/新実Playerへ入力。results/yaw-palm-mouth/{before,after}.png.audit.jsonlとcomparison.json。掌誤差中央値/95%点は左1.67/96.78→0.27/35.99度、右2.60/128.28→0.39/43.70度。入力との一致であり人体精度ではない。大きい未到達は残る。summarize_control_auditの古い100度閾値も現160へ訂正。
- 口：元ログは左右下向きの値も送信（left<−.1が322/right113frames）、基準確立は1260/1800framesで序盤540framesは未確立。初期閉口10観測の安定判定範囲を.2→.4へ緩和、左右差分gain1.5→3。Unityの作者口角モーフを、100%時の上下変位目標6mm・最大3倍まで強調して左右へ分割。元アバター未変更。正しい側かだけでなくUpは上/Downは下へ実頂点が変位する検査を追加。左右非対称は引き続き独立モーフ。
- motion.logのCORNER_DEFORMATION_OK左右×上下4件、Up最大Y変位0.004108/Down0.006（root単位）。これはメッシュ実変位の検査で、実人物の表情が十分表現されるかは未確認。PALM_BACK_REACH_OKも左右×両方向で合格。への字の弱さを完全解決と扱わない。
- pytest127件合格1.01秒、Unity再ビルド成功。初回ビルドは旧60度を期待するEditor検査が失敗したため、新90度と横指し到達検査へ更新し成功。実Player motion.png、同入力audit成功。最新点群再処理reprocessedは1800frames/torso1787で、旧ウォームアップ状態は復元していない。
- before-yaw-palm-mouth-20260912.zip、デスクトップ同名.bat更新、SPEC0.25/AGENTS/PROGRESS更新。顔距離補正と内側腕前方prior、画面外保持、舌撤去、腕幅診断専用は維持。
- 次：顔との相対肩幅が安定するか、横指しの残誤差と口角左右/への字を実評価する。初期自然な正面/口閉じを基準とする仮定が残る。肩基準を再び永久最大へ戻さない。

## 最新：2026-09-12 — 正面ヨー基準・内側の腕を前へ・掌退化と口角

- 最新ユーザー指定：正面でもヨーが出る、掌返しが時々取れない。見えている手が同側肩より内側/反対側なら前方とし、後方の可能性は外側か遮蔽時だけ。口角上下/左右のゆがみが実装されているか確認を要求。
- 肩の問題経路：顔尺度補正の肩幅を固定0.36mと比較してacosを取っていたため、正面の個人/検出幅が小さいだけでyaw量を生成できた。ShoulderWidthReferenceへ変更し5秒以内10回支持の観測最大を基準化、2%以内の縮みをゼロ扱い。腕長の値とは別。顔尺度欠測は基準確立後は量を保持、確立前は旧モデル肩代替が残る。10観測の初期収集中は顔尺度がある限り0。横向きから起動した場合は後の広い肩観測で基準が更新されるため、正面の絶対正解を保証しない。方向は引き続きひじのみ。
- visible_hand_inward：画像内で有効な肩/手首、同側肩から反対肩へ向かうX方向に手首があれば前方。手のひらの点や向き、高さの制限なし。頭の近くでも検出できていれば使う。既存境界処理で画面外を無効化後に判定。従来overlap cueとORし、DepthAssist後・時間フィルター後も手首+Zを確保。後ろの深度枝から前に反映する際、前腕を伸ばす前に上腕の符号反射を使う。人体の遮蔽推定ではなくユーザー指定prior。外側まで一律前へはしない（既存overlapで前と判断する場合はある）。
- 掌：従来のwrist/index/little三角形が退化した時だけ、middle-wristとlittle-indexの2軸で面が定義できれば採用。middleがindex/little間にあることも検査。旧基底が有効な場合は変更しない。新たな可動域制限や長経路切替は加えていない。palm_observationを診断へ追加。腕無効・掌の真の欠測・Unityの既存可動域制限による停止は残る。退化ケースの回復で全停止原因を直したとは扱わない。
- 口：左右別の上げ/下げは既にTC_Left/RightCornerUp/DownとしてUnity接続済み。最新182939の1522frames中mouthContourTracked1428、元口角中央値左+.313/右+.256、上向き偏り。FaceFilterで初期の口閉じ(mouth<.3)の10安定観測（幅<.2）中央値を左右別基準に取り、差分×1.5を±1へ。口閉じ状態が自然な初期姿勢という仮定で、笑顔/への字を保って起動すると基準化される限界あり。顔欠測でも確立基準は保持。口角基準を新ログmouth_corner_referenceへ記録。口幅/開閉/ωは維持。
- pytest127件合格1.00秒、内側の左右腕/頭上でも前、実観測肩幅で0/距離不変、左右逆口角、退化掌の回復を検査。results/neutral-inward/releaseで最新1522点群を再処理、torso1426、腕1233/1233、掌1090/1146。元は1428、1248/1235、1092/1130。ウォームアップ差と制約変更を含み精度率ではない。左bone_length64（元45）が残り、腕位置不良の全解決ではない。
- Unity motion.pngで口角左右/上下、掌回転、肩等の既存駆動に合格。Unity本体変更/ビルドなし。before-neutral-inward-palm-20260912.zip保存、デスクトップ同名.bat更新、SPEC0.24/AGENTS/PROGRESS更新。
- 次：正面yaw、初期口角基準、内側腕の前方保持と左腕の長さ棄却を実記録で評価。掌はpalm_observationとArmTrackedで欠測段階を分ける。腕画像幅の診断は維持、まだ奥行き未接続。

## 最新：2026-09-12 — 腕幅の可視性別評価と輪郭計測の修正

- ユーザーが画面外を検出率の分母へ入れる不適切さを指摘。前回の全フレーム4.5%/8.9%を「検出器の成功率」とする評価を訂正。画面外でも測れないのは当然であり、今回の条件付き率を使用する。
- width_eligibilityを導入。ひじ/手首の推定点が画面内（既存相当の最大8px/短辺2.5%マージン）、両信頼度>=0.5、投影長>=50pxならeligible。画面外/低信頼/短縮/欠測を別集計し、輪郭不明や幅不整合はeligible内の失敗に含める。手のひらの点には依存しない。推定による測定適格性で、人体の真の可視性を目視分類した結果ではない。
- tools/audit_width_eligibility.pyで旧181106と最新181805を再集計。旧1522framesは左69/1144=6.03%、右136/1254=10.85%。最新1400framesは左105/1159=9.06%、右315/1261=24.98%。顔尺度補正まで可能な率は最新左74/1159=6.38%、右227/1261=18.00%。画像の幅取得と顔尺度欠測を混同しない。除外内訳/分子/分母はresults/width-eligibility/audit.json。
- arm_width.pyの実装修正：探索線の一部が画面外へ出ても全前腕を棄却しない。画面内のサンプルだけで境界を探し、補間の画面外色は無効にする。また5断面に対する一律最大幅差30%を、4断面以上が支持する緩い線形先細りへ変更。前腕の手首へ向かう幅変化と、1断面の外れ値を許容。最大幅変化は中央幅80%以内、支持残差max(2px,中央幅10%)の暫定値。急変/非線形の不整合は棄却。中央の幅を出す。
- eligible/statusと断面候補section_widthsを数値ログへ追加。RGB保存なし、drives_pose=false維持。旧記録に画像/断面候補がないため抽出変更後の実検出率は再計算できない。上記率は旧抽出の分母訂正版であり、新抽出の改善率ではない。
- pytest122件合格0.93秒、compileall成功。画面外/低信頼と輪郭失敗の分離、探索線が端を越えても可視腕を計測、背景一色を腕としない、先細り/1外れ値/不規則幅を検査。アバター駆動変更なし、Unity再ビルド/同一ボーン検査の再実行は不要。
- before-width-eligibility-20260912.zip保存、デスクトップ同名.bat更新、SPEC0.23/AGENTS/PROGRESS更新。肩の量/方向の分離と既存保持等は維持。
- 次：新ログのeligible内で測定率とsection_widthsの連続性を評価する。腕幅の近さ推定への接続はまだ未実装。検出率向上と正しい輪郭取得を同一視せず、衣服/回転による変化の限界を確認する。

## 最新：2026-09-12 — 肩幅でヨー量、ひじで方向を分離

- ユーザー指定：肩の回転量を従来の肩推定から、方向だけを腕の前後から取る。前腕/手首を使わない既存指定を維持し、ひじ差の符号だけを採用する。
- torso_yaw.shoulder_yaw_magnitude：顔尺度が有効ならacos(clamp(肩2D距離×顔尺度/0.36,0,1))、上限80度。肩線のXY長なのでrollの傾きだけでは縮まない。顔尺度不良時はasin(clamp(abs(左右肩Z差)/0.36,0,1))の肩モデル由来の量へ代替し、肩尺度の自己正規化から常にゼロを作る循環を避ける。0.36mは既存の名目肩幅で人体実測ではなく、顔初期化/衣服/肩検出誤差の限界が残る。
- body3d：ひじ左Z-rightZの符号だけにヨー方向を限定。2D/3D照合の不一致/ひじ欠測、差の絶対値0.015m未満は方向を保持（初回0）。方向保持中も肩幅による回転量は更新する。以前のheld_elbow等の診断文字列は今後「方向の保持」を意味し、角度全体の保持ではない。3平均stride1/最後の姿勢保持/掌範囲維持。torso_yaw_magnitude/source/directionを診断へ追加。
- 腕幅記録results/20260911T181106-027282Z-rtmw-l-384を解析。1522frames中measuredは左69（4.5%）/右136（8.9%）、最長連続10/16。ambiguous_contour1103/1168が主因。補正幅5〜95%範囲は左0.0353〜0.1501、右0.0263〜0.0879（実寸ではない）。画像未保存で真の輪郭との比較不可。現方式をそのまま奥行きへ接続する根拠は不足し、駆動未接続のまま維持。計測の疎さを閾値緩和で隠さない。results/shoulder-width-yaw/width-audit.json参照。
- pytest119件合格0.96秒。肩幅角度/距離/roll不変性、ひじ深度差が増えても回転量不変、方向保持/復帰と既存検査に成功。最新点群再処理は同フォルダreprocessed、新torso1519/1522、尺度停止なし、初期確認待ち等あり。元のウォームアップ状態は再現していない。実Unity motion.pngで肩左右/掌回転等合格、Unity変更/再ビルドなし。人体追従は未評価。
- バックアップbefore-shoulder-width-yaw-20260912.zip、デスクトップ同名.bat更新、SPEC0.22/AGENTS/PROGRESS更新。
- 次：肩の量/方向の分離を実評価。腕幅は色差横断法では計測不足。近さ推定へ進むには輪郭抽出自体の見直しと評価が必要で、現値から前方へ押す処理はまだ実装していない。肩の名目幅と顔尺度のずれ、前傾不足、大きな深度飛びも未解決。

## 最新：2026-09-12 — 画像の腕幅計測と肩の小刻みな丸めを減らす試行

- ユーザーは「よくなってきた」と評価。一方で腕の後方化が残り、姿勢推定以外の映像の見かけサイズから近さを推定する案、肩の震えを推論パラメーターで改善する案を要求。
- capture_lab/arm_width.pyで前腕の30〜70%位置を5横断し、中心色との対比から両端を計測。4断面以上が整合すると幅pixelsと、有効な顔尺度を掛けたdistance_normalized_widthを記録。これは実寸ではない。短縮/画面端/低信頼/同色や不整合の輪郭は欠測。-Diagnose時のみ、画像は保存せず数値arm_image_widthと計算時間をframes.jsonlへ残す。画像から幅が取れる合成試験は成功、実人物の袖幅精度・近さ推定は未確認。drives_pose=falseで奥行き/ヨーへ未接続。袖の変形と回転だけでも幅が変わるため自動的に前方へ押し出さない。
- inference.py：肩5/6、ひじ7/8、腰11/12のX/Y/Zだけ、argmax近傍3binのlog放物線で局所ピークを補間。正で凹な内側ピークのみ±0.5bin以内を補正、端/平坦/非正は整数へ戻す。離れた山を平均しない。公式DARKそのものではなく独自の限定補間。手首/顔/指のデコードと信頼度は変更しない。追加推論・待ちフレームなし、3平均stride1維持。
- 旧Zは1bin=2.1744869/288=0.0075503（モデルのm単位）、yaw正面付近1.2015度相当。最新180020の1800記録ではraw yaw差95%16.38度/最大102.84度、送信6.62/63.64度。動作とノイズを区別するラベルはなく、全て震えとは読まないが、丸め幅を超える変化はこの補間で解決しない。大きな誤推定・腕後方化は未解決。
- body_decodeに対象joint_idsと整数/refined_z_binsを記録し次回比較可能にした。旧ログは分布/画像を持たず新デコード/画像幅の再処理は不可。run-avatar-lab.ps1 -IntegerBodyPeaks（CLI --integer-body-peaks）で旧デコードへ戻せる。新モデル/再学習なし。
- pytest117件合格0.96秒。合成分布で連続ピーク/多峰性/平坦/端、対象外関節不変、同じ点群で画像幅だけ変化/無輪郭を検査。GPU synthetic20記録frames+warmupはresults/20260911T180755-607527Z-rtmw-l-384、body26推論callsでCUDA9724nodeevents、CPU computeなし。実人物精度ではない。画像幅合成計測中央値0.154ms/95%0.215ms（片腕有効）。
- results/width-subbin/summary.jsonとmotion.pngへ検証保存。実Unityの既存肩左右・掌到達・指/欠測保持合格、Unity変更/再ビルドなし。バックアップbefore-width-subbin-20260912.zip、デスクトップ同名.bat更新。SPEC0.21/PROGRESS/AGENTS更新、調査根拠docs/ARM_IMAGE_WIDTH.md。
- 次：新実記録のarm_image_widthの可用性/幅変化とbody_decodeを確認する。画像幅の変化が距離変化と区別できる根拠がなければ奥行きへ接続しない。大きな肩飛びは分布の多峰性/ひじの不良観測と切り分け、根拠なく全体の追従を遅くしない。前回のヨー符号撤去/2D3D照合、顔尺度不良時の肩代替、最大腕長短縮禁止、最後の姿勢保持は維持。

## 最新：2026-09-12 — ひじ誤検出のヨー波及を抑える試行

- ユーザーは2回評価し、肩ヨー不良の継続と袖の垂れをひじと検出することを確認。極性反転が不要かもしれないと指摘。改善案があれば試行、なければ次へという指示。今回、既存の2D/3D推定の不一致をヨーにだけ反映する限定的な対策を実装。人体精度は未合格。
- torso_yaw.py：経験的な符号反転を撤去しatan2(leftZ-rightZ,.36)へ戻す。+Zが前のアバター座標で左ひじ前→+yaw→左肩前。モデルが深度を誤る問題を符号で補償しない。左右/XYZ全体とUnity前腕±160/掌制約は変更なし。
- elbow_agreementは同じフレームで既に計算されている2D RTMWと3D RTMW3Dの肩→ひじXYベクトルを比較。どちらかの誤差が3D側肩幅の0.25倍超なら肩yawのみ最終採用値保持。信頼度0.3未満/非有限/画面外の照合も保持。両方一致で既存3平均stride1経由で再開。新規推論/待ちフレーム追加なし。前腕/手首は判定にも不使用。腕駆動・長さ校正は変更していない。旧記録等で照合データ自体が未指定なら旧方式へ互換。
- 最新172300（1800frames）/172547（1747frames）はtorso全有効、scale_unavailable0。前回の全身停止の再発なし。2D/3Dひじ相対XY誤差の中央値は肩幅の左2.2/右3.0%、次は3.2/3.9%。不一致保持は12/1800、120/1747回。これは袖を正しく判定した数ではない。両モデルが同じ袖へ吸着したり、XYが合ってZだけ誤る場合は検出できない。
- results/elbow-agreement/{first,second}に再処理、summary.jsonに比較/速度。新torso1798/1745（初期確認待ち2frames）、腕左1708/1345、右1776/1346。再処理はウォームアップ状態を復元しない。数値点群のみで袖の画像はなく、誤検出の正解ラベルなし。純粋な照合計算中央値0.0248ms/95%点0.0259ms、最大UDP2141bytes。
- pytest114件合格0.98秒。距離変化、不一致時yaw保持/roll・腕継続、復帰、手首非依存、非有限を検査。compileall成功。実Unity fixture-player.pngで再処理packetの受信/描画成功、独立motion.pngでSHOULDER_FORWARD_SIDE_OKと甲側到達等の既存検査成功。Unity変更/再ビルドなし。
- 検証途中のplayer.logは--packet-fileと--motion-checkを同時使用し、記録の口輪郭状態が合成の口角検査を妨げ失敗。別々のPlayerへ分離して成功。smoke_unity.pyに併用拒否を追加し再発防止。アプリの実人物不良の実証とは区別する。
- バックアップbefore-elbow-agreement-20260912.zip、デスクトップ同名.bat更新。SPEC0.20/AGENTS/PROGRESS更新。詳細と調査候補はdocs/ELBOW_AGREEMENT.md。
- 次：ユーザー評価でこの限定対策に効果がなければ閾値を狭め続けず、袖/ひじ推定は未解決として次項へ進む。腰欠測のpitch不足も未解決。舌/画面外ひじ/指骨長履歴の撤去と最大腕長短縮禁止、最後の姿勢保持は維持。

## 最新：2026-09-12 — 顔距離尺度による腕・胴体の停止を修正

- ユーザー申告「腕、体をほぼ検出しなくなった」を調査。最新実記録results/20260911T171152-437216Z-rtmw-l-384の704frames中659がscale_unavailableで腕/胴体まとめて無効、顔追跡は702。顔尺度のface_geometry_rejectedが687回。モデルの全身点消失ではなく、顔尺度を全身駆動の必須条件にした制御上の停止と確認。直前のひじヨー極性/前腕範囲より前に導入された依存である。
- capture_lab/body3d.py：顔尺度を優先し、不良時は肩尺度×最後に顔と一致した尺度比で追跡を継続。肩も使えない場合のみ既存0.5秒キャッシュ後に停止/最後の姿勢保持。顔不良中は腕長学習を停止し、body_geometry.pyで保存腕長からの奥行き追加も休止。採用済み最大長を消去/短縮しない。肩の向きに影響される代替尺度なので距離/奥行き精度は顔尺度時と同等ではない。
- face_scale.py：単発の起動時顔形状を固定せず、5秒内10候補のうち8以上に整合する実観測形状から基準を選択する。初期化中も肩で動く。顔基準/残差/尺度源/腕長学習の可否を診断へ記録。元記録はウォームアップの基準形状を保存していないため、当時の基準が悪かったという部分は直接実証できていない。
- 修正前に「顔欠測継続」「不良顔基準」の回帰テスト2件が失敗することを確認し修正。最終pytest111件合格0.94秒、compileall成功。単発の起動外れ値、距離移動、最大腕長維持、顔回復と全尺度欠測も検査。
- results/scale-recovery/beforeとafterに同じ704点群の旧/新再処理を保存。旧再処理torso685/左腕605/右腕604、新700/606/605、scale_unavailable15→0。新尺度はface654、shoulder_fallback50。元の実記録では各41だが、再処理はウォームアップ後の初期状態を復元しないため41→700を同一状態比較や精度改善率として扱わない。画面端判定での腕停止は残し、新左94/右97回。summary.json参照。
- 再処理した両腕/胴体/掌の有効packetを実Unity Playerへ送り、受信・描画・掌制約・欠測保持の検査成功（results/scale-recovery/player.pngと付随ログ）。最大UDP2133bytes。Unityコード変更はなく既存ビルドを使用。実人物での復旧と動作品質は未確認。
- バックアップresults/checkpoints/before-scale-recovery-20260912.zip。デスクトップtanakacap-test.bat更新済み。SPEC0.19/AGENTS/PROGRESS更新。
- 次：次回実人物記録でgeometry_scale_sourceと追跡継続を確認し、既存のひじ→同側肩、甲側への到達を評価。腰欠測時のピッチ不足は引き続き未解決。舌/画面外ひじ部分追跡/指骨長履歴棄却は戻さず、3平均stride1と最後の姿勢保持を維持。

## 最新：2026-09-12 — ひじヨー極性の修正と掌180度の到達

- 最新評価：ユーザーは右ひじを前にすると左肩が前に出ると報告。掌の不自然な遠回りは解消したが、手の甲を見せる向きへ届かない。今回の実装・合成/実Player検証は完了、実人物での改善はまだ未確認。
- elbow_yawをatan2(rightZ-leftZ,.36)へ反転。これはユーザーの実測申告に合わせた「モデルのひじ深度→肩ヨー」の極性修正であり、Unity座標の数学自体が反対だったと実証したものではない。モデル深度の人体正解はない。全体のXYZ変換、左右の腕・目・口、前腕/手首非依存、欠測保持、3平均stride1は維持。
- UnityのForearmTwistLimit定数を160度に設定（旧100）。元アバター基準の前腕駆動角であり、人体の解剖学的可動域を160度と測定した意味ではない。残余手首ねじり±40/曲げ60、前腕速度900度/秒、手首1080度/秒、最短側を選んでから制約する方式は維持。±140度の反対枝切替や肘面中立の履歴は復活させていない。腕姿勢によって制約による未到達は残り得る。
- pytest107件合格0.80秒。極性変更後もひじ差/共通移動相殺、前腕・手首非依存、欠測保持が通る。Unityビルド成功、smokeの上限検査を新定数に整合。Editorの両符号制約端検査は160→240度の継続と中立復帰へ変更。
- results/yaw-polarity-hand-range/motion.pngと.logでPALM_BACK_REACH_OKを左右×回転両方向の計4件確認。合成腕姿勢で0→180→0度の目標へ到達、180側誤差はUnity報告で全て0度（20描画ステップの整定後）。往復経路357.16〜357.26度、最大更新2.07度。整定中の小さい経路分は集計しないため理論360度とは一致しない。前回の±80だけ/制約端停止だけの検証に加えて到達を検査した。
- 同ログSHOULDER_FORWARD_SIDE_OKはyaw−45でRightUpperArm側が+Zへ、+45でLeftUpperArm側が+Zへ前進する実ボーン位置を確認。入力の人物ひじ深度の正解を測定したものではない。首/胸ロール・目/口の左右・指・画面外保持の既存検査も成功。
- 170→230度の境界入力では新実経路57.91/59.75度・最大更新0.46/0.47度。旧版の約10度から動く範囲が増えたが大逆回転はない。旧±80往復316.16/316.49度も維持。
- 最新実記録results/20260911T170201-673503Z-rtmw-l-384（1800frames）をresults/yaw-polarity-hand-range/reprocessedへ再処理。新torso有効1769、元1790。再処理は起動前warmup状態を持たず、初期化や欠測を含むため単純な符号反転と有効数が一致するとは限らない。人体追従の品質評価ではない。
- バックアップresults/checkpoints/before-yaw-polarity-hand-range-20260912.zip。デスクトップ同名.bat更新済み。SPEC0.18。次は実人物の右ひじ/右肩方向と、実姿勢で甲側が届くかを確認。ピッチの独立観測不足は未解決。舌、画面外ひじ部分追跡、指骨長履歴対策は撤去状態を維持。

## 最新：2026-09-12 — 舌撤去、ひじ由来ヨー、掌の遠回り修正

- ユーザーは2回試行し、舌不良で削除、掌→甲の不自然な遠回り再発、肩ヨーへひじ前後を使うこと（前腕は禁止）を指定。実装/検証完了、実人物品質は未合格。バックアップresults/checkpoints/before-elbow-yaw-no-tongue-20260912.zip。
- 舌の画像処理・FaceFilter専用ゲート・UDP項目・実行時ぺろっ駆動・数値ログを削除。口輪郭/左右口角は維持。原本アバターの舌モーフは変更しない。旧記録は保存し、replay_bodyが旧tongueOut/Trackedを除去する。過去のsummarize_axis_revisionの舌ベンチ処理も撤去した。
- torso_yaw.elbow_yawは補正前のモデルXYZの左ひじ7/右ひじ8だけから、atan2(leftZ-rightZ,0.36m)を±80度へ制限。+Zが前、左ひじが前なら+Yawで左肩が前へ出る。両ひじの共通移動は差で相殺。左右いずれか欠測なら採用済みyaw保持（初回0）。肩幅ヨーとモデル肩深度ヨーの採用経路を撤去。前腕/手首/DepthAssistの出力は読まない。モデル自体が全身画像からひじを推定している点とは区別する。
- ヨーは肩/尺度/胴体基底の既存有効判定を通ったフレームで更新し、3平均stride1/.35度確認へ通す。rollは肩、pitchは有効腰の従来経路。顔尺度による腕長校正、±50/80/25の範囲、欠測時停止、首/目/口左右を維持。肩独立並進は追加しておらず左右差で胴体を回す。ひじ屈曲だけでも肩が回り得るユーザー指定の連動仮定で、人体の肩角度の直接測定ではない。
- 遠回りの原因となるSelectForearmTwistのabs(raw)<=140で符号付き絶対角へ戻す分岐を撤去。例えば+100度の前腕にraw−140を渡すと旧版は−100へ200度逆回転し得た。最短側の連続角を選んでから±100へ制限する方式へ戻した。手首60/±40と速度上限は維持。届かない側は止まり、別の枝へ遠回りしない。全姿勢での解剖学的一致を保証した意味ではない。
- 検証：pytest107件合格0.78秒。左右ひじの前後/共通移動/欠測保持、前腕手首変化のヨー非依存、舌出力撤去を検証。Unityビルド成功。Editorで両符号140→240度に対し前腕が反対端へ切り替わらず、中立へ復帰することを確認。
- 実Player results/elbow-yaw-no-tongue/motion.pngと.log。既存±80往復の経路左316.16/右316.49度・最大約2度/更新。旧境界170→190を170→230へ拡張し、実経路9.67/9.94度・最大0.37/0.38度/更新で大逆回転なし。残余手首が一部動くので経路0ではない。OFFSCREEN_FULL_ARM_HOLD、FACE_SIDE_CONTOUR等5個のOKを確認。旧「140度内なら反対枝へ戻す」テストは今回の指定に反するため変更。
- 最新実記録164535（1616frames）/164736（1800frames）を同ディレクトリreplay-164535/replay-164736へ再処理。summary.json参照。ひじヨー採用1601/1521、後者はひじ欠測保持5。他は尺度等で全体無効。旧/新yaw p5/50/95は1回目−37.40/0.42/35.63→−36.27/−5.98/15.11、2回目−35.86/0.03/61.10→−17.57/2.39/38.90。新torso有効フレームを母集団に比較。人体正解はなく精度改善率ではない。全パケットで舌項目0、最大UDP1996bytes。
- デスクトップ同名.bat更新済み。SPEC0.17。次は新方式でひじの前後と肩方向が一致するか、掌反転が制約端で止まりすぎないかを実人物で評価。ピッチの独立観測不足は依然未解決。汎用出力/物理/OBS等の全体残項目も維持。

## 最新：2026-09-12 — 指/画面外の巻き戻し、左右統一、輪郭と舌

- 最新ユーザー指示を優先。画面外の上腕部分追跡を撤去し、腕全体の局所姿勢保持へ戻した。指の履歴骨長検査も撤去。元からの境界/信頼度/符号屈曲/3平均stride1は維持。upperTrackedは互換用に残るがfalse/駆動なし。詳細：[AXES_CONTOUR_TONGUE](docs/AXES_CONTOUR_TONGUE.md)。
- 首rollのマイナス符号が胴体と逆だったため修正。Unity headTargetをroot*Euler*headRestへ揃えた。目は入替えず、実シェイプの影響頂点で人物の左右を確認。左目42〜47、左口角54、アバターroot−Xが左。
- 口の左右口角上下と上唇の曲がりを追加。口角モーフは実行時の複製メッシュ上だけで作者デルタを左右分割し、4シェイプを駆動。上唇bowはωへ対応する造形上の近似。従来3.5倍の口とaa/oh/ouは維持。詳細欠測は対称smileへ切り替えず保持。
- 舌は新しいmouth_detail.tongue_evidenceで口周囲128×96画像の色/連結/下唇より下への突出を検査する試験実装。専用の学習済みモデルではない。tongueTracked/tongueOutを確認処理からぺろっへ接続。画像は保存せずtongue_input数値だけ記録。古い記録から舌を捏造しない。実人物の舌精度は未検証、口紅/照明/皮膚等の誤検出リスクあり。
- ヨーは顔距離補正後の肩投影幅から角度を取り、モデルZは符号へ使うShoulderYawを追加して試行。5秒10観測で正面幅を学ぶ。最新839フレームで534回作動し、yaw p5/50/95は−9.17/−3.45/1.70→−41.58/−25.37/10.70。過大推定の可能性あり、精度改善とは未判定。
- **ピッチは未解決**：最新162517記録の腰Yは下端約701〜713px/720で全839回held_missing_hips、旧pitchは全0。首の傾きを代入する偽の解決はしていない。独立した胴体上部の観測を増やす必要がある。今回の変更で肩全体が解決したとしない。
- pytest106件合格0.77秒、Unityビルド成功。results/axis-contour-tongue/motion.logの5個のOKマーカーを確認（詳細文書参照）。首/胸の同方向、目/口角の実左右、舌/輪郭の実重み、画面外全腕保持、手首往復/境界が成功。
- 最新元記録results/20260911T162517-268332Z-rtmw-l-384（839frames）、その前162129。再処理axis-contour-tongue/reprocessed、summary.json。指フラグ総数左449→707/右106→379。合成画像の舌処理中央値0.22ms、95%点0.40ms、正出力0、最大UDP1991bytes。実人物画像の評価ではない。
- バックアップbefore-axis-contour-tongue-20260912.zip。デスクトップ同名.bat更新済み。SPEC0.16。次回はヨーの過大回転・口輪郭/舌の誤検出・指定巻き戻しの実評価、ピッチ観測の追加を進める。配布/物理/OBS等の全体残項目も維持。

## 最新：2026-09-12 — 顔尺度による腕長、胴体制限、回転整理、指と口

- 今回の依頼は実装済み。詳細は[距離・回転・指と口の変更](docs/DISTANCE_AND_MOUTH_REVISION.md)。実人物品質は未合格。バックアップresults/checkpoints/before-face-distance-shape-20260912.zip。
- 胴体pitch±50/yaw±80へPython/Unity両方を変更（旧30/55）。前後/ひねりは直前の肩の会話から胴体と解釈。腕前方条件・手首数値上限・3平均stride1は維持。腰欠測で新しい前傾は推定できないままであり、可動域拡大だけで解決済みとしない。
- FaceScaleは顎/唇を除く鼻/目角8点のアフィン最大特異値で相対サイズを推定し、最初だけ肩幅で基準尺度を固定。その後は肩尺度へ戻さない。XY共通尺度へ適用し、腕長は5秒10観測の支持最大で短縮禁止。顔欠測は校正停止、尺度キャッシュ0.5秒後は停止。実画像サイズなしの旧単体呼出しは肩校正互換。大きな横向きや斜めの初期基準は限界。顔モデル追加なし。
- Unity ForearmNeutralとその履歴/旧テストを撤去。元アバター基準を前腕方向へ最短回転して使用。SelectForearmTwistは±140度内の目標なら実現可能な枝へ戻し、反対側制約端への張り付きを修正。±180度付近は従来の連続側保持。前腕±100、手首60/±40、速度上限は変えていない。
- 最新160326実記録1049フレームの同一packet/同一初期状態で旧Playerと比較。final-comparison.jsonの右掌方向誤差中央値/95%点57.55/114.15→0.93/88.74度、左0.36/40.64→0.36/38.16度。入力追従の値で人体正解ではない。中間after.pngは左が悪化した版、採用版はfinal.png。結果はresults/wrist-distance-review/。
- 指は直近2秒/最大40採用観測の骨長中央値に対し0.45〜2.2倍を外れた指だけ観測を棄却。5観測から有効。DirectionGate.missingで平均窓/方向連続性を切り、表示基準を保持して再確認。旧3/1ルールの設定互換を維持。新有効指総数は左994/右1050（旧2242/2261）、保持増加が大きく実屈曲抑制が未確認。単純に手の速度で指を止めてはいない。
- 口感度は開閉3.5倍/幅3.5倍へ（旧2/2.5）。mouthRound（口幅の狭さ）/mouthSmile（上唇中央と口角高さ）を追加し、同じ表情確認へ通す。vrc.v_aa/oh/ouと口角上げへ混合、従来口幅も維持。舌・音素分類・個人口幅中立校正は追加していない。
- 最終pytest103件合格0.79秒、Unityビルド成功。実Player release-motion.pngの.logでEXTENDED_FINGERS/UPPER_ONLY_HOLD/MOUTH_SHAPES_TORSO_RANGE/MOTION_PATHのOKを実確認。左右手首往復316.17/316.50度、境界追加0、口の実重み・胴体45/70度到達・表情/部分欠測保持成功。
- 最終Python再処理はreprocessed-release。distance-summary.jsonで顔尺度採用1049/1049、計算時間中央値0.025ms/95%点0.034ms（推論除く）、最大UDP1836bytes。デスクトップ同名.bat更新済み。SPEC0.15。
- 次に確認すること：実距離移動での腕奥行き、指を本当に曲げた際の保持しすぎ、右掌の大残差、口の過強調/すぼめ誤判定。カメラを勝手に再撮影して人間品質合格としない。全体の汎用出力・物理・OBS等の残作業も継続。

## 最新：2026-09-12 — 画面外でも見えるひじ方向だけ追従

- 最終検証の訂正：指伸展/上腕部分追跡の検査コードがAuditRecording側に配置されていて、--motion-checkでは実行されていないことをログ照合で発見。CheckMotionPaths内へ移し再ビルド。results/unity/upper-only-final.pngで成功し、.logのTANAKACAP_EXTENDED_FINGERS_OKとTANAKACAP_UPPER_ONLY_HOLD_OKを確認した。以前のvisibility-fingers-mouth*.pngやupper-only.pngだけで指の実伸展を確認済みとした記述は不正確で、本最終検証を根拠とする。

- ユーザーは画面外の手の形・角度を保持し、ひじの回転方向だけ反映する指定。実装上は観測可能な「肩→ひじ」の方向を上腕へ適用し、前腕の局所曲がり・手首・指を保持すると解釈して説明した。見えない手首から新しい肘屈曲角を推定する方式ではない。
- BodyRetargetにupper_motion（3平均stride1、DirectionGate .006）とleft/rightUpperArmTrackedを追加。肩・ひじが有効なら通常追跡中から平均を維持し、手が境界で無効になった時だけ部分追跡として出す。ひじも画面端/欠測なら部分追跡を停止。世界のひじ座標を固定せず上腕方向を用いる。腕長の自動校正に欠測手首を入れない方針は維持。
- UnityのDriveUpperOnlyは上腕を現方向から新しいひじ方向へ最短回転し、既存gain36で補間。下流ボーンのlocalRotationを変えない。手首の回旋履歴と整合するようlowerUntwistedを現在の下腕から再計算し、通常追跡復帰へ引き継ぐ。通常のArmTrackedと区別し、全体tracked判定には部分追跡も含める。
- 98pytest合格0.77秒。片手だけの画面外、見えるひじの移動反映、ひじも切れた時の停止を検証。最終ビルド成功、results/unity/upper-only.png(.bones.json/.motion.json/.log)。TANAKACAP_UPPER_ONLY_HOLD_OKで実上腕方向追従・前腕/手首の局所姿勢・全指角の不変を検証。既存手首往復・境界・指伸展・口幅・欠測保持も成功。デスクトップ同名.bat更新済み。
- 舌の質問：現RTMW/COCO-WholeBody133点に舌専用出力はなく、新しい分類/検出器が必要。Apple ARKitにはtongueOut出力があるがWebカメラの現構成へそのまま使える意味ではない。口領域のみの軽量分類は候補にできるが負荷・精度未測定。重いと断定せず今回は舌モデル/依存は未追加。https://github.com/jin-s13/COCO-WholeBody/blob/master/data_format.md と https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapelocation/tongueout?changes=_1 を確認。
- 続いてユーザーは現在の肩の制御要素の一覧を要求し、余計なものを排除したいと表明。説明のためだけに追加撤去は行わない。現在は肩3D方向のyaw/roll、腰由来pitch、境界/信頼度検査、3平均2点確認（deadband .35度）、C中立補正、角度上限、Unity補間gain16、背骨35%/胸100%世界回転。胸100%は背骨35%に加算して135%ではない。推測鎖骨駆動/肩幅増幅/上腕肘面回旋は撤去済み。
- 口開閉2倍/幅2.5倍と腰周辺可視性の修正は前セクションのとおり保持。胴体ひねり精度は未解決。新しい「削除する要素」の具体的指定が来たら前後比較と可逆性を維持して反映する。

## 最新：2026-09-12 — 口の誇張、画面下端の腰を前傾に使わない

- ユーザーは「とてもよくなった」と評価。胴体は依然不良、口をもっと大げさに動かす要求。改善した手首/指/腕/画面外停止の制御は維持。口は開閉・幅の両方と解釈。
- retarget.pyの開閉感度を2倍、横幅感度を2.5倍に変更。中立比率/開閉のdead zone/上限/表情の確認方式は同じ。Unityシェイプの可動上限を広げたのではなく、弱い入力で上限に届きやすくした。飽和領域が増える交換条件あり。幅の旧0.2は新0.5相当。幅の中立個人校正はまだない。
- 最新154253は1278フレーム、torso有効1278。旧pitch p5/50/95=6.18/22.06/30度、yaw=−4.48/−0.39/12.71度。腰中心Yのp5/50/95=698.23/705.87/710.77（720px高）。従来は手だけに境界除外を適用し、画面下端の腰から強い前傾を算出できていた。人物の真の角度は不明なので全てが誤推定だったと断定しない。
- visibility.pyで腰2点にも境界/周囲の余裕を要求。margin=max(従来の8px/短辺2.5%, 肩投影幅の25%)を左右と下側に適用。腰中心だけ画面内に出ても周囲が切れた点を採用しない。閾値は暫定。腕・掌の既存境界条件は変更していない。
- BodyRetargetでpitch_observedを独立判定。腰が見えない/不整合なら既に採用したpitchを保持、まだ有効pitchがない時だけ0。肩からyaw/rollは続ける。torso_pitch_source='hips'/'held_missing_hips'を記録。長い人物欠測でgateリセットした後は初期値0。前傾の独立Trackedフラグは増やしていないので診断sourceを読む。
- 腰へ従来の18px境界帯だけ適用した中間再処理results/mouth-gain-torso-20260911T154253では84フレームをまだ採用し、pitch中央値は22.69度のままだった。十分な周囲を要求する最終版の記録はresults/mouth-gain-torso-final-20260911T154253、summary.json参照。停止は新しい前傾の推定ではなく欠測時の扱いの修正であり、左右ひねり精度は未解決。
- 97pytest合格0.72秒。腰の境界点で前傾を作らないこと、有効pitch後の欠測保持とyaw継続、誇張した口の中立/上限を検証。Unityソース変更なしで再ビルド不要、既存実Player回帰results/unity/mouth-gain-torso.pngで手首往復316.17/316.49度、180境界追加0、指伸展/口幅実変形/欠測保持成功。
- バックアップresults/checkpoints/before-mouth-gain-torso-20260912.zip。デスクトップ同名.bat更新済み。次は胴体の左右ひねりが回転量不足/逆方向/別動作混入/遅延のどれかを切り分ける。前回の非同期質問の具体的選択はまだ回答されていない。今回も人体ひねりの正解データはない。口の飽和と誇張量、腰が見えない着席での前傾推定は評価対象として残る。

## 最新：2026-09-12 — 画面境界の除外、指の伸展、口幅

- 最新ユーザー評価：手首は改善を確認。画面外の手の推定点が端へ集まりアバターを動かす、伸ばした指が曲がって震える、胴体ひねりは依然不良。口の横幅も追加指定。手首・腕奥行きの既存修正は保持。
- 人体構造を深く考える指定でdeep-researchスキルを適用し、一次資料と実装判断をdocs/OFFSCREEN_HAND_RESEARCH.mdへ保存。単眼の多義性/姿勢依存関節制限、滑らかな運動研究の適用限界、指の屈伸と連動運動を区別。減速案は必須ではない指定のため、誤った端点速度を外挿せず最後の有効な局所関節姿勢で停止する方式を採用。滑らかな減速軌道を実装したとは言わない。
- capture_lab/visibility.pyのscreen_visibilityをBodyRetargetの校正/幾何計算より前に適用。境界帯max(8px,短辺2.5%)。身体手首、信頼度あり手モデル手首、掌4点中3点の端集積で腕と手全体を無効化。個々の境界指先はその指のみ無効化。スコア低下だけで原点にある掌は身体腕の画面外理由にしない。元スコア配列は破壊しない。
- 境界時はArm/Handの短欠測キャッシュを消し、*OutOfView=true、各Tracked=false。Unityは既存の最後の局所姿勢保持を使う。胴体には付随するため、手を机上の世界位置に固定する方式ではない。UIへ画面外のL/R表示を追加。表示時の位置外挿・待機姿勢復帰はない。
- image_sizeをBodyRetargetへ渡し、各診断行にも実画像幅高さを保存。replay_bodyは各行の値を優先し、旧記録はreport.json arguments.width/heightを使う。寸法がない古い記録/単体呼出しでは境界検査なし。旧報告の要求解像度は実取得サイズの保証ではないため再処理条件として区別する。
- 指：符号なしacos/絶対値傾斜から、掌内側と指方向が定める屈曲面の符号付き角へ変更。左右の内側方向をUnityと揃え、横ずれ・反りを正の屈曲にしない。符号付き値の平均/方向確認の後に負値を0とし、7度の不確実帯、2.5度deadbandを使用。指の有効曲げを過剰に抑える可能性も残す。親指専用処理は保持。
- Unityで親指以外の屈曲ゼロ基準を作成。MCPの横開きを保持して掌面へ伸ばし、PIP/DIPを前の骨へ揃える。元の指の曲がりへの単純加算をやめる。原本アバターは未変更。指の横開き追跡や親指対向の完全再現は未実装。
- mouthWidthをUDP v1に追加（旧送信側省略=0）。口角間距離/眼中心間距離を比率0.8中心・幅0.35で−1〜1へ正規化し、他の表情と同じ3平均/方向確認へ通す。個人別中立校正はまだない。haolanの口横広げへ−50〜100を適用、口開閉vrc.v_aaとは別。負重みの逆変形は実BakeMeshで確認したが、作者の専用すぼめモーフではなく逆向き利用。
- 最終94pytest合格0.71秒、CLI help/compileall成功。画像境界での腕長不更新/他腕継続/指先だけの欠測、符号付き屈曲の左右/回転不変性/反り/横ノイズ/符号平均、口幅の距離・ロール不変性と確認方式を検証。
- 最終Unityビルド成功。results/unity/visibility-fingers-mouth-final.pngと.bones.json/.motion.json。口幅拡縮が実メッシュを逆方向へ変形すること、指屈曲0の中間・末端が実際に伸展すること、手首往復316.17/316.49度・最大約2度更新、180度境界の追加0度、指指定値/欠測保持を検証。PNGも視認。実人物の新しい品質の合格ではない。
- 最新152045の1800フレームをresults/visibility-fingers-20260911T152045へ再処理。境界による腕除外左308/右303。腕有効1779→1469、1776→1449（端の偽追跡を除外する目的なので有効数減少を精度低下/改善率と読まない）。全5指有効の行で親指以外の角度中央値は左20.378/右38.039→両方0。正解ラベルなし・母集団差あり、本当に曲げた指の抑えすぎを次回評価する。
- 胴体は今回も未解決で推定方式は変更していない。元記録のtorso有効1793/1800、yaw p5/50/95=−22.67/−2.41/25.13度。送信角があることは人体一致の証拠ではない。症状を「回転量が小さい」「方向/別動作への反応」「遅い/止まる」のどれか非同期質問済み、まだ回答なし。既定選択を回答と扱わない。回答を次の切り分けへ反映し、根拠なく以前撤去した補正を復活させない。
- バックアップresults/checkpoints/before-visibility-fingers-mouth-20260912.zip。デスクトップ同名.bat更新済み。SPEC0.12。次は胴体の症状切り分け、画面内ぎりぎりの早期停止/復帰、指の開閉と左右符号・抑制過剰、口幅の個人差/造形を評価する。全体の汎用出力・物理・OBS等は別途未完了。

## 最新：2026-09-12 — 手首・胴体の精査と補正の整理

- ユーザーは数回前より手首回転が悪化、腕前後は前回より改善、肩（胴体）のひねりは不良と評価。「補正追加より整理」を優先指定。腕のDepthAssist/front_length_fit/0.2秒保持、3平均stride1、親指、最後の姿勢保持を維持した。
- 新しい記録150722（1800フレーム）を実Playerへ再生する診断を追加。tools/smoke_unity.py --replay-file results/control-audit/input.jsonl --output 任意.pngで起動、.audit.jsonlに送信yaw/胸yaw/左右上腕位置からの肩線yaw、掌目標と実ボーンのQuaternion角度差、前腕制限前後の角度を出す。記録dtを60Hz相当で分割してLateUpdateを進めるため実時間のカメラ遅延測定ではない。input.jsonlは元記録の送信packetとdtだけを保存。
- 変更前実測（before.png.audit.jsonl）：前腕の非制限累積角は左−608.89〜338.59、右−464.50〜799.35度。制限±100度の手前に無制限の履歴があり、動く腕/基準/掌を再生すると制限端への張り付きが発生していた。固定腕の±80度往復だけの従来試験では検出できなかった。
- 手首：無制限の累積状態を撤去。SelectForearmTwistは直前の表示角（±100以内）からraw角へのDeltaAngleを選び、その結果を±100へ制限する。履歴を積分して何周も保持しない。180境界で即反対側へ切り替わらない試験は維持。前回のStraightHandFrameと80/40楕円を削除し、ユーザーが以前良好とした時期のhandRest基準・60度円錐へ戻した。残余ねじり±40、既存の速度/平滑化、親更新前の世界回転からの補間、ForearmNeutralは維持。人間の全可動域の再現は未解決。
- 肩/胴体：追加した上腕の肘面回旋制御（upperBendAxis/upperRoll一式）を撤去。腕方向から鎖骨を15/30度等で推測駆動する処理も撤去し、肩は胸の回転を継承する元姿勢へ整理。肩すくめの独立追跡はない。Pythonの肩幅/胴高さからyawを増幅するTorsoGeometryと履歴・専用テストを削除し、肩の3D方向→yaw/roll、腰方向→pitch、共通観測確認に一本化。肩由来尺度と腕の奥行き処理は変更していない。
- torso_raw_angles/torso_shoulder_direction/torso_mode=shoulder_directionを診断に追加。変更前の実Playerは送信yawに対して胸誤差中央値0.38度、95%点5.25度、肩線誤差中央値1.03度。表示側が全く動かない状況ではない。正解人物角は記録されておらず推定yawの精度は未確定。元モデル・尺度・2観測・補間のどこで体感とずれるか引き続き分けて調べる。
- 比較結果results/control-audit/comparison.json。同じ送信1800フレーム・同じsnapshot初期条件で掌誤差中央値は左1.48→0.87度、右15.55→0.76度。95%点は左121.48→123.12度（改善していない）、右130.51→60.78度。制限外目標フレーム左692→536/右1090→146。これらは送信された掌との一致であり人体精度の改善率ではない。左の大誤差・右の残差・基準の履歴依存が未解決。
- 途中のcleaned.png.audit.jsonlは--motion-check後の関節履歴を引き継いでおりbeforeと直接比較不可。cleaned-comparableと最終finalは別起動で同じ初期条件を使用。再発防止としてsmokeの--motion-checkと--replay-file併用は引数エラーにした。今後の比較も入力と初期条件を必ず揃える。
- 最終88pytest合格0.73秒（旧幅補助2件撤去、既知の肩方向−45/−20/0/20/45度5件追加）。Unityビルドの前腕複数周後のゼロ復帰と±180境界検査成功。実Player results/control-audit/motion.png.motion.jsonで往復316.17/316.49度、最大更新約2度、170→190境界追加0度、指/欠測保持/前方制約成功。奥行き実駆動results/unity/arm-depth-1789139865987566400でdelta Z=0.286。
- 元150722をresults/control-audit/reprocessedへ再処理。共通torso有効1784フレームのyaw p5/50/95は−26.34/−2.43/19.30→−25.18/−2.43/13.13度。幅補助は435フレームで作動していた。振幅の縮小は撤去の結果で、ひねり精度向上の証明ではない。
- 変更前ソースresults/checkpoints/before-control-cleanup-20260912.zip。デスクトップ同名.bat更新成功。SPEC0.11、研究文書へ更新案内を記録。次は残る左掌の誤差区間と、モデルの肩深度/推定yawの不正確さを優先し、補正の積み増しを避ける。汎用出力・物理・OBS等の未完了も継続。

## 最新：2026-09-12 — 手首基準、上腕回旋、前方の腕長解

- ユーザーは手首制約の基準ずれ/狭さ、前後位置の不正確さ、肩が何かに反応するが不自然と申告。今回は遅延だけでなく可動域の申告として扱う。以下は実装・自動検証済みで、実人物品質は未確認。
- 手首の中立を、元アバターの掌方向から前腕軸へ最短回転で揃えて作る。元の手首の曲がりを制限中心へ残さない。従来の全方向60度円錐を、掌面に垂直な曲げ80度/横曲げ40度の楕円へ変更。左右・屈伸の非対称性や個人差までは表現しない暫定調整値。前腕±100度、残余手首ねじり±40度、連続角、速度上限、親更新前からの世界回転補間は維持。
- 上腕の肘面への軸回転を連続角化、±60度・最大360度/秒に限定。肘がほぼ直線で面が不安定なときは更新を弱め、退化時は直前値を保持。これは上腕回旋の新しい安定化であり人体の全可動域ではない。胴体yawは肩線の水平/深度から直接算出し、肩傾斜と腰深度の組合せがyawへ混入する経路を除去。肩幅補助や鎖骨の手続き的連動は残り、実際の肩角度への一致は未確認。
- DepthAssistは前方条件と支持腕長が揃った場合、投影が85%未満の骨を支持長から深度復元し4通りの符号候補を評価（front_length_fit）。手首の前方/短い上腕の前方条件、元モデルへの距離と直前深度への距離で選択する。XYは保持、前腕の体側への折返しは可能。条件を満たす候補なし/長さ学習中は既存の補助へフォールバック。条件なしでは従来のモデル補助。腕長は5秒10観測・短縮禁止を維持。
- 前方条件が2回確認された時刻から最大0.2秒を保持し、掌の単発欠測による前後反転を抑える。欠測で保持時間を延長しない。遮蔽順の真の検出ではなく、誤った前方補助・投影長の過大校正・条件漏れは残る。
- 85pytest合格0.65秒。前方腕長/投影XYの維持、前腕折返し、前方伸展、条件失効、腰深度とyawの分離を検証。Unity BuildLabは傾いた初期手首の基準補正と75度屈曲/40度横曲げを追加検証。最終ビルド成功。
- 実Player: results/unity/transport-1789139131336282600.png（.bones.json/.motion.json）。左右往復316.39/316.08度、最大1更新約2度、170→190度境界は追加0度。指・欠測保持・前方制約成功。奥行き実駆動results/unity/arm-depth-1789139131276782100でdelta Z=0.286。
- 最新145254の1800フレームをresults/joint-reference-20260911T145254/へ再処理。後方手首は左119→85、右146→116。新前方条件1083/1135、その中の負Zは0。左腕有効1285→1295、右1311のまま。比較母集団と補助条件が変わっており精度改善率ではない。追跡品質の未解決を維持する。
- 3平均/stride1、親指の専用制御は維持。変更前ソースresults/checkpoints/before-joint-reference-20260912.zip。PowerShell Compress-Archiveがモジュール読込失敗したためPython標準zipfileで保存。設定による平均方式の可逆性も維持。
- 次は前方候補の誤選択/条件漏れ、回旋上限への張り付き、肩幅補助と上腕/鎖骨の見え方を切り分ける。元モデル深度や各関節の正解値を取得済みとは扱わない。汎用出力・物理・OBS等は別途未完了。デスクトップ同名.batで最新ビルドを起動する。

更新：2026-09-11（日本時間）。AGENTS.md、docs/SPEC.md、docs/PROGRESS.md末尾も読む。

## 最新：重複する３平均、親指の専用制御、肩幅基準と前方条件の修正

- ユーザーが2回計測。肩ひねり、親指が折れる、腕が前に出ず後ろへ行く問題を申告。手首の異常回転は解消を確認したため維持。6フレーム方式は滑らかさ低下。1〜3と2〜4のような重複する平均2点へ変更を指定。
- tracking-settings.jsonは`observation_block:3, observation_stride:1`が最新（4フレームにまたがる2平均、以後毎フレーム更新）。`3,3`で旧6フレーム、`1,1`で平均なし2観測。起動し直すと反映、同じデスクトップ.batを使う。CLI `--observation-stride`とPS `-ObservationStride`も追加。クラス単体のstride=Noneは従来どおり非重複で互換維持。変更前ソースはresults/checkpoints/before-rolling-20260911-234239.zip。
- 平均化はObservationMeanへstrideを追加して全制御へ伝搬。掌は既存SO(3)平均・半回転確認・前腕連続角の修正を維持。20Hz合成ステップ90%到達は旧6方式250ms→重複100ms（平均なし50ms）。最初の変化した推論値から測った値で総遅延ではない。2平均の窓が計4フレームという意味であり、動作開始から常に4フレーム待つという意味ではない。
- 親指：他指と共通だった掌面への傾斜による付け根曲げを撤去。CMC相当の元ボーン姿勢を保持する。MCP/IP相当は親指→人差し指側の面を基準に符号付き角を算出、5度deadband、暫定上限50/65度。Unity側も親指専用軸へ変更。対向・横開きは未推定であり、完全な親指追跡とはしない。折れ軽減と引換えに可動自由度を限定している。
- 腕前方：前回は肩幅の投影で狭い領域を定義し、体をひねると手が領域外になっていた。既存3D尺度から名目肩幅を作り、その範囲へ拡大（最大投影幅3倍、左右半径1.25幅）。身体側手首と手モデル側手首の一致を要求し、中指付け根が見えれば一部指欠測でも判定。短い前腕の深度がほぼ0なら前方幾何深度を補う。以前の前方制約は維持。これは身体の遮蔽順の測定ではなく、可視手の位置と着席前提の広めの近似であり、誤って前へ出す可能性は残る。
- 肩：TorsoGeometryの正面比率をEMAで縮める代わりに、5秒内10観測で支持された最大の肩幅/胴高さ比を採用。model yawが小さいまま体が回っても基準を縮めない。深度符号条件を維持し、幅補助の混合率0.4→0.6。Unity胸/背骨をアバター基準の世界回転で駆動し、上腕にも観測された肘の曲がる面に合わせた軸回転を追加。haolanの胸local upは実測でほぼroot upに一致するため「元の胸の軸が違ったのが主原因」とは断定しない。
- 最終82pytest合格0.63秒、compileall/CLI help/PS構文検査成功。Unityビルドと実Player検証成功：results/unity/transport-1789137951960656900.png（.bones.json/.motion.json）。胸の目標回転誤差0度、親指を含む指駆動・欠測保持・前方切替を確認。手首の往復経路は左右316.31/316.16度、最大1更新約2度、180度境界は保持。実人物の新しい品質は未評価。
- 最新記録143457は1800フレーム、143733は660。最終再処理はresults/rolling-final-20260911T143457-346759Z-rtmw-l-384/ と rolling-final-20260911T143733-832184Z-rtmw-l-384/。比較はresults/rolling-report.json。手首Z負の出力は1回目左65→26/右168→37、2回目左320→55/右249→65。制約有効中のZ負は0だが、無効中の後方出力はまだ残る。母集団と判断の変化もあるため精度の合格ではない。最大UDP1700bytes。
- 1回目yaw p05/p95は−21.5/9.2→−23.7/17.5度へ変化。これは振幅変化であって実際の肩角度への一致ではない。親指付け根は常に追加曲げ0、他2関節の中央値も下がるが、人体の再現性を証明するものではない。
- デスクトップ.batを更新。次は残る前方判定漏れ/誤判定、肩の回転量、親指の方向と可動範囲を実人物で評価する。手首の既存修正を保持しながら進める。汎用書き出し・物理・OBS統合など未完了の全体項目も残る。

## 最新：３フレーム平均×２観測、前方制約、連続した前腕回転

- 最新ユーザー指示：従来の２観測を、重複しない３フレーム平均２点へ変更して試す。戻せること。体の前にある腕が背面へ回る問題、掌→手の甲で遠回りする問題を深く調査して修正。自走指定継続。
- 既定の起動はtracking-settings.jsonの`observation_block: 3`。同じファイルの値を1にして同じデスクトップ.batから再起動すれば平均化だけ従来へ戻る。PSの`-ObservationBlock 1`は設定ファイルより優先。CLIは`--observation-block {1,3}`、既定3。BodyRetarget/FaceFilter等のクラス単体既定は1で既存テスト・過去再処理互換を維持。変更前のソースはresults/checkpoints/before-average3-20260911-231440.zipに保存済み。
- ObservationMeanをDirectionGate/RotationGateへ追加。頭/表情/胴体/腕/掌/指へ伝搬。3観測の非重複平均で既存確認を進める。掌は行列平均をSVDでSO(3)へ戻す（Euler角の算術平均にしない）。初回は最初の完成平均で基準初期化、その前は新規有効姿勢を出さない。以後、区間先頭からのステップは6観測目で採用。校正の10フレームは引き続き生の有効観測。
- 掌の半回転付近のゲートで軸の符号が反転する問題も修正。完全な180度補間は方向履歴を参照。Pythonゲイン48/秒・720度/秒、Unity60/秒・1080度/秒・前腕900度/秒は維持。平均化の遅れをこれらの無断撤去で相殺していない。
- 前方条件：手の基準点を0.3以上、身体付近の投影を顔付近まで拡大。2回連続の前方手掛かりで学習中にも深度制約。前腕が折り返しても手首はカメラ側に残す。Python平滑化後、Unity IK後の実位置にも制約。`left/rightWristInFront`と`UpperInFront`をUDPへ追加、短い腕欠測保持でも引継ぐ。基準は肩相対のカメラZであり、正確な胴体表面の推定・衝突検出ではない。
- 回転：Unity ForearmNeutralで肘の曲がる面から親指側の基準を作る。肘がほぼ一直線なら前の方向を運ぶ。前腕角はDeltaAngleを積算して連続角にしてから±100度へ制限する。179→−179で+100→−100へ飛ばない。手首補間は腕を解く前の世界回転から開始。残余ねじり40度/曲げ60度は維持。制限外の向きは端で停止し、全姿勢への追従保証ではない。
- 調査成果物：[docs/ARM_ROTATION_RESEARCH.md](docs/ARM_ROTATION_RESEARCH.md)。生体モデル・姿勢依存の制約・Unity角度API・回転平均の一次資料、実装上の近似、評価結果を区別して記載。外部モデル/ライブラリは追加していない。
- 最終検証：77pytest合格0.61秒、CLI help/compileall・PS構文検査成功。Unityビルド・制約検査成功。実Player `results/unity/transport-1789136733963116900.png` と `.motion.json`：左右−80→80→−80の入力320度に対し実ボーン経路316.39/316.26度、最大1更新約2度。170→190の制限外入力は両手とも端で停止して追加0度。後方から前方条件ONの直後も実肘/手首Zが負にならない。既存の指30関節・欠測保持も成功。実人物精度の合格ではない。
- 奥行き駆動回帰：results/unity/arm-depth-1789136780295668300で平面→前方の手首Z差0.286。最新140701記録1596フレームをaverage1-final-20260911T140701/average3-final-20260911T140701へ再処理。旧出力には新しい重なり条件で手首Z負が左21/右14。新3平均で前方条件有効左145/右123フレーム、そのうちZ負は0。判定条件の母集団差があり精度改善率ではない。最大UDP1717bytes。
- `results/motion-revision-report.json`に合成ステップの待ち時間。約20Hzで従来50ms→新250ms（最初の変化した推論観測から、推論/描画時間除外）。対象記録の観測間隔中央値49.89ms。震え低減が体感遅延に見合うか未確認。短い瞬きの減衰も評価対象。
- 次の作業：実人物の親指側を通る掌反転、肘がほぼ一直線のときの基準変化、体をひねったときの前方誤判定を評価。前方補助の作動範囲や観測の取り違えは未解決。汎用書き出し・物理・OBS統合等の残作業も継続。デスクトップ同名.bat更新済み。

## 最新：停止時は最後の姿勢、掌の応答短縮、指の関節駆動

- 最新ユーザー指定：欠測保持時間が過ぎても、その他の停止理由でも最後の姿勢を保持。「追従が悪い」は到達角度不足ではなく遅いという意味。指の姿勢取得も今回から実装対象。下の古い待機姿勢復帰・指は未実装という記載よりこちらを優先する。
- Unityは部位が無効ならその部位の更新をせず、親に対するボーン姿勢・表情値を保持。人物不在/UDP停止0.3秒後はLateUpdateを止める。Pythonの最大0.12秒の腕/掌観測保持は残し、それを過ぎてもUnityでニュートラルへ戻さない。未検出を検出成功と偽装しない。初回検出前はアバターの初期姿勢。
- 指：capture_lab/fingers.pyが既存RTMW3Dの左右21点から左右各5本×3関節の屈曲角を算出。指単位の信頼度/有限値/長さ検査、1度のdeadbandと2観測DirectionGate。新規GPUモデルは追加していない。MCPは掌面からの傾斜、残る2関節は隣接骨の角度。指の横開きは送らず、親指の対向動作も屈曲近似で完全には再現しない。初回観測は他部位同様に基準初期化。
- UDP v1へleft/rightFingerTracked（bool[5]）、FingerFlex（float[15]度）を追加。順序は親指/人差し指/中指/薬指/小指、各付け根/中間/末端。配列長・有限値をUnity側でも検査、旧送信側のフィールド省略は許容。UnityはHumanoidの元のボーン軸・掌面から曲げ軸を作り、元姿勢への加算で駆動する。指欠測時はリセットしない。
- 掌の遅延対策：2観測ルール維持。Pythonの回転平滑化gain12〜36→48/秒（720度/秒上限維持）、Unity手首補間36→60/秒・速度上限720→1080度/秒・前腕540→900度/秒。前腕±100度、手首曲げ60度・残余ねじり40度は維持。腕/頭/表情のゲインは変更していない。角度制限の撤去で遅延を解決したと扱わない。
- 検証：68pytest合格0.61秒、Unity制約検証とビルド成功。実Playerのresults/unity/transport-1789135353871058500.pngで左右30関節の指定曲げ角反映、部位欠測/人物不在/ストリームタイムアウトによる全ボーンlocalRotation・表情値の不変を確認。これは合成入力と受信側状態変更のテストであり、カメラ精度・実時間の通信断復帰を測ったものではない。
- 掌合成20度ステップ/20Hz：1回目は保留、2回目採用時に18度超へ到達するテスト追加。カメラから表示までの総遅延ではない。既存134217の1108フレームをresults/fingers-20260911T134217へ再処理、指有効フレームは左733/692/666/669/686、右728/714/689/699/712。最大UDP1606bytesで4096以内。指の正確さの証明ではない。
- デスクトップtanakacap-test.batを上書き済み。次は実人物での指の曲がり方向・親指・遮蔽復帰・掌遅延の評価、前方肘位置/ひねりの推定改善を続ける。指の横開き/親指対向、髪服物理、汎用書き出し、OBS統合も残っており全体完成ではない。

## 最新：常時腕長校正（5秒/10観測・短縮禁止）、掌の補正は保持

- ユーザー指定でKによる校正開始を通常CLIから撤去。SupportedLengthsを常時動作させ、各腕の上腕・前腕それぞれ直近5秒の有効投影長の10番目に長い値を候補とする（10個以上の観測がその長さ以上）。採用値=max(旧値,候補)。検出不在・短い姿勢でも下げない。起動ごとに初期化、再起動を越える永続適用はしていない。
- 旧手動ArmCalibrationは古い記録の再処理と単体テスト用に残るが通常UIから起動しない。通常の校正はDepthAssist.lengths。arm-calibration.jsonはmode/lengths/window_seconds/min_framesの自動校正形式へ変更。プレビューはAUTO lengthsを表示。
- SupportedLengths単体10000更新の簡易測定で片腕約0.0154ms/更新。軽いCPU数値処理でありモデルのGPU要件を変更しない。支持の最低数を満たさない外れ値で最大を更新しない。支持された誤推定まで完全排除できるわけではない。
- 肘・前方伸展：補助より先に最小骨長で落とす順序を修正。前方手掛かりが確認された上腕は投影15%未満でも復元対象。異常なモデルZで骨長が過大になった時、観測XYが支持長以内なら直前の方向と支持長から補う。XYや掌の補正設定は変更しない。
- 胴体：横向きで肩の投影が交差しても、肩深度差が十分ある場合はyawを続ける。深度の裏付けがない左右反転は従来どおり拒否。全身の回転精度の解決を意味しない。
- 65テスト合格（0.61秒）。5秒窓・10観測・単発外れ値・伸長のみ・検出不在でも維持・極端な投影短縮・深度異常・横向きyawを検証。今回Unity/掌フィルタ変更なし。デスクトップ.bat更新済み。
- 最新133830/134217をcontinuous-20260911*へ再処理。133830の骨長除外は左86→49、右55→19。134217のtorso_basis除外46→28。追跡の除外減少であって精度の合格ではない。長い前方動作での検出抜けとひねりの不正確さは残る。
- 掌についてユーザーはすぐに補正を外さず現状を説明する指定。維持しているもの：2観測確認、Pythonの角度依存平滑化12〜36/秒と720度/秒上限、最大0.12秒欠測保持、Unity補間36/秒・手首720度/秒・前腕540度/秒、前腕±100度・手首曲げ60度・追加ねじり40度の制限。後者は目標姿勢への完全一致を意図的に制限する。低信頼度・退化した掌の無効化もある。どれが弱い追従の主因かは未確定。

## 最新：全体の2観測確認・顔応答短縮・体前方の上腕優先

- ユーザーが2観測確認を全体へ適用、首・表情の高速化、体の前に見える短い上腕の前方優先を指示。頭3軸、目・口にFaceFilterを追加。腕・胴体・掌も大動作の即時バイパスを撤去し、2観測へ統一。校正腕も対象。掌の二重反転ゲートは撤去して余分な待ちを防いだ。初回観測/長い断後は基準を初期化し、2観測は以後の変化に適用する。
- Unityの首と表情は有効時の補間16→45/秒へ短縮。腕・手首の高速補間と可動域制限は維持。再ビルド済み。2観測確認には約1推論更新分の遅れがあり、描画フレーム数ではない。従来の150ms合成応答値は今回より前の大動作バイパスあり条件。
- visible_in_front_of_torso：肩から腰付近の投影領域へ手首と中指付け根が入り、手の複数点と肩が十分検出されていることを前方の手掛かりとする。腰欠測は肩幅から近似領域を使う。物体の遮蔽順を直接見た証明ではない。
- DepthAssistで前方手掛かりが2観測続き、上腕の投影が既存の参考長の15〜85%なら上腕Zを前向きへ優先（幾何深度の70%）。モデルが弱い後方深度を出す場合も優先。前腕の符号は固定しない。十分な参考長がまだない場合には作動しない。XYと有効判定は維持。
- 59 Pythonテスト合格（0.62秒）、Unity制約・ビルド、実描画受信検証合格：transport-1789133765592897300.png。頭・全表情の単発保留/次観測採用、欠測、前方候補の確認、前腕保持、低信頼度除外を検証。
- 131007/131426をresults/wholebody-20260911*へ再処理。faceは保存した生2D点から再生成して確認を通す。前方優先は前者右3フレーム、後者右1フレームのみ。既存ログでは条件成立が少ないため、広範な奥行き改善を確認済みとしない。
- デスクトップtanakacap-test.batを上書き済み、K不要。通常カメラ撮影は追加していない。SPECの追跡制御合意を更新。以後の評価では2観測の遅延と瞬きの短い閉眼取りこぼし、前方手掛かりの適用範囲を確認する。

## 最優先：現在の追跡課題をまとめて実装（振動・欠測・奥行き・ひねり）

ユーザーは小変化の方向が2観測続いた場合だけ採用する案を提示し、現在の課題をひと通り実装するまで自走する指示。下記を実装・独立検証済み。実人物精度を解決済みとは扱わない。今回の範囲は追跡の既知課題であり、汎用エクスポータ・揺れ物・OBS完了を意味しない。

- motion_gate.py：腕の各軸、胴体角度、小さな掌回転で方向の継続を確認。単発の小振動は保留、同方向2観測で採用。新しい位置で静止した場合も2観測目で採用し永久停止を防ぐ。大きい明瞭な動作は即追従、100度超の掌反転は従来の連続確認を維持。腕deadband0.006/大変化0.08（肩幅正規化値）、胴体0.35/4度、掌0.6/12度は暫定値。
- 短い腕・掌の欠測は最大0.12秒だけ直前姿勢を保持。保持で期限を延長せず、人物不在で直ちに解除。*Heldと診断を記録し、新規観測と区別する。長い欠測は従来の待機姿勢へ戻す。
- body_geometry.py DepthAssist：各腕の過去90観測の投影長85パーセンタイルを下限の参考値とする。25観測・1秒以上から動作。投影短縮がありモデル深度の符号が連続して支持される場合だけ深度の大きさを半分補う。未知の前後符号は作らず、XYを書き換えず、腕の有効判定を落とさない。Kの硬い校正は依然任意の実験機能。
- TorsoGeometry：肩幅/画面内の胴体高さの比を正面付近で記憶し、幅の短縮とモデル深度の符号が整合する時だけyawを補う。腰欠測・前後方向不明・正面基準なしは元の推定。カメラ距離だけが変わる合成例では補助yawを生成しない。前傾に必要な腰がない場合の代替推定は実装していない。
- 54 Pythonテスト合格（0.60秒）。大きな動作のフィルタ簡易比較90%応答150msを維持（カメラ実遅延ではない）。4ログをresults/stability-20260911*へ再処理、stability-summary.jsonに保持数を別記。例131007の手首有効/無効切り替えは左269→111、右239→103だが、保持による減少を含むので検出精度改善ではない。
- 実Unityへ補正済み記録姿勢を送信、手首制約・有限値・描画を確認。results/unity/stability-depth.png、stability-torso.pngと各.bones.json。静止姿勢の検証であり、動的な精度の検証ではない。
- 今回はPython制御のみ変更。手首制限と腕の高速なUnity補間を維持。デスクトップtanakacap-test.batは上書き更新済み。K不要、Camera1/Diagnose/1800フレーム。確認依頼で中断していない。
- 残る限界：単眼で符号が曖昧な深度、完全に隠れた腰からの前傾、服で隠れた関節、補助深度/幅と実動作の一致は未保証。全課題の対策実装と実用品質の達成は別。次のログが来れば先に解析し、幾何補助が正しい動作まで増幅していないか・方向ゲートの遅れを評価する。

## 最新：腕応答改善を確認、手首を高速化・デスクトップ起動・奥行き切り分け

- ユーザーが腕追従改善と手首追従を確認。手首は遅いため単発反転だけ抑え、素早い連続反転は許容する指示。確認待ちで止めず次に進める指示。今後検証はデスクトップの同じ.batを毎回上書きする。AGENTSにも記録。
- 掌は100度超の急変を1観測だけ保留し、次の有効な観測でも近い向きなら追従開始。欠測で連続確認は解除。固定120ms待ちを撤去。大きい回転では平滑化を弱め、最大720度/秒。Unityの前腕540度/秒、手首720度/秒と36/秒の補間へ変更。曲げ60度・ねじり40度、前腕±100度の制限は維持。
- デスクトップC:\Users\LLMTEST\Desktop\tanakacap-test.bat作成済み。tools/update-desktop-launcher.ps1で同じ場所へ上書きする。現在Camera1/Diagnose/1800フレーム。Kは不要。ユーザーへコマンド入力や今回の確認を要求せず進める。
- 47 Pythonテスト合格。単発反転を保留、2観測目で開始、300ms時点で180度反転の法線が目標と内積>.95となる合成テストを追加。Unityビルド・実手首制約検証合格。実カメラから表示までの遅延は未測定。
- 続く奥行き調査：tools/check_arm_depth_unity.pyで既知の平面/前方入力を実プレイヤーへ送信し、肩からの手首Zが0付近→約0.286増加することを確認。results/unity/arm-depth-1789132349023619800/report.jsonと描画・実ボーン座標。Unityで奥行きが常に消失しているわけではない。任意の人物姿勢で正しいことの証明ではない。
- 最初の自動奥行き検証arm-depth-1789132289524770000はパケット未受信で失敗（原因未確定）。検証専用の空きUDPポート指定と初回受信待ちを追加して成功。ユーザーの通常39540受信と干渉させない。通常アプリは停止していない。
- 最新人物ログ130252-050911Zは471フレーム。左手首の肩相対深度p05/p95はモデル約-0.125/+0.151、送信約-0.099/+0.144名目m、右は-0.098/+0.159→-0.100/+0.143。深度レンジは送信側にも残る。ユーザー動作の正解深度がないためモデル精度は判断できない。胴体yaw p05/p95は約-10/+29度。
- 次は推定深度と人体尺度・骨長の不整合を中心に改善。校正を再度既定必須にしない。body_diagnostics.geometryにスケール、肩投影長、肩深度差を追加し、胴体ひねりと尺度の切り分けを進める。胴体専用推定更新はまだ。

## 最新：手首のねじれ改善をユーザー確認、腕の遅れを修正

- ユーザーが3回試し、手首のねじ切れなしを確認。腕は以前より遅れて見えると報告。手首の制限は維持する。以前のどのビルドとの差かは特定できておらず、遅れの増加時点を断定しない。
- results/20260911T125401-390458Z-rtmw-l-384、125540-805562Z、125707-867845Z（同じ接尾辞）を解析。1200/1191/446フレーム、全て校正なし。更新間隔中央値49.4/50.0/50.1ms、取得後〜推定結果中央値63.1/64.6/64.3ms。露光から描画までの遅延ではない。
- capture_lab/arm_filter.py追加。XYとZの速度制限を分離し、奥行きの異常がXY腕上げを抑制しないよう修正。小変化は従来相当の平滑化、大きいXY変化は応答を上げる。奥行きの抑制は維持。
- Unityの有効腕だけ補間係数を16→36 /秒へ変更。顔・胴体・手首の平滑化と手首制限は維持。再ビルド済み。
- 45 Pythonテスト合格（0.56秒）。Unity制約・ビルド、記録姿勢の実手首可動域検証合格：results/unity/transport-1789131658884842200.pngと.bones.json。新規カメラ計測なし。
- tools/check_arm_response.py：20Hz入力＋60Hzのスカラー描画近似で単位ステップ90%応答283→150ms。results/arm-response-synthetic.json。これはカメラ・推論・UDP・実IK・Quaternion描画を含まない合成比較で、実遅延の半減を意味しない。
- 3記録の再処理はresults/responsive-20260911T125*。追跡有効数・切り替え数は変化なし。新旧の実際の動作遅延・震えの評価は未完了。2回目の掌有効数は左121/右9と低いので、ねじれなしの報告を掌追従全般の合格としない。
- 次もKなしで通常起動し、腕の遅れと震えの交換条件を評価。奥行き精度・胴体ひねりは未解決。下段の42テスト・再ビルド不要は前段階の情報。

## 最優先の最新状態：校正後の腕追従悪化を修正

ユーザーは校正版で腕上げが悪化、前後も改善なし、腕が不明瞭で手首を評価できなかったと報告。results/20260911T124706-908428Z-rtmw-l-384を受領・解析済み。1200フレーム中1114で校正値あり、左406・右519をcalibration_inconsistentで停止していた。推定骨長は左0.192/0.154、右0.190/0.165（名目m）。後の投影が骨長を超え、短い骨長にクランプして深度をゼロへ寄せる処理も問題だった。校正操作の不履行と扱わない。

- 今回Pythonを修正。校正矛盾時は腕を止めず、その腕を従来のモデル追従へフォールバック。15〜30観測の半数超で校正長の1.15倍を超す投影を見たら校正を自動解除、画面にMODEL tracking restoredを表示する。解除根拠・旧校正値を記録。
- モデル追従用のスケールを継続推定し、腕校正で胴体・掌のスケールを変更しない。校正長の1.05倍超の投影では固定長復元を使わずモデルへ戻す。腕の観測信頼度・異常骨長のチェックは維持。
- 同じ記録の再処理results/recovery-20260911T124706：左794→1192、右668→1172有効、切り替え左70→10、右81→20。校正解除はframe240。解除後は旧モデルの奥行き推定なので、奥行き精度改善を達成済みとしない。
- 42テスト合格（0.58秒）。短すぎる校正でも腕が動く、継続矛盾の自動解除、胴体の独立性を追加検証。Unityコード変更なし・再ビルド不要。前腕回旋・手首制限は維持しているが、ユーザーの見た目評価は未完了。
- 通常終了でbody_modelをNoneへ戻すためarm-calibration.jsonが保存されないバグも修正。今後は通常終了でも校正値とarm-calibration-status.jsonを保存する。
- 次は**まずKを押さず** .\run-avatar-lab.ps1 -Camera 1 -Diagnose -Frames 1200 で以前の腕上げが戻るか評価。校正は実験機能として残すが、今回再校正を必須にしない。根本的な校正の短縮・単眼深度の符号問題は未解決。以下の「最初にK」は前段階の手順であり、この最新指示を優先。

## 許可と現在地

ユーザーは実装開始と6フェーズの文書化を承認済み。実装完了まで再確認せず自走し、重大な疑問だけ質問する指示。通常の作業で開始許可を取り直さない。環境の権限制約は別途守る。

フェーズ1の人物精度評価が残る状態で、フェーズ2の独立Unityアプリ表示・駆動接続まで先行実装。実カメラ→GPU推論→Unity受信を確認済み。人物の動作精度、揺れ物、汎用変換、OBS出力の検証は未完了。Gitリポジトリは未作成。

最新：ユーザーが骨長校正案での実装継続を承認。**腕校正＋固定骨長の奥行き復元、掌の急反転抑制、前腕回旋と手首制限を実装・Unity再ビルド済み。** カメラプレビューのKキーで校正開始、正面で両腕を横〜斜め下へまっすぐ伸ばし約2秒静止。画面のArms calibratedを確認。Cキーは従来どおりUnity側の胴体中立。腕校正の初期値は未設定で、K操作前は旧奥行き経路を維持する。

首の追従、Z閾値修正後の腕上げ・掌の改善はユーザー確認済み。今回の骨長校正・手首制限は実使用評価待ち。胴体ひねりの品質は未解決。校正後は肩幅の見かけの変化を距離変化として毎フレーム吸収しないが、胴体専用の新しい向き推定は未実装。

## 今回実装した校正・制約と検証

- capture_lab/arm_constraints.py：2秒以上・30点以上の安定した直線腕を観測し、仮定肩幅0.36mに対する骨長と投影スケールを保持。実際の人体cm計測ではない。12秒で失敗、再校正失敗なら前の値を保持。カメラ距離を変えたら再校正。セッションごとに校正し、自動読み込みはしない。
- 長さと投影から前後4候補を列挙。肘155度上限、前フレーム、モデル奥行き、身体前方の弱い優先で選ぶ。カメラ方向へ一律固定しない。方向を平滑化しても骨長は維持。投影が校正長の1.3倍を超える時はcalibration_inconsistentとして除外。校正中の画像面内姿勢はユーザーの操作条件であり、単眼で完全に検証できない。
- PalmFilter：65度超の変化は約0.12秒持続を確認、回転を平滑化・240度/秒制限。真の180度の掌返しが持続したら追従する回帰テストあり。欠測の長い復帰で状態をリセット。短い欠測の既定姿勢戻りは課題。
- Unity：前腕軸回旋を±100度へ制限しつつ分担、手首は中立から曲げ60度・追加ねじり40度の暫定上限。補間後も制限を適用。人体の個別可動域を測った値ではない。腕ごとのtwistボーンへの分散は未実装。
- 40 Pythonテスト合格、Unity腕・手首制約テストとビルド合格。実プレイヤーの固定姿勢検証はresults/unity/transport-1789130533585826000.png、transport-1789130587200393900.png等。旧smokeの「任意の入力回転に完全一致」から「制約内の実ボーン姿勢」へ検証を変更。制約にかかる入力は完全一致させない。
- 3記録を再処理：results/constraints-20260911T12*。掌の隣接有効フレームの角度変化p95は約64〜129度から約11〜13度へ。results/constraints-palm-comparison.json。記録には校正操作がないため、この比較は掌フィルタを評価し、校正した腕の実人物精度は評価しない。
- 診断時はbody_diagnostics.calibrationに校正値、*_constrained_lengthsに補正後骨長を保存。終了時arm-calibration.jsonにも保存。tools/replay_body.pyはログ内の校正を再適用する。
- 次の実使用では、校正成功表示→前方伸展→掌返し→胴体ひねりを評価。腰が映らない前傾、透視・距離変化、遮蔽、復帰の震えは残る制約。無人カメラ計測を追加して精度合格にしない。

## 最新の診断と次の評価

### 追加評価受領：3回の実使用と骨長校正の提案

- 最新ユーザー評価：腕上げ・掌の動きは改善。胴体ひねり、腕の前後位置、手首の過剰なねじれ、震えは未達。直前の「修正後の実使用評価待ち」はこの評価で更新する。
- results/20260911T121810-770318Z-rtmw-l-384、121949-460742Z、122120-307173Z（後二つも同じモデル接尾辞）を確認。1200/1200/660フレーム。集計はresults/analysis-20260911-three-trials.json。
- 1回目の左前腕推定長p05/p95は約0.076/0.379m。掌法線の隣接フレーム間の最大変化は各試行・左右で約165〜178度。モデル出力・近似復元の不安定性があり、検出率だけでは品質を判断できない。胴体yawはゼロ固定ではないが正解動作との対応は未確認。
- ユーザーは「初期に上腕・前腕の長さを校正し、曲がる方向をカメラ側へ制限して投影長から奥行きを求められないか」と提案。返答方針：骨長固定は有力、画面内の長さと同単位なら弱透視近似で奥行き差は±sqrt(L²-dxy²)。符号の曖昧さ、カメラ距離・透視の影響、正面付近のノイズ増幅が残る。カメラ前方への一律固定は、身体をひねる／肘を引く動作を壊すため、身体基準の関節制約・前フレーム・モデル深度を組み合わせる試作を提案する。
- 校正はカメラと平行に近い姿勢を複数フレーム観測して骨長比と投影スケールを推定する案。画像だけで絶対cmを計測済みにはしない。現在Cキーは胴体中立のみ、腕校正は未実装。今回の変更は解析と文書のみ。
- 次の実装候補は校正付き腕復元、掌反転の時間整合性、前腕への回旋分配と手首可動域制約。胴体ひねりは肩幅・胴体方向とスケールの推定を別に改善。骨長制約で全問題が解けると扱わない。

- 計測は受領済み。準備確認を再度求めない。440フレーム中、身体座標あり407、人物なし33。元の数値ログは保持。
- 同じ記録をtools/replay_body.pyで再処理。results/replay-20260911-depth-confidence/report.jsonに比較、packets.jsonlに修正後の送信値を保存。胴体143→407、左腕40→386、右腕108→402、左掌30→327、右掌90→287フレーム有効。分母は全440フレーム。これは有効判定数であり精度ではない。リプレイは記録前のウォームアップ状態を持たない。
- 修正後も左腕21・右腕5フレームを骨長で除外。掌の有効／無効切り替えは左54・右57回あり、連続性は課題。身体推論と幾何判定の残る誤差を次に調べる。単に閾値を緩めて有効率を上げることを品質改善と扱わない。
- 32 Pythonテスト合格。記録のframe286と450（左掌法線の差約148度）を各々固定して実プレイヤーへ送り、左右の実手ボーン方向が入力と一致することを検証。results/unity/transport-1789102640241808400.png、transport-1789102654410042000.pngおよび各.tracking.json/.bones.json。描画も確認。元の動作の正解値はなく、推定精度や動的な追従を証明する検証ではない。
- 起動：.\run-avatar-lab.ps1 -Camera 1 -Diagnose -Frames 1200。まず正面でC、腕上げ・前方伸展・ひねり・掌返し。カメラを繰り返し勝手に起動して無人結果を集めない。数値ログだけでできる再処理はtools/replay_body.pyを使う。
- 公式根拠、再現手順、残る限界はdocs/UNITY_LAB.mdとdocs/PROGRESS.md末尾。

## 実装済み

- capture_lab/：カメラ最新フレーム取得、RTMW/DWPoseの133点2D推定、YOLOX人物検出、3連続検出による姿勢開始。CUDA必須、実行プロファイルで主要演算のCPUフォールバックを検査。
- setup-lab.ps1、run-lab.ps1：導入と診断プレビュー。モデル3個を取得済み、ハッシュ・出典は各model.receipt.json。再配布条件の最終確認は未完了。
- tools/camera_modes.cpp：Media Foundationで名前・ネイティブモードを列挙。VS2022 Communityでビルド済み。
- tests/：最新フレーム、切断、座標変換、GPUプロファイル、検出出力、連続検出ゲート、部位別無効化、ローカルUDP送受信、3D深度復元・符号・欠測・速度制限、掌向き・退化、片側肩欠測と胴体失敗の分離、Zピーク変動と非有限値の回帰。32テスト合格。Unity内の腕の極端姿勢4ケースも合格。
- capture_lab/body3d.py：XYピクセルとZ相対メートルの単位を分け、仮定肩幅0.36 mで近似復元。画面外の腰は無効化し、欠測時に前傾を捏造しない。腕の深度変化を制限・平滑化。
- capture_lab/hand_orientation.py：手首と示指・中指・小指の付け根から掌の長軸・法線を作る。指の個別駆動は未実装。Unity側は人型の指ボーンからアバターの掌基準を取得して姿勢を反映。退化／低信頼度では手首を既定へ戻す。
- unity/TanakaCap：haolan表示、UDP受信、頭・口・まばたき・胴体・腕の暫定駆動。builds/lab/TanakaCap.exeをビルド済み。run-avatar-lab.ps1で起動。
- tools/prepare_unity.py：BOOTH原本の安全な取り込み。原本保持、作業コピーの変更済みファイルは上書き拒否。
- tools/smoke_unity.py、tools/check_live_unity.py：実プレイヤーの合成制御・実カメラ接続検証。
- docs/IMPLEMENTATION_PHASES.md：ユーザーが採用した6フェーズ。docs/CAPTURE_LAB.md：実行方法と限界。

## 実機と依存

RTX 4090（24564 MiB、driver 595.71）、i9-12900KS、約64 GB、Windows 10 Pro 10.0.19045を確認。Python 3.11.16、ONNX Runtime GPU 1.30.0、OpenCV 5.0.0.93、numpy 2.4.6。推移依存はrequirements-lab.lock.txt、仮想環境は.venv。uvはユーザーの.local/bin、キャッシュは.cache/uv。

カメラ番号0はDroidCam Source 3（仮想カメラ）、1がHD webcam-CMS-V43BK。実機1はMSMFで1280×720取得、ネイティブに30fpsモードあり。番号は列挙順に依存。初期の番号0・640×480の結果を実カメラの測定と扱わない。DSHOW0失敗も実カメラの非対応証拠ではない。

## 測定結果

すべて短時間・プロファイラ有効、OBSやUnity描画なし。精度や動作から表示までの遅延ではない。

| 結果フォルダ（results/以下） | 条件・結果 |
|---|---|
| 20260911T031433-914512Z-rtmw-l-384 | 人工入力100計測フレーム。中央値7.62 ms、p95 8.56 ms |
| 20260911T031450-812921Z-dwpose-l-384 | 人工入力100計測フレーム。中央値5.61 ms、p95 6.18 ms |
| 20260911T032439-783959Z-rtmw-l-384 | 実カメラ1、固定全画面ROI、90計測。中央値12.42 ms、p95 20.56 ms。人物検出なし、精度評価に使わない |
| 20260911T032804-719801Z-dwpose-l-384 | 実カメラ1、固定ROI、90計測。中央値8.72 ms、p95 11.66 ms |
| 20260911T033655-395640Z-rtmw-l-384 | 人物検出＋3連続確認。90計測でpose_frames=0、中央値20.47 ms、p95 24.16 msは人物検出処理。姿勢CUDA記録3回は起動ウォームアップのみ |

固定ROIの診断画像で人物不在でも多数の点が出たため、人物検出を追加。一瞬の誤検出もあったので3連続確認を追加した。最新90フレームでは姿勢の誤起動なし。ただし在席・着席時の検出成功や遮蔽復帰は未評価。ORTがplugin EP device関連の警告を出すが、プロファイル上のCUDA演算実行を確認。CPU補助演算Slice/Concatは記録しており、CPU主要演算なし。

## アバター取得・Unity表示：確認済み

ユーザーがBOOTHから取得したHAOLAN_Ver1.6.zipをassets-sourceへ配置。既存の改変プロジェクトは使わず、このZIP内のPC用unitypackageから73アセットを独立Unityプロジェクトへ取り込んだ。ZIPのSHA256はTHIRD_PARTY.md、取得・取り込み履歴はassets-source/unity-import.receipt.json。

- 公式：https://booth.pm/ja/items/3818504
- 掲載ファイル：HAOLAN_Ver1.6.zip、218 MB、無料。
- 公開ダウンロードリンク：https://booth.pm/downloadables/3318795?variation_id=6359201
- ダウンロードのログイン問題はユーザーのZIP配置で解決。再度取得を依頼しない。
- 作者指定Google Driveから日本語規約PDFを取得し、本文を確認。クレジット「かなリぁ」を記録し、ビルドに素材情報と規約PDFをコピー。詳細はdocs/THIRD_PARTY.md。
- lilToon公式2.3.4を取得、独立Packagesへ導入。インポート後のマテリアル変換は作業コピー内のみ。
- Unity 2022.3.22f1は導入済み環境を用いたローカル検証限定。一般配布前にセキュリティ修正版へ更新・再検証する。公開配布版の採用決定ではない。
- VRC等の未解決コンポーネント71個をシーンのインスタンスから削除し、results/unity/avatar-inspection.txtへ列挙。揺れ物やVRC機能は保持済みと扱わない。
- vrc.blink_*の最大変位は約0.0002〜0.0003、実際には閉眼しなかった。変位約0.0276のウィンク２／ウィンク２右へ変更し、描画画像で片目の閉眼を確認。左腕はアバターの-X方向。初期待機姿勢の左右反転も修正。
- 合成制御の受信・描画検証：results/unity/transport-1789099792010103200.png と .tracking.json。実カメラ接続：results/unity/live-1789099807860645400、sequence=144を受信。person_tracked=falseなので人物の追跡品質の証拠ではない。

## 最新の3D身体検証

- RTMW3D-XはRTMlibが案内するコミュニティONNX変換。SHA256はTHIRD_PARTY.md、重み369330857 bytes。再配布判断は未完了。
- 公式MMPose設定のinput_size=(288,384,288)、出力576/768/576 binsを照合。深度の分母は288。画像高さ384を使わない。RGB入力は新しい身体モデルにのみ適用、既存顔経路は維持。
- 人工黒画像で顔＋身体60計測、中央値22.96 ms / p95 24.59 ms、results/20260911T042245-750828Z-rtmw-l-384。人物検出なし・プロファイラ有効。身体CUDA83呼び出し、CPU演算なし。
- 3Dの実描画確認：results/unity/transport-1789100899257024500.png と .tracking.json。腕の奥行きと胴体回転を受信・描画。
- 実カメラ＋3D経路：results/unity/live-1789100934531380800、sequence118受信。results/20260911T042854-734378Z-rtmw-l-384で300計測、人物追跡0。身体CUDA3回は起動ウォームアップ。新モデルの実人物精度を実証したわけではない。
- Unityは背骨と胸へ回転分配、首をカメラ基準で独立維持。肩の動きは腕と連動させる近似で独立推定ではない。腕は実骨長を使う幾何IK、肘5〜155度。手首回転は実装済み、衝突は未対応。
- Cキーをアバターウィンドウで押すと胴体の現在姿勢を基準にする。腰が画面外では前傾は停止する仕様上の制約が残る。

## 再開・次の作業

1. 更新したrun-avatar-lab.ps1で、手をカメラへ伸ばす・肘を曲げる・胴体をひねる動作を評価。首の良好な追従はユーザー確認済み。新しい身体推論は無人測定で精度合格にしない。
2. 同じ人物映像で2モデルの精度・遮蔽を比較。顔専用モデル・3D姿勢・個人キャリブレーションは未実装。現在の顔制御は2D比率による暫定近似。
3. 追加した奥行き・肘制約の実用性、腰が映らないときの前傾、肩幅近似と遮蔽時の誤推定を調整。顔・目・口も評価。0.3秒受信途切れで待機姿勢へ補間。
4. フェーズ2の動作評価後、汎用変換とOBSへ。髪・服の揺れ、透過出力、OBS側の実取り込み検証はまだない。

実行：.\run-lab.ps1 -Camera 1。試験：.venv\Scripts\python.exe -m pytest -q。直接CLIはカメラ既定0のため必ず --camera 1 を指定する。詳細はdocs/CAPTURE_LAB.md。

アバター付き：.\run-avatar-lab.ps1 -Camera 1。再ビルド：.\build-unity-lab.ps1。操作と制限はdocs/UNITY_LAB.md。Pythonからは--unity-port 39540で接続。外部アドレスへの送信機能はない。

カメラアクセスはサンドボックス内で失敗し、require_escalatedで成功した。pytestは通常権限で合格、昇格実行ではtmp/cacheアクセス権問題が出たため、意味なく昇格しない。失敗結果もresults/へ残している。意味のある変更後は本ファイルと追記ログを更新する。
