<template>
  <div class="novel-manage">
    <!-- 数据统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_novels }}</div>
        <div class="stat-label">小说总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_chapters }}</div>
        <div class="stat-label">章节总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_views }}</div>
        <div class="stat-label">总浏览量</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.reading_users }}</div>
        <div class="stat-label">阅读用户</div>
      </div>
    </div>

    <!-- 分类管理 -->
    <el-card class="category-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>小说分类</span>
          <el-button type="primary" size="small" @click="showCategoryDialog()">
            <el-icon><Plus /></el-icon>添加分类
          </el-button>
        </div>
      </template>
      <el-table :data="categories" size="small">
        <el-table-column prop="name" label="分类名称" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.novel_type === 'text' ? 'primary' : 'success'" size="small">
              {{ row.novel_type === 'text' ? '文字' : '有声' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="novel_count" label="小说数" width="80" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showCategoryDialog(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="deleteCategory(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 小说列表 -->
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="filters">
            <el-select v-model="filters.novel_type" placeholder="类型" clearable style="width: 100px">
              <el-option label="文字" value="text" />
              <el-option label="有声" value="audio" />
            </el-select>
            <el-select v-model="filters.category_id" placeholder="选择分类" clearable style="width: 150px">
              <el-option v-for="c in filteredCategories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-select v-model="filters.status" placeholder="状态" clearable style="width: 100px">
              <el-option label="连载中" value="ongoing" />
              <el-option label="已完结" value="completed" />
            </el-select>
            <el-input v-model="filters.keyword" placeholder="搜索标题/作者" clearable style="width: 180px" @keyup.enter="loadNovels" />
            <el-button type="primary" @click="loadNovels">搜索</el-button>
          </div>
          <div class="header-actions">
            <el-button @click="showBatchImportDialog">批量导入</el-button>
            <el-button type="primary" @click="showNovelDialog()">
              <el-icon><Plus /></el-icon>添加小说
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="novels" v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />
        <el-table-column label="封面" width="80">
          <template #default="{ row }">
            <el-image :src="row.cover" style="width: 50px; height: 70px" fit="cover" />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="150">
          <template #default="{ row }">
            <div class="novel-title-cell">
              <span class="title">{{ row.title }}</span>
              <span class="author">{{ row.author || '佚名' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category_name" label="分类" width="100" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.novel_type === 'text' ? 'primary' : 'success'" size="small">
              {{ row.novel_type === 'text' ? '文字' : '有声' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="章节" width="100">
          <template #default="{ row }">
            <span>{{ row.chapter_count }}章</span>
            <el-tag v-if="row.status === 'completed'" type="success" size="small" style="margin-left: 4px">完结</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="数据" width="140">
          <template #default="{ row }">
            <div class="data-cell">
              <span>👁 {{ row.view_count || 0 }}</span>
              <span>❤️ {{ row.like_count || 0 }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="热门" width="70">
          <template #default="{ row }">
            <el-switch v-model="row.is_hot" size="small" @change="updateNovel(row, 'is_hot')" />
          </template>
        </el-table-column>
        <el-table-column label="推荐" width="70">
          <template #default="{ row }">
            <el-switch v-model="row.is_recommended" size="small" @change="updateNovel(row, 'is_recommended')" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showNovelDialog(row)">编辑</el-button>
            <el-button type="success" link size="small" @click="showChaptersDialog(row)">章节</el-button>
            <el-button type="danger" link size="small" @click="deleteNovel(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 批量操作 -->
      <div class="batch-actions" v-if="selectedNovels.length > 0">
        <span>已选 {{ selectedNovels.length }} 项</span>
        <el-button size="small" @click="batchSetHot(true)">设为热门</el-button>
        <el-button size="small" @click="batchSetHot(false)">取消热门</el-button>
        <el-button size="small" type="danger" @click="batchDelete">批量删除</el-button>
      </div>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadNovels"
        @size-change="loadNovels"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- 分类弹窗 -->
    <el-dialog v-model="categoryDialogVisible" :title="categoryForm.id ? '编辑分类' : '添加分类'" width="400px">
      <el-form :model="categoryForm" label-width="80px">
        <el-form-item label="分类名称" required>
          <el-input v-model="categoryForm.name" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="categoryForm.novel_type" style="width: 100%">
            <el-option label="文字小说" value="text" />
            <el-option label="有声小说" value="audio" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="categoryForm.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="categoryForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCategory">保存</el-button>
      </template>
    </el-dialog>

    <!-- 小说弹窗 -->
    <el-dialog v-model="novelDialogVisible" :title="novelForm.id ? '编辑小说' : '添加小说'" width="700px">
      <el-form :model="novelForm" label-width="80px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="标题" required>
              <el-input v-model="novelForm.title" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="作者">
              <el-input v-model="novelForm.author" placeholder="默认：佚名" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="类型" required>
              <el-select v-model="novelForm.novel_type" style="width: 100%">
                <el-option label="文字小说" value="text" />
                <el-option label="有声小说" value="audio" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类">
              <el-select v-model="novelForm.category_id" placeholder="选择分类" clearable style="width: 100%">
                <el-option v-for="c in novelFormCategories" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="封面" required>
          <div class="cover-upload">
            <el-upload
              class="cover-uploader"
              :action="uploadImageUrl"
              :headers="uploadHeaders"
              :data="{ subdir: 'novel' }"
              :show-file-list="false"
              :on-success="handleCoverSuccess"
              :before-upload="beforeImageUpload"
              accept="image/*"
            >
              <el-image v-if="novelForm.cover" :src="novelForm.cover" class="cover-preview" fit="cover" />
              <div v-else class="cover-placeholder">
                <el-icon><Plus /></el-icon>
                <span>上传封面</span>
              </div>
            </el-upload>
            <div class="cover-url-input">
              <el-input v-model="novelForm.cover" placeholder="或输入封面URL" clearable />
            </div>
          </div>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="状态">
              <el-select v-model="novelForm.status" style="width: 100%">
                <el-option label="连载中" value="ongoing" />
                <el-option label="已完结" value="completed" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="热门">
              <el-switch v-model="novelForm.is_hot" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="推荐">
              <el-switch v-model="novelForm.is_recommended" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="简介">
          <el-input v-model="novelForm.description" type="textarea" :rows="4" placeholder="小说简介..." />
        </el-form-item>

        <!-- 章节内容区域 -->
        <el-divider content-position="left">添加章节（可选）</el-divider>
        
        <!-- 有声小说：音频上传 -->
        <template v-if="novelForm.novel_type === 'audio'">
          <el-form-item label="章节标题">
            <el-input v-model="novelForm.first_chapter_title" placeholder="第1章 标题（可选）" />
          </el-form-item>
          <el-form-item label="上传音频">
            <div class="audio-upload-section">
              <el-upload
                class="audio-uploader"
                :action="uploadAudioUrl"
                :headers="uploadHeaders"
                :show-file-list="false"
                :on-success="handleFirstAudioSuccess"
                :before-upload="beforeAudioUpload"
                accept=".mp3,.wav,.ogg,.m4a,.aac"
              >
                <el-button type="primary" :loading="firstAudioUploading">
                  <el-icon><Upload /></el-icon>
                  {{ firstAudioUploading ? '上传中...' : '上传音频文件' }}
                </el-button>
              </el-upload>
              <el-input v-model="novelForm.first_chapter_audio" placeholder="或输入音频URL" style="margin-left: 12px; flex: 1" />
            </div>
            <div v-if="novelForm.first_chapter_audio" class="audio-preview">
              <audio :src="novelForm.first_chapter_audio" controls style="width: 100%; margin-top: 8px"></audio>
            </div>
          </el-form-item>
        </template>

        <!-- 文字小说：文字输入或文本上传 -->
        <template v-else>
          <el-form-item label="章节标题">
            <el-input v-model="novelForm.first_chapter_title" placeholder="第1章 标题（可选）" />
          </el-form-item>
          <el-form-item label="内容方式">
            <el-radio-group v-model="novelForm.content_input_type">
              <el-radio label="text">直接输入</el-radio>
              <el-radio label="file">上传TXT文件</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item v-if="novelForm.content_input_type === 'text'" label="章节内容">
            <el-input v-model="novelForm.first_chapter_content" type="textarea" :rows="8" placeholder="输入第一章内容..." />
            <div class="content-stats">字数: {{ (novelForm.first_chapter_content || '').length }}</div>
          </el-form-item>
          <el-form-item v-else label="上传文件">
            <el-upload
              drag
              :auto-upload="false"
              :limit="1"
              :file-list="novelForm.txt_file_list"
              @change="handleTxtFileChange"
              accept=".txt"
            >
              <el-icon class="el-icon--upload"><Upload /></el-icon>
              <div class="el-upload__text">拖拽TXT文件到此处，或<em>点击上传</em></div>
              <template #tip>
                <div class="el-upload__tip">支持TXT格式，将自动解析章节</div>
              </template>
            </el-upload>
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="novelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveNovel" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 章节管理弹窗 -->
    <el-dialog v-model="chaptersDialogVisible" :title="'章节管理 - ' + (currentNovel?.title || '')" width="900px">
      <div class="chapters-toolbar">
        <div class="toolbar-left">
          <el-button type="primary" size="small" @click="showChapterDialog()">
            <el-icon><Plus /></el-icon>添加章节
          </el-button>
          <el-button size="small" @click="showBatchChapterDialog">批量添加</el-button>
        </div>
        <div class="toolbar-right">
          <el-button size="small" @click="batchSetFree(true)" :disabled="selectedChapters.length === 0">
            设为免费
          </el-button>
          <el-button size="small" @click="batchSetFree(false)" :disabled="selectedChapters.length === 0">
            设为付费
          </el-button>
        </div>
      </div>
      
      <el-table :data="chapters" size="small" max-height="450" @selection-change="handleChapterSelection">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="chapter_num" label="章节" width="70" />
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column label="内容" width="120">
          <template #default="{ row }">
            <span v-if="currentNovel?.novel_type === 'audio'">
              {{ row.audio_url ? '✓ 有音频' : '✗ 无音频' }}
            </span>
            <span v-else>{{ row.content_length > 0 ? row.content_length + '字' : '无内容' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="免费" width="80">
          <template #default="{ row }">
            <el-switch v-model="row.is_free" size="small" @change="updateChapterFree(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showChapterDialog(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="deleteChapter(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="chapters-footer">
        <span>共 {{ chapters.length }} 章</span>
        <span>免费章节: {{ chapters.filter(c => c.is_free).length }} 章</span>
      </div>
    </el-dialog>

    <!-- 章节编辑弹窗 -->
    <el-dialog v-model="chapterDialogVisible" :title="chapterForm.id ? '编辑章节' : '添加章节'" width="750px">
      <el-form :model="chapterForm" label-width="80px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="章节号" required>
              <el-input-number v-model="chapterForm.chapter_num" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="免费">
              <el-switch v-model="chapterForm.is_free" />
              <span class="tip-text">{{ chapterForm.is_free ? '所有用户可读' : '仅VIP可读' }}</span>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="标题" required>
          <el-input v-model="chapterForm.title" placeholder="章节标题" />
        </el-form-item>

        <!-- 有声小说：音频上传 -->
        <el-form-item v-if="currentNovel?.novel_type === 'audio'" label="音频">
          <div class="audio-upload">
            <el-upload
              class="audio-uploader"
              :action="uploadAudioUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :on-success="handleAudioSuccess"
              :before-upload="beforeAudioUpload"
              accept=".mp3,.wav,.ogg,.m4a,.aac"
            >
              <el-button type="primary" :loading="audioUploading">
                <el-icon><Upload /></el-icon>
                {{ audioUploading ? '上传中...' : '上传音频' }}
              </el-button>
            </el-upload>
            <el-input v-model="chapterForm.audio_url" placeholder="或输入音频URL" style="margin-left: 12px; flex: 1" />
          </div>
          <div v-if="chapterForm.audio_url" class="audio-preview">
            <audio :src="chapterForm.audio_url" controls style="width: 100%; margin-top: 8px"></audio>
          </div>
        </el-form-item>

        <!-- 文字小说：内容输入 -->
        <el-form-item v-else label="内容">
          <el-input v-model="chapterForm.content" type="textarea" :rows="15" placeholder="输入章节内容..." />
          <div class="content-stats">字数: {{ (chapterForm.content || '').length }}</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="chapterDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveChapter" :loading="savingChapter">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量添加章节弹窗 -->
    <el-dialog v-model="batchChapterDialogVisible" title="批量添加章节" width="700px">
      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        <template #title>
          格式说明：每章用分隔符隔开，第一行为章节标题，后面为内容
        </template>
      </el-alert>
      <el-form label-width="100px">
        <el-form-item label="起始章节号">
          <el-input-number v-model="batchChapterForm.start_num" :min="1" />
        </el-form-item>
        <el-form-item label="章节分隔符">
          <el-input v-model="batchChapterForm.separator" placeholder="默认: ====" style="width: 200px" />
        </el-form-item>
        <el-form-item label="默认免费">
          <el-switch v-model="batchChapterForm.is_free" />
        </el-form-item>
        <el-form-item label="章节内容">
          <el-input 
            v-model="batchChapterForm.content" 
            type="textarea" 
            :rows="15" 
            placeholder="第一章 开始&#10;章节内容...&#10;====&#10;第二章 继续&#10;章节内容..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchChapterDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveBatchChapters" :loading="savingBatch">
          批量添加
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量导入小说弹窗 -->
    <el-dialog v-model="batchImportDialogVisible" title="智能导入TXT小说" width="900px">
      <el-steps :active="importStep" finish-status="success" style="margin-bottom: 20px">
        <el-step title="上传文件" />
        <el-step title="预览解析" />
        <el-step title="确认导入" />
      </el-steps>

      <!-- 步骤1：上传文件 -->
      <div v-if="importStep === 0">
        <el-alert type="info" :closable="false" style="margin-bottom: 16px">
          <template #title>
            <div v-if="importForm.novel_type === 'text'">
              <div>支持智能识别TXT小说的标题、作者、简介和章节</div>
              <div style="margin-top: 4px; font-size: 12px; color: #909399">
                识别规则：第一行为标题，"作者："开头为作者，"简介："后为简介，"第X章"为章节分隔
              </div>
            </div>
            <div v-else>
              <div>有声小说批量导入：上传音频文件自动创建章节</div>
              <div style="margin-top: 4px; font-size: 12px; color: #909399">
                音频文件名格式：001_第一章标题.mp3 或 第1章_标题.mp3（按文件名排序）
              </div>
            </div>
          </template>
        </el-alert>
        <el-form label-width="80px">
          <el-form-item label="小说类型">
            <el-select v-model="importForm.novel_type" style="width: 200px" @change="handleNovelTypeChange">
              <el-option label="文字小说" value="text" />
              <el-option label="有声小说" value="audio" />
            </el-select>
          </el-form-item>
          <el-form-item label="分类">
            <el-select v-model="importForm.category_id" placeholder="选择分类" clearable style="width: 200px">
              <el-option v-for="c in importCategories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="免费章节">
            <el-input-number v-model="importForm.freeChapters" :min="0" :max="100" />
            <span style="margin-left: 8px; color: #909399">前N章设为免费</span>
          </el-form-item>
          
          <!-- 有声小说额外字段 -->
          <template v-if="importForm.novel_type === 'audio'">
            <el-form-item label="小说标题" required>
              <el-input v-model="importForm.audioNovelTitle" placeholder="请输入小说标题" style="width: 300px" />
            </el-form-item>
            <el-form-item label="作者">
              <el-input v-model="importForm.audioNovelAuthor" placeholder="佚名" style="width: 200px" />
            </el-form-item>
            <el-form-item label="简介">
              <el-input v-model="importForm.audioNovelDesc" type="textarea" :rows="2" placeholder="小说简介（可选）" />
            </el-form-item>
            <el-form-item label="封面">
              <div class="cover-upload-inline">
                <el-upload
                  class="cover-uploader-small"
                  :action="uploadImageUrl"
                  :headers="uploadHeaders"
                  :data="{ subdir: 'novel' }"
                  :show-file-list="false"
                  :on-success="handleImportCoverSuccess"
                  :before-upload="beforeImageUpload"
                  accept="image/*"
                >
                  <el-image v-if="importForm.audioNovelCover" :src="importForm.audioNovelCover" class="cover-preview-small" fit="cover" />
                  <div v-else class="cover-placeholder-small">
                    <el-icon><Plus /></el-icon>
                  </div>
                </el-upload>
                <el-input v-model="importForm.audioNovelCover" placeholder="或输入封面URL" style="flex: 1; margin-left: 12px" />
              </div>
            </el-form-item>
          </template>

          <el-form-item :label="importForm.novel_type === 'text' ? '上传TXT' : '上传音频'">
            <el-upload
              drag
              multiple
              :auto-upload="false"
              :file-list="importFiles"
              @change="handleImportFileChange"
              :accept="importForm.novel_type === 'text' ? '.txt' : '.mp3,.wav,.ogg,.m4a,.aac'"
            >
              <el-icon class="el-icon--upload"><Upload /></el-icon>
              <div class="el-upload__text">
                拖拽文件到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip" v-if="importForm.novel_type === 'text'">
                  支持多个TXT文件，每个文件为一本小说
                </div>
                <div class="el-upload__tip" v-else>
                  支持 mp3/wav/ogg/m4a/aac 格式，每个文件为一个章节
                </div>
              </template>
            </el-upload>
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤2：预览解析结果 -->
      <div v-else-if="importStep === 1">
        <div class="parse-results">
          <div v-for="(novel, idx) in parsedNovels" :key="idx" class="parsed-novel-card">
            <div class="novel-header">
              <el-tag type="primary" size="small">小说 {{ idx + 1 }}</el-tag>
              <el-button type="danger" link size="small" @click="removeParsedNovel(idx)">移除</el-button>
            </div>
            <el-form :model="novel" label-width="70px" size="small">
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="标题">
                    <el-input v-model="novel.title" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="作者">
                    <el-input v-model="novel.author" placeholder="佚名" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="简介">
                <el-input v-model="novel.description" type="textarea" :rows="2" />
              </el-form-item>
              <el-form-item label="章节">
                <div class="chapters-preview">
                  <el-tag 
                    v-for="(ch, ci) in novel.chapters.slice(0, 10)" 
                    :key="ci" 
                    size="small" 
                    :type="ci < importForm.freeChapters ? 'success' : 'info'"
                    style="margin: 2px"
                  >
                    {{ ch.title }}
                  </el-tag>
                  <el-tag v-if="novel.chapters.length > 10" size="small" type="warning">
                    +{{ novel.chapters.length - 10 }}章
                  </el-tag>
                </div>
                <div class="chapters-stats">
                  共 {{ novel.chapters.length }} 章，约 {{ formatWordCount(novel.totalWords) }} 字
                </div>
              </el-form-item>
            </el-form>
          </div>
          <div v-if="parsedNovels.length === 0" class="empty-parse">
            <el-empty description="暂无解析结果，请返回上传文件" />
          </div>
        </div>
      </div>

      <!-- 步骤3：导入进度 -->
      <div v-else-if="importStep === 2">
        <div class="import-progress">
          <el-progress :percentage="importProgress" :status="importStatus" />
          <div class="progress-text">{{ importProgressText }}</div>
          <div class="import-logs" v-if="importLogs.length">
            <div v-for="(log, i) in importLogs" :key="i" :class="['log-item', log.type]">
              <el-icon v-if="log.type === 'success'"><CircleCheck /></el-icon>
              <el-icon v-else-if="log.type === 'error'"><CircleClose /></el-icon>
              <el-icon v-else><Loading /></el-icon>
              <span>{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="batchImportDialogVisible = false" v-if="importStep !== 2 || importStatus">取消</el-button>
        <el-button @click="importStep--" v-if="importStep === 1">上一步</el-button>
        <el-button type="primary" @click="parseImportFiles" v-if="importStep === 0" :disabled="importFiles.length === 0">
          解析文件 ({{ importFiles.length }}个)
        </el-button>
        <el-button type="primary" @click="confirmImport" v-if="importStep === 1" :disabled="parsedNovels.length === 0">
          确认导入 ({{ parsedNovels.length }}本)
        </el-button>
        <el-button type="primary" @click="finishImport" v-if="importStep === 2 && importStatus">
          完成
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, CircleCheck, CircleClose, Loading } from '@element-plus/icons-vue'
import api from '@/utils/api'

const loading = ref(false)
const saving = ref(false)
const savingChapter = ref(false)
const savingBatch = ref(false)
const importing = ref(false)
const categories = ref([])
const novels = ref([])
const chapters = ref([])
const currentNovel = ref(null)
const selectedNovels = ref([])
const selectedChapters = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ category_id: null, novel_type: null, status: null, keyword: '' })

// 统计数据
const stats = reactive({
  total_novels: 0,
  total_chapters: 0,
  total_views: 0,
  reading_users: 0
})

const categoryDialogVisible = ref(false)
const categoryForm = reactive({ id: null, name: '', novel_type: 'text', sort_order: 0, is_active: true })

const novelDialogVisible = ref(false)
const novelForm = reactive({
  id: null, category_id: null, title: '', author: '', cover: '',
  description: '', novel_type: 'text', status: 'ongoing', is_hot: false, is_recommended: false,
  // 章节相关
  first_chapter_title: '',
  first_chapter_content: '',
  first_chapter_audio: '',
  content_input_type: 'text',
  txt_file_list: []
})

const chaptersDialogVisible = ref(false)
const chapterDialogVisible = ref(false)
const chapterForm = reactive({
  id: null, chapter_num: 1, title: '', content: '', audio_url: '', is_free: true
})

const batchChapterDialogVisible = ref(false)
const batchChapterForm = reactive({
  start_num: 1, separator: '====', is_free: true, content: ''
})

const batchImportDialogVisible = ref(false)
const importForm = reactive({ 
  novel_type: 'text', 
  category_id: null, 
  freeChapters: 3,
  // 有声小说字段
  audioNovelTitle: '',
  audioNovelAuthor: '',
  audioNovelDesc: '',
  audioNovelCover: ''
})
const importFiles = ref([])
const importStep = ref(0)
const parsedNovels = ref([])
const importProgress = ref(0)
const importStatus = ref('')
const importProgressText = ref('')
const importLogs = ref([])

const audioUploading = ref(false)
const firstAudioUploading = ref(false)

// 上传配置
const uploadImageUrl = computed(() => `${api.defaults.baseURL}/admin/gallery-novel/upload/image`)
const uploadAudioUrl = computed(() => `${api.defaults.baseURL}/admin/gallery-novel/upload/audio`)
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${localStorage.getItem('token')}` }))

const filteredCategories = computed(() => {
  if (!filters.novel_type) return categories.value
  return categories.value.filter(c => c.novel_type === filters.novel_type)
})

const novelFormCategories = computed(() => {
  return categories.value.filter(c => c.novel_type === novelForm.novel_type)
})

const importCategories = computed(() => {
  return categories.value.filter(c => c.novel_type === importForm.novel_type)
})

onMounted(() => {
  loadCategories()
  loadNovels()
  loadStats()
})

async function loadStats() {
  try {
    // 尝试使用统计API
    const { data } = await api.get('/admin/gallery-novel/novel/statistics')
    stats.total_novels = data.total_novels || 0
    stats.total_chapters = data.total_chapters || 0
    stats.total_views = data.total_views || 0
    stats.reading_users = data.reading_users || 0
  } catch (e) {
    // 如果统计API不可用，从列表计算
    try {
      const { data } = await api.get('/admin/gallery-novel/novels', { params: { page: 1, page_size: 100 } })
      stats.total_novels = data.total || 0
      stats.total_chapters = data.items?.reduce((sum, n) => sum + (n.chapter_count || 0), 0) || 0
      stats.total_views = data.items?.reduce((sum, n) => sum + (n.view_count || 0), 0) || 0
      stats.reading_users = Math.floor(stats.total_views / 10)
    } catch (e2) {
      console.error('加载统计失败', e2)
    }
  }
}

async function loadCategories() {
  try {
    const { data } = await api.get('/admin/gallery-novel/novel/categories')
    categories.value = data
  } catch (e) {
    ElMessage.error('加载分类失败')
  }
}

async function loadNovels() {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.pageSize, ...filters }
    Object.keys(params).forEach(k => { if (!params[k]) delete params[k] })
    const { data } = await api.get('/admin/gallery-novel/novels', { params })
    novels.value = data.items
    pagination.total = data.total
  } catch (e) {
    ElMessage.error('加载小说失败')
  } finally {
    loading.value = false
  }
}

function handleSelectionChange(selection) {
  selectedNovels.value = selection
}

function handleChapterSelection(selection) {
  selectedChapters.value = selection
}

// 分类管理
function showCategoryDialog(row = null) {
  if (row) {
    Object.assign(categoryForm, row)
  } else {
    Object.assign(categoryForm, { id: null, name: '', novel_type: 'text', sort_order: 0, is_active: true })
  }
  categoryDialogVisible.value = true
}

async function saveCategory() {
  if (!categoryForm.name) return ElMessage.warning('请输入分类名称')
  try {
    if (categoryForm.id) {
      await api.put(`/admin/gallery-novel/novel/categories/${categoryForm.id}`, categoryForm)
    } else {
      await api.post('/admin/gallery-novel/novel/categories', categoryForm)
    }
    ElMessage.success('保存成功')
    categoryDialogVisible.value = false
    loadCategories()
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function deleteCategory(row) {
  await ElMessageBox.confirm('确定删除该分类？', '提示')
  try {
    await api.delete(`/admin/gallery-novel/novel/categories/${row.id}`)
    ElMessage.success('删除成功')
    loadCategories()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

// 小说管理
function showNovelDialog(row = null) {
  if (row) {
    Object.assign(novelForm, row)
    // 编辑时清空章节字段
    novelForm.first_chapter_title = ''
    novelForm.first_chapter_content = ''
    novelForm.first_chapter_audio = ''
    novelForm.content_input_type = 'text'
    novelForm.txt_file_list = []
  } else {
    Object.assign(novelForm, {
      id: null, category_id: null, title: '', author: '', cover: '',
      description: '', novel_type: 'text', status: 'ongoing', is_hot: false, is_recommended: false,
      first_chapter_title: '',
      first_chapter_content: '',
      first_chapter_audio: '',
      content_input_type: 'text',
      txt_file_list: []
    })
  }
  novelDialogVisible.value = true
}

function beforeImageUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isImage) { ElMessage.error('只能上传图片文件'); return false }
  if (!isLt10M) { ElMessage.error('图片大小不能超过 10MB'); return false }
  return true
}

function handleCoverSuccess(response) {
  if (response.url) {
    novelForm.cover = response.url
    ElMessage.success('封面上传成功')
  } else {
    ElMessage.error('上传失败')
  }
}

// 第一章音频上传
function handleFirstAudioSuccess(response) {
  firstAudioUploading.value = false
  if (response.url) {
    novelForm.first_chapter_audio = response.url
    ElMessage.success('音频上传成功')
  } else {
    ElMessage.error('上传失败')
  }
}

// TXT文件选择
function handleTxtFileChange(file, fileList) {
  novelForm.txt_file_list = fileList.slice(-1) // 只保留最后一个
}

async function saveNovel() {
  if (!novelForm.title || !novelForm.cover) return ElMessage.warning('请填写标题和封面')
  saving.value = true
  try {
    let novelId = novelForm.id
    
    if (novelForm.id) {
      await api.put(`/admin/gallery-novel/novels/${novelForm.id}`, novelForm)
    } else {
      const { data } = await api.post('/admin/gallery-novel/novels', novelForm)
      novelId = data.id
    }
    
    // 如果是新建小说且有章节内容，创建第一章
    if (!novelForm.id && novelId) {
      let hasChapter = false
      let chapterData = {
        chapter_num: 1,
        title: novelForm.first_chapter_title || '第1章',
        is_free: true
      }
      
      if (novelForm.novel_type === 'audio' && novelForm.first_chapter_audio) {
        // 有声小说
        chapterData.audio_url = novelForm.first_chapter_audio
        chapterData.content = ''
        hasChapter = true
      } else if (novelForm.novel_type === 'text') {
        if (novelForm.content_input_type === 'text' && novelForm.first_chapter_content) {
          // 直接输入文字
          chapterData.content = novelForm.first_chapter_content
          hasChapter = true
        } else if (novelForm.content_input_type === 'file' && novelForm.txt_file_list.length > 0) {
          // 上传TXT文件，解析并批量创建章节
          try {
            const file = novelForm.txt_file_list[0].raw
            const text = await file.text()
            const parsed = parseNovelText(text, file.name)
            
            // 批量创建章节
            for (let i = 0; i < parsed.chapters.length; i++) {
              const ch = parsed.chapters[i]
              await api.post(`/admin/gallery-novel/novels/${novelId}/chapters`, {
                chapter_num: ch.chapter_num,
                title: ch.title,
                content: ch.content,
                is_free: i < 3 // 前3章免费
              })
            }
            ElMessage.success(`成功导入 ${parsed.chapters.length} 章`)
          } catch (e) {
            console.error('解析TXT失败', e)
            ElMessage.warning('TXT文件解析失败')
          }
          hasChapter = false // 已批量创建，不需要再创建单章
        }
      }
      
      // 创建单章
      if (hasChapter) {
        try {
          await api.post(`/admin/gallery-novel/novels/${novelId}/chapters`, chapterData)
        } catch (e) {
          console.error('创建章节失败', e)
        }
      }
    }
    
    ElMessage.success('保存成功')
    novelDialogVisible.value = false
    loadNovels()
    loadStats()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function updateNovel(row, field) {
  try {
    await api.put(`/admin/gallery-novel/novels/${row.id}`, { [field]: row[field] })
  } catch (e) {
    ElMessage.error('更新失败')
    row[field] = !row[field]
  }
}

async function deleteNovel(row) {
  await ElMessageBox.confirm('确定删除该小说及所有章节？', '提示', { type: 'warning' })
  try {
    await api.delete(`/admin/gallery-novel/novels/${row.id}`)
    ElMessage.success('删除成功')
    loadNovels()
    loadStats()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function batchSetHot(isHot) {
  try {
    for (const novel of selectedNovels.value) {
      await api.put(`/admin/gallery-novel/novels/${novel.id}`, { is_hot: isHot })
    }
    ElMessage.success('批量更新成功')
    loadNovels()
  } catch (e) {
    ElMessage.error('批量更新失败')
  }
}

async function batchDelete() {
  await ElMessageBox.confirm(`确定删除选中的 ${selectedNovels.value.length} 本小说？`, '提示', { type: 'warning' })
  try {
    for (const novel of selectedNovels.value) {
      await api.delete(`/admin/gallery-novel/novels/${novel.id}`)
    }
    ElMessage.success('批量删除成功')
    selectedNovels.value = []
    loadNovels()
    loadStats()
  } catch (e) {
    ElMessage.error('批量删除失败')
  }
}

// 章节管理
async function showChaptersDialog(novel) {
  currentNovel.value = novel
  selectedChapters.value = []
  try {
    const { data } = await api.get(`/admin/gallery-novel/novels/${novel.id}/chapters`)
    chapters.value = data
    chaptersDialogVisible.value = true
  } catch (e) {
    ElMessage.error('加载章节失败')
  }
}

function showChapterDialog(row = null) {
  if (row) {
    Object.assign(chapterForm, row)
  } else {
    const maxNum = chapters.value.length > 0 ? Math.max(...chapters.value.map(c => c.chapter_num)) : 0
    Object.assign(chapterForm, { id: null, chapter_num: maxNum + 1, title: '', content: '', audio_url: '', is_free: true })
  }
  chapterDialogVisible.value = true
}

function beforeAudioUpload(file) {
  const allowedExts = ['.mp3', '.wav', '.ogg', '.m4a', '.aac']
  const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
  if (!allowedExts.includes(ext)) { ElMessage.error('只支持 mp3/wav/ogg/m4a/aac 格式'); return false }
  if (file.size / 1024 / 1024 > 100) { ElMessage.error('音频文件不能超过 100MB'); return false }
  audioUploading.value = true
  return true
}

function handleAudioSuccess(response) {
  audioUploading.value = false
  if (response.url) {
    chapterForm.audio_url = response.url
    ElMessage.success('音频上传成功')
  } else {
    ElMessage.error('上传失败')
  }
}

async function saveChapter() {
  if (!chapterForm.title) return ElMessage.warning('请输入章节标题')
  savingChapter.value = true
  try {
    if (chapterForm.id) {
      await api.put(`/admin/gallery-novel/novels/${currentNovel.value.id}/chapters/${chapterForm.id}`, chapterForm)
    } else {
      await api.post(`/admin/gallery-novel/novels/${currentNovel.value.id}/chapters`, chapterForm)
    }
    ElMessage.success('保存成功')
    chapterDialogVisible.value = false
    showChaptersDialog(currentNovel.value)
    loadNovels()
    loadStats()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    savingChapter.value = false
  }
}

async function updateChapterFree(row) {
  try {
    await api.put(`/admin/gallery-novel/novels/${currentNovel.value.id}/chapters/${row.id}`, { is_free: row.is_free })
  } catch (e) {
    ElMessage.error('更新失败')
    row.is_free = !row.is_free
  }
}

async function deleteChapter(row) {
  await ElMessageBox.confirm('确定删除该章节？', '提示')
  try {
    await api.delete(`/admin/gallery-novel/novels/${currentNovel.value.id}/chapters/${row.id}`)
    ElMessage.success('删除成功')
    showChaptersDialog(currentNovel.value)
    loadNovels()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function batchSetFree(isFree) {
  try {
    for (const chapter of selectedChapters.value) {
      await api.put(`/admin/gallery-novel/novels/${currentNovel.value.id}/chapters/${chapter.id}`, { is_free: isFree })
    }
    ElMessage.success('批量更新成功')
    showChaptersDialog(currentNovel.value)
  } catch (e) {
    ElMessage.error('批量更新失败')
  }
}

// 批量添加章节
function showBatchChapterDialog() {
  const maxNum = chapters.value.length > 0 ? Math.max(...chapters.value.map(c => c.chapter_num)) : 0
  Object.assign(batchChapterForm, { start_num: maxNum + 1, separator: '====', is_free: true, content: '' })
  batchChapterDialogVisible.value = true
}

async function saveBatchChapters() {
  if (!batchChapterForm.content.trim()) return ElMessage.warning('请输入章节内容')
  
  const separator = batchChapterForm.separator || '===='
  const parts = batchChapterForm.content.split(separator).filter(p => p.trim())
  
  if (parts.length === 0) return ElMessage.warning('未识别到章节内容')
  
  savingBatch.value = true
  let successCount = 0
  
  try {
    for (let i = 0; i < parts.length; i++) {
      const lines = parts[i].trim().split('\n')
      const title = lines[0]?.trim() || `第${batchChapterForm.start_num + i}章`
      const content = lines.slice(1).join('\n').trim()
      
      await api.post(`/admin/gallery-novel/novels/${currentNovel.value.id}/chapters`, {
        chapter_num: batchChapterForm.start_num + i,
        title,
        content,
        is_free: batchChapterForm.is_free
      })
      successCount++
    }
    
    ElMessage.success(`成功添加 ${successCount} 章`)
    batchChapterDialogVisible.value = false
    showChaptersDialog(currentNovel.value)
    loadNovels()
    loadStats()
  } catch (e) {
    ElMessage.error(`添加失败，已成功 ${successCount} 章`)
  } finally {
    savingBatch.value = false
  }
}

// 批量导入小说
function showBatchImportDialog() {
  importFiles.value = []
  importStep.value = 0
  parsedNovels.value = []
  importProgress.value = 0
  importStatus.value = ''
  importProgressText.value = ''
  importLogs.value = []
  // 重置有声小说字段
  importForm.audioNovelTitle = ''
  importForm.audioNovelAuthor = ''
  importForm.audioNovelDesc = ''
  importForm.audioNovelCover = ''
  batchImportDialogVisible.value = true
}

function handleNovelTypeChange() {
  importFiles.value = []
}

function handleImportFileChange(file, fileList) {
  importFiles.value = fileList
}

function handleImportCoverSuccess(response) {
  if (response.url) {
    importForm.audioNovelCover = response.url
    ElMessage.success('封面上传成功')
  }
}

// 智能解析文件
async function parseImportFiles() {
  if (importForm.novel_type === 'text') {
    await parseTextNovels()
  } else {
    await parseAudioNovels()
  }
}

// 解析文字小说TXT文件
async function parseTextNovels() {
  parsedNovels.value = []
  
  for (const fileItem of importFiles.value) {
    try {
      const file = fileItem.raw
      const text = await file.text()
      const parsed = parseNovelText(text, file.name)
      parsedNovels.value.push(parsed)
    } catch (e) {
      console.error('解析文件失败:', fileItem.name, e)
      ElMessage.warning(`解析 ${fileItem.name} 失败`)
    }
  }
  
  if (parsedNovels.value.length > 0) {
    importStep.value = 1
  }
}

// 解析有声小说音频文件
async function parseAudioNovels() {
  if (!importForm.audioNovelTitle) {
    ElMessage.warning('请输入小说标题')
    return
  }
  
  // 按文件名排序
  const sortedFiles = [...importFiles.value].sort((a, b) => {
    return a.name.localeCompare(b.name, 'zh-CN', { numeric: true })
  })
  
  const chapters = sortedFiles.map((fileItem, idx) => {
    const filename = fileItem.name
    // 从文件名提取章节标题
    const title = extractChapterTitle(filename, idx + 1)
    return {
      chapter_num: idx + 1,
      title,
      file: fileItem.raw,
      filename,
      audio_url: '' // 上传后填充
    }
  })
  
  parsedNovels.value = [{
    title: importForm.audioNovelTitle,
    author: importForm.audioNovelAuthor || '佚名',
    description: importForm.audioNovelDesc,
    cover: importForm.audioNovelCover,
    chapters,
    totalWords: 0,
    isAudio: true
  }]
  
  importStep.value = 1
}

// 从音频文件名提取章节标题
function extractChapterTitle(filename, defaultNum) {
  // 去掉扩展名
  let name = filename.replace(/\.(mp3|wav|ogg|m4a|aac)$/i, '')
  
  // 尝试匹配各种格式
  // 001_第一章标题 -> 第一章标题
  // 第1章_标题 -> 第1章_标题
  // 01.标题 -> 标题
  
  // 去掉开头的数字序号
  name = name.replace(/^\d+[._\-\s]*/, '')
  
  // 如果还有内容，返回处理后的名称
  if (name.trim()) {
    return name.trim()
  }
  
  // 否则返回默认章节名
  return `第${defaultNum}章`
}

// 解析小说文本内容
function parseNovelText(text, filename) {
  const lines = text.split(/\r?\n/)
  let title = filename.replace(/\.txt$/i, '')
  let author = '佚名'
  let description = ''
  const chapters = []
  
  let currentChapter = null
  let contentStartLine = 0
  let inDescription = false
  let descriptionLines = []
  
  // 章节标题正则：第X章、第X回、第X节、Chapter X 等
  const chapterRegex = /^(第[零一二三四五六七八九十百千万\d]+[章回节卷部集篇]|Chapter\s*\d+|卷[零一二三四五六七八九十百千万\d]+|序章|序言|楔子|尾声|番外|后记)/i
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    
    // 跳过空行（在内容开始前）
    if (!line && !currentChapter) continue
    
    // 识别标题（第一个非空行，且不是作者/简介行）
    if (i < 10 && !currentChapter && !line.startsWith('作者') && !line.startsWith('简介') && 
        !line.startsWith('内容简介') && !chapterRegex.test(line) && contentStartLine === 0) {
      if (!title || title === filename.replace(/\.txt$/i, '')) {
        title = line.replace(/^《|》$/g, '').trim()
      }
      contentStartLine = i + 1
      continue
    }
    
    // 识别作者
    if (line.match(/^作者[：:]\s*(.+)$/)) {
      author = line.replace(/^作者[：:]\s*/, '').trim()
      continue
    }
    
    // 识别简介开始
    if (line.match(/^(简介|内容简介|作品简介)[：:]?\s*$/i)) {
      inDescription = true
      continue
    }
    
    // 简介内容（直到遇到章节标题）
    if (inDescription) {
      if (chapterRegex.test(line)) {
        inDescription = false
        description = descriptionLines.join('\n').trim()
      } else {
        descriptionLines.push(line)
        continue
      }
    }
    
    // 识别章节标题
    if (chapterRegex.test(line)) {
      // 保存上一章
      if (currentChapter) {
        currentChapter.content = currentChapter.contentLines.join('\n').trim()
        currentChapter.wordCount = currentChapter.content.length
        delete currentChapter.contentLines
        chapters.push(currentChapter)
      }
      
      // 开始新章节
      currentChapter = {
        chapter_num: chapters.length + 1,
        title: line,
        contentLines: [],
        content: '',
        wordCount: 0
      }
      continue
    }
    
    // 章节内容
    if (currentChapter) {
      currentChapter.contentLines.push(line)
    }
  }
  
  // 保存最后一章
  if (currentChapter) {
    currentChapter.content = currentChapter.contentLines.join('\n').trim()
    currentChapter.wordCount = currentChapter.content.length
    delete currentChapter.contentLines
    chapters.push(currentChapter)
  }
  
  // 如果没有识别到章节，把整个内容作为一章
  if (chapters.length === 0 && text.trim()) {
    const contentText = lines.slice(contentStartLine).join('\n').trim()
    if (contentText) {
      chapters.push({
        chapter_num: 1,
        title: '第一章',
        content: contentText,
        wordCount: contentText.length
      })
    }
  }
  
  // 如果没有简介，取第一章前200字
  if (!description && chapters.length > 0) {
    description = chapters[0].content.substring(0, 200) + '...'
  }
  
  const totalWords = chapters.reduce((sum, ch) => sum + ch.wordCount, 0)
  
  return { title, author, description, chapters, totalWords }
}

function removeParsedNovel(idx) {
  parsedNovels.value.splice(idx, 1)
}

function formatWordCount(count) {
  if (count >= 10000) {
    return (count / 10000).toFixed(1) + '万'
  }
  return count
}

// 确认导入
async function confirmImport() {
  importStep.value = 2
  importProgress.value = 0
  importStatus.value = ''
  importLogs.value = []
  
  const total = parsedNovels.value.length
  let successCount = 0
  
  for (let i = 0; i < parsedNovels.value.length; i++) {
    const novel = parsedNovels.value[i]
    importProgressText.value = `正在导入: ${novel.title} (${i + 1}/${total})`
    
    try {
      // 创建小说
      importLogs.value.push({ type: 'info', message: `创建小说: ${novel.title}` })
      
      const { data: createdNovel } = await api.post('/admin/gallery-novel/novels', {
        title: novel.title,
        author: novel.author || '佚名',
        description: novel.description,
        novel_type: importForm.novel_type,
        category_id: importForm.category_id,
        cover: novel.cover || '/images/default-novel-cover.webp',
        status: 'ongoing'
      })
      
      // 导入章节
      for (let j = 0; j < novel.chapters.length; j++) {
        const chapter = novel.chapters[j]
        
        // 有声小说需要先上传音频
        if (novel.isAudio && chapter.file) {
          importLogs.value.push({ type: 'info', message: `上传音频: ${chapter.filename}` })
          
          const formData = new FormData()
          formData.append('file', chapter.file)
          
          try {
            const uploadRes = await api.post('/admin/gallery-novel/upload/audio', formData, {
              headers: { 'Content-Type': 'multipart/form-data' }
            })
            chapter.audio_url = uploadRes.data.url
          } catch (uploadErr) {
            importLogs.value.push({ type: 'error', message: `音频上传失败: ${chapter.filename}` })
            continue
          }
        }
        
        // 创建章节
        const chapterData = {
          chapter_num: chapter.chapter_num,
          title: chapter.title,
          is_free: j < importForm.freeChapters
        }
        
        if (novel.isAudio) {
          chapterData.audio_url = chapter.audio_url
          chapterData.content = ''
        } else {
          chapterData.content = chapter.content
        }
        
        await api.post(`/admin/gallery-novel/novels/${createdNovel.id}/chapters`, chapterData)
        
        // 更新进度
        const chapterProgress = ((j + 1) / novel.chapters.length) * (100 / total)
        importProgress.value = Math.floor((i * 100 / total) + chapterProgress)
      }
      
      importLogs.value.push({ 
        type: 'success', 
        message: `✓ ${novel.title} - ${novel.chapters.length}章导入成功` 
      })
      successCount++
      
    } catch (e) {
      console.error('导入失败:', novel.title, e)
      importLogs.value.push({ 
        type: 'error', 
        message: `✗ ${novel.title} 导入失败: ${e.response?.data?.detail || e.message}` 
      })
    }
  }
  
  importProgress.value = 100
  importStatus.value = successCount === total ? 'success' : 'warning'
  importProgressText.value = `导入完成: 成功 ${successCount}/${total} 本`
}

function finishImport() {
  batchImportDialogVisible.value = false
  loadNovels()
  loadStats()
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', { 
    year: 'numeric', month: '2-digit', day: '2-digit', 
    hour: '2-digit', minute: '2-digit' 
  })
}
</script>

<style lang="scss" scoped>
.novel-manage {
  .stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 20px;
  }
  
  .stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 20px;
    color: #fff;
    text-align: center;
    
    .stat-value {
      font-size: 28px;
      font-weight: 600;
      margin-bottom: 8px;
    }
    
    .stat-label {
      font-size: 14px;
      opacity: 0.9;
    }
    
    &:nth-child(2) { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    &:nth-child(3) { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    &:nth-child(4) { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
  }
  
  .category-card { margin-bottom: 20px; }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .filters { display: flex; gap: 10px; flex-wrap: wrap; }
    .header-actions { display: flex; gap: 10px; }
  }
  
  .novel-title-cell {
    .title { display: block; font-weight: 500; }
    .author { display: block; font-size: 12px; color: #999; margin-top: 4px; }
  }
  
  .data-cell {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 12px;
    color: #666;
  }
  
  .batch-actions {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: #f5f7fa;
    border-radius: 8px;
    margin-top: 16px;
    
    span:first-child { color: #409eff; font-weight: 500; }
  }
  
  .chapters-toolbar {
    display: flex;
    justify-content: space-between;
    margin-bottom: 16px;
    
    .toolbar-left, .toolbar-right { display: flex; gap: 8px; }
  }
  
  .chapters-footer {
    display: flex;
    gap: 20px;
    padding: 12px 0;
    color: #666;
    font-size: 13px;
  }
}

.cover-upload {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  
  .cover-uploader {
    :deep(.el-upload) {
      border: 1px dashed #d9d9d9;
      border-radius: 6px;
      cursor: pointer;
      overflow: hidden;
      transition: border-color 0.3s;
      &:hover { border-color: #409eff; }
    }
  }
  
  .cover-preview { width: 100px; height: 140px; }
  
  .cover-placeholder {
    width: 100px;
    height: 140px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #8c939d;
    .el-icon { font-size: 24px; margin-bottom: 8px; }
    span { font-size: 12px; }
  }
  
  .cover-url-input { flex: 1; }
}

.audio-upload {
  display: flex;
  align-items: center;
}

.audio-upload-section {
  display: flex;
  align-items: center;
  width: 100%;
}

.audio-preview { margin-top: 8px; }

.tip-text {
  margin-left: 8px;
  font-size: 12px;
  color: #999;
}

.content-stats {
  text-align: right;
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

/* 有声小说封面上传 */
.cover-upload-inline {
  display: flex;
  align-items: center;
  
  .cover-uploader-small {
    :deep(.el-upload) {
      border: 1px dashed #d9d9d9;
      border-radius: 6px;
      cursor: pointer;
      overflow: hidden;
      &:hover { border-color: #409eff; }
    }
  }
  
  .cover-preview-small {
    width: 60px;
    height: 80px;
  }
  
  .cover-placeholder-small {
    width: 60px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #8c939d;
    .el-icon { font-size: 20px; }
  }
}

/* 智能导入样式 */
.parse-results {
  max-height: 450px;
  overflow-y: auto;
}

.parsed-novel-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fafafa;
  
  .novel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  
  .chapters-preview {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 8px;
  }
  
  .chapters-stats {
    font-size: 12px;
    color: #909399;
  }
}

.empty-parse {
  padding: 40px 0;
}

.import-progress {
  padding: 20px 0;
  
  .progress-text {
    text-align: center;
    margin: 16px 0;
    font-size: 14px;
    color: #606266;
  }
  
  .import-logs {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    padding: 12px;
    background: #fafafa;
    
    .log-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 0;
      font-size: 13px;
      
      &.success { color: #67c23a; }
      &.error { color: #f56c6c; }
      &.info { color: #909399; }
    }
  }
}
</style>
