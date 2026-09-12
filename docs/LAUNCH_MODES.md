# 起動モード（2026-09-13）

最新採用（2026-09-13）：ピッチはPnP・口角はZ。通常body3d/pnp_depthmouth、`-HeadPoseMode pnp`で両方旧補正へ。test/liveは採用構成。以下のdepth3d試行・通常separate/pnpは過去の状態。[最新引き継ぎ](../HANDOFF.md)。

デスクトップのbatは `tools/update-desktop-launcher.ps1` で生成・更新する。

| bat | 用途 | 動作記録 | 終了 |
|---|---|---|---|
| tanakacap-test.bat | 全部ON・RTMW3D-X顔Zピッチ/口角試行 | 数値/診断ログあり | 1800フレーム、またはQ/Esc |
| tanakacap-test-face-pnp.bat | 全部ON・同じRTMW3D-X顔でPnP対照 | 数値/診断ログあり | 1800フレーム、またはQ/Esc |
| tanakacap-test-face-original.bat | 全部ON・従来RTMW-L顔方式 | 数値/診断ログあり | 1800フレーム、またはQ/Esc |
| tanakacap-compare-face.bat | 顔比較動画の保存先を開く | なし・カメラ不使用 | Explorerで確認 |
| tanakacap-head-only.bat | 頭専用auto | なし | 制限なし。アバターを閉じるかQ/Esc |
| tanakacap-live.bat | 普段使いのカメラ版 | なし | 制限なし。アバターを閉じるかプレビューでQ/Esc |
| tanakacap-motion.bat | カメラを使わないモーション版 | なし | 制限なし。アバターを閉じる |

いずれも更新した外部haolan.tcapを読む。F6は髪・服の揺れON/OFF、F3はOBS向け表示。Spoutの送信名TanakaCapは共通。比較のための同時起動ではなく、使いたい版を一つ起動する。

非記録版ではframes.jsonl/結果レポート/校正レポート/スナップショット/ORT profilingを生成せず、メモリ内のフレーム履歴も1件に制限する。Unityは-nolog。GPUの明示指定とCPU-only拒否は維持するが、ノード別の実測監査は検証版で行う。起動エラーの画面表示やOS/ドライバーのキャッシュまで無くす機能ではない。過去の記録を消さない。

モーションは `ProceduralMotion.cs` の自作24秒周期。首振り、体のロール/ヨー、左右の腕の上げ下げ、指、瞬きなどを合成し、同じアバター駆動へ入力する。カメラ、推論、UDP受信は起動しない。これは追跡品質のデモではない。

外部モーション素材・人物の録画は使っていない。このソースと生成モーションは0BSDとし、利用・改変・商用/非商用再配布に表示義務を加えない。docs/PROCEDURAL_MOTION_LICENSE.txtを参照。モーションの許諾とHAOLAN/シェーダー/Unity等の許諾は別で、アバター原本の再配布許可を意味しない。

直接起動：run-avatar-lab.ps1 -NoLog / run-motion-lab.ps1。アバター指定はどちらも-Avatar。カメラ版はtracking-settings.jsonの採用設定を引き継ぐ。

検証：tests/test_no_log.pyで保存処理が呼ばれないこと、無期限ループがPlayer終了で止まること、保存指定との競合拒否を確認。実GPUモデルのsynthetic 3フレームでも非記録で終了成功。30分連続の実カメラ安定性は未確認。

追加検証：モーション版の4秒起動で既定Player.logとresultsフォルダーが増えないことを確認（results/secondary-motion/no-log-smoke.json）。モーションの実描画と終了code0はmotion-final.png/log。

## 2026-09-12 描画の追加設定

全起動で追加の軽量AAを既定ON。F7で切替、両PowerShell起動スクリプトの-NoEdgeAAで起動OFF（元のMSAAは維持）。Spout出力はFull HD（1920×1080）既定。-OutputWidth/-OutputHeightで各64〜4096の自由指定、幅省略は16:9。-NoPreview/F8でプレビューだけ非表示、-LegacyPreviewで旧二重描画へ復帰。通常はOBS画像をプレビューに共有。ウインドウサイズ/カメラ入力は独立。非記録・無期限・モーション専用の挙動はそのまま。[詳細](SHARED_PREVIEW.md)。

Playerの--performance-logと--performance-secondsは明示的な検証専用。live/motion版は渡さない。検証版-Diagnoseはresults/player-performanceへPlayer統計を記録するが、新たな自動終了時間は指定しない。GPU計測はさらに--performance-gpuを指定する。検証の保存先と条件はPHASE4_VALIDATION.md。

## 2026-09-12 統合構成オプション

共通run-avatar-lab.ps1の-TrackingMode full（既定）/face_head/head_onlyで切替。tracking-settings.jsonにもtracking_mode。-NoBody/-NoGaze/-NoPersonDetectorの個別OFFは推論生成を省略。-HeadOnlyはhead_onlyの別名。頭専用ショートカットtanakacap-head-only.batは-NoLogで無期限、自動頭領域取得/ロスト復帰あり。音声口パクは後日。[頭専用](HEAD_ONLY.md)。run-avatar-lab.ps1とrun-motion-lab.ps1の-LegacySecondaryResponseで以前の減衰へ戻せる。

## 2026-09-13 頭専用の自動化

tanakacap-head-only.batは頭領域自動取得・非記録・無期限。今回のtanakacap-test.batは-HeadOnly -Diagnose -Frames 1800へ更新。通常liveはfullのまま。-HeadRoiMode fixedで従来の手動固定へ戻る。autoのP/R/Sと取得2モデルはHEAD_ONLY.md参照。以前の「固定範囲・自動再取得未対応」は旧状態。
