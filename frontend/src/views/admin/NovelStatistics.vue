<template>
  <div class="novel-statistics">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card purple">
        <div class="stat-icon">📚</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_novels }}</div>
          <div class="stat-label">小说总数</div>
        </div>
        <div class="stat-detail">
          <span>文字: {{ stats.text_novels }}</span>
          <span>有声: {{ stats.audio_novels }}</span>
        </div>
      </div>
      <div class="stat-card blue">
        <div class="stat-icon">📖</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_chapters }}</div>
          <div class="stat-label">章节总数</div>
        </div>
      </div>
      <div class="stat-card green">
        <div class="stat-icon">👁</div>
        <div class="stat-info">
          <div class="stat-value">{{ formatNumber(stats.total_views) }}</div>
          <div class="stat-label">总浏览量</div>
        </div>
      </div>
      <div class="stat-card orange">
        <div class="stat-icon">👥</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.reading_users }}</div>
          <div class="stat-label">阅读用户</div>
        </div>
        <div class="stat-detail">
          <span>今日新增: {{ stats.today_readers }}</span>
        </div>
      </div>
    </div>

    <!-- 排行榜区域 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>🔥 热门排行</span>
              <el-radio-group v-model="rankType" size="small" @change="loadRanking">
                <el-radio-button label="views">浏览量</el-radio-button>
                <el-radio-button label="likes">点赞数</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="ranking-list">
            <div v-for="item in ranking" :key="item.id" class="ranking-item">
              <span class="rank" :class="'rank-' + item.rank">{{ item.rank }}</span>
              <img :src="item.cover" class="novel-cover" />
              <div class="novel-info">
                <div class="novel-title">{{ item.title }}</div>
                <div class="novel-meta">
                  <el-tag size="small" :type="item.novel_type === 'text' ? 'primary' : 'success'">
                    {{ item.novel_type === 'text' ? '文字' : '有声' }}
                  </el-tag>
                  <span>{{ item.chapter_count }}章</span>
                </div>
              </div>
              <div class="novel-stats">
                <div>👁 {{ formatNumber(item.view_count) }}</div>
                <div>❤️ {{ item.like_count }}</div>
              </div>
            </div>
            <el-empty v-if="ranking.length === 0" description="暂无数据" />
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>📊 阅读进度</span>
              <el-select v-model="selectedNovelId" placeholder="选择小说" clearable size="small" style="width: 200px" @change="loadProgress">
                <el-option v-for="n in novelOptions" :key="n.id" :label="n.title" :value="n.id" />
              </el-select>
            </div>
          </template>
          <el-table :data="progressList" size="small" max-height="400">
            <el-table-column prop="user_nickname" label="用户" width="100" />
            <el-table-column prop="novel_title" label="小说" min-width="120" show-overflow-tooltip />
            <el-table-column label="进度" width="100">
              <template #default="{ row }">
                第{{ row.chapter_num }}章
              </template>
            </el-table-column>
            <el-table-column label="位置" width="80">
              <template #default="{ row }">
                {{ row.scroll_position > 0 ? row.scroll_position + '%' : (row.audio_position > 0 ? formatTime(row.audio_position) : '-') }}
              </template>
            </el-table-column>
            <el-table-column prop="updated_at" label="更新时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.updated_at) }}
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            v-model:current-page="progressPage"
            :total="progressTotal"
            :page-size="20"
            layout="total, prev, pager, next"
            @current-change="loadProgress"
            style="margin-top: 12px; justify-content: flex-end"
            small
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 章节分析 -->
    <el-card shadow="never" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>📈 章节阅读分析</span>
          <el-select v-model="analysisNovelId" placeholder="选择小说查看章节数据" size="small" style="width: 250px" @change="loadChapterStats">
            <el-option v-for="n in novelOptions" :key="n.id" :label="n.title" :value="n.id" />
          </el-select>
        </div>
      </template>
      
      <div v-if="chapterStats.length > 0" class="chapter-analysis">
        <div class="analysis-header">
          <span>{{ analysisNovelTitle }} - 共{{ chapterStats.length }}章</span>
        </div>
        <div class="chapter-bars">
          <div v-for="c in chapterStats" :key="c.chapter_id" class="chapter-bar-item">
            <div class="chapter-label">
              <span class="chapter-num">{{ c.chapter_num }}</span>
              <span class="chapter-title">{{ c.title }}</span>
              <el-tag v-if="!c.is_free" size="small" type="warning">付费</el-tag>
            </div>
            <div class="bar-container">
              <div class="bar" :style="{ width: getBarWidth(c.reader_count) + '%' }"></div>
              <span class="bar-value">{{ c.reader_count }}人</span>
            </div>
          </div>
        </div>
      </div>
      <el-empty v-else description="选择小说查看章节阅读数据" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const stats = reactive({
  total_novels: 0,
  total_chapters: 0,
  total_views: 0,
  total_likes: 0,
  reading_users: 0,
  today_readers: 0,
  text_novels: 0,
  audio_novels: 0
})

const rankType = ref('views')
const ranking = ref([])
const novelOptions = ref([])
const selectedNovelId = ref(null)
const progressList = ref([])
const progressPage = ref(1)
const progressTotal = ref(0)
const analysisNovelId = ref(null)
const analysisNovelTitle = ref('')
const chapterStats = ref([])
const maxReaderCount = ref(1)

