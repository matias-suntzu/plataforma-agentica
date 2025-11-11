"""
Caching System - Día 3
Sistema de caché para optimizar costos y latencia

FUNCIONALIDADES:
1. Cache de respuestas de herramientas
2. Cache de resultados del LLM
3. Invalidación inteligente
4. Estadísticas de hit/miss rate
"""

import json
import hashlib
import pickle
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class CacheEntry:
    """Entrada de caché."""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_expired(self) -> bool:
        """Verifica si la entrada ha expirado."""
        return datetime.now() > self.expires_at
    
    def increment_hit(self):
        """Incrementa el contador de hits."""
        self.hit_count += 1


class CacheManager:
    """
    Manager de caché con soporte para TTL y persistencia.
    """
    
    def __init__(
        self,
        cache_dir: str = "cache",
        default_ttl: int = 3600,  # 1 hora
        max_size: int = 1000
    ):
        """
        Args:
            cache_dir: Directorio para persistir la caché
            default_ttl: Tiempo de vida por defecto (segundos)
            max_size: Máximo número de entradas en caché
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.default_ttl = default_ttl
        self.max_size = max_size
        
        # Cache en memoria
        self.cache: Dict[str, CacheEntry] = {}
        
        # Estadísticas
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
        
        # Cargar caché persistente
        self._load_from_disk()
    
    def _generate_key(self, namespace: str, identifier: Any) -> str:
        """
        Genera una clave única para el cache.
        
        Args:
            namespace: Namespace del cache (ej: "tool", "llm", "query")
            identifier: Identificador único (puede ser dict, str, etc.)
        
        Returns:
            String hash único
        """
        
        if isinstance(identifier, dict):
            # Serializar dict de forma determinista
            identifier_str = json.dumps(identifier, sort_keys=True)
        else:
            identifier_str = str(identifier)
        
        # Generar hash
        hash_obj = hashlib.sha256(f"{namespace}:{identifier_str}".encode())
        return hash_obj.hexdigest()
    
    def get(self, namespace: str, identifier: Any) -> Optional[Any]:
        """
        Obtiene un valor del caché.
        
        Args:
            namespace: Namespace
            identifier: Identificador
            
        Returns:
            Valor cacheado o None si no existe/expiró
        """
        
        key = self._generate_key(namespace, identifier)
        
        if key not in self.cache:
            self.stats["misses"] += 1
            return None
        
        entry = self.cache[key]
        
        # Verificar expiración
        if entry.is_expired():
            del self.cache[key]
            self.stats["misses"] += 1
            return None
        
        # Hit exitoso
        entry.increment_hit()
        self.stats["hits"] += 1
        
        return entry.value
    
    def set(
        self,
        namespace: str,
        identifier: Any,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Guarda un valor en el caché.
        
        Args:
            namespace: Namespace
            identifier: Identificador
            value: Valor a cachear
            ttl: Tiempo de vida en segundos (usa default si None)
            metadata: Metadata adicional
        """
        
        key = self._generate_key(namespace, identifier)
        
        if ttl is None:
            ttl = self.default_ttl
        
        now = datetime.now()
        expires_at = now + timedelta(seconds=ttl)
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        # Eviction si excede max_size
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        self.cache[key] = entry
    
    def invalidate(self, namespace: str, identifier: Any):
        """Invalida una entrada específica."""
        
        key = self._generate_key(namespace, identifier)
        
        if key in self.cache:
            del self.cache[key]
    
    def invalidate_namespace(self, namespace: str):
        """Invalida todas las entradas de un namespace."""
        
        keys_to_delete = [
            key for key, entry in self.cache.items()
            if entry.key.startswith(namespace)
        ]
        
        for key in keys_to_delete:
            del self.cache[key]
    
    def clear(self):
        """Limpia todo el caché."""
        self.cache.clear()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def _evict_oldest(self):
        """Elimina la entrada más antigua."""
        
        if not self.cache:
            return
        
        # Encontrar la más antigua
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].created_at)
        
        del self.cache[oldest_key]
        self.stats["evictions"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del caché."""
        
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_entries": len(self.cache),
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests
        }
    
    def print_stats(self):
        """Imprime estadísticas del caché."""
        
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("📊 ESTADÍSTICAS DE CACHÉ")
        print("="*60)
        print(f"Total entradas: {stats['total_entries']}/{self.max_size}")
        print(f"Hits: {stats['hits']}")
        print(f"Misses: {stats['misses']}")
        print(f"Hit Rate: {stats['hit_rate']}%")
        print(f"Evictions: {stats['evictions']}")
        print("="*60)
    
    def _load_from_disk(self):
        """Carga caché persistente desde disco."""
        
        cache_file = self.cache_dir / "cache.pkl"
        
        if not cache_file.exists():
            return
        
        try:
            with open(cache_file, "rb") as f:
                self.cache = pickle.load(f)
            
            # Limpiar entradas expiradas
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            print(f"✅ Caché cargada: {len(self.cache)} entradas")
        
        except Exception as e:
            print(f"⚠️  Error al cargar caché: {e}")
    
    def save_to_disk(self):
        """Guarda caché en disco."""
        
        cache_file = self.cache_dir / "cache.pkl"
        
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(self.cache, f)
            
            print(f"✅ Caché guardada: {len(self.cache)} entradas")
        
        except Exception as e:
            print(f"❌ Error al guardar caché: {e}")


class QueryCache:
    """
    Caché específico para queries del usuario.
    """
    
    def __init__(self, cache_manager: CacheManager, ttl: int = 1800):
        self.cache_manager = cache_manager
        self.ttl = ttl
        self.namespace = "query"
    
    def get_cached_response(self, query: str) -> Optional[str]:
        """Obtiene respuesta cacheada para una query."""
        
        # Normalizar query (lowercase, strip)
        normalized_query = query.lower().strip()
        
        return self.cache_manager.get(self.namespace, normalized_query)
    
    def cache_response(self, query: str, response: str):
        """Cachea una respuesta para una query."""
        
        normalized_query = query.lower().strip()
        
        self.cache_manager.set(
            self.namespace,
            normalized_query,
            response,
            ttl=self.ttl,
            metadata={"original_query": query}
        )


class ToolCache:
    """
    Caché específico para resultados de herramientas.
    """
    
    def __init__(self, cache_manager: CacheManager, ttl: int = 3600):
        self.cache_manager = cache_manager
        self.ttl = ttl
        self.namespace = "tool"
    
    def get_cached_result(self, tool_name: str, tool_args: dict) -> Optional[Any]:
        """Obtiene resultado cacheado de una herramienta."""
        
        identifier = {"tool": tool_name, "args": tool_args}
        
        return self.cache_manager.get(self.namespace, identifier)
    
    def cache_result(self, tool_name: str, tool_args: dict, result: Any):
        """Cachea el resultado de una herramienta."""
        
        identifier = {"tool": tool_name, "args": tool_args}
        
        self.cache_manager.set(
            self.namespace,
            identifier,
            result,
            ttl=self.ttl,
            metadata={"tool": tool_name}
        )
    
    def invalidate_tool(self, tool_name: str):
        """Invalida todas las entradas de una herramienta específica."""
        
        # Esto requiere iterar sobre todas las claves
        # En producción, usar un índice por tool_name
        keys_to_delete = []
        
        for key, entry in self.cache_manager.cache.items():
            if entry.metadata.get("tool") == tool_name:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.cache_manager.cache[key]


# Tests
if __name__ == "__main__":
    print("🧪 Testing Caching System...\n")
    
    cache_manager = CacheManager(cache_dir="test_cache", default_ttl=60)
    query_cache = QueryCache(cache_manager, ttl=30)
    tool_cache = ToolCache(cache_manager, ttl=60)
    
    # Test 1: Query Cache
    print("TEST 1: Query Cache")
    query = "lista todas las campañas"
    
    # Miss inicial
    result = query_cache.get_cached_response(query)
    print(f"Primera consulta: {'HIT' if result else 'MISS'}")
    
    # Cachear respuesta
    query_cache.cache_response(query, "Respuesta cacheada de prueba")
    
    # Hit en segunda consulta
    result = query_cache.get_cached_response(query)
    print(f"Segunda consulta: {'HIT' if result else 'MISS'}")
    print(f"Valor: {result}\n")
    
    # Test 2: Tool Cache
    print("TEST 2: Tool Cache")
    tool_args = {"campana_id": "123", "limite": 3}
    
    # Miss inicial
    result = tool_cache.get_cached_result("ObtenerAnunciosRendimiento", tool_args)
    print(f"Primera llamada: {'HIT' if result else 'MISS'}")
    
    # Cachear resultado
    tool_cache.cache_result("ObtenerAnunciosRendimiento", tool_args, {"data": [1, 2, 3]})
    
    # Hit en segunda llamada
    result = tool_cache.get_cached_result("ObtenerAnunciosRendimiento", tool_args)
    print(f"Segunda llamada: {'HIT' if result else 'MISS'}")
    print(f"Valor: {result}\n")
    
    # Test 3: Estadísticas
    cache_manager.print_stats()
    
    # Test 4: Persistencia
    print("\nTEST 4: Persistencia")
    cache_manager.save_to_disk()
    print("✅ Caché guardada en disco")