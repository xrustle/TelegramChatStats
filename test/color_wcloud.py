import os
from PIL import Image
import numpy as np
from scipy.ndimage import gaussian_gradient_magnitude
from wordcloud import WordCloud, ImageColorGenerator

d = os.path.dirname(__file__)

text = open(os.path.join(d, 'test_words.txt'), encoding='UTF-8').read()

cloud_image = np.array(Image.open(os.path.join(d, 'red_cloud.jpg')))
cloud_image = cloud_image[::3, ::3]

cloud_mask = cloud_image.copy()
cloud_mask[cloud_mask.sum(axis=2) == 0] = 255

image_edges = np.mean([gaussian_gradient_magnitude(cloud_image[:, :, i] / 255., 2) for i in range(3)], axis=0)
cloud_mask[image_edges > .08] = 255

wc = WordCloud(max_words=2000,
               mask=cloud_mask,
               relative_scaling=1,
               colormap='Pastel1')

wc.generate(text)

wc.to_file("red_cloud_pastel.png")

image_colors = ImageColorGenerator(cloud_image)
wc.recolor(color_func=image_colors)
wc.to_file("red_cloud.png")
# wc.to_image()
