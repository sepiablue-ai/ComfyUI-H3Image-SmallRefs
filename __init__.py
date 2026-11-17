"""MiniMax-H3-Image conditioning with small reference images.

The stock MiniMaxH3ImageConditioning node scales every reference picture to a
1024 px short edge (text encoder) and a 1024-2048 px short edge (VAE). This node
keeps that behavior for image_1 (the picture to edit) and scales the other
references to a fixed long edge (512 px by default) for both consumers.
"""

import torch

import comfy.model_management
import comfy.utils
import node_helpers
from comfy_api.latest import ComfyExtension, io

CANVAS_MULTIPLE = 32
MAIN_SHORT_EDGE = 1024
MAIN_VAE_MAX_SHORT_EDGE = 2048


def _snap(side, scale):
    return max(CANVAS_MULTIPLE, round(side * scale / CANVAS_MULTIPLE) * CANVAS_MULTIPLE)


def short_edge_size(width, height, low, high):
    scale = min(max(min(width, height), low), high) / min(width, height)
    return _snap(width, scale), _snap(height, scale)


def long_edge_size(width, height, long_edge):
    scale = long_edge / max(width, height)
    return _snap(width, scale), _snap(height, scale)


def resize_to(image, size):
    if (image.shape[2], image.shape[1]) == size:
        return image[..., :3]
    samples = image[..., :3].movedim(-1, 1)
    samples = comfy.utils.common_upscale(samples, size[0], size[1], "lanczos", "disabled")
    return samples.movedim(1, -1)


class H3ImageSmallPropConditioning(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="H3ImageSmallPropConditioning",
            display_name="H3 Image Conditioning (small refs)",
            category="model/conditioning/minimax",
            description="MiniMax H3 Image Conditioning that keeps image_1 at the stock size and scales the other references to a smaller long edge.",
            inputs=[
                io.Clip.Input("clip"),
                io.Vae.Input("vae", optional=True),
                io.String.Input("prompt", multiline=True, dynamic_prompts=True),
                io.Int.Input("width", default=0, min=0, max=16384, step=CANVAS_MULTIPLE,
                             tooltip="0 uses the width of image_1 after its reference scaling, or 2048 without images."),
                io.Int.Input("height", default=0, min=0, max=16384, step=CANVAS_MULTIPLE,
                             tooltip="0 uses the height of image_1 after its reference scaling, or 2048 without images."),
                io.Int.Input("ref_long_edge", default=512, min=CANVAS_MULTIPLE, max=2048, step=CANVAS_MULTIPLE, optional=True,
                             tooltip="Long edge for image_2 and later, for both the text encoder and the VAE."),
                io.Autogrow.Input("images", optional=True, template=io.Autogrow.TemplatePrefix(
                    input=io.Image.Input("image", tooltip="Reference picture, <Picture n> in the prompt; image_1 is the picture to edit."),
                    prefix="image_", min=0, max=100)),
            ],
            outputs=[io.Conditioning.Output(display_name="positive"), io.Latent.Output()],
        )

    @classmethod
    def execute(cls, clip, prompt, width, height, vae=None, images=None, ref_long_edge=512) -> io.NodeOutput:
        names = sorted(images or {}, key=lambda name: int(name.rsplit("_", 1)[-1]))
        vision_images = []
        refs = []
        main_vae_size = None
        for name in names:
            image = images[name]
            if image is None:
                continue
            image = image[:1]
            size = (image.shape[2], image.shape[1])
            if name == "image_1":
                vision_size = short_edge_size(*size, MAIN_SHORT_EDGE, MAIN_SHORT_EDGE)
                vae_size = short_edge_size(*size, MAIN_SHORT_EDGE, MAIN_VAE_MAX_SHORT_EDGE)
                main_vae_size = vae_size
            else:
                vision_size = vae_size = long_edge_size(*size, ref_long_edge)
            vision_images.append(resize_to(image, vision_size))
            if vae is not None:
                z = vae.encode(resize_to(image, vae_size))
                refs.append({"kind": "image", "latent_h": z.shape[-2], "latent_w": z.shape[-1], "latent": z})

        tokens = clip.tokenize(prompt, images=vision_images, picture_label="Picture %d: ")
        conditioning = clip.encode_from_tokens_scheduled(tokens)
        if refs:
            conditioning = node_helpers.conditioning_set_values(conditioning, {"minimax_refs": refs})
        if not (width and height):
            size = main_vae_size or (2048, 2048)
            width, height = width or size[0], height or size[1]
        latent = torch.zeros([1, 24, 1, height // 16, width // 16],
                             device=comfy.model_management.intermediate_device())
        return io.NodeOutput(conditioning, {"samples": latent})


class H3ImageSmallRefsExtension(ComfyExtension):
    async def get_node_list(self):
        return [H3ImageSmallPropConditioning]


async def comfy_entrypoint():
    return H3ImageSmallRefsExtension()
