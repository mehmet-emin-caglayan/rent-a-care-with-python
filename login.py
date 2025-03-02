# login.py
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from auth import authenticate_user  # auth.py'deki doğrulama fonksiyonunu kullanıyoruz

def create_login_layout():
    return html.Div([
        html.H2("📊 Modbus İzleme Sistemi - Giriş", style={"textAlign": "center", "marginBottom": "40px"}),
        dbc.Input(id="username", type="text", placeholder="Kullanıcı Adı", style={"marginBottom": "20px"}),
        dbc.Input(id="password", type="password", placeholder="Şifre", style={"marginBottom": "20px"}),
        dbc.Button("Giriş Yap", id="login-button", n_clicks=0, style={"width": "100%", "marginBottom": "20px"}),
        html.Div(id="error-message", style={"color": "red", "marginTop": "20px"}),
        dcc.Location(id="redirect", refresh=True)
    ])

# Giriş sayfası için callback'ler
def login_callbacks(app):
    @app.callback(
        [Output("error-message", "children"), Output("redirect", "pathname")],
        [Input("login-button", "n_clicks")],
        [State("username", "value"), State("password", "value")]
    )
    def login_user(n_clicks, username, password):
        if n_clicks == 0:
            return "", None

        if not username or not password:
            return "Kullanıcı adı ve şifre boş olamaz.", None

        if authenticate_user(username, password):
            return "", "/canli_graf"
        else:
            return "Kullanıcı adı veya şifre yanlış.", None
