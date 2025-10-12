import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/sobre-nos', name='Sobre Nós')

layout = html.Div([
    html.Link(rel='stylesheet', href='/static/css/styleConfigs.css'),
    
    html.Div([
        html.H1("Sobre Nós", style={
            "color": "var(--accent-color)",
            "textAlign": "center", 
            "marginBottom": "2rem",
            "fontSize": "2.5rem",
            "fontWeight": "bold"
        }),
        
        dbc.Card([
            dbc.CardBody([
                html.P("""
                    Somos uma equipe formada por cinco desenvolvedores, estudantes do curso técnico 
                    em Informática para Internet na Etec Antônio Furlan. Este aplicativo foi desenvolvido 
                    como parte do nosso Trabalho de Conclusão de Curso (TCC), sendo orientado por nossos professores.
                """, style={
                    "textAlign": "justify", 
                    "lineHeight": "1.6", 
                    "marginBottom": "2rem",
                    "color": "var(--primary-text-color)",
                    "fontWeight": "500"
                }),
                
                html.H2("Desenvolvedores", style={
                    "color": "var(--accent-color)", 
                    "marginBottom": "1rem",
                    "textAlign": "center",
                    "fontWeight": "bold"
                }),
                
                html.Ul([
                    html.Li("Otávio Augusto - Desenvolvimento do aplicativo e integração com banco de dados.", 
                           style={
                               "padding": "0.5rem 0", 
                               "borderBottom": "2px solid var(--border-color)",
                               "color": "var(--primary-text-color)",
                               "fontWeight": "500"
                           }),
                    html.Li("Otávio Pinheiro - Desenvolvimento do aplicativo e prototipação.", 
                           style={
                               "padding": "0.5rem 0", 
                               "borderBottom": "2px solid var(--border-color)",
                               "color": "var(--primary-text-color)",
                               "fontWeight": "500"
                           }),
                    html.Li("Kevin Martins - Desenvolvimento do site e integração do banco de dados.", 
                           style={
                               "padding": "0.5rem 0", 
                               "borderBottom": "2px solid var(--border-color)",
                               "color": "var(--primary-text-color)",
                               "fontWeight": "500"
                           }),
                    html.Li("Leonardo Alves - Desenvolvimento do site e prototipação.", 
                           style={
                               "padding": "0.5rem 0", 
                               "borderBottom": "2px solid var(--border-color)",
                               "color": "var(--primary-text-color)",
                               "fontWeight": "500"
                           }),
                    html.Li("Miguel Gonçalves - Criação do banco de dados e documentação.", 
                           style={
                               "padding": "0.5rem 0",
                               "color": "var(--primary-text-color)",
                               "fontWeight": "500"
                           })
                ], style={
                    "listStyle": "none", 
                    "padding": "0", 
                    "margin": "1rem 0"
                }),
            ])
        ], style={
            "backgroundColor": "var(--card-bg-color)",
            "border": "2px solid var(--border-color)",
            "borderRadius": "12px",
            "padding": "2rem",
            "marginBottom": "2rem",
            "boxShadow": "0 0 15px var(--accent-color)"
        }),
        
        html.Div([
            dcc.Link(
                "← Voltar para o Dashboard",
                href="/dashboard/",
                style={
                    "display": "inline-block",
                    "padding": "10px 20px",
                    "backgroundColor": "var(--button-bg-color)",
                    "color": "var(--button-text-color)",
                    "textDecoration": "none",
                    "borderRadius": "5px",
                    "marginTop": "2rem",
                    "border": "2px solid var(--border-color)",
                    "fontWeight": "bold"
                }
            )
        ], style={"textAlign": "center"})
        
    ], style={
        "maxWidth": "800px",
        "margin": "0 auto",
        "padding": "2rem",
        "color": "var(--primary-text-color)"
    })
], style={
    "backgroundColor": "var(--bg-color)", 
    "minHeight": "100vh",
    "color": "var(--primary-text-color)"
})