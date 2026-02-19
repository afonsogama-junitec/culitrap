# 🦟 CuliTrap - Armadilha Inteligente para Culicoides (AI)

Sistema de visão computacional para monitorização automática de culicoides usando Raspberry Pi 5, YOLOv11 e SAHI (Sliced Inference).

**Compatibilidade:** Arducam 16MP (IMX519), Arducam 64MP (OV64A40), Pi Camera V3/HQ/V2

---

## ✨ Funcionalidades

- ✅ Deteção automática de câmeras e sensores (16MP, 64MP, 12MP, etc.)
- ✅ Captura de imagens em alta resolução (até 64MP)
- ✅ Inferência YOLOv11 para deteção de insetos
- ✅ **SAHI (Sliced Inference)** para detetar objetos muito pequenos (+150% deteções)
- ✅ Processamento em batch (múltiplas imagens)
- ✅ Suporta modelos custom treinados
- ✅ Scripts universais (alternar resoluções via CLI)

---

## 📷 Suporte de Câmeras

| **Modelo**                | **Sensor**  | **Resolução** | **Auto-Deteção** | **Configuração**  |
| ------------------------- | ----------- | ------------- | ---------------- | ----------------- |
| Arducam 16MP              | IMX519      | 4656×3496     | ✅ Sim           | dtoverlay=imx519  |
| **Arducam 64MP Hawk-Eye** | **OV64A40** | **9248×6944** | ✅ Sim           | dtoverlay=ov64a40 |
| Pi Camera V3              | IMX708      | 4608×2592     | ✅ Sim           | Plug & Play       |
| Pi HQ Camera              | IMX477      | 4056×3040     | ✅ Sim           | Plug & Play       |
| Pi Camera V2              | IMX219      | 3280×2464     | ✅ Sim           | Plug & Play       |

### Configuração Manual (Arducam)

**Arducam 16MP (IMX519):**

```bash
sudo nano /boot/firmware/config.txt
# Adicionar:
dtoverlay=imx519,vcm=off,cam0
dtoverlay=imx519,vcm=off,cam1
camera_auto_detect=0
# Reiniciar:
sudo reboot
```

**Arducam 64MP (OV64A40):**

```bash
sudo nano /boot/firmware/config.txt
# Adicionar:
dtoverlay=ov64a40,cam0,link-frequency=456000000
dtoverlay=ov64a40,cam1,link-frequency=456000000
camera_auto_detect=0
# Reiniciar:
sudo reboot
```

**Nota:** Câmera 64MP requer Raspberry Pi 5 com 4GB ou 8GB RAM (cada captura ~400MB).

---

## 📋 Instalação

### 1. Preparação de Sistema

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-numpy rpicam-apps libcamera-apps git
```

### 2. Instalação do Projeto

```bash
git clone https://github.com/afonsogama-junitec/culitrap
cd culitrap
pip install -r requirements.txt --break-system-packages
```

---

## 🚀 Workflow de Validação

### 1. Validar Hardware

```bash
python3 setup_cameras.py
```

### 2. Testar Captura (Universal)

```bash
# Auto-deteta resolução
python3 capture_test.py

# 64MP com foco manual
python3 capture_test.py --resolution 64mp --manual-focus --lens-position 7.5

# 16MP com zoom 2x
python3 capture_test.py --resolution 16mp --zoom 2.0

# Full HD para testes rápidos
python3 capture_test.py --resolution fhd
```

**Opções disponíveis:**

- `--camera 0` - ID da câmera (default: 0)
- `--resolution auto` - auto, 64mp, 16mp, 12mp, 4k, fhd
- `--manual-focus` - Ativar foco manual
- `--lens-position 7.5` - Posição lente (0.0=infinito, 10.0+=macro)
- `--zoom 2.0` - Zoom digital (1.0=sem zoom, 4.0=4x)

### 3. Captura Intervalada

```bash
# Auto-deteta tudo
python3 capture_interval.py

