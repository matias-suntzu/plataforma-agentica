"""
Setup script para habilitar LangSmith tracing y generar diagramas
"""
import os
from pathlib import Path
import sys

def setup_langsmith():
    """Configura LangSmith tracing en .env"""
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ No se encontró archivo .env")
        print("   Creando .env nuevo...")
        env_file.touch()
    
    # Leer .env actual
    with open(env_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verificar si ya está configurado
    has_langsmith = "LANGCHAIN_TRACING_V2" in content
    
    if has_langsmith:
        print("✅ LangSmith ya está configurado en .env")
        return
    
    # Agregar configuración
    print("📝 Agregando configuración de LangSmith a .env...")
    
    langsmith_config = """
# =============================================================================
# LangSmith Configuration (Observability & Tracing)
# =============================================================================
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_PROJECT=meta-ads-agent

# ⚠️ IMPORTANTE: Reemplaza con tu API key real de LangSmith
# Obtén tu key en: https://smith.langchain.com → Settings → API Keys
LANGCHAIN_API_KEY=tu_langsmith_api_key_aqui
"""
    
    with open(env_file, "a", encoding="utf-8") as f:
        f.write(langsmith_config)
    
    print("✅ Configuración agregada a .env")
    print("\n" + "="*70)
    print("⚠️  ACCIÓN REQUERIDA:")
    print("="*70)
    print("1. Ve a https://smith.langchain.com")
    print("2. Crea cuenta gratuita (si no la tienes)")
    print("3. Settings → API Keys → Create API Key")
    print("4. Copia la API key")
    print("5. Abre .env y reemplaza 'tu_langsmith_api_key_aqui' con tu key real")
    print("\n6. Reinicia slack_bot.py")
    print("7. ✅ Las trazas aparecerán automáticamente en LangSmith!")
    print("="*70)

def generate_diagrams():
    """Genera diagramas del grafo actual"""
    
    print("\n📊 Generando diagramas del grafo...")
    
    try:
        # Importar el grafo compilado
        from agent import workflow
        
        graph = workflow.get_graph()
        
        # 1. ASCII Diagram
        print("   Generando diagrama ASCII...")
        try:
            ascii_diagram = graph.draw_ascii()
            with open("docs/graph_ascii.txt", "w", encoding="utf-8") as f:
                f.write(ascii_diagram)
            print("   ✅ graph_ascii.txt")
        except Exception as e:
            print(f"   ⚠️ Error con ASCII: {e}")
        
        # 2. Mermaid Diagram
        print("   Generando diagrama Mermaid...")
        try:
            mermaid_diagram = graph.draw_mermaid()
            with open("docs/graph_mermaid.md", "w", encoding="utf-8") as f:
                f.write("# Agent Graph Visualization\n\n")
                f.write("```mermaid\n")
                f.write(mermaid_diagram)
                f.write("\n```\n\n")
                f.write("## Nodos:\n")
                f.write("- **call_llm**: Invoca al LLM (Gemini) para decisiones\n")
                f.write("- **execute_tools**: Ejecuta herramientas (Meta Ads API)\n")
            print("   ✅ graph_mermaid.md")
        except Exception as e:
            print(f"   ⚠️ Error con Mermaid: {e}")
        
        # 3. PNG (opcional, requiere graphviz)
        print("   Intentando generar PNG...")
        try:
            png_data = graph.draw_mermaid_png()
            with open("docs/graph.png", "wb") as f:
                f.write(png_data)
            print("   ✅ graph.png")
        except Exception as e:
            print("   ⚠️ PNG no disponible (requiere graphviz)")
            print("      Para instalar: pip install pygraphviz")
        
        print("\n✅ Diagramas generados en carpeta 'docs/'")
        
    except ImportError as e:
        print(f"❌ Error importando agent.py: {e}")
        print("   Asegúrate de estar en la carpeta correcta")
        return False
    except Exception as e:
        print(f"❌ Error generando diagramas: {e}")
        return False
    
    return True

def create_docs_folder():
    """Crea carpeta docs si no existe"""
    docs_folder = Path("docs")
    if not docs_folder.exists():
        docs_folder.mkdir()
        print("📁 Carpeta 'docs/' creada")

def verify_dependencies():
    """Verifica que las dependencias necesarias estén instaladas"""
    
    print("\n🔍 Verificando dependencias...")
    
    required = {
        "langsmith": "langsmith",
        "langgraph": "langgraph",
        "langchain_core": "langchain-core"
    }
    
    missing = []
    
    for module, package in required.items():
        try:
            __import__(module)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - FALTA")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Instalar dependencias faltantes:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    print("✅ Todas las dependencias instaladas")
    return True

def create_readme():
    """Crea README con instrucciones de uso"""
    
    readme_content = """# Meta Ads Agent - Observabilidad

## 🎯 Setup Completado

Tu agente ahora tiene observabilidad completa con LangSmith.

## 📊 Ver Trazas

1. Ve a: https://smith.langchain.com/projects
2. Selecciona proyecto: **meta-ads-agent**
3. Verás todas las ejecuciones con:
   - Árbol de llamadas
   - Input/Output de cada nodo
   - Latencias (ms)
   - Costos por token ($)
   - Errores si los hay

## 📁 Archivos Generados

- `docs/graph_ascii.txt` - Diagrama en texto (ASCII)
- `docs/graph_mermaid.md` - Diagrama para GitHub/docs
- `docs/graph.png` - Imagen (si graphviz está instalado)

## 🚀 Uso

### Ejecutar el bot:
```bash
python slack_bot.py
```

### Ver trazas en tiempo real:
- Cada interacción aparece automáticamente en LangSmith
- No requiere cambios en el código
- Funciona con memoria persistente

## 🔧 Troubleshooting

### No aparecen trazas en LangSmith:
1. Verifica que `LANGCHAIN_API_KEY` esté configurado en `.env`
2. Reinicia el bot: `Ctrl+C` y `python slack_bot.py`
3. Verifica en los logs: "✅ LangSmith tracing: true"

### Error de autenticación:
- Tu API key puede ser inválida
- Genera una nueva en: https://smith.langchain.com → Settings → API Keys

## 📚 Siguiente Paso

Desarrollar Router + Workflows para optimizar latencia y costos.
"""
    
    with open("docs/README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("📄 README creado en docs/README.md")

def main():
    """Función principal"""
    
    print("\n" + "="*70)
    print("🚀 SETUP DE OBSERVABILIDAD - META ADS AGENT")
    print("="*70)
    print()
    
    # 1. Verificar dependencias
    if not verify_dependencies():
        print("\n❌ Instala las dependencias faltantes antes de continuar")
        sys.exit(1)
    
    # 2. Crear carpeta docs
    create_docs_folder()
    
    # 3. Configurar LangSmith
    setup_langsmith()
    
    # 4. Generar diagramas
    generate_diagrams()
    
    # 5. Crear README
    create_readme()
    
    print("\n" + "="*70)
    print("✅ SETUP COMPLETADO")
    print("="*70)
    
    print("\n📋 RESUMEN:")
    print("   ✅ LangSmith configurado en .env")
    print("   ✅ Diagramas generados en docs/")
    print("   ✅ README creado")
    
    print("\n⚠️  PRÓXIMOS PASOS:")
    print("   1. Configura LANGCHAIN_API_KEY en .env")
    print("   2. Reinicia el bot: python slack_bot.py")
    print("   3. Prueba una consulta en Slack")
    print("   4. Ve las trazas en: https://smith.langchain.com/projects")
    
    print("\n🎯 Cuando esté listo, continuaremos con:")
    print("   - Router inteligente")
    print("   - Workflows especializados")
    print("   - Optimización de latencia")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()