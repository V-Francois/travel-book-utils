import numpy as np

from PIL import Image
from PIL import ImageChops

img = Image.open("watercolor_base.png").convert("RGB")

w, h = img.size

noise = np.random.normal(220, 8, (h, w))

noise = np.clip(noise, 0, 255).astype(np.uint8)

paper = Image.fromarray(noise)

paper = paper.convert("RGB")

final = ImageChops.multiply(img, paper)

final.save("watercolor_map.png")