onMounted(() => {
  loadStats()
  loadRanking()
  loadNovelOptions()
  loadProgress()
})

async function loadStats() {
  try {
    const { data } = await api.get('/admin/gallery-novel/novel/statistics')
    Object.assign(stats, data)
  } catch (e) {
    console.error('加载统计失败', e)
  }
}

async function loadRanking() {
  try {
    const { data } = await api.get('/admin/gallery-novel/novel/ranking', {
      params: { rank_type: rankType.value, limit: 10 }
    })
    ranking.value = data
  } catch (e) {
    console.error('加载排行失败', e)
  }
}

async function loadNovelOptions() {
  try {
    const { data } = await api.get('/admin/gallery-novel/novels', { params: { page_size: 100 } })
    novelOptions.value = data.items || []
  } catch (e) {
    console.error('加载小说列表失败', e)
  }
}

async function loadProgress() {
  try {
    const params = { page: progressPage.value, page_size: 20 }
    if (selectedNovelId.value) params.novel_id = selectedNovelId.value
    const { data } = await api.get('/admin/gallery-novel/novel/reading-progress', { params })
    progressList.value = data.items || []
    progressTotal.value = data.total || 0
  } catch (e) {
    console.error('加载进度失败', e)
  }
}

async function loadChapterStats() {
  if (!analysisNovelId.value) {
    chapterStats.value = []
    return
  }
  try {
    const { data } = await api.get(`/admin/gallery-novel/novel/chapter-stats/${analysisNovelId.value}`)
    chapterStats.value = data.chapters || []
    analysisNovelTitle.value = data.novel_title
    maxReaderCount.value = Math.max(...chapterStats.value.map(c => c.reader_count), 1)
  } catch (e) {
    ElMessage.error('加载章节统计失败')
  }
}

function getBarWidth(count) {
  return Math.min(100, (count / maxReaderCount.value) * 100)
}

function formatNumber(num) {
  if (!num) return '0'
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num.toString()
}

function formatTime(seconds) {
  if (!seconds) return '-'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
  })
}
</script>

<style lang="scss" scoped>
.novel-statistics {
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 20px;
  }
  
  .stat-card {
    background: #fff;
    border-radius: 12px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    position: relative;
    overflow: hidden;
    
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 4px;
      height: 100%;
    }
    
    &.purple::before { background: linear-gradient(180deg, #667eea, #764ba2); }
    &.blue::before { background: linear-gradient(180deg, #4facfe, #00f2fe); }
    &.green::before { background: linear-gradient(180deg, #43e97b, #38f9d7); }
    &.orange::before { background: linear-gradient(180deg, #fa709a, #fee140); }
    
    .stat-icon {
      font-size: 36px;
      opacity: 0.9;
    }
    
    .stat-info {
      flex: 1;
    }
    
    .stat-value {
      font-size: 28px;
      font-weight: 600;
      color: #333;
    }
    
    .stat-label {
      font-size: 14px;
      color: #888;
      margin-top: 4px;
    }
    
    .stat-detail {
      position: absolute;
      bottom: 12px;
      right: 16px;
      font-size: 12px;
      color: #999;
      
      span {
        margin-left: 12px;
      }
    }
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .ranking-list {
    .ranking-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 0;
      border-bottom: 1px solid #f0f0f0;
      
      &:last-child { border-bottom: none; }
      
      .rank {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 600;
        background: #f0f0f0;
        color: #666;
        
        &.rank-1 { background: linear-gradient(135deg, #ffd700, #ffaa00); color: #fff; }
        &.rank-2 { background: linear-gradient(135deg, #c0c0c0, #a0a0a0); color: #fff; }
        &.rank-3 { background: linear-gradient(135deg, #cd7f32, #b87333); color: #fff; }
      }
      
      .novel-cover {
        width: 40px;
        height: 56px;
        border-radius: 4px;
        object-fit: cover;
      }
      
      .novel-info {
        flex: 1;
        min-width: 0;
        
        .novel-title {
          font-size: 14px;
          font-weight: 500;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .novel-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 4px;
          font-size: 12px;
          color: #999;
        }
      }
      
      .novel-stats {
        text-align: right;
        font-size: 12px;
        color: #666;
        
        div { margin-bottom: 2px; }
      }
    }
  }
  
  .chapter-analysis {
    .analysis-header {
      margin-bottom: 16px;
      font-size: 14px;
      color: #666;
    }
    
    .chapter-bars {
      max-height: 400px;
      overflow-y: auto;
    }
    
    .chapter-bar-item {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
      
      .chapter-label {
        width: 200px;
        display: flex;
        align-items: center;
        gap: 8px;
        
        .chapter-num {
          color: #999;
          font-size: 12px;
          min-width: 30px;
        }
        
        .chapter-title {
          flex: 1;
          font-size: 13px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
      
      .bar-container {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 8px;
        
        .bar {
          height: 20px;
          background: linear-gradient(90deg, #667eea, #764ba2);
          border-radius: 4px;
          min-width: 4px;
          transition: width 0.3s;
        }
        
        .bar-value {
          font-size: 12px;
          color: #666;
          min-width: 50px;
        }
      }
    }
  }
}
</style>
