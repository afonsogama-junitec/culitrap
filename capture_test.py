#!/usr/bin/env python3
"""
capture_test.py - Teste de Captura Individual para Raspberry Pi Camera
================================================================================
PROPÓSITO: Captura 1 foto de teste para validar qualidade/foco/iluminação
VERSÃO: 2.0 (17/02/26) - Adaptado para câmera única com foco manual e zoom
COMPATIBILIDADE: Raspberry Pi Camera V3 (12MP), HQ, Arducam IMX519

FUNCIONALIDADE:
1. Testa uma câmera (configurável via CAMERA_ID)
2. Suporta foco manual (essencial para evitar focar no background)
3. Suporta zoom digital (ROI) para ampliar insetos
4. Aguarda estabilização auto-exposição/white balance
5. Guarda imagens com timestamp em ./camera_test_images/

EXECUÇÃO: python3 capture_test.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Tenta importar Picamera2 
try:
    from picamera2 import Picamera2
    from libcamera import controls
except ImportError:
    print("ERRO: Picamera2 não instalado")
    print("Execute: sudo apt install python3-picamera2")
    sys.exit(1)

# ============================================================================
# CONFIGURAÇÃO - EDITAR AQUI
# ============================================================================

# ID da câmera a testar (normalmente 0 se só tiver uma ligada)
CAMERA_ID = 0

# Resolução (para Raspberry Pi Camera V3 - 12MP)
RESOLUTION = (4608, 2592)  # Full HD para V3
# Alternativa rápida para testes: (1920, 1080)

# --- FOCO MANUAL ---
USE_MANUAL_FOCUS = True  # Desativar se quiser autofocus
LENS_POSITION = 7.5  # Valor de foco (ajustar conforme testado)
# Valores típicos: 0.0 = infinito, 10.0+ = macro/perto

# --- ZOOM DIGITAL (ROI) ---
USE_ZOOM = False  # Mudar para True se quiser zoom
ZOOM_FACTOR = 4.0  # 2.0x, 4.0x, 8.0x
# O zoom é calculado automaticamente com base no fator

# Pasta onde as imagens de teste vão ser guardadas
OUTPUT_DIR = Path("./camera_test_images")

print("="*60)
print("TESTE DE CAPTURA - Raspberry Pi Camera")
print("="*60)
print(f"Câmera ID: {CAMERA_ID}")
print(f"Resolução: {RESOLUTION}")
print(f"Foco Manual: {'Ativado' if USE_MANUAL_FOCUS else 'Desativado'}")
if USE_MANUAL_FOCUS:
    print(f"  Posição da Lente: {LENS_POSITION}")
print(f"Zoom: {'Ativado' if USE_ZOOM else 'Desativado'}")
if USE_ZOOM:
    print(f"  Fator de Zoom: {ZOOM_FACTOR}x")
print("="*60)

# ============================================================================
# CRIAR PASTA DE OUTPUT
# ============================================================================

OUTPUT_DIR.mkdir(exist_ok=True)
print(f"\n✓ Pasta de output: {OUTPUT_DIR.absolute()}")

# ============================================================================
# CALCULAR ROI PARA ZOOM
# ============================================================================

def calculate_roi(zoom_factor):
    """Calcula ROI (x, y, width, height) para zoom centralizado"""
    if zoom_factor <= 1.0:
        return None
    
    # ROI é fração do sensor (valores de 0.0 a 1.0)
    width = 1.0 / zoom_factor
    height = 1.0 / zoom_factor
    x = (1.0 - width) / 2.0
    y = (1.0 - height) / 2.0
    
    return (x, y, width, height)

# ============================================================================
# TESTAR CÂMERA
# ============================================================================

def test_camera():
    """Captura 1 foto de teste"""
    
    print(f"\n[CÂMERA {CAMERA_ID}] A inicializar...")
    
    try:
        # Cria objeto Picamera2
        picam = Picamera2(CAMERA_ID)
        
        # Obtém informação da câmera
        camera_info = picam.camera_properties
        print(f"  Modelo: {camera_info.get('Model', 'Desconhecido')}")
        
        # Configura para captura de alta qualidade
        config = picam.create_still_configuration(
            main={"size": RESOLUTION}
        )
        picam.configure(config)
        
        # Inicia câmera
        picam.start()
        print(f"  Câmera iniciada, a aguardar estabilização (2s)...")
        
        # Aguarda estabilização
        import time
        time.sleep(2)
        
        # --- APLICAR FOCO MANUAL ---
        if USE_MANUAL_FOCUS:
            picam.set_controls({
                "AfMode": controls.AfModeEnum.Manual,
                "LensPosition": LENS_POSITION
            })
            print(f"  ✓ Foco manual aplicado: {LENS_POSITION}")
            time.sleep(1)  # Aguarda lente mover
        
        # --- APLICAR ZOOM (se ativado) ---
        if USE_ZOOM:
            roi = calculate_roi(ZOOM_FACTOR)
            if roi:
                picam.set_controls({"ScalerCrop": roi})
                print(f"  ✓ Zoom {ZOOM_FACTOR}x aplicado: ROI = {roi}")
        
        # Nome do ficheiro com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        focus_label = f"focus{LENS_POSITION}" if USE_MANUAL_FOCUS else "autofocus"
        zoom_label = f"zoom{ZOOM_FACTOR}x" if USE_ZOOM else "nozoom"
        filename = OUTPUT_DIR / f"cam{CAMERA_ID}_test_{timestamp}_{focus_label}_{zoom_label}.jpg"
        
        # Captura imagem
        print(f"  A capturar para: {filename.name}")
        picam.capture_file(str(filename))
        
        # Para a câmera
        picam.stop()
        picam.close()
        
        # Verifica se ficheiro foi criado
        if filename.exists():
            size_mb = filename.stat().st_size / (1024*1024)
            print(f"  ✓ Sucesso! Tamanho: {size_mb:.2f} MB")
            return True
        else:
            print(f"  ✗ Erro: ficheiro não foi criado")
            return False
        
    except Exception as e:
        print(f"  ✗ ERRO: {e}")
        return False

# ============================================================================
# MAIN
# ============================================================================

def main():
    success = test_camera()
    
    print("\n" + "="*60)
    if success:
        print("✓ TESTE COMPLETO")
        print(f"Verifique a imagem em: {OUTPUT_DIR.absolute()}")
        return 0
    else:
        print("✗ TESTE FALHOU")
        return 1

if __name__ == "__main__":
    sys.exit(main())
