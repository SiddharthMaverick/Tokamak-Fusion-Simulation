"""
Tokamak MHD Fluid Simulation — PIML Fusion Reactor Dashboard
Entry point: python app.py  (or gradio app.py)
"""

import gradio as gr
import base64
from src.physics import derivedParams
from src.html_template import build_html
from src.css import APP_CSS

def build_iframe() -> str:
    html = build_html()
    b64  = base64.b64encode(html.encode("utf-8")).decode("utf-8")
    return (
        f"<iframe src='data:text/html;base64,{b64}' "
        f"width='100%' height='720px' "
        f"style='border:none; border-radius:6px; display:block;'></iframe>"
    )

PHYSICS_NOTES = """
<div style="margin-top:12px; padding:14px;
            background:#05101f; border:1px solid #0a2233;
            border-radius:6px; font-size:11px;
            color:#4a6a80; line-height:2.1; font-family:'Courier New',monospace;">
  <strong style="color:#00d4ff; display:block; margin-bottom:6px;">Physics derivation</strong>
  <strong style="color:#aaccdd">q (safety factor)</strong>
    &nbsp;&#8773; (a&sup2;&middot;B<sub>t</sub>) / (R&middot;&mu;&sub0;&middot;I<sub>p</sub>/2&pi;)
    &nbsp;&mdash; Kruskal-Shafranov: q &lt; 2 = tearing/disruption risk<br>
  <strong style="color:#aaccdd">&beta;<sub>N</sub> (norm. pressure)</strong>
    &nbsp;&#8733; P<sub>NBI</sub> / (n<sub>e</sub>&middot;B<sub>t</sub>&sup2;)
    &nbsp;&mdash; Troyon stability limit: &beta;<sub>N</sub> &lt; 3.5<br>
  <strong style="color:#aaccdd">v<sub>tor</sub> (toroidal rotation)</strong>
    &nbsp;&#8733; P<sub>NBI</sub> / n<sub>e</sub>
    &nbsp;&mdash; NBI momentum input, collisional damping by n<sub>e</sub><br>
  <strong style="color:#aaccdd">&delta;B/B (turbulence)</strong>
    &nbsp;&#8733; &beta;<sub>N</sub> / q&sup2;
    &nbsp;&mdash; ideal ballooning drive, zero at low &beta; or high q<br>
  <strong style="color:#aaccdd">Particle advance</strong>
    &nbsp;: &Delta;&theta; = v<sub>tor</sub>&middot;s &nbsp;,&nbsp;
    &Delta;&phi; = &Delta;&theta;/q &nbsp;&mdash; rotational transform &iota; = 1/q
</div>
"""

def create_app() -> gr.Blocks:
    with gr.Blocks(title="Tokamak MHD Simulation", css=APP_CSS) as demo:
        gr.HTML("""
        <div class="title-bar">
          <div class="title-main">&#9889; TOKAMAK MHD FLUID SIMULATION</div>
          <div class="title-sub">
            WebGL &middot; Three.js r128 &middot; ITER-scale geometry &middot; Fusion reactor operator inputs
          </div>
        </div>
        """)
        gr.HTML(build_iframe())
        gr.HTML(PHYSICS_NOTES)
    return demo


if __name__ == "__main__":
    demo = create_app()
    demo.launch(share=False)
