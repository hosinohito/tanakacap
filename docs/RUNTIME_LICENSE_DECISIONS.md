# NVIDIA・FFmpeg・Unityの配布判定（2026-09-13）

公開資料と使用中の実物を照合した結果。ユーザーのUnityプランは **Personal**。
従来の3件は以下の条件付きで配布可と判断し、確認中から外した。GitHubへの公開は行っていない。

| 対象 | 判定 | 守る条件・今回の対応 |
| --- | --- | --- |
| NVIDIA CUDA / cuDNN / nvJitLink | アプリへの同梱可 | NVIDIA GPU用のTanakaCapの一部としてDLLを使用。SDK単体配布・独自コードMITへの再許諾はしない。公式採用版契約を追加、元wheel本文も保持 |
| OpenCV内部FFmpeg | LGPL-2.1条件で同梱可 | 通知・対応ソース・ビルド手順を同梱し、DLLの差し替えと改変のデバッグを認める。アプリ全体をGPLにする必要はない |
| Unity 2022.3.22f1 Personal | 作成アプリの配布可 | Personalの財務条件を満たすこと。Unityランタイムを製品へ組み込んで配布、ロゴと第三者通知を保持。実行ユーザーのEditor導入は不要。変換プラグイン利用時は各自のEditorが必要 |

## NVIDIA：古いwheel契約の問題をどう解消したか

Web上の最新版を任意に代入したのではない。NVIDIA公式の採用版再配布マニフェストを参照した。

- CUDA 13.4.1: https://developer.download.nvidia.com/compute/cuda/redist/redistrib_13.4.1.json
- cuDNN 9.26.0: https://developer.download.nvidia.com/compute/cudnn/redist/redistrib_9.26.0.json

CUDA側はcudart 13.4.49、NVRTC 13.4.59、cuBLAS 13.7.0.27、cuFFT 12.4.0.34、cuRAND 10.4.4.49、nvJitLink 13.4.52。すべて採用wheel版と一致する。CUDA契約Attachment Aの各ライブラリ系列と版番号付きファイルの規定で確認。

問題だった **cuDNN 9.26.0.51 CUDA13 Windows ZIPとnvJitLink 13.4.52 Windows ZIPを実際に取得**し、公式マニフェストのSHA-256一致を確認。そのZIP内のcuDNN 10 DLL・nvJitLink 1 DLLが現行wheelとSHA-256一致した。ZIP内のLICENSEではcuDNNのruntime `.dll` が対象、CUDA Attachment AにはNVIDIA JIT Linking Libraryも明記される。旧wheel補足のcuDNN7限定・nvJitLink欠落を、同じバイナリの公式配布物で解消した。

原文はrelease/notices/NVIDIA-*.txt、出所と本文SHAはruntime-notice-sources.json、公式ZIPとDLL対応はruntime-license-evidence.json。全20 DLLを固定し、変更時は監査を失敗させる。残るCUDA9 DLLは版・ライブラリ系列との照合で、今回公式ZIPとの全ファイル一致まで行ったのは上記11 DLL。

契約条件はアプリに追加機能があること、SDK部分をアプリ専用にすること、適合する利用条件・権利表示を保持することなど。ドライバーは同梱せず利用者が導入する。TensorRT不採用は変更しない。

公式本文: https://docs.nvidia.com/cuda/eula/index.html

## FFmpeg：実DLLから対応ソースまで

実物はopencv-python 5.0.0.93の `opencv_videoio_ffmpeg500_64.dll`。
SHA-256: `7aabff029d1fa47cf56ede4dbbe05dc62da3208f07cd16471d4c966a33f9aa31`。
対応source branch内のDLLのGit blob SHAも現物と一致（117f46365f6bba0d0553989a96d86e10d2d89d39）。OpenCV 5.0.0のffmpeg.cmakeが指定するMD5 `a821a1135251859655090c795af05789` と一致。

- バイナリcommit: `06dc20cad65dc7fcf784f70c95d46750520889a7`
- 対応source commit: `664c0098dcb47b361f20c1d6a518653c23f5f2b5`（ffmpeg/5.x_20260602_src）
- OpenCV wrapper/core: `a0a660fcb1e58a295e6caa6aee64ed4d369b0181`
- FFmpeg n7.1 / libvpx v1.16.0 / AOM v3.14.1 / OpenH264 API v2.5.0

https://github.com/opencv/opencv_3rdparty/tree/664c0098dcb47b361f20c1d6a518653c23f5f2b5

