from PIL import Image

# 打开图片
img = Image.open("static/four_finger_hand.png").convert("RGBA")
pixels = img.load()

for y in range(img.height):
    for x in range(img.width):
        r, g, b, a = pixels[x, y]
        # 判断是否为红色区域 (可以调节阈值)
        if r > 20 and g < 100 and b < 100:
            pixels[x, y] = (0, 255, 0, a)  # 替换为绿色

img.save("output.png")
