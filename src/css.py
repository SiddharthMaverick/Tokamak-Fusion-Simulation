"""src/css.py — Gradio stylesheet for the Tokamak dashboard."""

APP_CSS: str = """
body, .gradio-container {
    background: #020409 !important;
    font-family: 'Courier New', monospace !important;
}
.title-bar {
    border-bottom: 1px solid rgba(0,212,255,0.2);
    padding-bottom: 10px;
    margin-bottom: 14px;
}
.title-main {
    font-size: 20px;
    font-weight: 900;
    color: #00d4ff;
    letter-spacing: .15em;
}
.title-sub {
    font-size: 11px;
    color: #3a5070;
    margin-top: 4px;
    letter-spacing: .07em;
}
"""
