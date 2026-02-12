#!/usr/bin/env python3
"""
yolo_test_pi.py - Teste de Inferência YOLOv26 no Raspberry Pi 5
================================================================================
PROPÓSITO: Valida que YOLOv26 carrega e executa inferência no Raspberry Pi
VERSÃO: 2.0 (12/02/26)

FUNCIONALIDADE:
1. Carrega modelo YOLOv26 (PyTorch .pt ou OpenVINO)
2. Executa inferência numa(s) imagem(ns) de teste
3. Mostra deteções (classe + confiança + bounding boxes )
4. Suporta processamento de imagem única ou uma pasta completa

EXECUÇÃO: 
   python3 yolo_test_pi.py --image ./test.jpg
   python3 yolo_test_pi.py --input-dir ./camera_test_images/

NOTA: O YOLO faz resize automático da imagem. Por isso, imagens de 8MP,
      12MP ou 16MP funcionam todas da mesma forma.
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

print("="*60)
print("TESTE DE INFERÊNCIA - YOLOv26 no Raspberry Pi 5")
print("="*60)

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Modelo YOLOv26 (estou a usar YOLOv11 por agora)
DEFAULT_MODEL = "yolo11s.pt"  # ou "yolo26s_openvino_model/" para OpenVINO

# Threshold de confiança mínimo para deteções
CONFIDENCE_THRESHOLD = 0.25   # podemos mudar

# Formatos de imagem suportados 
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}

# ============================================================================
# FUNÇÃO: CARREGAR MODELO
# ============================================================================

def load_model(model_path):
    """Carrega modelo YOLOv26 (PyTorch .pt ou OpenVINO)"""
    print(f"\n[1/3] A carregar o modelo: {model_path}")
    
    # Se for um ficheiro .pt padrão do YOLO (ex: yolo26s.pt, yolov8n.pt),
    # deixamos a biblioteca tentar baixar sozinha, mesmo que não exista localmente.
    # Só bloqueamos se for um caminho customizado que parece local mas não existe.
    
    is_standard_model = model_path.startswith("yolo") and model_path.endswith(".pt")
    
    if not is_standard_model and not Path(model_path).exists():
        print(f"✗ Modelo local não encontrado: {model_path}")
        print("\n  Para usar modelo pré-treinado:")
        print("  1. Download: yolo11s.pt (Ultralytics)")
        print("  2. Ou treine: yolo train model=yolo11s.pt data=dataset.yaml")
        return None
    
    try:
        # Carrega modelo (Ultralytics baixa automático se for standard)
        model = YOLO(model_path)
        print(f"✓ Modelo carregado com sucesso")
        print(f"  Classes: {list(model.names.values())}")
        return model
    except Exception as e:
        print(f"✗ Erro ao carregar modelo: {e}")
        return None


# ============================================================================
# FUNÇÃO: EXECUTAR INFERÊNCIA
# ============================================================================

def run_inference(model, image_path, conf_threshold):
    """Executa inferência YOLOv26 numa imagem"""
    print(f"\n[2/3] Inferência em: {Path(image_path).name}")
    
    try:
        # Executa deteção ( força device='cpu' pois o Raspberry Pi nao tem GPU)
        results = model(
            image_path,
            conf=conf_threshold,
            device='cpu',
            verbose=False
        )
        
        # Extrai primeiro resultado (single image)
        result = results[0]
        num_detections = len(result.boxes)
        
        print(f"✓ Inferência concluída")
        print(f"  Deteções (conf ≥ {conf_threshold}): {num_detections}")
        
        return result, num_detections
        
    except Exception as e:
        print(f"✗ Erro durante inferência: {e}")
        return None, 0

# ============================================================================
# FUNÇÃO: MOSTRAR RESULTADOS
# ============================================================================

def display_results(model, result, num_detections):
    """Mostra deteções no terminal"""
    print(f"\n[3/3] RESULTADOS:")
    print("="*60)
    
    if num_detections == 0:
        print("  Nenhuma deteção acima do threshold")
    else:
        print(f"  Total de deteções: {num_detections}\n")
        
        # Itera sobre cada deteção
        for i in range(num_detections):
            cls_id = int(result.boxes.cls[i])
            conf = float(result.boxes.conf[i])
            class_name = model.names[cls_id]
            
            # Bounding box (x1, y1, x2, y2)
            box = result.boxes.xyxy[i].cpu().numpy()
            
            print(f"  [{i+1}] {class_name}")
            print(f"      Confiança: {conf:.3f} ({conf*100:.1f}%)")
            print(f"      BoundingBox: ({box[0]:.0f}, {box[1]:.0f}) → ({box[2]:.0f}, {box[3]:.0f})")
    
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
    # Parser de argumentos no terminal (CLI) 
    parser = argparse.ArgumentParser(
        description="Teste de inferência YOLOv11 no Raspberry Pi 5"
    )
    parser.add_argument(
        '--image',
        help='Path da imagem de teste (ex: ./camera_test_images/cam0_test_*.jpg)'
    )
    parser.add_argument(
        '--input-dir',
        help='Pasta com múltiplas imagens (processa todas *.jpg/*.png)'
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
    
    args = parser.parse_args()
    
    # Validação: precisa de --image OU --input-dir
    if not args.image and not args.input_dir:
        print("\n✗ Erro: Forneça --image ou --input-dir")
        print("Exemplos:")
        print("  python3 yolo_test_pi.py --image test.jpg")
        print("  python3 yolo_test_pi.py --input-dir ./test_images/")
        return 1
    
    # Determina lista de imagens a processar
    images = []
    if args.input_dir:
        # Modo: Pasta completa
        dir_path = Path(args.input_dir)
        if not dir_path.exists():
            print(f"\n✗ Pasta não encontrada: {dir_path}")
            return 1
        # Recolhe TODOS os formatos suportados
        all_files = []
        for fmt in SUPPORTED_FORMATS:
            all_files.extend(dir_path.glob(f"*{fmt}"))
        
        images = get_valid_images(all_files)  
        
        if not images:
            print(f"\n✗ Nenhuma imagem válida encontrada em: {dir_path}")
            print(f"  Formatos suportados: {', '.join(SUPPORTED_FORMATS)}")
            return 1
        print(f"✓ Encontradas {len(images)} imagens em: {dir_path}")

    else:
        # Modo: Ficheiro único
        img_path = Path(args.image)
        if not img_path.exists():
            print(f"\n✗ Imagem não encontrada: {img_path}")
            return 1
        
        # VALIDAÇÃO DE FORMATO
        if img_path.suffix.lower() not in SUPPORTED_FORMATS:
            print(f"\n✗ Formato não suportado: {img_path.suffix}")
            print(f"  Formatos aceites: {', '.join(SUPPORTED_FORMATS)}")
            return 1
        
        images = [img_path]
        print(f"✓ Imagem encontrada: {img_path.name}")

    
    # PASSO 1: Carrega o modelo (uma vez só)
    model = load_model(args.model)
    if model is None:
        return 1
    
    # PASSO 2 e 3: Processa todas as imagens
    total_detections = 0
    for i, img_path in enumerate(images, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(images)}] PROCESSANDO: {img_path.name}")
        print('='*60)
        
        # Executa inferência
        result, num_detections = run_inference(model, str(img_path), args.conf)
        if result is None:
            continue
        
        # Mostra resultados
        display_results(model, result, num_detections)
        total_detections += num_detections
    
    # Resumo final
    print("\n" + "="*60)
    print("RESUMO FINAL")
    print("="*60)
    print(f"  Imagens processadas: {len(images)}")
    print(f"  Total de deteções: {total_detections}")
    print("\n✅ YOLOv11 FUNCIONAL NO RASPBERRY PI 5!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())