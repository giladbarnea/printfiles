from pathlib import Path
from prin.core import StringWriter
from prin.prin import main as prin_main

base = Path('/tmp/prin-debug')
base.mkdir(parents=True, exist_ok=True)
(base/'a.py').write_text('print(1)\n', encoding='utf-8')
(base/'b.py').write_text('print(2)\n', encoding='utf-8')

buf = StringWriter()
prin_main(argv=['--max-files','4', str(base)], writer=buf)
out = buf.text()
print('LEN', len(out))
print(out)
