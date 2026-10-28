"""Run PID.py without a hub: python3 -m src.sim.run_pid --route demo.

Exports actual Python simulation samples to a standalone HTML replay and CSV.
The browser REPLAYS data; it does not implement a second copy of the PID law.
"""

import argparse
import csv
import json
from math import isfinite
from pathlib import Path
import sys
from time import perf_counter

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import PID as program
from lib import competition_config as config
from src.sim.competition import Simulation

ROUTES = ("1", "2", "3-left", "3-right", "4", "5", "6", "7")


def run_case(name, args, kp=None):
    world = Simulation(
        heading_deg=args.start_heading if name == "demo" else 0,
        turn_lag_s=args.turn_lag, speed_lag_s=args.speed_lag,
        drift_dps=args.gyro_drift, slip_fraction=args.slip,
        assume_stall_ms=args.assume_stall_ms,
    )
    world.connect(program)
    world.motion.heading_pid.kp = args.kp if kp is None else kp
    world.motion.heading_pid.kd = args.kd
    error = None
    started = perf_counter()
    try:
        if name == "demo":
            program.motors_pid(0, 300, 50)
            program.ausrichten2(90)
            program.motors_pid(90, -200, 20)
        else:
            program.run_route(name)
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
    finally:
        program.stop_all()
    elapsed = perf_counter() - started
    return {
        "name": name if kp is None else "demo / Kp=" + str(kp),
        "error": error, "wall_s": elapsed, "virtual_s": world.time_ms / 1000.0,
        "assumptions": sorted(world.assumptions),
        "settings": {
            "kp": world.motion.heading_pid.kp, "ki": world.motion.heading_pid.ki,
            "kd_seconds": world.motion.heading_pid.kd,
            "loop_ms": config.LOOP_MS, "diameter_mm": config.WHEEL_DIAMETER_MM,
            "track_mm": config.AXLE_TRACK_MM, "turn_lag_s": args.turn_lag,
            "speed_lag_s": args.speed_lag, "gyro_drift_dps": args.gyro_drift,
            "slip_fraction": args.slip,
        },
        "samples": world.samples,
    }


