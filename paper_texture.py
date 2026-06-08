import numpy as np

from PIL import Image
from PIL import ImageChops
from PIL import ImageEnhance
from PIL import ImageFilter

img = Image.open("watercolor_base.png").convert("RGB")

w, h = img.size


def smooth_noise(width, height, scale, strength, blur):
    small_w = max(2, width // scale)
    small_h = max(2, height // scale)
    noise = np.random.normal(0, 1.0, (small_h, small_w))
    noise = ((noise - noise.min()) / (np.ptp(noise) or 1.0) * 255).astype(np.uint8)
    layer = Image.fromarray(noise).resize(
        (width, height), resample=Image.Resampling.BICUBIC
    )
    layer = layer.filter(ImageFilter.GaussianBlur(radius=blur)).point(
        lambda p: max(0, min(255, int(236 + (p - 128) * strength / 32)))
    )
    return layer.convert("RGB")


# Build a smooth paper texture with layered low-frequency variations.
fine = smooth_noise(w, h, scale=32, strength=10, blur=1.2)
coarse = smooth_noise(w, h, scale=140, strength=18, blur=6.0)
fibers = smooth_noise(w, h, scale=10, strength=4, blur=0.4)

paper = ImageChops.multiply(fine, coarse)
paper = ImageChops.add(paper, fibers, scale=2.8, offset=-22)
paper = ImageEnhance.Contrast(paper).enhance(1.08)
paper = ImageEnhance.Color(paper).enhance(1.02)

texture = ImageChops.multiply(img, paper)
texture = ImageChops.blend(texture, img, alpha=0.12)
final = ImageChops.blend(img, texture, alpha=0.72)
final = ImageEnhance.Color(final).enhance(1.24)

final.save("watercolor_map.png")
