A captcha/login page which only allows you to register if you post an image of you touching grass 

To install, you have to install everything in requirements.txt or do uv sync, but you also have to install easyocr.
On my machine, i did this because i wanted to install the CPU version of torch or otherwise it would install NVIDIA bloat.
If you want to do the same, add `extra-index-url`:

```bash
uv pip install easyocr --extra-index-url https://download.pytorch.org/whl/cpu
```
Dont add the flag if you have a dedicated GPU on the computer where you host the project.
Run the command without uv if you use pip.