def write_outputs(cases, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    csv_path = output.with_suffix(".csv")
    fields = ["case"] + list(cases[0]["samples"][0])
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for case in cases:
            for row in case["samples"]:
                writer.writerow(dict(row, case=case["name"]))
    payload = json.dumps(cases, allow_nan=False, separators=(",", ":")).replace("<", "\\u003c")
    html = REPORT.replace("__SAMPLES__", payload)
    # Relative file link works on file:// without a web server.
    from urllib.parse import quote
    html = html.replace("__CSV__", quote(csv_path.name))
    output.write_text(html, encoding="utf-8")
    return csv_path


REPORT = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PID Lab — Python simulation replay</title>
<style>
:root{color-scheme:dark;--bg:#0b0e16;--panel:#141b29;--line:#2b3549;--ink:#eef2fc;--muted:#aab7cf;--pink:#ff58b5;--cyan:#4bdfed;--green:#74e5ad}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 15% 0,#28172e,transparent 50%),var(--bg);color:var(--ink);font:16px/1.6 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:30px 20px 70px}h1{font-size:clamp(30px,5vw,52px);line-height:1.1;letter-spacing:-.04em;margin:8px 0 16px}h2{font-size:19px;margin:0 0 12px}p{margin:0 0 14px}.eyebrow{color:var(--pink);font-weight:800;letter-spacing:.12em;font-size:12px;text-transform:uppercase}.muted,small{color:var(--muted)}a{color:var(--cyan)}code{background:#222e43;padding:2px 6px;border-radius:5px;font-size:.9em}.box{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:20px;margin-top:18px}.notice{border-left:4px solid #ffc56b;background:#241e19}.grid{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(270px,1fr);gap:18px}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.metric{background:#0e1421;border-radius:12px;padding:12px}.metric b{display:block;color:var(--cyan);font:700 22px ui-monospace,monospace}.metric small{font-size:12px}button,select{font:inherit;border:1px solid #43516a;background:#212b40;color:var(--ink);padding:9px 14px;border-radius:10px;cursor:pointer}button:hover{border-color:var(--cyan)}button.primary{background:var(--pink);border-color:var(--pink);color:#160c15;font-weight:800}select{max-width:100%}input[type=range]{width:100%;accent-color:var(--pink)}.toolbar{display:flex;gap:10px;flex-wrap:wrap;align-items:center}.toolbar label{font-size:14px}.tag{display:inline-block;padding:4px 10px;border:1px solid #37624f;background:#18372c;color:var(--green);border-radius:99px;font-size:12px;font-weight:700}.bad{border-color:#ae5449;background:#442420;color:#ffb0a5}canvas{display:block;width:100%;height:420px;background:#0d1420;border-radius:12px}#errorPlot{height:200px}dl{display:grid;grid-template-columns:1fr auto;gap:5px;font-size:14px}dt{color:var(--muted)}dd{margin:0;font-family:ui-monospace,monospace}ul,ol{padding-left:22px}li{margin-bottom:7px}.legend{font-size:12px;color:var(--muted);margin:8px 0 0}.error{color:#ffada6;overflow-wrap:anywhere;white-space:pre-wrap;font:14px/1.5 ui-monospace,monospace}:focus-visible{outline:2px solid var(--cyan);outline-offset:3px}@media(max-width:760px){.grid{grid-template-columns:1fr}.metrics{grid-template-columns:1fr 1fr}canvas{height:340px}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto}}
</style></head><body><main>
<div class="eyebrow">SPIKE / Pybricks · offline development</div>
<h1>PID <span style="color:var(--pink)">Lab.</span></h1>
<p class="muted">Your Python ran on the laptop. This page replays the resulting samples — it does not calculate a different PID in JavaScript.</p>
<div class="box notice"><b>Simulation is not a robot test.</b> No hub was contacted. Geometry, motor polarity and lag are unverified. No mat collisions, forces, battery or accurate braking model. Each route starts independently at the local origin.</div>
<div class="box">
<h2>Start here — three steps</h2>
<ol><li>Choose a <b>route</b> below. <b>demo</b> drives crooked, corrects heading, turns to 90°, and reverses.</li><li>Press <b>Play</b>. The pink path and error plot use the same clock.</li><li>Drag the time slider to inspect one instant. Change Python/config settings and rerun the terminal command to calculate a new simulation.</li></ol>
<div class="toolbar"><label for="case">Route</label><select id="case"></select><button class="primary" id="play" type="button">▶ Play</button><button id="step" type="button">Step +20 ms</button><button id="reset" type="button">Reset replay</button><label for="rate">Replay speed</label><select id="rate"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="4">4×</option><option value="10">10×</option></select></div>
<label for="time" class="muted" style="display:block;margin-top:14px">Replay time: <output id="clock">0.00 s</output></label><input id="time" type="range" min="0" max="1" step="0.02" value="0">
</div>
<div class="metrics box"><div class="metric"><b id="virtual">—</b><small>virtual robot time</small></div><div class="metric"><b id="wall">—</b><small>Python calculation time (excludes report export)</small></div><div class="metric"><b id="sampleCount">—</b><small>recorded samples</small></div></div>
<div class="grid">
<div class="box"><h2>Robot path · millimetres</h2><canvas id="path" role="img" aria-label="Top-down path of the simulated robot"></canvas><p class="legend">Dim line = full route · pink = travelled · cyan = robot. +X forward points right; +Y to the right points down. The path is not a map of your field.</p></div>
<div class="box"><span class="tag" id="status">OFFLINE MODEL</span><h2 style="margin-top:12px">What the controller sees</h2><dl id="readout"></dl><h2>Heading error · degrees</h2><canvas id="errorPlot" role="img" aria-label="Wrapped heading error against virtual time"></canvas><p class="legend">Pink error = wrapped(target − gyro). Sudden jumps can be a new move or a heading reset, not instability.</p><p class="error" id="failure"></p></div>
</div>
<div class="box"><h2>Settings used by Python</h2><dl id="settings"></dl><p class="muted">Kp and Kd overrides only change this laptop experiment. They do not edit the hub settings.</p></div>
<div class="box"><h2>Assumptions — please read before trusting a plot</h2><ul id="assumptions"></ul><p><a href="__CSV__" download>Download the exact samples as CSV</a> · <a href="PID-Explainer.html">Original PID explainer</a></p><p class="muted">The original explainer describes the pre-refactor paste. The maintained instructions are in <code>docs/Guides/Laptop Simulation.md</code> and <code>docs/Systems/Motion Control.md</code>.</p></div>
<noscript><div class="box">Enable JavaScript to replay the samples. The CSV still contains every calculated sample.</div></noscript>
</main>
<script id="simulation-data" type="application/json">__SAMPLES__</script>
<script>
'use strict';
const cases=JSON.parse(document.getElementById('simulation-data').textContent);
const byId=id=>document.getElementById(id);
let active=cases[0], rows=active.samples, cursor=0, playing=false, previous=null;
const selector=byId('case');
cases.forEach((c,i)=>{const option=document.createElement('option');option.value=i;option.textContent=c.name+(c.error?' — stopped with error':'');selector.appendChild(option)});
function pairs(el,values){el.replaceChildren();Object.entries(values).forEach(([label,value])=>{const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;el.append(dt,dd)})}
function selectCase(){playing=false;previous=null;active=cases[Number(selector.value)];rows=active.samples;cursor=0;byId('time').max=active.virtual_s;byId('virtual').textContent=active.virtual_s.toFixed(2)+' s';byId('wall').textContent=(active.wall_s*1000).toFixed(2)+' ms';byId('sampleCount').textContent=rows.length;byId('status').textContent=active.error?'MODEL STOPPED':'OFFLINE RUN COMPLETED';byId('status').classList.toggle('bad',!!active.error);byId('failure').textContent=active.error||'';pairs(byId('settings'),active.settings);byId('assumptions').replaceChildren();active.assumptions.forEach(text=>{const li=document.createElement('li');li.textContent=text;byId('assumptions').appendChild(li)});paint()}
function prepare(id){const el=byId(id),dpr=Math.min(devicePixelRatio||1,2),w=el.clientWidth,h=el.clientHeight;el.width=Math.round(w*dpr);el.height=Math.round(h*dpr);const c=el.getContext('2d');c.setTransform(dpr,0,0,dpr,0,0);c.clearRect(0,0,w,h);return {c,w,h}}
function sampleIndex(){let lo=0,hi=rows.length-1;while(lo<hi){const mid=Math.ceil((lo+hi)/2);if(rows[mid].time_s<=cursor)lo=mid;else hi=mid-1}return lo}
function paintPath(index){const {c,w,h}=prepare('path'),pad=35;let x0=0,x1=0,y0=0,y1=0;rows.forEach(r=>{x0=Math.min(x0,r.x_mm);x1=Math.max(x1,r.x_mm);y0=Math.min(y0,r.y_mm);y1=Math.max(y1,r.y_mm)});const scale=Math.min((w-2*pad)/Math.max(120,x1-x0),(h-2*pad)/Math.max(120,y1-y0));const X=x=>(w-(x1-x0)*scale)/2+(x-x0)*scale,Y=y=>(h-(y1-y0)*scale)/2+(y-y0)*scale;
c.strokeStyle='#243047';c.lineWidth=1;const grid=Math.max(50,Math.ceil(Math.max(x1-x0,y1-y0)/1000)*100);for(let x=Math.floor(x0/grid)*grid;x<=x1+grid;x+=grid){c.beginPath();c.moveTo(X(x),0);c.lineTo(X(x),h);c.stroke()}for(let y=Math.floor(y0/grid)*grid;y<=y1+grid;y+=grid){c.beginPath();c.moveTo(0,Y(y));c.lineTo(w,Y(y));c.stroke()}
function trail(end,color,width){c.beginPath();rows.slice(0,end+1).forEach((r,i)=>i?c.lineTo(X(r.x_mm),Y(r.y_mm)):c.moveTo(X(r.x_mm),Y(r.y_mm)));c.strokeStyle=color;c.lineWidth=width;c.stroke()}trail(rows.length-1,'#344460',2);trail(index,'#ff58b5',3);
const r=rows[index];c.fillStyle='#74e5ad';c.beginPath();c.arc(X(0),Y(0),4,0,Math.PI*2);c.fill();c.save();c.translate(X(r.x_mm),Y(r.y_mm));c.rotate(r.world_heading_deg*Math.PI/180);c.fillStyle='#4bdfed';c.beginPath();c.moveTo(15,0);c.lineTo(-10,-9);c.lineTo(-6,0);c.lineTo(-10,9);c.closePath();c.fill();c.restore();c.fillStyle='#aab7cf';c.font='12px system-ui';c.fillText('grid '+grid+' mm',12,h-12)}
function paintError(index){const {c,w,h}=prepare('errorPlot'),pad=28;const max=Math.max(5,...rows.map(r=>Math.abs(r.error_deg||0))),total=Math.max(.02,active.virtual_s),X=t=>pad+(w-2*pad)*t/total,Y=e=>h/2-e/max*(h/2-pad);c.strokeStyle='#344460';c.beginPath();c.moveTo(pad,h/2);c.lineTo(w-pad,h/2);c.stroke();c.beginPath();let pen=false;rows.forEach(r=>{if(r.error_deg===null){pen=false;return}if(pen)c.lineTo(X(r.time_s),Y(r.error_deg));else c.moveTo(X(r.time_s),Y(r.error_deg));pen=true});c.strokeStyle='#ff58b5';c.lineWidth=1.8;c.stroke();c.strokeStyle='#4bdfed';c.beginPath();c.moveTo(X(cursor),10);c.lineTo(X(cursor),h-10);c.stroke();c.fillStyle='#aab7cf';c.font='11px system-ui';c.fillText('±'+max.toFixed(1)+'°',5,14);c.fillText(total.toFixed(1)+' s',w-52,h-6)}
function paint(){const i=sampleIndex(),r=rows[i];byId('time').value=cursor;byId('clock').textContent=cursor.toFixed(2)+' s';byId('play').textContent=playing?'❚❚ Pause':'▶ Play';const f=(v,unit)=>v===null?'—':v.toFixed(2)+' '+unit;pairs(byId('readout'),{'Gyro heading':f(r.heading_deg,'°'),'Target':f(r.target_deg,'°'),'Error':f(r.error_deg,'°'),'Encoder distance':f(r.encoder_mm,'mm'),'Speed command':f(r.speed_command_mm_s,'mm/s'),'Turn command':f(r.turn_command_deg_s,'°/s'),'Left module':f(r.left_module_deg,'°'),'Right module':f(r.right_module_deg,'°')});paintPath(i);paintError(i)}
function tick(now){if(!playing)return;if(previous!==null)cursor=Math.min(active.virtual_s,cursor+Math.min(.1,(now-previous)/1000)*Number(byId('rate').value));previous=now;if(cursor>=active.virtual_s)playing=false;paint();if(playing)requestAnimationFrame(tick)}
selector.addEventListener('change',selectCase);byId('play').addEventListener('click',()=>{playing=!playing;if(playing){if(cursor>=active.virtual_s)cursor=0;previous=null;requestAnimationFrame(tick)}paint()});byId('step').addEventListener('click',()=>{playing=false;cursor=Math.min(active.virtual_s,cursor+.02);paint()});byId('reset').addEventListener('click',()=>{playing=false;cursor=0;paint()});byId('time').addEventListener('input',()=>{playing=false;cursor=Number(byId('time').value);paint()});window.addEventListener('resize',paint);selectCase();
</script></body></html>'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", choices=("demo", "all") + ROUTES, default="demo")
    parser.add_argument("--output", type=Path, default=Path("docs/Attachments/PID-Simulation.html"))
    parser.add_argument("--start-heading", type=float, default=15.0, help="demo's initial heading error, deg")
    parser.add_argument("--kp", type=float, default=config.HEADING_KP, help="simulation-only Kp override")
    parser.add_argument("--kd", type=float, default=config.HEADING_KD, help="simulation-only time-based Kd, seconds")
    parser.add_argument("--turn-lag", type=float, default=0.12, help="assumed turn lag, seconds")
    parser.add_argument("--speed-lag", type=float, default=0.08, help="assumed speed lag, seconds")
    parser.add_argument("--gyro-drift", type=float, default=0.0, help="assumed gyro bias drift, deg/s")
    parser.add_argument("--slip", type=float, default=0.0, help="fraction of encoder travel lost at the floor (0..1)")
    parser.add_argument("--assume-stall-ms", type=float, help="explicit timing assumption for route 5; no contact model")
    parser.add_argument("--sweep", action="store_true", help="demo at Kp=0,1,4,8; source settings are not edited")
    args = parser.parse_args(argv)
    for name in ("start_heading", "kp", "kd", "turn_lag", "speed_lag", "gyro_drift", "slip"):
        if not isfinite(getattr(args, name)):
            parser.error(name + " must be finite")
    if args.turn_lag < 0 or args.speed_lag < 0 or not 0 <= args.slip <= 1:
        parser.error("lags must be non-negative and slip must be between 0 and 1")
    if args.assume_stall_ms is not None and (
        not isfinite(args.assume_stall_ms) or args.assume_stall_ms <= 0
    ):
        parser.error("assumed stall time must be finite and positive")
    if args.sweep and args.route != "demo":
        parser.error("--sweep is only for --route demo")
    if args.output.suffix.lower() != ".html":
        parser.error("--output must end in .html")
    if args.sweep:
        cases = [run_case("demo", args, kp=kp) for kp in (0.0, 1.0, 4.0, 8.0)]
    else:
        names = ROUTES if args.route == "all" else (args.route,)
        cases = [run_case(name, args) for name in names]
    csv_path = write_outputs(cases, args.output)
    for case in cases:
        status = "STOPPED: " + case["error"] if case["error"] else "offline model completed"
        print("%s: %.2f virtual seconds in %.4f wall seconds — %s" % (
            case["name"], case["virtual_s"], case["wall_s"], status,
        ))
    print("HTML replay:", args.output.resolve())
    print("CSV samples:", csv_path.resolve())
    print("Hub validation: not run — no hub connected. Model assumptions are in the report.")
    return 1 if any(case["error"] for case in cases) else 0


if __name__ == "__main__":
    raise SystemExit(main())
