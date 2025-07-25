#!/usr/bin/env python3
"""
👑 MÓDULO ADMIN BACKEND
Sistema de administração completo para gerenciar o sistema multi-plataforma
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import jwt
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
import subprocess
import psutil
import os

# Imports do nosso sistema
from plataformas_api import GerenciadorPlataformas
from analisador_estrategias import AnalisadorEstrategias
from validador_configuracoes import ValidadorConfiguracoes

# Configurações
SECRET_KEY = "admin_backend_secret_key_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Usuários admin (em produção, usar banco de dados)
ADMIN_USERS = {
    "admin": {
        "username": "admin",
        "password": hashlib.sha256("admin123".encode()).hexdigest(),  # admin123
        "role": "super_admin",
        "created_at": "2025-01-25"
    },
    "manager": {
        "username": "manager", 
        "password": hashlib.sha256("manager123".encode()).hexdigest(),  # manager123
        "role": "manager",
        "created_at": "2025-01-25"
    }
}

app = FastAPI(
    title="🤖 Admin Backend - Sistema Multi-Plataforma",
    description="Painel de administração para gerenciar robôs e monitorar sistema",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

class AdminAuth:
    """Sistema de autenticação para administradores"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Cria token JWT"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str):
        """Verifica token JWT"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return username
        except jwt.PyJWTError:
            return None
    
    @staticmethod
    def authenticate_user(username: str, password: str):
        """Autentica usuário"""
        user = ADMIN_USERS.get(username)
        if not user:
            return False
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return user["password"] == password_hash
    
    @staticmethod
    def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Obtém usuário atual do token"""
        username = AdminAuth.verify_token(credentials.credentials)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = ADMIN_USERS.get(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado"
            )
        
        return user

class SystemMonitor:
    """Monitor do sistema"""
    
    @staticmethod
    def get_system_stats():
        """Obtém estatísticas do sistema"""
        try:
            # CPU e Memória
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Processos Python
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                try:
                    if 'python' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if any(script in cmdline for script in ['executor_bots.py', 'admin_backend.py', 'gerenciador_sistema.py']):
                            python_processes.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'script': cmdline.split()[-1] if cmdline else 'Unknown',
                                'cpu_percent': proc.info['cpu_percent'],
                                'memory_percent': proc.info['memory_percent']
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'python_processes': python_processes
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_log_files():
        """Lista arquivos de log"""
        logs = []
        log_patterns = ['*.log', '*.txt']
        
        for pattern in log_patterns:
            for log_file in Path('.').glob(pattern):
                if log_file.is_file():
                    stat = log_file.stat()
                    logs.append({
                        'name': log_file.name,
                        'path': str(log_file),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        return sorted(logs, key=lambda x: x['modified'], reverse=True)

class RobotManager:
    """Gerenciador de robôs"""
    
    @staticmethod
    def load_robots_config():
        """Carrega configuração dos robôs"""
        try:
            config_file = Path("robos_configurados.json")
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"robos": [], "configuracao_global": {}}
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def save_robots_config(config: Dict):
        """Salva configuração dos robôs"""
        try:
            config_file = Path("robos_configurados.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def get_robots_stats():
        """Obtém estatísticas dos robôs"""
        config = RobotManager.load_robots_config()
        if "error" in config:
            return config
        
        robos = config.get("robos", [])
        
        stats = {
            'total_robots': len(robos),
            'active_robots': len([r for r in robos if r.get('status') == 'ativo']),
            'inactive_robots': len([r for r in robos if r.get('status') != 'ativo']),
            'platforms': {},
            'total_strategies': 0
        }
        
        for robo in robos:
            # Contar por plataforma
            platform = robo.get('plataforma', {}).get('id', 'unknown')
            if platform not in stats['platforms']:
                stats['platforms'][platform] = 0
            stats['platforms'][platform] += 1
            
            # Contar estratégias
            stats['total_strategies'] += len(robo.get('estrategias', []))
        
        return stats

# ================================
# ROTAS DE AUTENTICAÇÃO
# ================================

@app.post("/api/auth/login")
async def login(credentials: Dict[str, str]):
    """Login de administrador"""
    username = credentials.get("username")
    password = credentials.get("password")
    
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username e password são obrigatórios"
        )
    
    if not AdminAuth.authenticate_user(username, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AdminAuth.create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    
    user_info = ADMIN_USERS[username].copy()
    del user_info["password"]  # Não retornar senha
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user_info
    }

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(AdminAuth.get_current_user)):
    """Informações do usuário atual"""
    return current_user

