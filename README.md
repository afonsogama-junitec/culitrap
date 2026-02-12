# 🦟 CuliTrap - Armadilha Inteligente para Culicoides (AI)

Sistema de visão computacional para monitorização automática de culicoides usando Raspberry Pi 5 e Modelo de AI (YOLO).

**Compatibilidade:** Este projeto é universal e suporta várias câmeras (V3, HQ, V2 e Arducam).

---

## 📋 Instalação e Configuração (Raspberry Pi OS)

### 1. Preparação de Sistema

Instalar as bibliotecas de sistema necessárias para controlar as câmaras e processamento numérico.

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-numpy rpicam-apps libcamera-apps git
```

### 2. Instalação do Projeto

```bash
# Clonar o repositório
git clone https://github.com/afonsogama-junitec/culitrap
cd culitrap

# Instalar dependências Python
pip install -r requirements.txt --break-system-packages
```

### 3. Configuração Especial (Apenas Arducam IMX519)

Se usar a Arducam 16MP, edite o config.txt:

```bash
sudo nano /boot/firmware/config.txt

# Adicionar no final do ficheiro:
dtoverlay=imx519,vcm=off,cam0
dtoverlay=imx519,vcm=off,cam1

# Reiniciar:
sudo reboot
```

## 📋 Workflow de Validação (Raspberry Pi)

### 1. Validar Hardware

```bash
python3 setup_cameras.py
```

### 2. Testar Captura

```bash
python3 capture_test.py
```

### 3. Executar Deteção (YOLO)

```bash
# Imagem única

python3 yolo_test_pi.py --image capture_test.jpg

# Pasta de imagens

python3 yolo_test_pi.py --input-dir ./imagens_teste/
```
