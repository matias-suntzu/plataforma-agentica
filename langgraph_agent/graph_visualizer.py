"""
Graph Visualizer - Studio Style
Visualizador interactivo del grafo LangGraph estilo LangSmith Studio

FUNCIONALIDADES:
1. Visualización del grafo con nodos y aristas
2. Ejecución interactiva paso a paso
3. Inspección de estado en cada nodo
4. Time travel debugging
5. Exportación a imagen

USO:
    python graph_visualizer.py
    # Abre http://localhost:8051
"""

import json
from datetime import datetime
from typing import List, Dict, Any
from dash import Dash, html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from agent import app as agent_app, should_continue
from langchain_core.messages import HumanMessage
import uuid


class GraphVisualizer:
    """Visualizador del grafo LangGraph."""
    
    def __init__(self, graph_app):
        self.graph = graph_app
        self.execution_history = []
    
    def get_graph_structure(self) -> Dict[str, Any]:
        """Obtiene la estructura del grafo."""
        
        # Estructura del grafo de tu agente
        nodes = [
            {"id": "call_llm", "label": "Call LLM", "type": "llm", "color": "#4CAF50"},
            {"id": "execute_tools", "label": "Execute Tools", "type": "tool", "color": "#2196F3"},
            {"id": "end", "label": "END", "type": "end", "color": "#F44336"}
        ]
        
        edges = [
            {"source": "call_llm", "target": "execute_tools", "condition": "has_tool_calls"},
            {"source": "call_llm", "target": "end", "condition": "no_tool_calls"},
            {"source": "execute_tools", "target": "call_llm", "condition": "always"}
        ]
        
        return {"nodes": nodes, "edges": edges}
    
    def create_graph_figure(self, highlighted_node: str = None) -> go.Figure:
        """Crea la figura de Plotly del grafo."""
        
        structure = self.get_graph_structure()
        
        # Posiciones de los nodos (layout manual)
        positions = {
            "call_llm": (0, 1),
            "execute_tools": (1, 0.5),
            "end": (0, 0)
        }
        
        # Crear nodos
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        
        for node in structure["nodes"]:
            x, y = positions[node["id"]]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node["label"])
            
            # Destacar nodo activo
            if highlighted_node == node["id"]:
                node_colors.append("#FFC107")  # Amarillo para nodo activo
                node_sizes.append(60)
            else:
                node_colors.append(node["color"])
                node_sizes.append(40)
        
        # Crear aristas
        edge_traces = []
        
        for edge in structure["edges"]:
            source_pos = positions[edge["source"]]
            target_pos = positions[edge["target"]]
            
            edge_trace = go.Scatter(
                x=[source_pos[0], target_pos[0], None],
                y=[source_pos[1], target_pos[1], None],
                mode='lines+text',
                line=dict(width=2, color='#888'),
                hoverinfo='text',
                text=[None, edge["condition"], None],
                textposition="middle center",
                showlegend=False
            )
            edge_traces.append(edge_trace)
        
        # Crear trace de nodos
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="bottom center",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white')
            ),
            hoverinfo='text',
            showlegend=False
        )
        
        # Crear figura
        fig = go.Figure(data=edge_traces + [node_trace])
        
        fig.update_layout(
            title="LangGraph Execution Flow",
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            height=500,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        return fig
    
    def execute_step(self, query: str, thread_id: str, step_index: int = 0) -> Dict[str, Any]:
        """Ejecuta un paso del grafo."""
        
        config = {"configurable": {"thread_id": thread_id}}
        
        if step_index == 0:
            # Primera ejecución
            input_state = {"messages": [HumanMessage(content=query)]}
            result = self.graph.invoke(input_state, config=config)
            
            return {
                "step": 0,
                "node": "call_llm",
                "state": result,
                "messages": len(result.get("messages", [])),
                "tool_calls": self._has_tool_calls(result)
            }
        
        return {"step": step_index, "node": "unknown", "state": {}}
    
    def _has_tool_calls(self, state: dict) -> bool:
        """Verifica si hay tool calls en el estado."""
        messages = state.get("messages", [])
        if not messages:
            return False
        
        last_message = messages[-1]
        return hasattr(last_message, 'tool_calls') and bool(last_message.tool_calls)


# Inicializar Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Visualizador
visualizer = GraphVisualizer(agent_app)

# Layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("🔍 LangGraph Studio Visualizer", className="text-center mb-4"),
            html.P("Visualización y debugging interactivo del grafo", 
                   className="text-center text-muted")
        ])
    ]),
    
    html.Hr(),
    
    # Control Panel
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🎮 Control Panel"),
                dbc.CardBody([
                    dbc.Label("Query:"),
                    dbc.Input(
                        id="query-input",
                        type="text",
                        placeholder="Ej: dame el TOP 3 de anuncios de Baqueira",
                        value="lista todas las campañas"
                    ),
                    html.Br(),
                    dbc.Button("▶️ Ejecutar", id="run-button", color="primary", className="me-2"),
                    dbc.Button("⏭️ Siguiente Paso", id="step-button", color="secondary", className="me-2"),
                    dbc.Button("🔄 Reiniciar", id="reset-button", color="warning"),
                    html.Hr(),
                    html.Div(id="execution-status", className="mt-3")
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    # Graph Visualization
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 Grafo de Ejecución"),
                dbc.CardBody([
                    dcc.Graph(id="graph-viz", figure=visualizer.create_graph_figure())
                ])
            ])
        ], width=8),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔍 Estado del Nodo"),
                dbc.CardBody([
                    html.Div(id="node-state")
                ])
            ])
        ], width=4)
    ], className="mb-4"),
    
    # Execution History
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📜 Historial de Ejecución"),
                dbc.CardBody([
                    html.Div(id="execution-history")
                ])
            ])
        ])
    ]),
    
    # Hidden state storage
    dcc.Store(id='execution-state', data={
        'thread_id': None,
        'current_step': 0,
        'query': None,
        'history': []
    })
    
], fluid=True)