# ================================
# ROTAS DO DASHBOARD
# ================================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(AdminAuth.get_current_user)):
    """Estatísticas do dashboard"""
    
    # Estatísticas do sistema
    system_stats = SystemMonitor.get_system_stats()
    
    # Estatísticas dos robôs
    robot_stats = RobotManager.get_robots_stats()
    
    # Dados das plataformas
    try:
        dados_file = Path("dados_plataformas.json")
        platform_data = {}
        if dados_file.exists():
            with open(dados_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            platform_data = {
                'timestamp': data.get('timestamp'),
                'platforms': {}
            }
            
            for platform, results in data.get('plataformas', {}).items():
                platform_data['platforms'][platform] = {
                    'total_results': len(results),
                    'last_result': results[-1] if results else None
                }
    except Exception as e:
        platform_data = {'error': str(e)}
    
    # Logs recentes
    log_files = SystemMonitor.get_log_files()
    
    return {
        'timestamp': datetime.now().isoformat(),
        'system': system_stats,
        'robots': robot_stats,
        'platforms': platform_data,
        'logs': log_files[:5]  # Últimos 5 logs
    }

@app.get("/api/dashboard/realtime")
async def get_realtime_data(current_user: dict = Depends(AdminAuth.get_current_user)):
    """Dados em tempo real"""
    return {
        'timestamp': datetime.now().isoformat(),
        'system': SystemMonitor.get_system_stats(),
        'uptime': os.popen('wmic os get lastbootuptime').read() if os.name == 'nt' else None
    }

# ================================
# ROTAS DE GERENCIAMENTO DE ROBÔS
# ================================

@app.get("/api/robots")
async def get_robots(current_user: dict = Depends(AdminAuth.get_current_user)):
    """Lista todos os robôs"""
    config = RobotManager.load_robots_config()
    return config

@app.post("/api/robots/{robot_id}/toggle")
async def toggle_robot_status(robot_id: str, current_user: dict = Depends(AdminAuth.get_current_user)):
    """Ativa/desativa um robô"""
    config = RobotManager.load_robots_config()
    
    if "error" in config:
        raise HTTPException(status_code=500, detail=config["error"])
    
    robos = config.get("robos", [])
    robot = None
    
    for r in robos:
        if r.get("id") == robot_id:
            robot = r
            break
    
    if not robot:
        raise HTTPException(status_code=404, detail="Robô não encontrado")
    
    # Toggle status
    new_status = "ativo" if robot.get("status") != "ativo" else "inativo"
    robot["status"] = new_status
    robot["last_modified"] = datetime.now().isoformat()
    robot["modified_by"] = current_user["username"]
    
    # Salvar
    result = RobotManager.save_robots_config(config)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return {
        "success": True,
        "robot_id": robot_id,
        "new_status": new_status
    }

@app.delete("/api/robots/{robot_id}")
async def delete_robot(robot_id: str, current_user: dict = Depends(AdminAuth.get_current_user)):
    """Remove um robô"""
    if current_user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Apenas super_admin pode deletar robôs")
    
    config = RobotManager.load_robots_config()
    
    if "error" in config:
        raise HTTPException(status_code=500, detail=config["error"])
    
    robos = config.get("robos", [])
    robot_index = None
    
    for i, r in enumerate(robos):
        if r.get("id") == robot_id:
            robot_index = i
            break
    
    if robot_index is None:
        raise HTTPException(status_code=404, detail="Robô não encontrado")
    
    # Remover
    removed_robot = robos.pop(robot_index)
    
    # Salvar
    result = RobotManager.save_robots_config(config)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return {
        "success": True,
        "robot_id": robot_id,
        "removed_robot": removed_robot["nome"]
    }

# ================================
# ROTAS DE VALIDAÇÃO
# ================================

@app.post("/api/validation/robots")
async def validate_robots(current_user: dict = Depends(AdminAuth.get_current_user)):
    """Valida configurações de todos os robôs"""
    try:
        validador = ValidadorConfiguracoes()
        resultado = await validador.validar_arquivo_robos()
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/validation/robot/{robot_id}")
async def validate_single_robot(robot_id: str, current_user: dict = Depends(AdminAuth.get_current_user)):
    """Valida um robô específico"""
    try:
        config = RobotManager.load_robots_config()
        
        if "error" in config:
            raise HTTPException(status_code=500, detail=config["error"])
        
        robos = config.get("robos", [])
        robot = None
        
        for r in robos:
            if r.get("id") == robot_id:
                robot = r
                break
        
        if not robot:
            raise HTTPException(status_code=404, detail="Robô não encontrado")
        
        validador = ValidadorConfiguracoes()
        resultado = await validador.validar_robo_completo(robot)
        return resultado
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ROTAS DE SISTEMA
# ================================

@app.get("/api/system/status")
async def get_system_status(current_user: dict = Depends(AdminAuth.get_current_user)):
    """Status geral do sistema"""
    return {
        'timestamp': datetime.now().isoformat(),
        'system': SystemMonitor.get_system_stats(),
        'robots': RobotManager.get_robots_stats(),
        'files': {
            'config_exists': Path("robos_configurados.json").exists(),
            'data_exists': Path("dados_plataformas.json").exists(),
            'logs': len(SystemMonitor.get_log_files())
        }
    }

@app.post("/api/system/collect-data")
async def collect_platform_data(current_user: dict = Depends(AdminAuth.get_current_user)):
    """Força coleta de dados das plataformas"""
    try:
        # Executar coleta de dados
        process = await asyncio.create_subprocess_exec(
            'python', 'plataformas_api.py',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return {
                "success": True,
                "message": "Coleta de dados executada com sucesso",
                "output": stdout.decode()
            }
        else:
            return {
                "success": False,
                "message": "Erro na coleta de dados",
                "error": stderr.decode()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs/{log_file}")
async def get_log_content(log_file: str, lines: int = 100, current_user: dict = Depends(AdminAuth.get_current_user)):
    """Obtém conteúdo de um arquivo de log"""
    try:
        log_path = Path(log_file)
        
        if not log_path.exists():
            raise HTTPException(status_code=404, detail="Arquivo de log não encontrado")
        
        # Ler últimas N linhas
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            'file': log_file,
            'total_lines': len(all_lines),
            'showing_lines': len(recent_lines),
            'content': ''.join(recent_lines)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# INTERFACE WEB
# ================================

@app.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    """Página principal do admin"""
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>👑 Admin Backend - Sistema Multi-Plataforma</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh; 
                color: #333;
            }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { 
                background: rgba(255,255,255,0.95); 
                padding: 20px; 
                border-radius: 10px; 
                margin-bottom: 20px; 
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .card { 
                background: rgba(255,255,255,0.95); 
                padding: 20px; 
                border-radius: 10px; 
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .stat-box { 
                background: linear-gradient(45deg, #4CAF50, #45a049); 
                color: white; 
                padding: 20px; 
                border-radius: 8px; 
                text-align: center;
            }
            .stat-box.warning { background: linear-gradient(45deg, #ff9800, #f57c00); }
            .stat-box.danger { background: linear-gradient(45deg, #f44336, #d32f2f); }
            .btn { 
                background: #2196F3; 
                color: white; 
                padding: 10px 20px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                margin: 5px;
                transition: background 0.3s;
            }
            .btn:hover { background: #1976D2; }
            .btn.success { background: #4CAF50; }
            .btn.success:hover { background: #45a049; }
            .btn.danger { background: #f44336; }
            .btn.danger:hover { background: #d32f2f; }
            .status { padding: 5px 10px; border-radius: 15px; color: white; font-size: 12px; }
            .status.active { background: #4CAF50; }
            .status.inactive { background: #757575; }
            .loading { text-align: center; padding: 40px; }
            .hidden { display: none; }
            .log-content { 
                background: #1e1e1e; 
                color: #00ff00; 
                padding: 15px; 
                border-radius: 5px; 
                font-family: 'Courier New', monospace; 
                max-height: 400px; 
                overflow-y: auto; 
                white-space: pre-wrap;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>👑 Admin Backend - Sistema Multi-Plataforma</h1>
                <p>Painel de administração para gerenciar robôs e monitorar sistema</p>
                <div id="loginSection">
                    <h3>🔐 Login de Administrador</h3>
                    <input type="text" id="username" placeholder="Username" style="padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 5px;">
                    <input type="password" id="password" placeholder="Password" style="padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 5px;">
                    <button class="btn" onclick="login()">Entrar</button>
                    <div style="margin-top: 10px; font-size: 12px; color: #666;">
                        <strong>Usuários demo:</strong> admin/admin123 ou manager/manager123
                    </div>
                </div>
                <div id="userInfo" class="hidden">
                    <span id="welcomeMessage"></span>
                    <button class="btn danger" onclick="logout()">Sair</button>
                </div>
            </div>

            <div id="adminContent" class="hidden">
                <!-- Dashboard Stats -->
                <div class="card">
                    <h2>📊 Dashboard</h2>
                    <button class="btn" onclick="loadDashboard()">🔄 Atualizar</button>
                    <div id="dashboardContent" class="loading">Carregando...</div>
                </div>

                <!-- Robot Management -->
                <div class="card">
                    <h2>🤖 Gerenciamento de Robôs</h2>
                    <button class="btn" onclick="loadRobots()">🔄 Atualizar</button>
                    <button class="btn success" onclick="validateAllRobots()">🔐 Validar Todos</button>
                    <div id="robotsContent" class="loading">Carregando...</div>
                </div>

                <!-- System Status -->
                <div class="card">
                    <h2>🖥️ Status do Sistema</h2>
                    <button class="btn" onclick="loadSystemStatus()">🔄 Atualizar</button>
                    <button class="btn success" onclick="collectPlatformData()">📊 Coletar Dados</button>
                    <div id="systemContent" class="loading">Carregando...</div>
                </div>

                <!-- Logs -->
                <div class="card">
                    <h2>📝 Logs do Sistema</h2>
                    <button class="btn" onclick="loadLogs()">🔄 Atualizar</button>
                    <div id="logsContent" class="loading">Carregando...</div>
                </div>
            </div>
        </div>

        <script>
            let authToken = localStorage.getItem('adminToken');
            
            if (authToken) {
                checkAuth();
            }

            async function login() {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                
                if (!username || !password) {
                    alert('Por favor, preencha username e password');
                    return;
                }

                try {
                    const response = await fetch('/api/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });

                    if (response.ok) {
                        const data = await response.json();
                        authToken = data.access_token;
                        localStorage.setItem('adminToken', authToken);
                        showAdminInterface(data.user);
                    } else {
                        const error = await response.json();
                        alert('Erro: ' + error.detail);
                    }
                } catch (error) {
                    alert('Erro de conexão: ' + error.message);
                }
            }

            async function checkAuth() {
                try {
                    const response = await fetch('/api/auth/me', {
                        headers: { 'Authorization': `Bearer ${authToken}` }
                    });

                    if (response.ok) {
                        const user = await response.json();
                        showAdminInterface(user);
                    } else {
                        logout();
                    }
                } catch (error) {
                    logout();
                }
            }

            function showAdminInterface(user) {
                document.getElementById('loginSection').classList.add('hidden');
                document.getElementById('userInfo').classList.remove('hidden');
                document.getElementById('adminContent').classList.remove('hidden');
                document.getElementById('welcomeMessage').textContent = `Bem-vindo, ${user.username} (${user.role})`;
                
                // Carregar dados iniciais
                loadDashboard();
                loadRobots();
                loadSystemStatus();
            }

            function logout() {
                localStorage.removeItem('adminToken');
                authToken = null;
                document.getElementById('loginSection').classList.remove('hidden');
                document.getElementById('userInfo').classList.add('hidden');
                document.getElementById('adminContent').classList.add('hidden');
            }

            async function apiRequest(endpoint, options = {}) {
                const defaultOptions = {
                    headers: {
                        'Authorization': `Bearer ${authToken}`,
                        'Content-Type': 'application/json'
                    }
                };

                const response = await fetch(endpoint, { ...defaultOptions, ...options });
                
                if (response.status === 401) {
                    logout();
                    throw new Error('Não autorizado');
                }

                return response;
            }

            async function loadDashboard() {
                try {
                    const response = await apiRequest('/api/dashboard/stats');
                    const data = await response.json();
                    
                    let html = '<div class="grid">';
                    
                    // Robot stats
                    if (data.robots) {
                        html += `
                            <div class="stat-box">
                                <h3>🤖 Robôs</h3>
                                <div style="font-size: 24px; margin: 10px 0;">${data.robots.total_robots}</div>
                                <div>Ativos: ${data.robots.active_robots} | Inativos: ${data.robots.inactive_robots}</div>
                            </div>
                        `;
                    }
                    
                    // System stats
                    if (data.system) {
                        const memoryPercent = data.system.memory?.percent || 0;
                        const cpuPercent = data.system.cpu_percent || 0;
                        
                        html += `
                            <div class="stat-box ${memoryPercent > 80 ? 'danger' : memoryPercent > 60 ? 'warning' : ''}">
                                <h3>💾 Sistema</h3>
                                <div>CPU: ${cpuPercent.toFixed(1)}%</div>
                                <div>RAM: ${memoryPercent.toFixed(1)}%</div>
                            </div>
                        `;
                    }
                    
                    // Platform data
                    if (data.platforms?.platforms) {
                        const totalResults = Object.values(data.platforms.platforms).reduce((sum, p) => sum + p.total_results, 0);
                        html += `
                            <div class="stat-box">
                                <h3>🎰 Plataformas</h3>
                                <div style="font-size: 24px; margin: 10px 0;">${totalResults}</div>
                                <div>Resultados coletados</div>
                            </div>
                        `;
                    }
                    
                    html += '</div>';
                    document.getElementById('dashboardContent').innerHTML = html;
                    
                } catch (error) {
                    document.getElementById('dashboardContent').innerHTML = `<div style="color: red;">Erro: ${error.message}</div>`;
                }
            }

            async function loadRobots() {
                try {
                    const response = await apiRequest('/api/robots');
                    const data = await response.json();
                    
                    const robots = data.robos || [];
                    
                    let html = '<div class="grid">';
                    
                    robots.forEach(robot => {
                        const statusClass = robot.status === 'ativo' ? 'active' : 'inactive';
                        const statusText = robot.status === 'ativo' ? 'Ativo' : 'Inativo';
                        
                        html += `
                            <div class="card" style="margin: 0;">
                                <h4>${robot.nome}</h4>
                                <div><strong>Plataforma:</strong> ${robot.plataforma?.nome || 'N/A'}</div>
                                <div><strong>Estratégias:</strong> ${robot.estrategias?.length || 0}</div>
                                <div><strong>Status:</strong> <span class="status ${statusClass}">${statusText}</span></div>
                                <div style="margin-top: 10px;">
                                    <button class="btn" onclick="toggleRobotStatus('${robot.id}')">
                                        ${robot.status === 'ativo' ? 'Desativar' : 'Ativar'}
                                    </button>
                                    <button class="btn success" onclick="validateRobot('${robot.id}')">Validar</button>
                                </div>
                            </div>
                        `;
                    });
                    
                    html += '</div>';
                    document.getElementById('robotsContent').innerHTML = html;
                    
                } catch (error) {
                    document.getElementById('robotsContent').innerHTML = `<div style="color: red;">Erro: ${error.message}</div>`;
                }
            }

            async function toggleRobotStatus(robotId) {
                try {
                    const response = await apiRequest(`/api/robots/${robotId}/toggle`, { method: 'POST' });
                    const data = await response.json();
                    
                    if (data.success) {
                        alert(`Robô ${data.new_status}!`);
                        loadRobots(); // Recarregar lista
                    }
                } catch (error) {
                    alert('Erro: ' + error.message);
                }
            }

            async function validateRobot(robotId) {
                try {
                    const response = await apiRequest(`/api/validation/robot/${robotId}`, { method: 'POST' });
                    const data = await response.json();
                    
                    const status = data.valido ? '✅ Válido' : '❌ Inválido';
                    let message = `Robô: ${status}\\n`;
                    
                    if (data.erros && data.erros.length > 0) {
                        message += 'Erros:\\n' + data.erros.join('\\n');
                    }
                    
                    if (data.avisos && data.avisos.length > 0) {
                        message += '\\nAvisos:\\n' + data.avisos.join('\\n');
                    }
                    
                    alert(message);
                } catch (error) {
                    alert('Erro: ' + error.message);
                }
            }

            async function validateAllRobots() {
                try {
                    const response = await apiRequest('/api/validation/robots', { method: 'POST' });
                    const data = await response.json();
                    
                    const message = `Validação completa:
✅ Robôs válidos: ${data.robos_validos}
❌ Robôs com erro: ${data.robos_com_erro}
⚠️ Robôs com aviso: ${data.robos_com_aviso}`;
                    
                    alert(message);
                } catch (error) {
                    alert('Erro: ' + error.message);
                }
            }

            async function loadSystemStatus() {
                try {
                    const response = await apiRequest('/api/system/status');
                    const data = await response.json();
                    
                    let html = '<div class="grid">';
                    
                    // System info
                    if (data.system) {
                        html += `
                            <div>
                                <h4>💻 Sistema</h4>
                                <div>CPU: ${data.system.cpu_percent?.toFixed(1)}%</div>
                                <div>RAM: ${data.system.memory?.percent?.toFixed(1)}% (${(data.system.memory?.used / 1024 / 1024 / 1024).toFixed(1)}GB usado)</div>
                                <div>Processos Python: ${data.system.python_processes?.length || 0}</div>
                            </div>
                        `;
                    }
                    
                    // Files info
                    if (data.files) {
                        html += `
                            <div>
                                <h4>📁 Arquivos</h4>
                                <div>Config: ${data.files.config_exists ? '✅' : '❌'}</div>
                                <div>Dados: ${data.files.data_exists ? '✅' : '❌'}</div>
                                <div>Logs: ${data.files.logs} arquivos</div>
                            </div>
                        `;
                    }
                    
                    html += '</div>';
                    document.getElementById('systemContent').innerHTML = html;
                    
                } catch (error) {
                    document.getElementById('systemContent').innerHTML = `<div style="color: red;">Erro: ${error.message}</div>`;
                }
            }

            async function collectPlatformData() {
                try {
                    const response = await apiRequest('/api/system/collect-data', { method: 'POST' });
                    const data = await response.json();
                    
                    if (data.success) {
                        alert('✅ Coleta de dados executada com sucesso!');
                        loadDashboard(); // Atualizar dashboard
                    } else {
                        alert('❌ Erro na coleta: ' + data.error);
                    }
                } catch (error) {
                    alert('Erro: ' + error.message);
                }
            }

            async function loadLogs() {
                try {
                    // Primeiro, listar arquivos de log disponíveis
                    const response = await apiRequest('/api/dashboard/stats');
                    const data = await response.json();
                    
                    let html = '<div>';
                    
                    if (data.logs && data.logs.length > 0) {
                        html += '<h4>📝 Arquivos de Log:</h4>';
                        data.logs.forEach(log => {
                            html += `
                                <div style="margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 5px;">
                                    <strong>${log.name}</strong> (${(log.size / 1024).toFixed(1)}KB)
                                    <br><small>Modificado: ${new Date(log.modified).toLocaleString()}</small>
                                    <br><button class="btn" onclick="loadLogContent('${log.name}')">Ver Conteúdo</button>
                                </div>
                            `;
                        });
                    } else {
                        html += '<div>Nenhum arquivo de log encontrado.</div>';
                    }
                    
                    html += '</div>';
                    document.getElementById('logsContent').innerHTML = html;
                    
                } catch (error) {
                    document.getElementById('logsContent').innerHTML = `<div style="color: red;">Erro: ${error.message}</div>`;
                }
            }

            async function loadLogContent(logFile) {
                try {
                    const response = await apiRequest(`/api/logs/${logFile}?lines=50`);
                    const data = await response.json();
                    
                    const logWindow = window.open('', '_blank', 'width=800,height=600');
                    logWindow.document.write(`
                        <html>
                            <head><title>Log: ${logFile}</title></head>
                            <body style="font-family: monospace; background: #1e1e1e; color: #00ff00; padding: 20px;">
                                <h3 style="color: white;">📝 ${logFile}</h3>
                                <div>Mostrando ${data.showing_lines} de ${data.total_lines} linhas</div>
                                <hr>
                                <pre style="white-space: pre-wrap;">${data.content}</pre>
                            </body>
                        </html>
                    `);
                } catch (error) {
                    alert('Erro ao carregar log: ' + error.message);
                }
            }

            // Auto-refresh a cada 30 segundos
            setInterval(() => {
                if (authToken && !document.getElementById('adminContent').classList.contains('hidden')) {
                    loadDashboard();
                }
            }, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ================================
# STARTUP
# ================================

if __name__ == "__main__":
    print("👑 INICIANDO ADMIN BACKEND")
    print("=" * 40)
    print("🌐 Interface: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔐 Login demo: admin/admin123")
    print()
    
    uvicorn.run(
        "admin_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 