公式source branchの全ソースとDocker/MinGW手順を取得。OpenH264ヘッダーtarが空、OpenCV tarがwrapperの一部のみだったため、ビルド指定のOpenCV commitとOpenH264 v2.5.0 commitの完全ソースを追加した。原本は改変せず、BUILDING.txtに展開・ビルド・DLL差し替え手順を記載。Git blobとSHA-256を照合しrelease/ffmpeg-source-lock.jsonへ固定。

`tools/prepare_ffmpeg_sources.py` が `assets-source/licenses/opencv-ffmpeg-sources.zip` を作る。ビルドはこれを `ライセンス/sources` へ同梱する。約161 MB増えるため、従来の約2.085 GB単一ZIPと合わせると2 GiB上限を超え、既存の連番ZIP分割処理が働く。ソースZIP自体をGitへコミットしない。実物DLLは無変更。ソースからの再ビルド・bit単位一致は未検証。

GPL/nonfreeを有効化するフラグはない。OpenH264はヘッダーと動的ローダーのみで、Ciscoのコーデック本体は同梱しない。開発動画作成用ffmpeg.exe（別のGPLビルド）も製品へ同梱しない。

配布根拠: https://ffmpeg.org/legal.html 、上記公式source branchのreadme.txt/license.txt。

## Unity Personal：契約・ランタイム・通知を区別

https://unity.com/legal/editor-terms-of-service/software （2026-06-30版）

§1.1の現行Personal上限は直近12か月のTotal Financesが20万USDを超えないこと。個人の自分の制作、法人、顧客への受託で算定対象が違うため、TanakaCapの売上だけを全員の基準にしない。Personal使用はユーザー申告で確認、財務資料を検査したという意味ではない。

§2.2はUnity RuntimeをProjectの組み込み部分として配布する権利を明記し、Unity 6以前もロイヤリティ・売上分配・Runtime Feeなしの対象。Personalだから無料配布しかできない、実行者にもEditorが必要、という条件はない。今回の対象はWindows上の娯楽配信用アバターアプリで、Editorをクラウド提供するサービスではない。プラットフォーム/SaaSへの将来変更は別に確認する。2022系PersonalのUnityスプラッシュは維持し、ProjectSettingsのshow screen/logo両方が1を確認。[2022.3の公式スプラッシュ条件](https://docs.unity3d.com/2022.3/Documentation/Manual/class-PlayerSettingsSplashScreen.html)。

内部ライセンスはEditor全体のlegal.txtだけから判断せず、公式[2022.3.22f1配布ページ](https://unity.com/releases/editor/whats-new/2022.3.22f1)の **Player / Windows / Mono専用TPN（32ページ、commit 887be4894c44）** を取得し全文同梱。ここにEditor側LAME/7-Zipを混同してPlayerへ対応ソース義務があるとした懸念は撤回。Playerの公開部品一覧にGPL/LGPL指定はなく、商用内部部品はUnityのランタイム許諾で扱う。独立したMonoBleedingEdgeのMIT通知も保持。

KlakSpout 2.0.6のUnlicense、内包SpoutのBSD、Unity Plugin APIのCompanion Licenseを保持。WIDL生成d3d11on12.hはCOM型宣言・定数・短いinlineのヘッダーで、Wine実行ライブラリのリンクではない（LGPL2.1 §5）。元IDLの著作権とLGPL本文も補足して残した。WIDLというツール名だけを根拠にPlayer全体へLGPLを拡張しない。

## 検査・公開状態

`tools/collect_runtime_license_evidence.py` は公式2 ZIPのSHAと現行DLL11個を再照合する。`tools/prepare_ffmpeg_sources.py` は固定ソースと現行FFmpeg DLLを検査。ビルド監査は通知20件、全NVIDIA DLL、FFmpegと対応ソースZIPを照合する。

公開ライセンスの未確定3項目は解消。`publication_approved=false` は最終リリース承認・品質確認のゲートとして残し、ライセンス禁止を意味しない。現在までのreview6 ZIPは今回の通知・対応ソースを含まないので、そのまま公開しない。新規PCや人による品質確認を今回の法務資料調査で合格扱いにしない。

検証完了：review7を既存release-playerから再梱包（Unity再ビルドなし）。part01=2,084,961,237 bytes、part02=162,028,059 bytes、計12,918ファイル。双方2 GiB未満・CRC合格。通知20/NVIDIA DLL20/全binary194、Unity runtime3のSHA、FFmpeg/source lock照合エラー0。同梱Python起動成功、FFmpeg不一致を模擬した拒否検査成功。resultsではなくbuilds/releases/0.1.0-review7/{release-report,license-audit}.jsonが検査結果。Playerの新規動作品質を今回確認したものではない。oversize-local-only.zipは公開対象外。
