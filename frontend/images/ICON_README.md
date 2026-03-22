# PWA图标说明

PWA需要不同尺寸的图标。请准备一个512x512的PNG图标，然后生成以下尺寸：

## 需要的图标尺寸：
- icon-72x72.png
- icon-96x96.png
- icon-128x128.png
- icon-144x144.png
- icon-152x152.png
- icon-192x192.png
- icon-384x384.png
- icon-512x512.png

## 在线生成工具：
1. https://realfavicongenerator.net/
2. https://www.pwabuilder.com/imageGenerator

## 或使用ImageMagick命令行生成：
```bash
# 从512x512的原图生成所有尺寸
convert icon-512x512.png -resize 72x72 icon-72x72.png
convert icon-512x512.png -resize 96x96 icon-96x96.png
convert icon-512x512.png -resize 128x128 icon-128x128.png
convert icon-512x512.png -resize 144x144 icon-144x144.png
convert icon-512x512.png -resize 152x152 icon-152x152.png
convert icon-512x512.png -resize 192x192 icon-192x192.png
convert icon-512x512.png -resize 384x384 icon-384x384.png
```

## 临时方案：
如果暂时没有图标，可以使用现有的logo或创建一个简单的纯色图标。
