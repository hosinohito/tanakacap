# 頭の追従速度比較（2026-09-13）

ユーザー提案：既存4フレーム処理後の頭角度について、小さい動きはゆっくり、大きい動きは速く追従させる。比較動画を作成する指定により試行実装。通常の固定追従は維持し、Playerの`--adaptive-head-follow`で試行する。引数を外すと従来へ戻る。UIの既定や頭角度方式は変更していない。

Unity AvatarDriverの既存Slerp係数を置換。表示中の頭と目標のQuaternion.Angle（最短角度差）をe度とし、u=clamp(e/12,0,1)、w=u²(3−2u)、rate=6+39w、係数=1−exp(−dt×rate)。従来はrate=45固定。12度以上で従来と同じ速度、微小差ではゆっくり収束する。新しい不動域や待機フレームは追加せず、同じ4フレームゲートの後に適用。無効追跡時の保持は既存の分岐のまま。口・眉・腕・揺れ物のアルゴリズムは変更なし。推定の大きな誤りも大きい動きとして速く追う限界がある。

新しい録画`results/comparison-takes/20260912T230559-718866Z`から`tools/compare_precision.py`で全853観測をCUDA FP16・全部ON・size2dで再推論。実観測時刻を使い、3平均/stride1は固定。顔有効849/853は精度ではない。`results/comparisons/head-follow-input/report.json`へモデルとGPU実行確認を保存。キャッシュを`tools/prepare_head_follow_comparison.py`で2方式へバイト単位で同じ制御値として複製。`results/comparisons/head-follow/report.json`に条件とハッシュ。

動画は`results/avatar-videos/head-follow/face-closeup.mp4`（左fixed/右adaptive）、全体表示は`side-by-side.mp4`。両方auto-custom表情。同じPlayer/アバター/制御/時刻を使い、頭の表示補間だけ比較。描画は既存比較器の30fps、オフライン動画のため推論遅延や60fpsの見た目の保証ではない。実写画面表示・実カメラ試験・エージェントの動画目視なし。品質はユーザー評価待ち。

ビルド成功、Unity motion-checkで小さい差/大きい差の係数、12度で従来一致、dt=0、微小動作の収束を確認。既存の受信・関節・表情の回帰も成功（`results/head-follow-smoke`）。動画全編デコードと長さ一致を比較器で確認する。自動採用せず、ユーザーの比較結果に合わせて採用/感度調整を行う。
