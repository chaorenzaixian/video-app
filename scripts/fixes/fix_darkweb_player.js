const fs = require('fs');

let content = fs.readFileSync('frontend/src/views/user/DarkwebPlayer.vue', 'utf8');

// 替换 API 路径
content = content.replace(/`\/videos\/\$\{videoId\}`/g, '`/darkweb/videos/${videoId}`');
content = content.replace(/`\/videos\/\$\{video\.value\.id\}\/like`/g, '`/darkweb/videos/${video.value.id}/like`');
content = content.replace(/`\/videos\/\$\{video\.value\.id\}\/favorite`/g, '`/darkweb/videos/${video.value.id}/favorite`');
content = content.replace(/`\/videos\/\$\{video\.value\.id\}\/download-info`/g, '`/darkweb/videos/${video.value.id}/download-info`');
content = content.replace(/`\/api\/v1\/videos\/\$\{video\.value\.id\}\/download`/g, '`/api/v1/darkweb/videos/${video.value.id}/download`');

// 替换路由路径
content = content.replace(/\/user\/video\//g, '/user/darkweb/video/');

// 替换颜色 - 紫色系改为红色系
content = content.replace(/#a855f7/g, '#ff4444');
content = content.replace(/#7c3aed/g, '#cc0000');
content = content.replace(/#8b5cf6/g, '#ff4444');
content = content.replace(/#ec4899/g, '#ff4444');
content = content.replace(/#6366f1/g, '#ff6666');
content = content.replace(/#c084fc/g, '#ff6666');
content = content.replace(/#e879f9/g, '#ff8888');
content = content.replace(/rgba\(168, 85, 247/g, 'rgba(255, 68, 68');
content = content.replace(/rgba\(124, 58, 237/g, 'rgba(204, 0, 0');
content = content.replace(/rgba\(59, 130, 246/g, 'rgba(255, 100, 100');

// 移除前贴广告模板
const preRollAdStart = '      <!-- 前贴广告 -->';
const preRollAdEnd = '      <!-- ArtPlayer 容器 -->';
const preRollAdRegex = /\s*<!-- 前贴广告 -->[\s\S]*?(?=\s*<!-- ArtPlayer 容器 -->)/;
content = content.replace(preRollAdRegex, '\n');

// 移除 hidden-by-ad class
content = content.replace(/:class="{ 'hidden-by-ad': showPreRollAd }"/g, '');

// 移除试看和购买相关模板
const trialOverlayRegex = /\s*<!-- 试看倒计时已移除[\s\S]*?<\/div>\s*<\/div>\s*<\/div>\s*(?=\s*<\/div>\s*<!-- 分享弹窗 -->)/;
content = content.replace(trialOverlayRegex, '\n    </div>\n\n');

// 移除下载按钮
const downloadBtnRegex = /<div class="stat-item clickable" @click="downloadVideo">[\s\S]*?<span class="stat-label">下载<\/span>\s*<\/div>/;
content = content.replace(downloadBtnRegex, '');

fs.writeFileSync('frontend/src/views/user/DarkwebPlayer.vue', content, 'utf8');
console.log('Done!');
