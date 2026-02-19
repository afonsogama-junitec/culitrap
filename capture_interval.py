#!/usr/bin/env python3
"""
capture_interval.py - Captura Intervalada para Monitorização CuliTrap
================================================================================
VERSÃO: 3.0 (19/02/26) - Universal: suporta 16MP, 64MP, Pi nativas
PROPÓSITO: Captura automática a intervalos regulares para armadilha de insetos


FUNCIONALIDADE:
- DETETA AUTOMATICAMENTE o sensor (16MP, 64MP, 12MP, etc.)
- Foco manual (essencial para evitar focar no background)
- Zoom digital (ROI) para ampliar insetos
- Intervalo configurável
- Guarda com timestamp em ./captured_images/cam{id}/


EXECUÇÃO: 
  python3 capture_interval.py                              # Auto (deteta sensor)
  python3 capture_interval.py --resolution 64mp            # Força 64MP
  python3 capture_interval.py --interval 600 --resolution 16mp  # 10min, 16MP
  
Pressione Ctrl+C para parar de forma limpa
"""


import sys
import time
import signal
import argparse
from pathlib import Path
from datetime import datetime


try:
    from picamera2 import Picamera2
    from libcamera import controls
except ImportError:
    print("ERRO: Picamera2 não instalado")
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


OUTPUT_BASE_DIR = Path("./captured_images")


# Controlo interno
running = True


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
    """Calcula ROI para zoom centralizado"""
    if zoom_factor <= 1.0:
        return None
    width = 1.0 / zoom_factor
    height = 1.0 / zoom_factor
    x = (1.0 - width) / 2.0
    y = (1.0 - height) / 2.0
    return (x, y, width, height)


# ============================================================================
# INICIALIZAR CÂMERA
# ============================================================================


camera = None
cam_dir = None


def init_camera(camera_id, resolution_key, use_manual_focus, lens_position, use_zoom, zoom_factor):
    """Inicializa a câmera com todas as configurações"""
    global camera, cam_dir
    print("\n[INIT] A inicializar câmera...")
    
    # Determina resolução a usar
    if resolution_key == 'auto':
        resolution, sensor_info = detect_camera_resolution(camera_id)
        print(f"  Auto-detetado: {sensor_info} → {resolution[0]}x{resolution[1]}")
    else:
        resolution = RESOLUTIONS[resolution_key]
        sensor_info = f"Manual ({resolution_key.upper()})"
        print(f"  Resolução forçada: {resolution[0]}x{resolution[1]}")
    
    # Cria pasta para a câmera
    cam_dir = OUTPUT_BASE_DIR / f"cam{camera_id}"
    cam_dir.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ Pasta criada: {cam_dir}")
    
    try:
        camera = Picamera2(camera_id)
        
        # Configuração (YUV420 para poupar RAM)
        config = camera.create_still_configuration(
            main={"size": resolution, "format": "YUV420"}
        )
        camera.configure(config)
        camera.start()
        
        print(f"  ✓ Câmera {camera_id} iniciada")
        
        # Aguarda estabilização
        print("  A aguardar estabilização (3s)...")
        time.sleep(3)
        
        # --- APLICAR FOCO MANUAL ---
        if use_manual_focus:
            camera.set_controls({
                "AfMode": controls.AfModeEnum.Manual,
                "LensPosition": lens_position
            })
            print(f"  ✓ Foco manual: {lens_position}")
            time.sleep(1)
        
        # --- APLICAR ZOOM ---
        if use_zoom:
            roi = calculate_roi(zoom_factor)
            if roi:
                camera.set_controls({"ScalerCrop": roi})
                print(f"  ✓ Zoom {zoom_factor}x: ROI = {roi}")
        
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
    """Para e fecha a câmera"""
    print("\n\n[CLEANUP] A parar a câmera...")
    if camera:
        try:
            camera.stop()
            camera.close()
            print("  ✓ Câmera parada")
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
    
    parser = argparse.ArgumentParser(
        description="Captura intervalada para CuliTrap (Universal 16MP/64MP)"
    )
    parser.add_argument('--camera', type=int, default=0, help='ID da câmera (default: 0)')
    parser.add_argument('--resolution', choices=list(RESOLUTIONS.keys()), default='auto',
                        help='Resolução: auto (deteta), 64mp, 16mp, 12mp, 4k, fhd (default: auto)')
    parser.add_argument('--interval', type=int, default=300,
                        help='Intervalo entre capturas em segundos (default: 300 = 5min)')
    parser.add_argument('--manual-focus', action='store_true', help='Ativar foco manual')
    parser.add_argument('--lens-position', type=float, default=7.5,
                        help='Posição da lente se foco manual (default: 7.5)')
    parser.add_argument('--zoom', type=float, default=1.0,
                        help='Fator de zoom digital (default: 1.0 = sem zoom)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("CAPTURA INTERVALADA - CuliTrap (UNIVERSAL)")
    print("="*60)
    print(f"Câmera ID: {args.camera}")
    print(f"Intervalo: {args.interval}s ({args.interval/60:.1f} minutos)")
    print(f"Resolução: {args.resolution}")
    print(f"Foco Manual: {'Ativado' if args.manual_focus else 'Desativado'}")
    if args.manual_focus:
        print(f"  Posição: {args.lens_position}")
    print(f"Zoom: {args.zoom}x")
    print("="*60)
    print("Pressione Ctrl+C para parar")
    print("="*60)
    
    # Inicializa
    if not init_camera(
        args.camera,
        args.resolution,
        args.manual_focus,
        args.lens_position,
        args.zoom > 1.0,
        args.zoom
    ):
        print("\n✗ Falha ao inicializar. A terminar...")
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
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()
    
    print(f"\n✓ Sessão terminada. Total de capturas: {capture_count}")
    print(f"✓ Imagens em: {cam_dir.absolute()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
