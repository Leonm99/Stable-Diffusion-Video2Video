# Stable-Diffusion-vid2vid

a simple script addon for https://github.com/AUTOMATIC1111/stable-diffusion-webui
takes video as input, runs it through img2img and then outputs a video with the generated frames.

---

# Installation
#### 1. [Download FFMPEG](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z) just put the ffmpeg.exe in the stable-diffusion-webui folder or install it like shown [here.](https://www.geeksforgeeks.org/how-to-install-ffmpeg-on-windows/)

#### 2. download vid2vid.py and put it in the scripts folder.

#### 3. start/restart the webui and on the img2img tab you will now have vid2vid in the scripts dropdown.

---

Generally i would advise you to play around with different settings, maybe a set seed, more or less denoising, more or less sampling steps etc, since the output quality can differ based on the input video, resolution, prompt and all that.

