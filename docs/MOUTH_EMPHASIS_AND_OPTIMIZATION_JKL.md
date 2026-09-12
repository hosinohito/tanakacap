# 口角強調度と高速化J/K/L（2026-09-13）

ユーザー指定：口角強調度を無段階にし既定0、将来UIで指定。GPU点復号(J)、GPU前処理(K)、CPU補正の割り当て削減(L)をそれぞれ実装し、Full HD60fpsで比較。遅くなる案や目に見える影響が出る案はrevertする。実カメラ/映像目視はせず、まず数値一致を検査し差がある場合は保守的に扱う。A/E保留、以前遅かったHは再導入しない。揺れ物は変更しない。

## 口角

`tracking-settings.json`の`mouth_corner_emphasis`、両起動スクリプトの`-MouthCornerEmphasis`、Playerの`--mouth-corner-emphasis`を追加。範囲0〜1の連続値、0が追加強調なし、1が従来と同じ強調、0.5がその中間。既存モーフを最大6mm/最大3倍へ増幅していた分だけを補間する。0でも口角の検出・上下/左右非対称の駆動は続ける。符号付きガンマ2・中立補正・開口時の上げ抑制・口横寄せは変更しない。

生成済み強調モーフへの駆動量を調節し、UI用の`AvatarDriver.MouthCornerEmphasis`で実行中も変更可能。UI自体は将来。元アバターやモーフの再書き出しは不要。

Unity実モーフで0/0.5/1の連続性と1の旧駆動量、左右・口形状・腕回帰・RGBA検証成功。results/mouth-emphasis-default-retry。最初のビルドはusing不足を修正、最初の回帰は旧強調量を前提とした検査に失敗し新仕様に合わせ更新。失敗を隠さずresults/mouth-emphasis-defaultに保持。実人物の新しい口角の見た目は未評価。

## J：GPU点復号（比較中）

RTMW3DのXYZ分布へArgMax/ReduceMax/近傍3値取得をONNXで接続。元の重み・計算精度は維持し、原本SHA別の派生モデルをローカル生成。CPUへ戻す量は1,021,440→7,980バイト。局所対数補間と画面/メートル座標変換は少量の値に対して従来と同じfloat64演算を行う。時間補正は不変。

`--gpu-decode`で試行、未指定は従来。80録画観測/4種類のROIでXY/Z/信頼度/補間診断差0、プロファイルはCUDAのみ。results/compact-simcc-audit、tools/audit_compact_simcc.py。Full HD＋OBS比較はこれから。K/Lは未実装。
