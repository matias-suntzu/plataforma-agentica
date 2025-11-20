def process_query(
    self,
    query: str,
    thread_id: Optional[str] = None,
    force_workflow: Optional[str] = None,
    messages: Optional[List[BaseMessage]] = None  # ✅ Nuevo parámetro
) -> WorkflowResult:
    """
    Procesa una consulta con arquitectura multi-agente (4 agentes).
    
    Args:
        query: Consulta del usuario
        thread_id: ID del thread para memoria (opcional)
        force_workflow: Forzar workflow específico (opcional)
        messages: Historial de mensajes para contexto (opcional) ✅
        
    Returns:
        WorkflowResult con la respuesta
    """
    start_time = datetime.now()
    
    if not thread_id:
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    
    print("\n" + "="*70)
    print(f"🔥 NUEVA CONSULTA (V5 - 4 Agentes)")
    print(f"   Query: '{query}' | Thread: {thread_id}")
    if messages:
        print(f"   📚 Contexto: {len(messages)} mensajes previos")
    print("="*70)
    
    try:
        # PASO 1: Clasificar con Router V4 (CON CONTEXTO) ✅
        if force_workflow:
            category = force_workflow
            print(f"   🔧 Forzando workflow: {category}")
        else:
            route_result = self.router.classify(query, messages=messages)  # ✅ Pasar mensajes
            category = route_result.category
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # PASO 2: Ejecutar según categoría (sin cambios)
        if category == "simple":
            result = self.fast_path.execute(query)
            workflow_type = "simple"
        
        elif category == "agentic":
            coord_decision = self.coordinator.route(query)
            
            if coord_decision.agent == "config":
                result = self._execute_single_agent(
                    self.config_agent, query, config, "agentic_config"
                )
                workflow_type = "agentic_config"
            
            elif coord_decision.agent == "performance":
                result = self._execute_single_agent(
                    self.performance_agent, query, config, "agentic_performance"
                )
                workflow_type = "agentic_performance"
            
            elif coord_decision.agent == "recommendation":
                result = self._execute_single_agent(
                    self.recommendation_agent, query, config, "agentic_recommendation"
                )
                workflow_type = "agentic_recommendation"
            
            else:  # multi
                result = self._execute_multi_agent(query, config)
                workflow_type = "multi_agent"
        
        elif category == "multi_agent":
            result = self._execute_multi_agent(query, config)
            workflow_type = "multi_agent"
        
        else:
            result = WorkflowResult(
                content=f"❌ Categoría desconocida: {category}",
                workflow_type="error",
                metadata={"error": "unknown_category"}
            )
            workflow_type = "error"
        
        # Actualizar métricas
        elapsed_time = (datetime.now() - start_time).total_seconds()
        if workflow_type in self.metrics:
            self.metrics[workflow_type]["count"] += 1
            self.metrics[workflow_type]["total_time"] += elapsed_time
        
        print(f"\n✅ Respuesta generada en {elapsed_time:.2f}s")
        print(f"   Workflow: {workflow_type}")
        print("="*70)
        
        return result
    
    except Exception as e:
        print(f"\n❌ ERROR EN ORCHESTRATOR: {e}")
        import traceback
        traceback.print_exc()
        
        return WorkflowResult(
            content=f"❌ Error inesperado: {str(e)}",
            workflow_type="error",
            metadata={"error": str(e)}
        )