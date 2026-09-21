# v0.1.4 公開前のデータ確認

2026-09-21。ユーザーの設定が保存された`0.1.3-ui-audit-final`をそのまま圧縮せず、許可リスト方式のビルドから`0.1.4`を新規作成した。元の個人設定はローカルに維持。

- 公開設定は`ui-settings.example.json`から作成し、相対アバターパスとカメラ0のみ。固有デバイスID・録画パス・照明設定は引き継がない。
- avatarsは空。logs/results/実写動画/アバターパッケージ/FBX/VRM/Blend等は公開ZIPに含まれない。
- Playerはアバターを内蔵しない`BuildRelease`の出力を使用。直前に検証した製品Playerと一致。開発用のアバター付きPlayerから梱包しない。
- Exporterのunitypackage内もpathnameを検査し、ソースとライセンスだけであることを確認。
- ZIPに見つかった29画像はPython同梱Tcl/Tkのアイコン・サンプル。インストール原本とSHA一致を確認し、利用者の実写素材と区別した。
- 全ローカルブランチ・タグの履歴を確認。旧`HaolanLab.unity`にアバター骨構造が残っていたため、ユーザー承認で同シーンとmetaを履歴から除去。153コミットを処理、除去後の該当0件。公開mainと旧タグも書換対象。旧リリース配布ZIPは変更しない。

Gitの復旧用bundleはGit管理外の`results/pre-public-history-cleanup.bundle`に保存し、公開しない。履歴書換後も、他人のcloneやGitHubの参照外キャッシュの削除まで保証するものではない。

監査結果は`results/public-data-audit-final.json`。公開ZIPは`builds/releases/0.1.4/release-report.json`に列挙したpart01/part02だけ。`oversize-local-only.zip`は公開しない。

再検査：

```powershell
.\.venv\Scripts\python.exe -X utf8 tools/diagnostics/audit_public_data.py --ref=--all --release builds/releases/0.1.4 --output results/public-data-audit-final.json
```
