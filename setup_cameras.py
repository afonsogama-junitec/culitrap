#!/usr/bin/env python3
"""
setup_cameras.py - Script de Diagnóstico UNIVERSAL para as câmeras
================================================================================
PROPÓSITO: Diagnóstico rápido das câmeras antes de qualquer desenvolvimento
VERSÃO: 2.2 (19/02/26) - Deteta automaticamente 16MP, 64MP, Pi nativas


FUNCIONALIDADE:
1. Verifica se as ferramentas 'rpicam-apps' (libcamera) estão instaladas.
2. Lista todas as câmeras detetadas pelo sistema.
3. IDENTIFICA O SENSOR (imx519 16MP, ov64a40 64MP, imx708 Pi V3, etc.)
4. MOSTRA RESOLUÇÃO MÁXIMA de cada câmera.
5. Valida se a biblioteca Python (Picamera2) consegue aceder-lhes.


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
    if not cmd_tool: return 0, []
    print("\n[2/3] A listar câmeras detetadas...")
    
    # Mapeamento de sensores conhecidos para resoluções
    SENSOR_RESOLUTIONS = {
        'imx519': (4656, 3496, '16MP'),      # Arducam 16MP
        'ov64a40': (9248, 6944, '64MP'),    # Arducam 64MP Hawk-Eye
        'imx708': (4608, 2592, '12MP'),     # Pi Camera V3
        'imx477': (4056, 3040, '12MP'),     # Pi HQ Camera
        'ov5647': (2592, 1944, '5MP'),      # Pi Camera V1
        'imx219': (3280, 2464, '8MP'),      # Pi Camera V2
    }
    
    try:
        result = subprocess.run(
            [cmd_tool, '--list-cameras'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        output = result.stdout + result.stderr
        
        if "Available cameras" in output:
            print("✓ Câmeras encontradas:\n")
            
            # Processa output linha a linha para extrair info
            camera_info_list = []
            for line in output.split('\n'):
                # Formato típico: "0 : imx519 [4656x3496] (/base/...)"
                if ':' in line and any(sensor in line.lower() for sensor in SENSOR_RESOLUTIONS.keys()):
                    # Extrai sensor name
                    sensor = None
                    for s in SENSOR_RESOLUTIONS.keys():
                        if s in line.lower():
                            sensor = s
                            break
                    
                    if sensor:
                        width, height, label = SENSOR_RESOLUTIONS[sensor]
                        camera_info_list.append({
                            'sensor': sensor,
                            'resolution': f"{width}x{height}",
                            'label': label,
                            'line': line.strip()
                        })
            
            # Mostra output original
            print(output)
            
            # Mostra resumo formatado
            if camera_info_list:
                print("\n" + "="*60)
                print("RESUMO DE CÂMERAS DETETADAS")
                print("="*60)
                for i, cam in enumerate(camera_info_list):
                    print(f"CAM{i}: {cam['sensor'].upper()} ({cam['label']}) - Resolução: {cam['resolution']}")
                print("="*60)
            
            return len(camera_info_list), camera_info_list
        else:
            print("✗ Nenhuma câmera detetada pelo sistema.")
            print("  Verifique se o cabo está ligado corretamente (dentes para o lado certo).")
            return 0, []
            
    except Exception as e:
        print(f"✗ Erro ao listar câmeras: {e}")
        return 0, []


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
    num_cameras, camera_info = list_cameras(cmd_tool)
    py_ok = check_picamera2()
    
    print("\n" + "="*60)
    print("RESUMO DA VALIDAÇÃO")
    print("="*60)
    
    if num_cameras > 0 and py_ok:
        print(f"✓ SUCESSO: {num_cameras} câmera(s) detetada(s) e acessível(eis).")
        
        # Mostra sugestão de uso
        if camera_info:
            print("\n📋 Próximo passo:")
            for i, cam in enumerate(camera_info):
                if cam['label'] == '64MP':
                    print(f"  python3 capture_test.py --camera {i} --resolution 64mp")
                elif cam['label'] == '16MP':
                    print(f"  python3 capture_test.py --camera {i} --resolution 16mp")
                else:
                    print(f"  python3 capture_test.py --camera {i} --resolution auto")
        
        return 0
    else:
        print("✗ FALHA: Verifique as ligações e reinicie o Raspberry Pi.")
        return 1 


if __name__ == "__main__":
    sys.exit(main())
