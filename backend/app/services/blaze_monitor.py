"""
Blaze Monitor - Sistema que monitora a API da Blaze em tempo real
Baseado no ScriptSolo.py original, mas assíncrono e escalável
"""

import asyncio
import aiohttp
import requests
from typing import List, Optional, Callable, Dict, Any
import structlog
from datetime import datetime
import json

from app.core.config import settings

logger = structlog.get_logger(__name__)

class BlazeMonitor:
    """Monitor principal para a API da Blaze"""
    
    def __init__(self):
        self.api_url = settings.BLAZE_API_URL
        self.last_results = []
        self.last_fetch_time = None
        self.is_running = False
        self.fetch_count = 0
        
    async def fetch_latest_results(self) -> Optional[List[int]]:
        """
        Busca os últimos resultados da API da Blaze
        
        Returns:
            Lista de números (mais recente primeiro) ou None em caso de erro
        """
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(self.api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = [item['roll'] for item in data]
                        
                        self.fetch_count += 1
                        self.last_fetch_time = datetime.now()
                        
                        logger.debug(
                            "Resultados da Blaze obtidos",
                            results_count=len(results),
                            results=results[:5],  # Apenas os 5 primeiros
                            fetch_count=self.fetch_count
                        )
                        
                        return results
                    else:
                        logger.error(
                            "Erro na API da Blaze",
                            status_code=response.status,
                            url=self.api_url
                        )
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("Timeout ao buscar dados da Blaze")
            return None
        except aiohttp.ClientError as e:
            logger.error("Erro de conexão com a Blaze", error=str(e))
            return None
        except Exception as e:
            logger.error("Erro inesperado ao buscar dados da Blaze", error=str(e))
            return None
    
    def fetch_latest_results_sync(self) -> Optional[List[int]]:
        """
        Versão síncrona para buscar resultados (para uso em workers Celery)
        
        Returns:
            Lista de números ou None em caso de erro
        """
        try:
            response = requests.get(self.api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = [item['roll'] for item in data]
                
                self.fetch_count += 1
                self.last_fetch_time = datetime.now()
                
                logger.debug(
                    "Resultados da Blaze obtidos (sync)",
                    results_count=len(results),
                    results=results[:5],
                    fetch_count=self.fetch_count
                )
                
                return results
            else:
                logger.error(
                    "Erro na API da Blaze (sync)",
                    status_code=response.status_code,
                    url=self.api_url
                )
                return None
                
        except requests.Timeout:
            logger.error("Timeout ao buscar dados da Blaze (sync)")
            return None
        except requests.RequestException as e:
            logger.error("Erro de conexão com a Blaze (sync)", error=str(e))
            return None
        except Exception as e:
            logger.error("Erro inesperado ao buscar dados da Blaze (sync)", error=str(e))
            return None
    
    async def monitor_continuous(self, 
                               callback: Callable[[List[int]], None],
                               interval: float = 1.0,
                               max_errors: int = 10) -> None:
        """
        Monitor contínuo da API da Blaze com callback para novos resultados
        
        Args:
            callback: Função chamada quando há novos resultados
            interval: Intervalo entre checks em segundos
            max_errors: Máximo de erros consecutivos antes de parar
        """
        self.is_running = True
        consecutive_errors = 0
        
        logger.info(
            "Iniciando monitor contínuo da Blaze",
            interval=interval,
            max_errors=max_errors
        )
        
        while self.is_running:
            try:
                results = await self.fetch_latest_results()
                
                if results is not None:
                    # Reset contador de erros em caso de sucesso
                    consecutive_errors = 0
                    
                    # Verificar se há mudanças
                    if results != self.last_results:
                        logger.info(
                            "Novos resultados detectados",
                            new_result=results[0] if results else None,
                            results_changed=len([r for r in results if r not in self.last_results])
                        )
                        
                        # Chamar callback com novos resultados
                        await callback(results)
                        self.last_results = results.copy()
                else:
                    consecutive_errors += 1
                    logger.warning(
                        "Erro ao buscar resultados",
                        consecutive_errors=consecutive_errors,
                        max_errors=max_errors
                    )
                    
                    # Parar se exceder máximo de erros
                    if consecutive_errors >= max_errors:
                        logger.error("Máximo de erros consecutivos atingido. Parando monitor.")
                        break
                
                # Aguardar próximo ciclo
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info("Monitor cancelado")
                break
            except Exception as e:
                consecutive_errors += 1
                logger.error(
                    "Erro inesperado no monitor",
                    error=str(e),
                    consecutive_errors=consecutive_errors
                )
                
                if consecutive_errors >= max_errors:
                    logger.error("Máximo de erros atingido. Parando monitor.")
                    break
                
                # Aguardar antes de tentar novamente
                await asyncio.sleep(interval * 2)
        
        self.is_running = False
        logger.info("Monitor da Blaze parado")
    
    def stop_monitoring(self):
        """Para o monitor contínuo"""
        self.is_running = False
        logger.info("Parando monitor da Blaze...")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna status atual do monitor
        
        Returns:
            Dict com informações de status
        """
        return {
            "is_running": self.is_running,
            "last_fetch_time": self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            "fetch_count": self.fetch_count,
            "last_results_count": len(self.last_results),
            "last_result": self.last_results[0] if self.last_results else None,
            "api_url": self.api_url
        }
    
    def validate_results(self, results: List[int]) -> bool:
        """
        Valida se os resultados da Blaze estão no formato esperado
        
        Args:
            results: Lista de resultados
            
        Returns:
            True se válidos
        """
        if not results or not isinstance(results, list):
            return False
        
        # Verificar se todos são números válidos (0-14)
        for result in results:
            if not isinstance(result, int) or result < 0 or result > 14:
                logger.warning("Resultado inválido detectado", result=result)
                return False
        
        return True

# Singleton instance para uso global
_blaze_monitor_instance = None

def get_blaze_monitor() -> BlazeMonitor:
    """Factory function para obter instância singleton do monitor"""
    global _blaze_monitor_instance
    if _blaze_monitor_instance is None:
        _blaze_monitor_instance = BlazeMonitor()
    return _blaze_monitor_instance 