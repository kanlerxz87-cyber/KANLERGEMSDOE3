import subprocess,json,base64,pathlib,concurrent.futures,hashlib
from datetime import datetime, timezone
root=pathlib.Path(__file__).resolve().parents[1]/'sources'
def get(task):
 repo,path=task
 try:
  j=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/contents/{path}'],stderr=subprocess.DEVNULL)); b=base64.b64decode(j['content']); dest=root/repo.split('/')[-1]/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
  return {'repo':repo,'path':path,'sha':j['sha'],'status':'retrieved','sha256':hashlib.sha256(b).hexdigest(),'retrieved_utc':datetime.now(timezone.utc).isoformat()}
 except Exception:return {'repo':repo,'path':path,'status':'unavailable'}
tasks=[]
for n in [24,25,27,28,30,31,32,33,36]:
 for p in ['README.md','docs/index.html','docs/score-ledger.csv']:tasks.append((f'buffedlizard55-lab/GEMSDOE{n}',p))
for p in ['evidence/h33_holdout.json','evidence/h33_candidates.json','evidence/h33_validation.json','docs/research/why-02778-analysis-20261025.md','scripts/evaluate_holdout.py','scripts/submission_writer.py','vendor/PROVENANCE.json','registry/data_manifest.json','registry/feature_receipt.json','scripts/restore_data.py','evidence/focus_site_winner_overlap_20261026.json']:
 tasks.append(('buffedlizard55-lab/GEMSDOE32',p))
tasks.append(('drivendataorg/gems-prize-reference-solution','README.md'))
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:r=list(ex.map(get,tasks))
(root/'retrieval.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r,indent=2))
