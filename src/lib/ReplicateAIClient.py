import replicate
from replicate.client import Client
from dotenv import dotenv_values

from .Config import Config

class ReplicateAIClient:

    def __init__(self, config:Config):
        self.client = Client(api_token=config.replicate_api_key)

    def tiktok_captions(self, internalVideoId, video_url, output_filename):
        # See https://replicate.com/fictions-ai/autocaption?input=python
        output = self.client.run(
            "shreejalmaharjan-27/tiktok-short-captions:46bf1c12c77ad1782d6f87828d4d8ba4d48646b8e1271b490cb9e95ccdbc4504",
            input={
                "video": video_url,
                "caption_size":100
            }
        )

        # Save the generated image
        with open(output_filename, 'wb') as f:
            f.write(output.read())

        print(f"Video saved as {output_filename}".format(output_filename=output_filename))
    
    def autocaption(self, internalVideoId, video_url, output_filename):
        # See https://replicate.com/fictions-ai/autocaption?input=python
        output = self.client.run(
            "fictions-ai/autocaption:18a45ff0d95feb4449d192bbdc06b4a6df168fa33def76dfc51b78ae224b599b",
            input={
                "font": "Poppins/Poppins-ExtraBold.ttf",
                "color": "white",
                "kerning": 0,
                "opacity": 0,
                "MaxChars": 20,
                "fontsize": 7,
                "translate": False,
                "output_video": True,
                "stroke_color": "black",
                "stroke_width": 2.6,
                "right_to_left": False,
                "subs_position": "bottom75",
                "highlight_color": "yellow",
                "video_file_input": video_url,
                "output_transcript": True
            }
        )

        # Save the generated image
        with open(output_filename, 'wb') as f:
            f.write(output[0].read())
 
        print(f"Video saved as {output_filename}".format(output_filename=output_filename))