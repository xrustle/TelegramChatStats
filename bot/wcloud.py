import os
from PIL import Image
import numpy as np
from scipy.ndimage import gaussian_gradient_magnitude
from wordcloud import WordCloud, ImageColorGenerator
import io


def generate_cloud_image(text):
    d = os.path.dirname(__file__)

    cloud_image = np.array(Image.open(os.path.join(d, 'cloud.png')))
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

    # wc.to_file("july_cloud_pastel.png")

    output = io.BytesIO()
    wc.to_image().save(output, format='JPEG')

    return output.getvalue()

    # image_colors = ImageColorGenerator(cloud_image)
    # wc.recolor(color_func=image_colors)
    # wc.to_file("july_job_cloud.png")


if __name__ == '__main__':
    print(type(generate_cloud_image('aa aa aa bb bb cc')))