# 64MP, capturas a cada 1 hora
python3 capture_interval.py --resolution 64mp --interval 3600 --manual-focus --lens-position 7.5
```

**Opções disponíveis:**

- `--camera 0` - ID da câmera
- `--resolution auto` - auto, 64mp, 16mp, 12mp, 4k, fhd
- `--interval 300` - Segundos entre capturas (300s = 5min)
- `--manual-focus` - Ativar foco manual
- `--lens-position 7.5` - Posição da lente
- `--zoom 1.0` - Zoom digital

### 4. Deteção YOLO Básica

```bash
# Imagem única
python3 yolo_test_pi.py --image capture_test.jpg

# Pasta de imagens
python3 yolo_test_pi.py --input-dir ./camera_test_images/
```

### 5. Deteção SAHI (Recomendado)

```bash
# Imagem única (slice 320x320)
python3 SAHI.py --image capture_test.jpg --slice-size 320 --conf 0.15

# Pasta completa
python3 SAHI.py --input-dir ./camera_test_images/ --slice-size 320 --overlap 0.3 --conf 0.15

# Modelo custom treinado
python3 SAHI.py --input-dir ./captures/ --model best.pt --slice-size 320 --conf 0.15
```

**Opções SAHI:**

- `--image foto.jpg` - Imagem única
- `--input-dir ./pasta/` - Processar pasta completa
- `--model yolo11s.pt` - Modelo YOLO
- `--slice-size 320` - Tamanho dos tiles (640, 320, 256)
- `--overlap 0.3` - Sobreposição entre tiles (0.2-0.4)
- `--conf 0.15` - Threshold de confiança (0.10-0.30)

---

## 📊 Comparação: YOLO vs SAHI

**Testes validados:**

| **Modo**           | **Objetos Grandes** | **Objetos Pequenos** | **Tempo (8MP)** |
| ------------------ | ------------------- | -------------------- | --------------- |
| **YOLO Normal**    | ✅ Deteta           | ⚠️ Perde muitos      | ~1-2s           |
| **SAHI (640x640)** | ✅ Deteta           | ✅ +50%              | ~2-4s           |
| **SAHI (320x320)** | ✅ Deteta           | ✅ **+150%** 🎯      | ~4-6s           |

**Exemplo real (bus.jpg):**

- Slice 640: 6 deteções
- Slice 320: 15 deteções (+150%)

**Recomendação Culicoides:** `--slice-size 320` com `--conf 0.15`

---

## 🎓 Treinar Modelo Custom (Google Colab)

### 1. Preparar Dataset

- Recolher imagens de Culicoides
- Anotar com Roboflow (recomendado), CVAT ou LabelImg
- Definir classes: culicoides_macho, culicoides_femea
- Exportar no formato YOLOv11

### 2. Treinar no Colab (GPU grátis T4)

```python
# Google Colab Notebook
!pip install ultralytics roboflow

from roboflow import Roboflow
rf = Roboflow(api_key="TUA_API_KEY")
project = rf.workspace("workspace").project("culicoides")
dataset = project.version(1).download("yolov11")

from ultralytics import YOLO
model = YOLO('yolo11s.pt')
results = model.train(
    data='culicoides_dataset/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    patience=20,
    device=0,
    project='culitrap_training',
    name='yolo11s_culicoides'
)

metrics = model.val()
print(f"mAP50: {metrics.box.map50}")

