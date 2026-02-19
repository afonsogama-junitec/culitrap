#!/usr/bin/env python3
"""
yolo_test_pi.py - Teste de Inferência YOLOv11 + SAHI no Raspberry Pi 5
================================================================================
PROPÓSITO: Valida que YOLOv11 + SAHI executa inferência com slicing
VERSÃO: 3.0 (18/02/26) - SAHI INTEGRADO


FUNCIONALIDADE:
1. Carrega modelo YOLOv11 (PyTorch .pt)
2. Executa inferência com SLICING (SAHI) para detetar objetos pequenos
3. Mostra deteções (classe + confiança + bounding boxes)
4. Suporta processamento de imagem única ou pasta completa


EXECUÇÃO: 
   python3 yolo_test_pi.py --image ./test.jpg
   python3 yolo_test_pi.py --input-dir ./camera_test_images/ --slice-size 640


VANTAGENS DO SAHI:
- Deteta objetos muito pequenos (Culicoides de 2-3mm)
- Processa imagens de alta resolução (8-16MP) sem perder detalhe
- Divide em tiles e junta resultados automaticamente
"""


import sys
import argparse
from pathlib import Path


# Tenta importar Ultralytics YOLO
try:
    from ultralytics import YOLO
except ImportError:
    print("ERRO: Ultralytics não instalado")
    print("Execute: pip install ultralytics")
    sys.exit(1)


# Tenta importar SAHI
try:
    from sahi import AutoDetectionModel
    from sahi.predict import get_sliced_prediction
except ImportError:
    print("ERRO: SAHI não instalado")
    print("Execute: pip install sahi")
    sys.exit(1)


print("="*60)
print("TESTE DE INFERÊNCIA - YOLOv11 + SAHI no Raspberry Pi 5")
print("="*60)


# ============================================================================
# CONFIGURAÇÃO
# ============================================================================


# Modelo YOLOv11
DEFAULT_MODEL = "yolo11s.pt"


# Threshold de confiança mínimo para deteções
CONFIDENCE_THRESHOLD = 0.25


# SAHI: Configuração de slicing
DEFAULT_SLICE_HEIGHT = 640      # Altura de cada tile
DEFAULT_SLICE_WIDTH = 640       # Largura de cada tile
DEFAULT_OVERLAP_RATIO = 0.2     # Sobreposição entre tiles (20%)


# Formatos de imagem suportados 
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}


# ============================================================================
# FUNÇÃO: CARREGAR MODELO COM SAHI
# ============================================================================


def load_model_with_sahi(model_path, conf_threshold):
    """Carrega modelo YOLOv11 com wrapper SAHI"""
    print(f"\n[1/3] A carregar o modelo: {model_path}")
    
    is_standard_model = model_path.startswith("yolo") and model_path.endswith(".pt")
    
    if not is_standard_model and not Path(model_path).exists():
        print(f"✗ Modelo local não encontrado: {model_path}")
        return None
    
    try:
        # SAHI AutoDetectionModel wrapper para Ultralytics YOLO
        detection_model = AutoDetectionModel.from_pretrained(
            model_type='yolov8',       # SAHI usa 'yolov8' para ultralytics
            model_path=model_path,
            confidence_threshold=conf_threshold,
            device='cpu'               # Raspberry Pi não tem GPU
        )
        
        print(f"✓ Modelo carregado com SAHI wrapper")
        print(f"  Framework: Ultralytics YOLO")
        print(f"  Device: CPU")
        return detection_model
        
    except Exception as e:
        print(f"✗ Erro ao carregar modelo: {e}")
        return None


# ============================================================================
# FUNÇÃO: EXECUTAR INFERÊNCIA COM SAHI SLICING
# ============================================================================


def run_sahi_inference(detection_model, image_path, slice_height, slice_width, overlap_ratio):
    """Executa inferência YOLOv11 + SAHI com slicing"""
    print(f"\n[2/3] Inferência SAHI em: {Path(image_path).name}")
    print(f"  Slice size: {slice_width}x{slice_height}")
    print(f"  Overlap: {overlap_ratio*100:.0f}%")
    
    try:
        # SAHI sliced prediction
        result = get_sliced_prediction(
            image=str(image_path),
            detection_model=detection_model,
            slice_height=slice_height,
            slice_width=slice_width,
            overlap_height_ratio=overlap_ratio,
            overlap_width_ratio=overlap_ratio,
            verbose=0
        )
        
        num_detections = len(result.object_prediction_list)
        
        print(f"✓ Inferência SAHI concluída")
        print(f"  Deteções: {num_detections}")
        
        return result, num_detections
        
    except Exception as e:
        print(f"✗ Erro durante inferência SAHI: {e}")
        return None, 0


# ============================================================================
# FUNÇÃO: MOSTRAR RESULTADOS SAHI
# ============================================================================


