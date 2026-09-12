# 起動モード（2026-09-12）

デスクトップのbatは `tools/update-desktop-launcher.ps1` で生成・更新する。

| bat | 用途 | 動作記録 | 終了 |
|---|---|---|---|
| tanakacap-test.bat | 既存のカメラ検証版 | 従来の数値/診断ログあり | 1800フレーム、またはQ/Esc |
| tanakacap-live.bat | 普段使いのカメラ版 | なし | 制限なし。アバターを閉じるかプレビューでQ/Esc |
| tanakacap-motion.bat | カメラを使わないモーション版 | なし | 制限なし。アバターを閉じる |

いずれも更新した外部haolan.tcapを読む。F6は髪・服の揺れON/OFF、F3はOBS向け表示。Spoutの送信名TanakaCapは共通。比較のための同時起動ではなく、使いたい版を一つ起動する。

非記録版ではframes.jsonl/結果レポート/校正レポート/スナップショット/ORT profilingを生成せず、メモリ内のフレーム履歴も1件に制限する。Unityは-nolog。GPUの明示指定とCPU-only拒否は維持するが、ノード別の実測監査は検証版で行う。起動エラーの画面表示やOS/ドライバーのキャッシュまで無くす機能ではない。過去の記録を消さない。

モーションは `ProceduralMotion.cs` の自作24秒周期。首振り、体のロール/ヨー、左右の腕の上げ下げ、指、瞬きなどを合成し、同じアバター駆動へ入力する。カメラ、推論、UDP受信は起動しない。これは追跡品質のデモではない。

外部モーション素材・人物の録画は使っていない。このソースと生成モーションは0BSDとし、利用・改変・商用/非商用再配布に表示義務を加えない。docs/PROCEDURAL_MOTION_LICENSE.txtを参照。モーションの許諾とHAOLAN/シェーダー/Unity等の許諾は別で、アバター原本の再配布許可を意味しない。

直接起動：run-avatar-lab.ps1 -NoLog / run-motion-lab.ps1。アバター指定はどちらも-Avatar。カメラ版はtracking-settings.jsonの採用設定を引き継ぐ。

検証：tests/test_no_log.pyで保存処理が呼ばれないこと、無期限ループがPlayer終了で止まること、保存指定との競合拒否を確認。実GPUモデルのsynthetic 3フレームでも非記録で終了成功。30分連続の実カメラ安定性は未確認。

追加検証：モーション版の4秒起動で既定Player.logとresultsフォルダーが増えないことを確認（results/secondary-motion/no-log-smoke.json）。モーションの実描画と終了code0はmotion-final.png/log。
