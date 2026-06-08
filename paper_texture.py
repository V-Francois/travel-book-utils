import numpy as np

from PIL import Image
from PIL import ImageChops
from PIL import ImageFilter

img = Image.open("watercolor_base.png").convert("RGB")

w, h = img.size

# Build a paper texture with both coarse mottling and fine fiber noise.
fine = np.random.normal(0, 1.0, (h, w))
coarse = np.random.normal(0, 1.0, (max(1, h // 80), max(1, w // 80)))
coarse = np.kron(coarse, np.ones((80, 80)))[:h, :w]

fibers = np.random.normal(0, 1.0, (h, 1))
fibers = np.repeat(fibers, w, axis=1)
fibers = np.roll(fibers, np.random.randint(0, 120), axis=1)

noise = 236 + (fine * 7) + (coarse * 12) + (fibers * 4)

noise = np.clip(noise, 0, 255).astype(np.uint8)

paper = Image.fromarray(noise)

paper = paper.convert("RGB").filter(ImageFilter.GaussianBlur(radius=0.6))

texture = ImageChops.multiply(img, paper)
texture = ImageChops.add(texture, paper, scale=2.2, offset=-35)
final = ImageChops.blend(img, texture, alpha=0.72)

final.save("watercolor_map.png")
