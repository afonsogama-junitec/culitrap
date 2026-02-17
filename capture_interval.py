#!/usr/bin/env python3
"""
capture_interval.py - Captura Intervalada para Monitorização CuliTrap
================================================================================
VERSÃO: 2.0 (17/02/26) - Adaptado para câmara única com foco manual e zoom
PROPÓSITO: Captura automática a intervalos regulares para armadilha de insetos

FUNCIONALIDADE:
- Suporta 1 câmara (configurável)
- Foco manual (essencial para evitar focar no background)
- Zoom digital (ROI) para ampliar insetos
- Intervalo configurável (recomendado: 300-900s para armadilhas)
- Guarda com timestamp em ./captured_images/cam{id}/

EXECUÇÃO: python3 capture_interval.py
Pressione Ctrl+C para parar de forma limpa
"""

import sys
import time
import signal
from pathlib import Path
from datetime import datetime

try:
    from picamera2 import Picamera2
    from libcamera import controls
except ImportError:
    print("ERRO: Picamera2 não instalado")
    sys.exit(1)

# ============================================================================
# CONFIGURAÇÃO - EDITAR AQUI
# ============================================================================

# ID da câmara (normalmente 0 se só tiver uma)
CAMERA_ID = 0

OUTPUT_BASE_DIR = Path("./captured_images")

# --- INTERVALO ---
INTERVAL_SECONDS = 300  # 300s = 5 minutos (recomendado para armadilhas)
# Valores típicos: 300 (5min), 600 (10min), 900 (15min)

# --- RESOLUÇÃO ---
RESOLUTION = (4608, 2592)  # Full para Pi Camera V3 (12MP)
# Alternativa para testes rápidos: (1920, 1080)

# --- FOCO MANUAL ---
USE_MANUAL_FOCUS = True
LENS_POSITION = 7.5  # Ajustar conforme testado no capture_test.py
# Valores típicos: 0.0 = infinito, 10.0+ = macro

# --- ZOOM DIGITAL (ROI) ---
USE_ZOOM = False  # Mudar para True se quiser zoom
ZOOM_FACTOR = 4.0  # 2.0x, 4.0x, 8.0x

# Controlo interno
running = True

print("="*60)
print("CAPTURA INTERVALADA - CuliTrap")
print("="*60)
print(f"Câmara ID: {CAMERA_ID}")
print(f"Intervalo: {INTERVAL_SECONDS}s ({INTERVAL_SECONDS/60:.1f} minutos)")
print(f"Resolução: {RESOLUTION}")
print(f"Foco Manual: {'Ativado' if USE_MANUAL_FOCUS else 'Desativado'}")
if USE_MANUAL_FOCUS:
    print(f"  Posição: {LENS_POSITION}")
print(f"Zoom: {'Ativado' if USE_ZOOM else 'Desativado'}")
if USE_ZOOM:
    print(f"  Fator: {ZOOM_FACTOR}x")
print("="*60)
print("Pressione Ctrl+C para parar")
print("="*60)

# ============================================================================
# SETUP
# ============================================================================

# Cria pasta para a câmara
cam_dir = OUTPUT_BASE_DIR / f"cam{CAMERA_ID}"
cam_dir.mkdir(parents=True, exist_ok=True)
print(f"✓ Pasta criada: {cam_dir}")

# ============================================================================
# CALCULAR ROI PARA ZOOM
# ============================================================================

def calculate_roi(zoom_factor):
    """Calcula ROI para zoom centralizado"""
    if zoom_factor <= 1.0:
        return None
    width = 1.0 / zoom_factor
    height = 1.0 / zoom_factor
    x = (1.0 - width) / 2.0
    y = (1.0 - height) / 2.0
    return (x, y, width, height)

# ============================================================================
# INICIALIZAR CÂMARA
# ============================================================================

camera = None

def init_camera():
    """Inicializa a câmara com todas as configurações"""
    global camera
    print("\n[INIT] A inicializar câmara...")
    
    try:
        camera = Picamera2(CAMERA_ID)
        
        # Configuração
        config = camera.create_still_configuration(
            main={"size": RESOLUTION}
        )
        camera.configure(config)
        camera.start()
        
        print(f"  ✓ Câmara {CAMERA_ID} iniciada")
        
        # Aguarda estabilização
        print("  A aguardar estabilização (3s)...")
        time.sleep(3)
        
        # --- APLICAR FOCO MANUAL ---
        if USE_MANUAL_FOCUS:
            camera.set_controls({
                "AfMode": controls.AfModeEnum.Manual,
                "LensPosition": LENS_POSITION
            })
            print(f"  ✓ Foco manual: {LENS_POSITION}")
            time.sleep(1)
        
        # --- APLICAR ZOOM ---
        if USE_ZOOM:
            roi = calculate_roi(ZOOM_FACTOR)
            if roi:
                camera.set_controls({"ScalerCrop": roi})
                print(f"  ✓ Zoom {ZOOM_FACTOR}x: ROI = {roi}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Erro ao inicializar: {e}")
        return False

# ============================================================================
# CAPTURA
# ============================================================================

def capture_image():
    """Captura e guarda uma imagem"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = cam_dir / f"{timestamp}.jpg"
        
        camera.capture_file(str(filename))
        
        size_kb = filename.stat().st_size / 1024
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] ✓ {filename.name} ({size_kb:.1f} KB)")
        return True
        
    except Exception as e:
        print(f"  ✗ Erro ao capturar: {e}")
        return False

# ============================================================================
# CLEANUP
# ============================================================================

def cleanup():
    """Para e fecha a câmara"""
    print("\n\n[CLEANUP] A parar câmara...")
    if camera:
        try:
            camera.stop()
            camera.close()
            print("  ✓ Câmara parada")
        except:
            pass

def signal_handler(sig, frame):
    """Handler para Ctrl+C"""
    global running
    running = False

signal.signal(signal.SIGINT, signal_handler)

# ============================================================================
# MAIN LOOP
# ============================================================================

def main():
    global running
    
    # Inicializa
    if not init_camera():
        print("\n✗ Falha ao inicializar. A terminar.")
        return 1
    
    print(f"\n{'='*60}")
    print("CAPTURA ATIVA")
    print(f"{'='*60}\n")
    
    capture_count = 0
    
    try:
        while running:
            capture_count += 1
            print(f"[Captura #{capture_count}]")
            capture_image()
            
            # Aguarda próximo intervalo
            time.sleep(INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()
    
    print(f"\n✓ Sessão terminada. Total de capturas: {capture_count}")
    print(f"✓ Imagens em: {cam_dir.absolute()}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
