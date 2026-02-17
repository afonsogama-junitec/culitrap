#!/usr/bin/env python3
"""
setup_cameras.py - Script de Diagnóstico UNIVERSAL para as câmeras
================================================================================
PROPÓSITO: Diagnóstico rápido das câmeras antes de qualquer desenvolvimento
VERSÃO: 2.1 (17/02/26) - Corrigido para API moderna do Picamera2

FUNCIONALIDADE:
1. Verifica se as ferramentas 'rpicam-apps' (libcamera) estão instaladas.
2. Lista todas as câmeras detetadas pelo sistema.
3. Valida se a biblioteca Python (Picamera2) consegue aceder-lhes.

EXECUÇÃO: python3 setup_cameras.py
"""

import sys
import subprocess

print("="*60)
print("SETUP E VALIDAÇÃO DE CÂMERAS - Raspberry Pi 5 (UNIVERSAL)")
print("="*60)

# ============================================================================
# PASSO 1: Verificar se rpicam-apps está instalado
# ============================================================================

def check_libcamera():
    print("\n[1/3] A verificar instalação de ferramentas de câmera...")
    
    # Tenta encontrar rpicam-hello ou libcamera-hello 
    cmd = None
    if subprocess.run(['which', 'rpicam-hello'], capture_output=True).returncode == 0:
        cmd = 'rpicam-hello'
    elif subprocess.run(['which', 'libcamera-hello'], capture_output=True).returncode == 0:
        cmd = 'libcamera-hello'

    if cmd:
        print(f"✓ Ferramentas encontradas ({cmd})")
        return cmd
    else:
        print("✗ Ferramentas não encontradas")
        print("  Instale com: sudo apt install rpicam-apps")
        return None

# ============================================================================
# PASSO 2: Listar câmeras detetadas pelo sistema
# ============================================================================

def list_cameras(cmd_tool):
    if not cmd_tool: return 0
    print("\n[2/3] A listar câmeras detetadas...")
    
    try:
        result = subprocess.run(
            [cmd_tool, '--list-cameras'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        output = result.stdout + result.stderr
        
        if "Available cameras" in output or "seq" in output.lower():
            print("✓ Câmeras encontradas:\n")
            print(output)
            
            # Conta quantas câmeras aparecem na lista
            num_cameras = output.count("seq")
            if num_cameras == 0 and "Available cameras" in output:
                # Se não encontrou "seq", mas encontrou "Available cameras",
                # conta linhas com resolução (padrão alternativo)
                num_cameras = output.count("x") // 3  # Heurística básica
                if num_cameras == 0:
                    num_cameras = 1  # Assume pelo menos 1 se chegou aqui
            return num_cameras
        else:
            print("✗ Nenhuma câmera detetada pelo sistema.")
            print("  Verifique se o cabo está ligado corretamente (dentes para o lado certo).")
            return 0
            
    except Exception as e:
        print(f"✗ Erro ao listar câmeras: {e}")
        return 0

# ============================================================================
# PASSO 3: Verificar se Picamera2 (Python) funciona
# ============================================================================

def check_picamera2():
    print("\n[3/3] A verificar biblioteca Python (Picamera2)...")
    
    try:
        from picamera2 import Picamera2
        print("✓ Biblioteca Picamera2 instalada.")
        
        try:
            # Tenta inicializar a câmera 0 com a API moderna
            picam = Picamera2(0)
            
            # Cria uma configuração simples (preview) para testar
            config = picam.create_preview_configuration()
            picam.configure(config)
            
            # Se chegou aqui sem erro, a câmera está acessível
            picam.close()
            print(f"✓ Picamera2 consegue aceder à câmera 0.")
            return True
            
        except Exception as e:
            print(f"⚠ Picamera2 instalada, mas erro ao aceder à câmera: {e}")
            return False
            
    except ImportError:
        print("✗ Picamera2 não instalado")
        print("  Instale com: sudo apt install python3-picamera2")
        return False

# ============================================================================
# MAIN
# ============================================================================

def main():
    cmd_tool = check_libcamera()
    num_cameras = list_cameras(cmd_tool)
    py_ok = check_picamera2()
    
    print("\n" + "="*60)
    print("RESUMO DA VALIDAÇÃO")
    print("="*60)
    
    if num_cameras > 0 and py_ok:
        print(f"✓ SUCESSO: {num_cameras} câmera(s) detetada(s) e acessível(eis).")
        return 0
    else:
        print("✗ FALHA: Verifique as ligações e reinicie o Raspberry Pi.")
        return 1 

if __name__ == "__main__":
    sys.exit(main())
