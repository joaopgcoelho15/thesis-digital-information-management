#!/usr/bin/env python3
"""Build the browser executable from reviewed source and a frozen data plan."""
import json
from pathlib import Path
p=Path(__file__).resolve().parent
plan=json.loads((p/'plan.json').read_text())
# Detailed raw cells stay in plan.json/snapshots, not in executable code.
for e in plan['entities']:e.pop('raw_cells',None)
(p/'execute.js').write_text((p/'runner.js').read_text()+'\nrunEphemeraPoC('+json.dumps(plan,ensure_ascii=False,separators=(',',':'))+','+json.dumps((p/'image-preview.js').read_text(),ensure_ascii=False)+');')
print(p/'execute.js')

finish_plan=json.loads((p/'plan.json').read_text())
finish_plan['entities']=[{k:e[k] for k in ('key','label','claims','source','source_row','post_id') if k in e} for e in finish_plan['entities']]
(p/'finish.js').write_text((p/'finish-source.js').read_text()+'\nfinishEphemera('+json.dumps(finish_plan,ensure_ascii=False,separators=(',',':'))+');')