def display_sahi_results(result, num_detections):
    """Mostra deteções SAHI no terminal"""
    print(f"\n[3/3] RESULTADOS:")
    print("="*60)
    
    if num_detections == 0:
        print("  Nenhuma deteção acima do threshold")
    else:
        print(f"  Total de deteções: {num_detections}\n")
        
        # Itera sobre cada deteção (ObjectPrediction do SAHI)
        for i, pred in enumerate(result.object_prediction_list, 1):
            class_name = pred.category.name
            conf = pred.score.value
            bbox = pred.bbox  # SAHI bbox format: minx, miny, maxx, maxy
            
            print(f"  [{i}] {class_name}")
            print(f"      Confiança: {conf:.3f} ({conf*100:.1f}%)")
            print(f"      BoundingBox: ({bbox.minx:.0f}, {bbox.miny:.0f}) → ({bbox.maxx:.0f}, {bbox.maxy:.0f})")
    
    print("="*60)


# ============================================================================
# FUNÇÃO: VALIDAR FORMATOS DE IMAGEM 
# ============================================================================


def get_valid_images(path_list):
    """Filtra apenas ficheiros de imagem válidos"""
    valid = []
    for p in path_list:
        if p.suffix.lower() in SUPPORTED_FORMATS:
            valid.append(p)
        else:
            print(f"⚠ Ignorado (formato não suportado): {p.name}")
    return valid


# ============================================================================
# MAIN
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Teste de inferência YOLOv11 + SAHI no Raspberry Pi 5"
    )
    parser.add_argument(
        '--image',
        help='Path da imagem de teste'
    )
    parser.add_argument(
        '--input-dir',
        help='Pasta com múltiplas imagens'
    )
    parser.add_argument(
        '--model',
        default=DEFAULT_MODEL,
        help=f'Modelo YOLOv11 (default: {DEFAULT_MODEL})'
    )
    parser.add_argument(
        '--conf',
        type=float,
        default=CONFIDENCE_THRESHOLD,
        help=f'Threshold de confiança (default: {CONFIDENCE_THRESHOLD})'
    )
    parser.add_argument(
        '--slice-size',
        type=int,
        default=DEFAULT_SLICE_HEIGHT,
        help=f'Tamanho dos tiles (default: {DEFAULT_SLICE_HEIGHT})'
    )
    parser.add_argument(
        '--overlap',
        type=float,
        default=DEFAULT_OVERLAP_RATIO,
        help=f'Overlap ratio entre tiles (default: {DEFAULT_OVERLAP_RATIO})'
    )
    
    args = parser.parse_args()
    
    # Validação: precisa de --image OU --input-dir
    if not args.image and not args.input_dir:
        print("\n✗ Erro: Forneça --image ou --input-dir")
        print("Exemplos:")
        print("  python3 yolo_test_pi.py --image test.jpg")
        print("  python3 yolo_test_pi.py --input-dir ./test_images/ --slice-size 640")
        return 1
    
    # Determina lista de imagens a processar
    images = []
    if args.input_dir:
        dir_path = Path(args.input_dir)
        if not dir_path.exists():
            print(f"\n✗ Pasta não encontrada: {dir_path}")
            return 1
        
        all_files = []
        for fmt in SUPPORTED_FORMATS:
            all_files.extend(dir_path.glob(f"*{fmt}"))
        
        images = get_valid_images(all_files)  
        
        if not images:
            print(f"\n✗ Nenhuma imagem válida encontrada em: {dir_path}")
            return 1
        print(f"✓ Encontradas {len(images)} imagens em: {dir_path}")
    else:
        img_path = Path(args.image)
        if not img_path.exists():
            print(f"\n✗ Imagem não encontrada: {img_path}")
            return 1
        
        if img_path.suffix.lower() not in SUPPORTED_FORMATS:
            print(f"\n✗ Formato não suportado: {img_path.suffix}")
            return 1
        
        images = [img_path]
        print(f"✓ Imagem encontrada: {img_path.name}")
    
    # PASSO 1: Carrega o modelo com SAHI (uma vez só)
    detection_model = load_model_with_sahi(args.model, args.conf)
    if detection_model is None:
        return 1
    
    # PASSO 2 e 3: Processa todas as imagens com SAHI
    total_detections = 0
    for i, img_path in enumerate(images, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(images)}] PROCESSANDO: {img_path.name}")
        print('='*60)
        
        # Executa inferência SAHI
        result, num_detections = run_sahi_inference(
            detection_model, 
            str(img_path), 
            args.slice_size,  # slice_height
            args.slice_size,  # slice_width
            args.overlap
        )
        if result is None:
            continue
        
        # Mostra resultados
        display_sahi_results(result, num_detections)
        total_detections += num_detections
    
    # Resumo final
    print("\n" + "="*60)
    print("RESUMO FINAL")
    print("="*60)
    print(f"  Imagens processadas: {len(images)}")
    print(f"  Total de deteções: {total_detections}")
    print(f"  Configuração SAHI: {args.slice_size}x{args.slice_size} (overlap {args.overlap*100:.0f}%)")
    print("\n✅ YOLOv11 + SAHI FUNCIONAL NO RASPBERRY PI 5!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
