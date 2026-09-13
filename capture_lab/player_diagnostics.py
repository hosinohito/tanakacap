"""Summarize new Player error-log entries without displaying stack-trace noise."""
import re
from pathlib import Path


class PlayerDiagnostics:
    def __init__(self, path):
        self.path = Path(path)
        self.reset()

    def reset(self):
        try:
            stat = self.path.stat()
            self.offset, self.identity = stat.st_size, stat.st_ino
        except OSError:
            self.offset, self.identity = 0, None
        self.pending = b''
        self.first_line = False

    def poll(self):
        try:
            stat = self.path.stat()
            if stat.st_ino != self.identity or stat.st_size < self.offset:
                self.offset, self.pending = 0, b''
                self.first_line = False
            self.identity = stat.st_ino
            with self.path.open('rb') as stream:
                stream.seek(self.offset)
                data = stream.read(65536)
                self.offset = stream.tell()
        except OSError:
            return []
        lines = (self.pending + data).split(b'\n')
        self.pending = lines.pop()
        result = []
        for raw in lines:
            line = raw.decode('utf-8-sig', errors='replace').strip()
            if re.match(r'^\d{4}-\d\d-\d\dT\S+ (Error|Exception|Assert)$', line):
                self.first_line = True
            elif self.first_line and line:
                self.first_line = False
                if line.startswith('Avatar renderer skipped; loading continues:'):
                    result.append('【警告・継続中】一部の描画を省略しました。' + line.split(':', 1)[1][:1800])
                    result.append('確認先：元のUnityプロジェクトのマテリアル／シェーダー。詳細ログ：' + str(self.path))
                else:
                    result.append('【エラー】' + line[:1800])
                    result.append('詳細ログ：' + str(self.path))
        return result
