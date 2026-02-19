#!/usr/bin/env python3
"""
capture_test.py - Teste de Captura Individual para Raspberry Pi Camera
================================================================================
PROPÓSITO: Captura 1 foto de teste para validar qualidade/foco/iluminação
VERSÃO: 3.0 (19/02/26) - Universal: suporta 16MP, 64MP, Pi nativas
COMPATIBILIDADE: Arducam 16MP (IMX519), 64MP (OV64A40), Pi Camera V3 (12MP)


FUNCIONALIDADE:
1. DETETA AUTOMATICAMENTE o sensor (16MP, 64MP, 12MP, etc.)
2. Suporta foco manual (essencial para evitar focar no background)
3. Suporta zoom digital (ROI) para ampliar insetos
4. Aguarda estabilização auto-exposição/white balance
5. Guarda imagens com timestamp em ./camera_test_images/


EXECUÇÃO: 
  python3 capture_test.py                           # Auto (deteta sensor)
  python3 capture_test.py --resolution 64mp         # Força 64MP
  python3 capture_test.py --resolution 16mp         # Força 16MP
  python3 capture_test.py --camera 1 --resolution auto  # Câmera 1, auto-deteta
"""


import sys
import os
import argparse
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
# CONFIGURAÇÃO - RESOLUÇÕES PREDEFINIDAS
# ============================================================================


RESOLUTIONS = {
    'auto': None,  # Deteta automaticamente
    '64mp': (9248, 6944),   # Arducam 64MP full
    '16mp': (4656, 3496),   # Arducam 16MP full
    '12mp': (4608, 2592),   # Pi Camera V3
    '8mp':  (3280, 2464),   # Pi Camera V2
    '4k':   (3840, 2160),   # 4K UHD
    'fhd':  (1920, 1080),   # Full HD
}


# Pasta onde as imagens de teste vão ser guardadas
OUTPUT_DIR = Path("./camera_test_images")


# ============================================================================
# DETETA SENSOR E RESOLUÇÃO MÁXIMA
# ============================================================================


def detect_camera_resolution(camera_id):
    """Deteta o sensor e retorna a melhor resolução"""
    try:
        picam = Picamera2(camera_id)
        camera_props = picam.camera_properties
        picam.close()
        
        model = camera_props.get('Model', '').lower()
        
        # Mapeamento sensor -> resolução
        if 'ov64a40' in model or '64mp' in model:
            return (9248, 6944), '64MP (OV64A40)'
        elif 'imx519' in model or '16mp' in model:
            return (4656, 3496), '16MP (IMX519)'
        elif 'imx708' in model:
            return (4608, 2592), '12MP (IMX708 - Pi V3)'
        elif 'imx477' in model:
            return (4056, 3040), '12MP (IMX477 - Pi HQ)'
        elif 'imx219' in model:
            return (3280, 2464), '8MP (IMX219 - Pi V2)'
        else:
            # Fallback: resolução padrão
            return (4608, 2592), f'Desconhecido ({model})'
            
    except Exception as e:
        print(f"⚠ Erro ao detetar sensor: {e}")
        return (1920, 1080), 'Fallback (1080p)'


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


def test_camera(camera_id, resolution_key, use_manual_focus, lens_position, use_zoom, zoom_factor):
    """Captura 1 foto de teste"""
    
    print(f"\n[CÂMERA {camera_id}] A inicializar...")
    
    # Determina resolução a usar
    if resolution_key == 'auto':
        resolution, sensor_info = detect_camera_resolution(camera_id)
        print(f"  Auto-detetado: {sensor_info} → {resolution[0]}x{resolution[1]}")
    else:
        resolution = RESOLUTIONS[resolution_key]
        sensor_info = f"Manual ({resolution_key.upper()})"
        print(f"  Resolução forçada: {resolution[0]}x{resolution[1]}")
    
    try:
        # Cria objeto Picamera2
        picam = Picamera2(camera_id)
        
        # Obtém informação da câmera
        camera_info = picam.camera_properties
        print(f"  Modelo: {camera_info.get('Model', 'Desconhecido')}")
        
        # Configura para captura de alta qualidade
        # YUV420 usa menos RAM que RGB (importante para 64MP)
        config = picam.create_still_configuration(
            main={"size": resolution, "format": "YUV420"}
        )
        picam.configure(config)
        
        # Inicia câmera
        picam.start()
        print(f"  Câmera iniciada, a aguardar estabilização (2s)...")
        
        # Aguarda estabilização
        import time
        time.sleep(2)
        
        # --- APLICAR FOCO MANUAL ---
        if use_manual_focus:
            picam.set_controls({
                "AfMode": controls.AfModeEnum.Manual,
                "LensPosition": lens_position
            })
            print(f"  ✓ Foco manual aplicado: {lens_position}")
            time.sleep(1)  # Aguarda lente mover
        
        # --- APLICAR ZOOM (se ativado) ---
        if use_zoom:
            roi = calculate_roi(zoom_factor)
            if roi:
                picam.set_controls({"ScalerCrop": roi})
                print(f"  ✓ Zoom {zoom_factor}x aplicado: ROI = {roi}")
        
        # Nome do ficheiro com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        focus_label = f"focus{lens_position}" if use_manual_focus else "autofocus"
        zoom_label = f"zoom{zoom_factor}x" if use_zoom else "nozoom"
        res_label = resolution_key if resolution_key != 'auto' else sensor_info.split()[0].lower()
        filename = OUTPUT_DIR / f"cam{camera_id}_test_{timestamp}_{res_label}_{focus_label}_{zoom_label}.jpg"
        
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
    parser = argparse.ArgumentParser(
        description="Teste de captura para Raspberry Pi Camera (Universal 16MP/64MP)"
    )
    parser.add_argument('--camera', type=int, default=0, help='ID da câmera (default: 0)')
    parser.add_argument('--resolution', choices=list(RESOLUTIONS.keys()), default='auto',
                        help='Resolução: auto (deteta), 64mp, 16mp, 12mp, 4k, fhd (default: auto)')
    parser.add_argument('--manual-focus', action='store_true', help='Ativar foco manual')
    parser.add_argument('--lens-position', type=float, default=7.5,
                        help='Posição da lente se foco manual (0.0=infinito, 10.0+=macro, default: 7.5)')
    parser.add_argument('--zoom', type=float, default=1.0,
                        help='Fator de zoom digital (1.0=sem zoom, 2.0=2x, 4.0=4x, default: 1.0)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("TESTE DE CAPTURA - Raspberry Pi Camera (UNIVERSAL)")
    print("="*60)
    print(f"Câmera ID: {args.camera}")
    print(f"Resolução: {args.resolution}")
    print(f"Foco Manual: {'Ativado' if args.manual_focus else 'Desativado'}")
    if args.manual_focus:
        print(f"  Posição da Lente: {args.lens_position}")
    print(f"Zoom: {args.zoom}x")
    print("="*60)
    
    # Criar pasta de output
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"\n✓ Pasta de output: {OUTPUT_DIR.absolute()}")
    
    # Testar
    success = test_camera(
        args.camera,
        args.resolution,
        args.manual_focus,
        args.lens_position,
        args.zoom > 1.0,
        args.zoom
    )
    
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
