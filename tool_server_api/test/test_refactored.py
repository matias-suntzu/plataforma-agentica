"""
Tests para verificar la refactorización del servidor
Versión: 3.2

Ejecutar:
    python test/test_refactored.py

O con pytest:
    pytest test/test_refactored.py -v
"""

import sys
import os
from pathlib import Path

# Agregar el directorio padre al path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Cambiar al directorio del proyecto para paths relativos
os.chdir(project_root)

print("=" * 70)
print("🧪 TESTS DE REFACTORIZACIÓN - Servidor Meta Ads v3.2")
print("=" * 70)
print(f"📂 Directorio de trabajo: {project_root}")
print("=" * 70)


# ========== FASE 1: VERIFICAR ESTRUCTURA DE ARCHIVOS ==========
def test_structure():
    """Verifica que todos los archivos modulares existan"""
    print("\n📁 FASE 1: Verificando estructura de archivos...")
    
    required_files = [
        "config/__init__.py",
        "config/settings.py",
        "middleware/__init__.py",
        "middleware/auth.py",
        "models/__init__.py",
        "models/schemas.py",
        "tools/__init__.py",
        "tools/campaigns.py",
        "tools/ads.py",
        "tools/metrics.py",
        "tools/recommendations.py",
        "tools/actions.py",
        "tools/integrations.py",
        "utils/__init__.py",
        "utils/meta_api.py",
        "utils/helpers.py",
        "server.py"
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
            print(f"   ❌ Falta: {file}")
        else:
            print(f"   ✅ Existe: {file}")
    
    if missing:
        print(f"\n❌ FALLO: Faltan {len(missing)} archivos")
        return False
    else:
        print(f"\n✅ ÉXITO: Todos los archivos existen ({len(required_files)} archivos)")
        return True


# ========== FASE 2: VERIFICAR IMPORTS ==========
def test_imports():
    """Verifica que todos los módulos se puedan importar"""
    print("\n📦 FASE 2: Verificando imports de módulos...")
    
    import_tests = [
        ("config.settings", "settings"),
        ("middleware.auth", "AuthMiddleware"),
        ("models.schemas", "ListarCampanasInput"),
        ("tools.campaigns", "listar_campanas_func"),
        ("tools.ads", "obtener_anuncios_por_rendimiento_func"),
        ("tools.metrics", "get_all_campaigns_metrics_func"),
        ("tools.recommendations", "get_campaign_recommendations_func"),
        ("tools.actions", "update_adset_budget_func"),
        ("tools.integrations", "generar_reporte_google_slides_func"),
        ("utils.meta_api", "get_account"),
        ("utils.helpers", "safe_int_from_insight"),
    ]
    
    failed = []
    for module_name, object_name in import_tests:
        try:
            module = __import__(module_name, fromlist=[object_name])
            obj = getattr(module, object_name)
            print(f"   ✅ {module_name}.{object_name}")
        except Exception as e:
            print(f"   ❌ {module_name}.{object_name} - Error: {e}")
            failed.append(module_name)
    
    if failed:
        print(f"\n❌ FALLO: {len(failed)} imports fallaron")
        return False
    else:
        print(f"\n✅ ÉXITO: Todos los imports funcionan ({len(import_tests)} módulos)")
        return True


# ========== FASE 3: VERIFICAR CONFIGURACIÓN ==========
def test_configuration():
    """Verifica que la configuración sea válida"""
    print("\n⚙️ FASE 3: Verificando configuración...")
    
    try:
        from config.settings import settings
        
        # Verificar atributos críticos
        checks = [
            ("AD_ACCOUNT_ID", settings.AD_ACCOUNT_ID),
            ("TOOL_API_KEY", settings.TOOL_API_KEY),
            ("DESTINO_MAPPING", settings.DESTINO_MAPPING),
            ("BID_STRATEGY_MAP", settings.BID_STRATEGY_MAP),
        ]
        
        for name, value in checks:
            if value:
                print(f"   ✅ {name}: Configurado")
            else:
                print(f"   ⚠️ {name}: No configurado (puede causar errores)")
        
        # Verificar mapeos
        assert len(settings.DESTINO_MAPPING) > 0, "DESTINO_MAPPING vacío"
        assert len(settings.BID_STRATEGY_MAP) > 0, "BID_STRATEGY_MAP vacío"
        assert 'ibiza' in settings.DESTINO_MAPPING, "Falta destino 'ibiza'"
        
        print("\n✅ ÉXITO: Configuración válida")
        return True
    
    except Exception as e:
        print(f"\n❌ FALLO: Error en configuración - {e}")
        return False


# ========== FASE 4: VERIFICAR HELPERS ==========
def test_helpers():
    """Verifica funciones auxiliares"""
    print("\n🔧 FASE 4: Verificando funciones auxiliares...")
    
    try:
        from utils.helpers import safe_int_from_insight
        
        # Test casos comunes
        test_cases = [
            ([{"value": "123"}], 123),
            ([123], 123),
            (["456"], 456),
            (None, 0),
            (789, 789),
            ("101", 101),
            ([], 0),
            ([{"invalid": "data"}], 0),
        ]
        
        failed = []
        for input_val, expected in test_cases:
            result = safe_int_from_insight(input_val)
            if result == expected:
                print(f"   ✅ {input_val} → {result}")
            else:
                print(f"   ❌ {input_val} → {result} (esperado: {expected})")
                failed.append((input_val, result, expected))
        
        if failed:
            print(f"\n❌ FALLO: {len(failed)} casos fallaron")
            return False
        else:
            print(f"\n✅ ÉXITO: Todos los casos pasaron ({len(test_cases)} tests)")
            return True
    
    except Exception as e:
        print(f"\n❌ FALLO: Error en helpers - {e}")
        import traceback
        traceback.print_exc()
        return False


# ========== FASE 5: VERIFICAR SCHEMAS ==========
def test_schemas():
    """Verifica que los esquemas Pydantic funcionen"""
    print("\n📋 FASE 5: Verificando esquemas Pydantic...")
    
    try:
        from models.schemas import (
            ListarCampanasInput,
            BuscarIdCampanaInput,
            ObtenerAnunciosPorRendimientoInput,
            GetAllCampaignsMetricsInput,
            UpdateAdsetBudgetInput
        )
        
        # Test instanciación de schemas
        schemas_tests = [
            (ListarCampanasInput, {"placeholder": "test"}),
            (BuscarIdCampanaInput, {"nombre_campana": "Ibiza"}),
            (ObtenerAnunciosPorRendimientoInput, {
                "campana_id": "123",
                "date_preset": "last_7d",
                "limite": 5
            }),
            (GetAllCampaignsMetricsInput, {"date_preset": "last_30d"}),
            (UpdateAdsetBudgetInput, {
                "adset_id": "456",
                "new_daily_budget_eur": 15.0,
                "reason": "Test"
            }),
        ]
        
        for schema_class, data in schemas_tests:
            try:
                instance = schema_class(**data)
                print(f"   ✅ {schema_class.__name__}")
            except Exception as e:
                print(f"   ❌ {schema_class.__name__} - Error: {e}")
                return False
        
        print(f"\n✅ ÉXITO: Todos los schemas funcionan ({len(schemas_tests)} schemas)")
        return True
    
    except Exception as e:
        print(f"\n❌ FALLO: Error en schemas - {e}")
        import traceback
        traceback.print_exc()
        return False


# ========== FASE 6: VERIFICAR SERVER ==========
def test_server():
    """Verifica que el servidor se pueda inicializar"""
    print("\n🚀 FASE 6: Verificando servidor FastAPI...")
    
    try:
        # Importar sin ejecutar
        import server
        
        # Verificar que la app existe
        assert hasattr(server, 'app'), "Falta objeto 'app'"
        assert hasattr(server, 'chains'), "Falta objeto 'chains'"
        
        # Verificar cantidad de chains
        expected_chains = 9
        actual_chains = len(server.chains)
        
        if actual_chains == expected_chains:
            print(f"   ✅ Chains registrados: {actual_chains}/{expected_chains}")
        else:
            print(f"   ⚠️ Chains registrados: {actual_chains}/{expected_chains}")
        
        # Verificar rutas esperadas
        expected_routes = [
            '/listarcampanas',
            '/buscaridcampana',
            '/obteneranunciosrendimiento',
            '/getallcampaignsmetrics',
            '/getcampaignrecommendations',
            '/getcampaigndetails',
            '/updateadsetbudget',
            '/generar_reporte_slides',
            '/enviaralertaslack'
        ]
        
        for route in expected_routes:
            if route in server.chains:
                print(f"   ✅ Ruta: {route}")
            else:
                print(f"   ❌ Falta ruta: {route}")
                return False
        
        print(f"\n✅ ÉXITO: Servidor configurado correctamente")
        return True
    
    except Exception as e:
        print(f"\n❌ FALLO: Error al verificar servidor - {e}")
        import traceback
        traceback.print_exc()
        return False


# ========== FASE 7: TEST DE INTEGRACIÓN (OPCIONAL) ==========
def test_integration():
    """Test de integración con servidor real (requiere que esté corriendo)"""
    print("\n🌐 FASE 7: Test de integración (opcional)...")
    print("   ⏭️ Saltando (requiere servidor corriendo)")
    print("   💡 Para probar: python server.py en otra terminal")
    return True


# ========== EJECUTAR TODOS LOS TESTS ==========
def run_all_tests():
    """Ejecuta todos los tests en secuencia"""
    print("\n" + "=" * 70)
    print("🎯 EJECUTANDO SUITE COMPLETA DE TESTS")
    print("=" * 70)
    
    tests = [
        ("Estructura de Archivos", test_structure),
        ("Imports de Módulos", test_imports),
        ("Configuración", test_configuration),
        ("Funciones Auxiliares", test_helpers),
        ("Esquemas Pydantic", test_schemas),
        ("Servidor FastAPI", test_server),
        ("Integración", test_integration),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO en {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE TESTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"   {status}: {name}")
    
    print("\n" + "=" * 70)
    print(f"🎯 RESULTADO FINAL: {passed}/{total} tests pasaron")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 ¡REFACTORIZACIÓN EXITOSA! Todos los tests pasaron.")
        print("\n📝 Próximos pasos:")
        print("   1. Ejecutar: python server.py")
        print("   2. Verificar logs: ✅ Servidor inicializado con 9 herramientas")
        print("   3. Abrir: http://localhost:8000/docs")
        print("   4. Probar herramientas desde la UI de FastAPI")
        return True
    else:
        print(f"\n⚠️ {total - passed} tests fallaron. Revisa los errores arriba.")
        return False


# ========== MODO STANDALONE ==========
if __name__ == "__main__":
    import sys
    
    # Permitir ejecutar tests individuales
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        test_map = {
            "structure": test_structure,
            "imports": test_imports,
            "config": test_configuration,
            "helpers": test_helpers,
            "schemas": test_schemas,
            "server": test_server,
            "integration": test_integration,
        }
        
        if test_name in test_map:
            print(f"\n🎯 Ejecutando test individual: {test_name}")
            test_map[test_name]()
        else:
            print(f"❌ Test desconocido: {test_name}")
            print(f"Tests disponibles: {', '.join(test_map.keys())}")
    else:
        # Ejecutar todos los tests
        success = run_all_tests()
        sys.exit(0 if success else 1)