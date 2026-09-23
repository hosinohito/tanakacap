# 顔ヨーの現行経路

2026-09-23の実装監査。ローカルui-settings.jsonはhead_pose_mode=pnp、observation_mode=overlap、head_follow=fixed。tracking-settings.jsonはfull、観測窓3/stride1。今回ヨーの変更は行わない。

| 段階 | 現在の処理 |
| --- | --- |
| 基準軸 | 両目それぞれの6ランドマークの平均を眼中心にし、両目を結ぶ方向へ鼻先のずれを投影。画像水平そのものを使わず、顔のロールに合わせる |
| 距離正規化 | 鼻先の横ずれを両眼中心の距離で割る。距離変化を緩和するが、横を向いて目の間隔が縮む影響も含む |
| 出力倍率・符号 | 比率×−100。鼻が両眼間隔の0.1だけずれると−10度。比率には線形だが真の首角度に対して線形とは限らない。atan/arcsin補正、ヨーの個人中立校正・ガンマはこの経路にない |
| Python制限 | ±60度でクリップ |
| 観測平滑化 | 3観測の移動平均、1観測ずつ更新。その値にDirectionGate、0.25度以下は保持し、同方向の変化を確認して採用。fast=無限大で即採用分岐なし。頭3成分は成分ごとに判定 |
| Unity制限 | 受信ヨーを再度±60度へクリップ |
| Unity追従 | 現在fixedで係数1−exp(−45dt)のQuaternion.Slerp。可変モードなら頭全体の角度差0〜12度をSmoothstepに通し追従率6〜45/s、現在は不使用 |
| 座標反映 | アバター原点と頭の初期姿勢を基準にカメラ相対の頭回転を設定。胴体回転は重ねない |

faceTrackedの条件（必要な顔点の信頼度0.3以上、両眼中心間隔15px以上）と部位別の有効判定を満たさない間は更新しない。DirectionGateは0.2秒を超える観測の途切れで履歴をリセットする。これらは角度の倍率補正ではなく欠測・観測採用条件。

根拠：tanakacap/retarget.pyのpacket_from_landmarks/FaceFilter、tanakacap/motion_gate.py、tanakacap/head_pose.pyのHeadPose.update、unity/TanakaCap/Assets/TanakaCap/AvatarDriver.csのHeadFollowAmountとheadTarget設定。HeadPose.updateはPnPの角度を計算してもheadPitchだけ書き換える。PnPのpitch_gain=1.8、基準10観測の校正、±40度制限をヨーの補正として説明しない。実験size2d・depth3dや頭のみ別モデルは別経路であり、本表は現在のfull/PnP設定に限定する。
