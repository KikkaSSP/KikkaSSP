import os
import sys
from PIL import Image


class FormatShellImage:
    def do_work(self, shell_path):
        pngs = {}
        pnas = {}
        for root, dirs, files in os.walk(shell_path):
            for file in files:
                filename, ext = os.path.splitext(file)
                if ext not in ['.png', '.pna']:
                    continue

                if ext == ".png":
                    pngs[filename] = os.path.join(root, file)
                elif ext == ".pna":
                    pnas[filename] = os.path.join(root, file)

        count = 0
        success = 0
        error = 0
        for filename in pngs.keys():
            if filename == 'background' \
            or filename == 'foreground' \
            or filename == 'sidebar':
                continue

            count += 1
            try:
                if filename in pnas:
                    self._mix_pna(pngs[filename], pnas[filename])
                else:
                    self._clear_alpha_color(pngs[filename])
                print(os.path.basename(pngs[filename]))
                success += 1
            except:
                print("ERROR in:", pngs[filename])
                error += 1
        print("Finish: success %d, error %d" % (success, error))

    def _mix_pna(self, png_path, pna_path):
        img1 = Image.open(png_path)
        img2 = Image.open(pna_path)
        img1 = img1.convert('RGBA')
        img2 = img2.convert('L')
        img1.putalpha(img2)
        img1.save(png_path)
        os.remove(pna_path)

    def _clear_alpha_color(self, png_path):
        img1 = Image.open(png_path)
        img1 = img1.convert('RGBA')

        color = img1.getpixel((0, 0))
        if color[3] == 0:
            return

        color2 = (color[0], color[1], color[2], 0)
        pixels = img1.load()
        for i in range(img1.size[0]):
            for j in range(img1.size[1]):
                    if pixels[i,j] == color:
                        pixels[i,j] = color2
        img1.save(png_path)


if __name__ == '__main__':
    work_dir = sys.argv[1]
    FormatShellImage().do_work(work_dir)