from google.colab import files
files.download('culitrap_training/yolo11s_culicoides/weights/best.pt')
```

**Tempo:** ~30 min no Colab Free

### 3. Deploy no Raspberry Pi

```bash
scp best.pt pi@192.168.x.x:~/culitrap/
cd ~/culitrap
python3 SAHI.py --input-dir ./captures/ --model best.pt --slice-size 320 --conf 0.15
```

---

## 📂 Estrutura do Projeto

```
culitrap/
├── setup_cameras.py       # Validação câmeras (universal)
├── capture_test.py        # Captura teste (16MP/64MP)
├── capture_interval.py    # Captura intervalada
├── yolo_test_pi.py        # Inferência YOLO básica
├── SAHI.py                # Inferência SAHI (slicing)
├── requirements.txt       # Dependências Python
├── README.md              # Este ficheiro
├── .gitignore             # Ficheiros ignorados
└── captures/              # Imagens capturadas
```

---

## ⚙️ Configurações Recomendadas

### Para Culicoides (2-3mm):

**Captura:**

```bash
python3 capture_interval.py --resolution 64mp --interval 3600 --manual-focus --lens-position 7.5
```

**Inferência:**

```bash
python3 SAHI.py --input-dir ./captures/ --model best.pt --slice-size 320 --overlap 0.3 --conf 0.15
```

### Para Testes Rápidos:

**Captura:**

```bash
python3 capture_test.py --resolution fhd
```

**Inferência:**

```bash
python3 SAHI.py --input-dir ./captures/ --slice-size 640 --conf 0.25
```

---

## 🐛 Troubleshooting

### "No cameras detected"

```bash
rpicam-hello --list-cameras
# Verificar cabo flat (dentes para baixo?)
# Verificar config.txt (dtoverlay correto?)
sudo reboot
```

### "SAHI muito lento"

```bash
# Usar slices maiores
--slice-size 640
# Reduzir overlap
--overlap 0.2
# Usar resolução menor
--resolution 16mp
```

### "Poucas deteções"

```bash
# Baixar threshold
--conf 0.10
# Slices menores
--slice-size 256
# Verificar foco manual
--lens-position 8.0
```

### "Cannot allocate memory" (64MP)

```bash
free -h
# Se Pi tem 2GB RAM: usar --resolution 16mp
# Se Pi tem 4GB+ RAM: 64MP funciona
```

### "Modelo não deteta Culicoides"

```
Normal! Modelo pré-treinado (yolo11s.pt) só conhece COCO classes.
Solução: Treinar modelo custom no Google Colab.
```

---

## 📝 Dependências

```
ultralytics>=8.2.0        # YOLOv11
sahi>=0.11.14             # Sliced inference
opencv-python-headless    # Processamento imagem
pandas                    # Logs CSV
matplotlib                # Visualização
numpy                     # Cálculos
```

**Nota:** picamera2 instalado via apt (não pip)

---

## 📊 Performance Esperada

### Captura (Raspberry Pi 5):

| **Resolução**    | **FPS** | **Tempo** | **Tamanho** |
| ---------------- | ------- | --------- | ----------- |
| 64MP (9248×6944) | 2 fps   | ~0.5s     | ~18-25 MB   |
| 16MP (4656×3496) | 7.6 fps | ~130ms    | ~6-8 MB     |
| 12MP (4608×2592) | 30 fps  | ~33ms     | ~4-6 MB     |
| FHD (1920×1080)  | 60 fps  | ~17ms     | ~1-2 MB     |

### Inferência SAHI (Pi 5, CPU):

| **Resolução** | **Slice 640** | **Slice 320** |
| ------------- | ------------- | ------------- |
| 64MP          | ~8-12s        | ~18-25s       |
| 16MP          | ~3-5s         | ~6-10s        |
| 12MP          | ~2-4s         | ~4-6s         |

---

## 🤝 Contribuições

**Desenvolvido por:** Afonso Gama @ Junitec  
**Projeto:** CuliTrap - Monitorização Culicoides  
**Versão:** 3.0 (19/02/26) - Universal 16MP/64MP

---

## 📌 Notas Técnicas

### Alternar 16MP ↔ 64MP:

1. Trocar câmera fisicamente
2. Editar /boot/firmware/config.txt (mudar dtoverlay)
3. sudo reboot
4. Scripts detetam automaticamente! ✅

```bash
python3 capture_test.py --resolution auto
```

### Zoom vs Resolução:

- **Zoom digital**: Crop do sensor, perde qualidade
- **Resolução alta (64MP)**: Mantém qualidade
- **Recomendação**: 64MP sem zoom + SAHI slice 320

### Foco Manual vs Autofocus:

- **Autofocus**: Pode focar no fundo
- **Foco manual**: Fixo na distância correta
- **Recomendação**: Testar --lens-position 5.0-10.0

---

**🚀 Sistema pronto para monitorização de Culicoides! 🦟🔬**
