2026-09-13追加：tanakacap.bat / run-ui.ps1は操作画面のみを開く。開始までカメラを起動しない。カメラ/録画/自作モーションをUIで選び、停止/設定適用は子プロセスを終了する。UI設定はui-settings.json、従来batとは別。CONTROL_PANEL.md参照。

2026-09-13表示ルール：実写は通常/診断/比較撮影でも非表示。完全一致の長い専用起動オプションのみ許可（[開発手順](DEVELOPMENT.md#開発ui設定ログ)参照）。通常batへ自動追加しない。アバター表示とOBSは従来どおり。

# 起動モード（2026-09-13）

最新試行（2026-09-13）：通常body3d/pnp、ピッチはPnPを維持し、口輪郭から推定Zを外す。`-HeadPoseMode pnp_depthmouth`で直前のZ口輪郭へ戻す。顔の向きを補正する固定テンプレートは残す。[比較動画と設定](MOUTH_NO_Z_TRIAL.md)。

デスクトップのbatは `tools/update-desktop-launcher.ps1` で生成・更新する。

| bat | 用途 | 動作記録 | 終了 |
|---|---|---|---|
| tanakacap-test.bat | 全部ON・PnPピッチ＋推定Zなし口輪郭 | 数値/診断ログあり | 1800フレーム、またはアバターを閉じる/Ctrl+C |
| tanakacap-test-mouth-z.bat | 全部ON・直前の推定Z口輪郭 | 数値/診断ログあり | 1800フレーム、またはアバターを閉じる/Ctrl+C |
| tanakacap-test-face-pnp.bat | 全部ON・同じRTMW3D-X顔でPnP対照 | 数値/診断ログあり | 1800フレーム、またはアバターを閉じる/Ctrl+C |
| tanakacap-test-face-original.bat | 全部ON・従来RTMW-L顔方式 | 数値/診断ログあり | 1800フレーム、またはアバターを閉じる/Ctrl+C |
| tanakacap-compare-face.bat | 顔比較動画の保存先を開く | なし・カメラ不使用 | Explorerで確認 |
| tanakacap-compare-f.bat | 高速化FのOFF／ON比較動画の保存先を開く | なし・カメラ不使用 | Explorerで確認 |
| tanakacap-head-only.bat | 頭専用auto | なし | 制限なし。アバターを閉じるかCtrl+C |
| tanakacap-live.bat | 普段使いのカメラ版 | なし | 制限なし。アバターを閉じるかCtrl+C |
| tanakacap-motion.bat | カメラを使わないモーション版 | なし | 制限なし。アバターを閉じる |

通常版はいずれも更新した外部haolan.tcapを読み、表情はexisting（既存キー優先）が既定。F6は髪・服の揺れON/OFF、F3はOBS向け表示。Spoutの送信名TanakaCapは共通。使いたい版を一つ起動する。

2026-09-13追加：両PowerShell起動スクリプトは`-ExpressionMode existing|auto-custom`を受ける。`tanakacap-test-auto-expressions.bat`はカメラ検証用、`tanakacap-motion-auto-expressions.bat`はカメラなし/非記録/無期限。`tanakacap-demo-custom-brows.bat`は例外としてbuilds/demos/haolan-custom-browsの旧Playerと専用.tcapを使う保存デモ（カメラなし/非記録/無期限）。通常ビルドで上書きしない。`tanakacap-compare-expressions.bat`は録画比較の顔拡大動画を選択表示する。詳細docs/EXPRESSION_PORTABILITY.md。

非記録版ではframes.jsonl/結果レポート/校正レポート/スナップショット/ORT profilingを生成せず、メモリ内のフレーム履歴も1件に制限する。Unityは-nolog。GPUの明示指定とCPU-only拒否は維持するが、ノード別の実測監査は検証版で行う。起動エラーの画面表示やOS/ドライバーのキャッシュまで無くす機能ではない。過去の記録を消さない。

モーションは `ProceduralMotion.cs` の自作24秒周期。首振り、体のロール/ヨー、左右の腕の上げ下げ、指、瞬きなどを合成し、同じアバター駆動へ入力する。カメラ、推論、UDP受信は起動しない。これは追跡品質のデモではない。

外部モーション素材・人物の録画は使っていない。このソースと生成モーションは0BSDとし、利用・改変・商用/非商用再配布に表示義務を加えない。docs/PROCEDURAL_MOTION_LICENSE.txtを参照。モーションの許諾とHAOLAN/シェーダー/Unity等の許諾は別で、アバター原本の再配布許可を意味しない。

直接起動：run-avatar.ps1 -NoLog / run-motion.ps1。アバター指定はどちらも-Avatar。カメラ版はtracking-settings.jsonの採用設定を引き継ぐ。

検証：tests/test_no_log.pyで保存処理が呼ばれないこと、無期限ループがPlayer終了で止まること、保存指定との競合拒否を確認。実GPUモデルのsynthetic 3フレームでも非記録で終了成功。30分連続の実カメラ安定性は未確認。

追加検証：モーション版の4秒起動で既定Player.logとresultsフォルダーが増えないことを確認（results/secondary-motion/no-log-smoke.json）。モーションの実描画と終了code0はmotion-final.png/log。

## 2026-09-13 CUDA FP16比較

ユーザー指定で通常test/liveをFP16へ統一、FもON。`tanakacap-test-fp16.bat`は互換用に通常testと同じ内容を維持。FP32を選ぶ起動引数・設定キーは削除済み。内部APIは将来UI追加の可能性に備えて保持するが、UI実装の確約ではない。比較動画の場所は`tanakacap-compare-fp16.bat`。実カメラ試験はユーザーの明示指示があるまでエージェントが実行しない。頭専用モードの精度は変更しない。

## 2026-09-12 描画の追加設定

全起動で追加の軽量AAを既定ON。F7で切替、両PowerShell起動スクリプトの-NoEdgeAAで起動OFF（元のMSAAは維持）。Spout出力はFull HD（1920×1080）既定。-OutputWidth/-OutputHeightで各64〜4096の自由指定、幅省略は16:9。-NoPreview/F8でプレビューだけ非表示、-LegacyPreviewで旧二重描画へ復帰。通常はOBS画像をプレビューに共有。ウインドウサイズ/カメラ入力は独立。非記録・無期限・モーション専用の挙動はそのまま。[詳細](SHARED_PREVIEW.md)。

Playerの--performance-logと--performance-secondsは明示的な検証専用。live/motion版は渡さない。検証版-Diagnoseはresults/player-performanceへPlayer統計を記録するが、新たな自動終了時間は指定しない。GPU計測はさらに--performance-gpuを指定する。検証の保存先と条件はPHASE4_VALIDATION.md。

## 2026-09-12 統合構成オプション

共通run-avatar.ps1の-TrackingMode full（既定）/face_head/head_onlyで切替。tracking-settings.jsonにもtracking_mode。-NoBody/-NoGaze/-NoPersonDetectorの個別OFFは推論生成を省略。-HeadOnlyはhead_onlyの別名。頭専用ショートカットtanakacap-head-only.batは-NoLogで無期限、自動頭領域取得/ロスト復帰あり。音声口パクは後日。[頭専用](HEAD_ONLY.md)。run-avatar.ps1とrun-motion.ps1の-LegacySecondaryResponseで以前の減衰へ戻せる。

## 2026-09-13 頭専用の自動化

tanakacap-head-only.batは頭領域自動取得・非記録・無期限。今回のtanakacap-test.batは-HeadOnly -Diagnose -Frames 1800へ更新。通常liveはfullのまま。-HeadRoiMode fixedで従来の手動固定へ戻る。autoのP/R/Sと取得2モデルはHEAD_ONLY.md参照。以前の「固定範囲・自動再取得未対応」は旧状態。
