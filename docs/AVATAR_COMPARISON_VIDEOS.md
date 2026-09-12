# アバター比較動画（2026-09-12）

ユーザーが既存2方式の3Dアバター動画を依頼。同じ実撮影に対する現行RTMW3Dと、指だけHaMeRへ交換した既存補正の結果を、実UnityのHAOLAN/lilToonで描画した。

## 完成ファイル

results/avatar-videos/rtmw-vs-hamer/

- current.mp4：現行、1280×720、約89MiB。
- hamer-fingers.mp4：指だけHaMeR、1280×720、約89MiB。
- side-by-side.mp4：左が現行・右がHaMeR、2560×768（48pxのラベル帯）、約174MiB。
- 全て30fps、5551frame、185.033秒、音声なし、H.264/yuv420p。暗色背景の比較用MP4。OBS用RGBAは維持。
- 1:05〜1:50付近に手の開閉がある。冒頭は手の有効観測がなく腕の初期姿勢を保持する。ライブの遅延や品質合格を証明する動画ではない。

## 再現方法

tools/render_comparison_videos.py --output 新しい出力フォルダー を本体Pythonで実行する。指定済みのfirst-takeとfirst-take-hamer/fingersを使う。Unity実行ファイルとtools/bin/ffmpeg.exeが必要。出力フォルダー既存時は上書きせず停止。

AvatarVideo.csは明示的な--render-replay/--video-output/--ffmpeg起動のみ。通常のUDP追跡・補正は維持。元の実取得間隔dtからイベント時刻を復元し、未来のpacketを先取りせず、既存LateUpdateを最大1/60秒の小刻みな時間更新で動かす。30fpsの描画時刻へ統一し最後の標本は1frame保持する。両方式は指以外のpacket・カメラを共通化。

初回は同じUnityフレーム内でCamera.Renderを繰り返したため、スキニング更新が映像に反映されずT姿勢になった。復号成功だけで完成と案内した後、85秒位置の画像監査で発見・訂正。各描画前にエンジンのフレーム更新を挟むcoroutineへ修正し、全編を再作成。旧出力はresults/avatar-videos/invalid-stale-skinningへ分離しreportもinvalid。これは品質比較に使わない。

修正版は手を上げた60packetの短い実動画で反映を目視確認後に全編を生成。全3動画をFFmpegで最後までエラーなし復号、フレーム数/長さ一致、左右比較の85秒の実画像で腕・掌・指の描画を確認。preview.jpg参照。通常Unity受信/描画の回帰試験成功、171pytest成功。骨の精度の合格判定ではない。

エンコーダーはimageio-ffmpeg 0.6.0 Windows wheelが同梱するFFmpeg 7.1。公式配布 https://github.com/imageio/imageio-ffmpeg からPyPI経由で取得。本体へPython依存を追加せずexeのみtools/binへ配置。必要なraw RGB24/パイプ/H.264エンコードを実測して使用。FFmpeg文書 https://ffmpeg.org/ffmpeg-formats.html#rawvideo 。exe SHA256の正確な値は各動画report.jsonのffmpeg_sha256を参照。配布物とライセンスはtools/bin（Git外）に保存。
