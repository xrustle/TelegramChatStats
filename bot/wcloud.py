import os
from PIL import Image
import numpy as np
from scipy.ndimage import gaussian_gradient_magnitude
from wordcloud import WordCloud, ImageColorGenerator
from bot.db_select import db

d = os.path.dirname(__file__)

chat_id = ''
text = db.text_for_cloud(chat_id)

cloud_image = np.array(Image.open(os.path.join(d, 'flag.jpg')))
cloud_image = cloud_image[::3, ::3]

cloud_mask = cloud_image.copy()
cloud_mask[cloud_mask.sum(axis=2) == 0] = 255

image_edges = np.mean([gaussian_gradient_magnitude(cloud_image[:, :, i] / 255., 2) for i in range(3)], axis=0)
cloud_mask[image_edges > .08] = 255

wc = WordCloud(height=1800,
               width=3200,
               max_words=500,
               scale=3,
               mask=cloud_mask,
               relative_scaling=1,
               colormap='Pastel1',
               background_color='black',
               repeat=False)

wc.generate(text)

wc.to_file("july_cloud_pastel.png")

image_colors = ImageColorGenerator(cloud_image)
wc.recolor(color_func=image_colors)
wc.to_file("july_job_cloud.png")
# wc.to_image()