# Callbacks
@app.callback(
    [
        Output('graph-viz', 'figure'),
        Output('execution-status', 'children'),
        Output('node-state', 'children'),
        Output('execution-history', 'children'),
        Output('execution-state', 'data')
    ],
    [
        Input('run-button', 'n_clicks'),
        Input('step-button', 'n_clicks'),
        Input('reset-button', 'n_clicks')
    ],
    [
        State('query-input', 'value'),
        State('execution-state', 'data')
    ]
)
def handle_execution(run_clicks, step_clicks, reset_clicks, query, exec_state):
    """Maneja la ejecución del grafo."""
    
    ctx = callback_context
    
    if not ctx.triggered:
        # Inicial
        return (
            visualizer.create_graph_figure(),
            html.Div("⏸️ Esperando comando...", className="text-muted"),
            html.P("Ejecuta una query para ver el estado", className="text-muted"),
            html.P("No hay historial", className="text-muted"),
            exec_state
        )
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Reset
    if button_id == 'reset-button':
        return (
            visualizer.create_graph_figure(),
            html.Div("🔄 Reiniciado", className="text-success"),
            html.P("Listo para nueva ejecución", className="text-muted"),
            html.P("Historial limpiado", className="text-muted"),
            {
                'thread_id': None,
                'current_step': 0,
                'query': None,
                'history': []
            }
        )
    
    # Run
    if button_id == 'run-button':
        if not query:
            return (
                visualizer.create_graph_figure(),
                html.Div("❌ Ingresa una query primero", className="text-danger"),
                html.P("", className="text-muted"),
                html.P("", className="text-muted"),
                exec_state
            )
        
        # Nueva ejecución
        thread_id = f"viz_{uuid.uuid4().hex[:8]}"
        
        try:
            # Ejecutar grafo completo
            config = {"configurable": {"thread_id": thread_id}}
            input_state = {"messages": [HumanMessage(content=query)]}
            result = agent_app.invoke(input_state, config=config)
            
            # Extraer información
            messages = result.get("messages", [])
            final_response = messages[-1].content if messages else "No response"
            
            # Crear historial
            history = []
            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                history.append({
                    "step": i,
                    "type": msg_type,
                    "content": str(msg.content)[:100] if hasattr(msg, 'content') else 'N/A'
                })
            
            # Visualización
            status = html.Div([
                html.H5("✅ Ejecución Completada", className="text-success"),
                html.P(f"Thread ID: {thread_id}"),
                html.P(f"Total mensajes: {len(messages)}")
            ])
            
            node_state = html.Div([
                html.H6("Estado Final:"),
                html.Pre(final_response[:500], style={"max-height": "300px", "overflow": "auto"})
            ])
            
            history_view = html.Div([
                html.Div([
                    dbc.Badge(f"Step {h['step']}", color="primary", className="me-2"),
                    dbc.Badge(h['type'], color="secondary", className="me-2"),
                    html.Span(h['content'][:80] + "...")
                ], className="mb-2") for h in history
            ])
            
            return (
                visualizer.create_graph_figure(highlighted_node="end"),
                status,
                node_state,
                history_view,
                {
                    'thread_id': thread_id,
                    'current_step': len(messages),
                    'query': query,
                    'history': history
                }
            )
        
        except Exception as e:
            return (
                visualizer.create_graph_figure(),
                html.Div(f"❌ Error: {str(e)}", className="text-danger"),
                html.P("Error en ejecución", className="text-danger"),
                html.P("Ver logs para más detalles", className="text-muted"),
                exec_state
            )
    
    # Default
    return (
        visualizer.create_graph_figure(),
        html.Div("⏸️ Esperando...", className="text-muted"),
        html.P("", className="text-muted"),
        html.P("", className="text-muted"),
        exec_state
    )


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎨 LangGraph Studio Visualizer")
    print("="*60)
    print("\n📊 Iniciando servidor...")
    print("🌐 Visualizador disponible en: http://localhost:8051")
    print("\n💡 Presiona Ctrl+C para detener\n")
    
    app.run(debug=True, host='0.0.0.0', port=8051)