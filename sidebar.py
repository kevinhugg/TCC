import dash
from dash import html

def get_sidebar():
    # Cria a lista de links das páginas registradas
    links = []
    for page in dash.page_registry.values():
        links.append(
            html.Div(
                html.A(page["name"], href=f"/dashboard{page["path"]}", className="sidebar-link")
            )
        )

    sidebar = html.Div([
        html.Div([
        html.Img(src="/static/assets/img/logoSemurb.png", alt="Logo da SEMURB", className="semurb-logo"),
        html.H2("SEMURB", className="sidebar-title"),  # Título no topo
        ], className="logo-title-container"),

        *links  # Desempacota a lista de links
    ], className="div6")

    return sidebar