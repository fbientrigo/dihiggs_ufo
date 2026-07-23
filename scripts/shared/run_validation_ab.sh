#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")"/../.. && pwd)
"$ROOT/scripts/pack_a/run_validation_pack_a.sh" "${1:-$ROOT/releases/pack_a/scientific_validation/external_validation_a}"
"$ROOT/scripts/pack_b/run_validation_pack_b.sh" "${2:-$ROOT/releases/pack_b/validation/external_validation_b}"
python - "$ROOT" <<'PY_AB'
import json, math, sys
from pathlib import Path
root=Path(sys.argv[1])
a_dir=root/'releases/pack_a/scientific_validation/external_validation_a/pi_ufo_baseline_v1/build/point_000001'
b_dir=root/'releases/pack_b/validation/external_validation_b/coupling_basis_ufo_v1/build/point_000001'

def load(path): return json.loads(path.read_text())
def ks(a,b):
    a=sorted(float(x) for x in a); b=sorted(float(x) for x in b)
    if not a or not b: return {'D':None,'p_value':None,'pass':False,'reason':'empty sample'}
    i=j=0; d=0.0
    while i<len(a) or j<len(b):
        x=min(a[i] if i<len(a) else float('inf'), b[j] if j<len(b) else float('inf'))
        while i<len(a) and a[i] <= x: i+=1
        while j<len(b) and b[j] <= x: j+=1
        d=max(d,abs(i/len(a)-j/len(b)))
    ne=len(a)*len(b)/(len(a)+len(b)); lam=(math.sqrt(ne)+0.12+0.11/math.sqrt(ne))*d
    p=2*sum(((-1)**(k-1))*math.exp(-2*k*k*lam*lam) for k in range(1,101))
    p=max(0.0,min(1.0,p))
    return {'D':d,'p_value':p,'pass':p>0.01,'n_a':len(a),'n_b':len(b)}

a_x=load(a_dir/'cross_section.json'); b_x=load(b_dir/'cross_section.json')
a_l=load(a_dir/'lhe_report.json'); b_l=load(b_dir/'lhe_report.json')
sa=float(a_x['sigma_pb']); sb=float(b_x['sigma_pb'])
ea=float(a_x.get('integration_error_pb') or 0.0); eb=float(b_x.get('integration_error_pb') or 0.0)
tol=max(0.02*max(abs(sa),abs(sb)),3.0*math.hypot(ea,eb))
xsec={'sigma_a_pb':sa,'sigma_b_pb':sb,'abs_difference_pb':abs(sa-sb),'tolerance_pb':tol,'pass':abs(sa-sb)<=tol}
shapes={
 'pt_phi_GeV':ks(a_l.get('pt_phi_GeV',[]),b_l.get('pt_phi_GeV',[])),
 'm_phiphi_GeV':ks(a_l.get('m_phiphi_GeV',[]),b_l.get('m_phiphi_GeV',[])),
 'rapidity_phi':ks(a_l.get('rapidity_phi',[]),b_l.get('rapidity_phi',[])),
}
static=load(root/'releases/pack_b/validation/external_validation_b/coupling_basis_ufo_v1/validation/AB_STATIC_REGRESSION.json')
compatible=xsec['pass'] and all(v['pass'] for v in shapes.values()) and a_l.get('llp_stable_in_lhe') and b_l.get('llp_stable_in_lhe')
report={
 'classification':'MONTE_CARLO_COMPATIBLE' if compatible else 'FAIL',
 'static_classification':static.get('status'),
 'cross_section':xsec,
 'shape_ks_tests':shapes,
 'stable_llp_contract':{'pack_a':a_l.get('llp_stable_in_lhe'),'pack_b':b_l.get('llp_stable_in_lhe')},
 'recast_acceptance':'PENDING_STANDARDIZED_CUTFLOW_COMPARISON',
}
(root/'AB_RUNTIME_COMPARISON.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report,indent=2,sort_keys=True))
raise SystemExit(0 if compatible else 5)
PY_AB
