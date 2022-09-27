#
# Image2Image Video by Leon M.
# intended for use with https://github.com/AUTOMATIC1111/stable-diffusion-webui
# Save this in script folder then restart the UI.
#
import glob
import math
import os
import random
import subprocess
import time

import gradio as gr
import modules.scripts as scripts
import numpy as np
from modules import images, processing, sd_samplers, shared
from modules.processing import Processed, process_images
from modules.sd_samplers import samplers
from modules.shared import cmd_opts, opts, state
from PIL import Image, ImageFilter


def do_round(x, base=64):
    return int(base * round(float(x) / base))
# remove dumb stuff from prompt


def sanitize(prompt, usage):
    if usage == 0:
        whitelist = set('abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789 _ ( ) | .')
        tmp = ''.join(filter(whitelist.__contains__, prompt))
        return tmp.replace(' ', '_')
    else:
        whitelist = set('abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789 _')
        tmp = ''.join(filter(whitelist.__contains__, prompt))
        return tmp.replace(' ', '_')
# input video gets chopped down to frames


def dump_frames(filepath, orig_path, x, y):

    image_path = os.path.join(filepath, "temp_%05d.png")

    cmd = [
        'ffmpeg',
        '-i', orig_path,
        '-vf', 'scale=' + str(x) + ':' + str(y),
        str(image_path)
    ]
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(stderr)
        raise RuntimeError(stderr)
# create output video


def make_mp4(filepath, filename, x, y, keep):
    image_path = os.path.join(filepath, f"{str(filename)}_%05d.png")
    mp4_path = os.path.join(filepath, f"{str(filename)}.mp4")
    cmd = [

        'ffmpeg',
        '-y',
        '-vcodec', 'png',
        '-r', str(30),
        '-start_number', str(0),
        '-i', str(image_path),
        '-c:v', 'libx264',
        '-vf', 'scale=' + str(x) + ':' + str(y),
        '-pix_fmt', 'yuv420p',
        '-crf', '17',
        '-preset', 'veryfast',
        str(mp4_path)
    ]
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(stderr)
        raise RuntimeError(stderr)
    if keep == False:
        for ifile in glob.glob(filepath + "/*.png"):
            os.remove(ifile)


class Script(scripts.Script):
    # this gets shown in the scripts drop down
    def title(self):
        return "img2img video"
    # makes this script only visible for img2img

    def show(self, is_img2img):
        return is_img2img
    # ui elements

    def ui(self, is_img2img):
        keep = gr.Checkbox(label='Keep generated pngs?', value=False)
        res = gr.Textbox(label="Resolution: (Put in like this x:y)",
                         visible=True, lines=1, value="640:480")
        input = gr.File(label="Input Video:", type="file")
        prompts = gr.Textbox(
            label="Prompt: (Seperate Positive and Negative by using ' | ') ", visible=True, lines=5, value="")
        return [prompts, input, res, keep]
    # here happens the good stuff

    def run(self, p, prompts, input, res, keep):
        prompts = sanitize(prompts, 0)
        if prompts.find("|") != -1:
            for l in prompts.splitlines():
                prompt_parts = l.split("|", 1)
                print(prompt_parts[0])
                print(prompt_parts[1])
                positive_prompt = prompt_parts[0]
                negative_prompt = prompt_parts[1]
        else:
            positive_prompt = prompts
            negative_prompt = ""

        for r in res.splitlines():
            res_parts = r.split(":")
            width = do_round(res_parts[0])
            height = do_round(res_parts[1])

        path_prompt = sanitize(prompts, 1)
        dateiname = path_prompt[:50]
        print(dateiname)
        stamm = os.getcwd() + "\\outputs\\img2img-videos\\"
        if not os.path.exists(stamm):
            os.mkdir(stamm)
        unterordner = stamm + dateiname + "\\"
        if not os.path.exists(unterordner):
            os.mkdir(unterordner)
        half_path = unterordner + "temp_"
        # extract frames from input video
        dump_frames(unterordner, input.name,
                    width, height)
        # get fps by literally counting the images... i know this is stupid
        loops = len([name for name in os.listdir(unterordner)
                     if os.path.isfile(os.path.join(unterordner, name))])
        p.do_not_save_samples = True
        p.do_not_save_grid = True
        processing.fix_seed(p)
        batch_count = p.n_iter
        p.extra_generation_params = {
            "Prompts:": prompts
        }
        p.batch_size = 1
        p.n_iter = 1
        output_images, info = None, None
        initial_seed = None
        initial_info = None
        grids = []
        all_images = []
        state.job_count = int(loops) * batch_count
        p.width = width
        p.height = height
        p.init_images[0] = Image.open(unterordner + "temp_00001.png")
        initial_color_corrections = [
            processing.setup_color_correction(p.init_images[0])]
        p.prompt = prompts
        p.negative_prompt = negative_prompt or ""
        for i in range(int(loops)):
            number_string = str(i)
            if len(number_string) > 4:
                full_path = half_path + str(i) + ".png"
            elif len(number_string) > 3:
                full_path = half_path + "0" + str(i) + ".png"
            elif len(number_string) > 2:
                full_path = half_path + "00" + str(i) + ".png"
            elif len(number_string) > 1:
                full_path = half_path + "000" + str(i) + ".png"
            elif number_string == "0":
                full_path = half_path + "00001.png"
            elif len(number_string) == 1:
                full_path = half_path + "0000" + str(i) + ".png"
            p.init_images[0] = Image.open(full_path)
            if state.interrupted:
                break
            p.color_corrections = initial_color_corrections
            state.job = f"Frame {i + 1}/{int(loops)}"
            processed = processing.process_images(p)
            if initial_seed is None:
                initial_seed = processed.seed
                initial_info = processed.info
            init_img = processed.images[0]
            p.init_images = [init_img]
            p.seed = processed.seed
            # Save every seconds worth of frames to the output set displayed in UI
            if (i % int(30) == 0):
                all_images.append(init_img)
            # Save current image to folder manually, with specific name we can iterate over.
            init_img.save(os.path.join(unterordner, f"{dateiname}_{i:05}.png"))
            processed = Processed(p, all_images, initial_seed, initial_info)
        print("All done.")
        processed = Processed(p, all_images, initial_seed, initial_info)
        make_mp4(unterordner, dateiname, width,
                 height, keep)
        return processed
