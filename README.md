A captcha/login page which only allows you to register if you post an image of you touching grass 

To install, you have to install everything in requirements.txt or do uv sync, but you also have to install easyocr.
On my machine, i did this because i wanted to install the CPU version of torch or otherwise it would install NVIDIA bloat.
If you want to do the same, do:

```bash
uv pip install torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cpu
uv pip install easyocr
```
or the same without uv if you use pip.

If you want to install it with GPU acceleration for the OCR part, do:

```bash
uv pip install easyocr
```
or the same without uv if you use pip.