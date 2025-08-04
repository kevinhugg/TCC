import dash
from dash import html

def get_sidebar():
    # Define a mapping of page paths to icons and names
    page_map = {
        "/": {"name": "Home", "icon": "fas fa-home"},
        "/pageVehicles": {"name": "Viaturas", "icon": "fas fa-car"},
        "/pageAgents": {"name": "Agentes", "icon": "fas fa-users"},
        "/services": {"name": "Serviços", "icon": "fas fa-concierge-bell"},
        "/ocurrences": {"name": "Ocorrências", "icon": "fas fa-exclamation-triangle"},
        "/historic": {"name": "Histórico", "icon": "fas fa-history"},
        "/configurations": {"name": "Configurações", "icon": "fas fa-cog"},
    }

    links = []
    for path, details in page_map.items():
        links.append(
            html.A(
                [
                    html.I(className=details["icon"]),
                    html.Span(details["name"], className="sidebar-link-text")
                ],
                href=f"/dashboard{path}",
                className="sidebar-link"
            )
        )

    sidebar = html.Div(
        [
            html.Div(
                [
                    html.Img(src="/static/assets/img/logoSemurb.png", alt="Logo da SEMURB", className="semurb-logo"),
                    html.H2("SEMURB", className="sidebar-title"),
                ],
                className="logo-title-container"
            ),
            html.Nav(links, className="sidebar-nav"),
        ]
    )

    return sidebar