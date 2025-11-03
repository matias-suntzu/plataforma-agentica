"""
Dashboard de Observability - Bonus
Dashboard web interactivo para monitorear el sistema en tiempo real

FUNCIONALIDADES:
1. Métricas en tiempo real
2. Gráficos de workflows
3. Estado de caché
4. Anomalías detectadas
5. Violaciones de guardrails
6. Logs en tiempo real

USO:
    python dashboard.py
    # Abre http://localhost:8050
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import plotly.graph_objs as go
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from collections import defaultdict


class DashboardDataLoader:
    """Carga datos de los archivos de logs."""
    
    def __init__(self):
        self.base_path = Path(".")
    
    def load_jsonl(self, filename: str) -> List[dict]:
        """Carga un archivo JSONL."""
        filepath = self.base_path / filename
        
        if not filepath.exists():
            return []
        
        data = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
        except Exception as e:
            print(f"Error loading {filename}: {e}")
        
        return data
    
    def get_router_decisions(self) -> List[dict]:
        """Carga decisiones del router."""
        return self.load_jsonl("router_v2_decisions.jsonl")
    
    def get_orchestrator_metrics(self) -> List[dict]:
        """Carga métricas del orchestrator."""
        return self.load_jsonl("orchestrator_v2_metrics.jsonl")
    
    def get_guardrails_violations(self) -> List[dict]:
        """Carga violaciones de guardrails."""
        return self.load_jsonl("guardrails_violations.jsonl")
    
    def get_anomalies(self) -> List[dict]:
        """Carga anomalías detectadas."""
        return self.load_jsonl("anomalies_detected.jsonl")
    
    def get_system_stats(self) -> dict:
        """Calcula estadísticas generales del sistema."""
        
        router_decisions = self.get_router_decisions()
        metrics = self.get_orchestrator_metrics()
        violations = self.get_guardrails_violations()
        anomalies = self.get_anomalies()
        
        # Contar por categoría
        categories = defaultdict(int)
        for decision in router_decisions:
            categories[decision.get('category', 'unknown')] += 1
        
        # Calcular latencia promedio
        latencies = [m.get('elapsed_time', 0) for m in metrics if m.get('elapsed_time')]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Hit rate de caché
        cached_queries = sum(1 for m in metrics if m.get('workflow_type') == 'cached')
        total_queries = len(metrics)
        cache_hit_rate = (cached_queries / total_queries * 100) if total_queries > 0 else 0
        
        return {
            'total_queries': len(router_decisions),
            'categories': dict(categories),
            'avg_latency': round(avg_latency, 2),
            'cache_hit_rate': round(cache_hit_rate, 2),
            'total_violations': len(violations),
            'total_anomalies': len(anomalies),
            'critical_anomalies': sum(1 for a in anomalies if a.get('severity') == 'critical')
        }


# Inicializar Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Loader de datos
data_loader = DashboardDataLoader()

# Layout del dashboard
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("🔍 Dashboard de Observability", className="text-center mb-4"),
            html.P("Monitoreo en Tiempo Real del Sistema de Agente de Meta Ads", 
                   className="text-center text-muted")
        ])
    ]),
    
    html.Hr(),
    
    # Métricas principales
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📊 Total Queries", className="card-title"),
                    html.H2(id="total-queries", children="0", className="text-primary"),
                ])
            ])
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("⚡ Latencia Promedio", className="card-title"),
                    html.H2(id="avg-latency", children="0s", className="text-success"),
                ])
            ])
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("💾 Cache Hit Rate", className="card-title"),
                    html.H2(id="cache-hit-rate", children="0%", className="text-info"),
                ])
            ])
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("🚨 Anomalías Críticas", className="card-title"),
                    html.H2(id="critical-anomalies", children="0", className="text-danger"),
                ])
            ])
        ], width=3),
    ], className="mb-4"),
    
    # Gráficos
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📈 Distribución de Workflows"),
                dbc.CardBody([
                    dcc.Graph(id="workflow-distribution")
                ])
            ])
        ], width=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("⏱️  Latencia por Workflow"),
                dbc.CardBody([
                    dcc.Graph(id="latency-chart")
                ])
            ])
        ], width=6),
    ], className="mb-4"),
    
    # Violaciones y Anomalías
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔒 Violaciones de Guardrails"),
                dbc.CardBody([
                    html.Div(id="violations-list")
                ])
            ])
        ], width=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("⚠️  Anomalías Detectadas"),
                dbc.CardBody([
                    html.Div(id="anomalies-list")
                ])
            ])
        ], width=6),
    ], className="mb-4"),
    
    # Auto-refresh
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # Actualizar cada 5 segundos
        n_intervals=0
    )
    
], fluid=True)


# Callbacks para actualizar datos
@app.callback(
    [
        Output('total-queries', 'children'),
        Output('avg-latency', 'children'),
        Output('cache-hit-rate', 'children'),
        Output('critical-anomalies', 'children'),
    ],
    Input('interval-component', 'n_intervals')
)
def update_metrics(n):
    """Actualiza las métricas principales."""
    
    stats = data_loader.get_system_stats()
    
    return (
        str(stats['total_queries']),
        f"{stats['avg_latency']}s",
        f"{stats['cache_hit_rate']}%",
        str(stats['critical_anomalies'])
    )


@app.callback(
    Output('workflow-distribution', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_workflow_distribution(n):
    """Actualiza el gráfico de distribución de workflows."""
    
    stats = data_loader.get_system_stats()
    categories = stats['categories']
    
    if not categories:
        categories = {'simple': 0, 'sequential': 0, 'agentic': 0, 'conversation': 0}
    
    # Colores por categoría
    colors = {
        'simple': '#17a2b8',
        'sequential': '#ffc107',
        'agentic': '#28a745',
        'conversation': '#6f42c1'
    }
    
    fig = go.Figure(data=[
        go.Pie(
            labels=list(categories.keys()),
            values=list(categories.values()),
            marker=dict(colors=[colors.get(k, '#cccccc') for k in categories.keys()]),
            hole=0.3
        )
    ])
    
    fig.update_layout(
        showlegend=True,
        height=300,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    return fig


@app.callback(
    Output('latency-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_latency_chart(n):
    """Actualiza el gráfico de latencia."""
    
    metrics = data_loader.get_orchestrator_metrics()
    
    if not metrics:
        return go.Figure()
    
    # Agrupar por workflow type
    workflow_latencies = defaultdict(list)
    
    for metric in metrics[-50:]:  # Últimos 50
        wf_type = metric.get('workflow_type', 'unknown')
        latency = metric.get('elapsed_time', 0)
        workflow_latencies[wf_type].append(latency)
    
    # Calcular promedios
    avg_latencies = {
        wf: sum(latencies) / len(latencies) 
        for wf, latencies in workflow_latencies.items()
        if latencies
    }
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(avg_latencies.keys()),
            y=list(avg_latencies.values()),
            marker_color=['#17a2b8', '#ffc107', '#28a745', '#6f42c1'][:len(avg_latencies)]
        )
    ])
    
    fig.update_layout(
        yaxis_title="Latencia (segundos)",
        showlegend=False,
        height=300,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    return fig


@app.callback(
    Output('violations-list', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_violations(n):
    """Actualiza la lista de violaciones."""
    
    violations = data_loader.get_guardrails_violations()
    
    if not violations:
        return html.P("✅ No hay violaciones recientes", className="text-success")
    
    # Mostrar últimas 5
    recent = violations[-5:]
    
    items = []
    for v in reversed(recent):
        severity_color = {
            'critical': 'danger',
            'error': 'warning',
            'warning': 'info'
        }.get(v.get('severity', 'info'), 'info')
        
        items.append(
            dbc.Alert([
                html.Strong(f"{v.get('severity', 'INFO').upper()}: "),
                v.get('reason', 'No reason'),
                html.Br(),
                html.Small(f"User: {v.get('user_id', 'unknown')} | {v.get('timestamp', '')}", 
                          className="text-muted")
            ], color=severity_color, className="mb-2")
        )
    
    return items


@app.callback(
    Output('anomalies-list', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_anomalies(n):
    """Actualiza la lista de anomalías."""
    
    anomalies = data_loader.get_anomalies()
    
    if not anomalies:
        return html.P("✅ No hay anomalías detectadas", className="text-success")
    
    # Mostrar últimas 5
    recent = anomalies[-5:]
    
    items = []
    for a in reversed(recent):
        severity_color = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'secondary'
        }.get(a.get('severity', 'info'), 'info')
        
        items.append(
            dbc.Alert([
                html.Strong(f"{a.get('type', 'UNKNOWN').upper()}: "),
                f"{a.get('metric_name', 'N/A')} = {a.get('current_value', 0):.2f}",
                html.Br(),
                html.Small(a.get('description', ''), className="text-muted")
            ], color=severity_color, className="mb-2")
        )
    
    return items


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎨 Dashboard de Observability")
    print("="*60)
    print("\n📊 Iniciando servidor...")
    print("🌐 Dashboard disponible en: http://localhost:8050")
    print("\n💡 Presiona Ctrl+C para detener\n")
    
    app.run(debug=True, host='0.0.0.0', port=8050)