<template>
  <div 
    ref="containerRef" 
    class="virtual-grid-container" 
    @scroll="handleScroll"
  >
    <div 
      class="virtual-grid-phantom" 
      :style="{ height: totalHeight + 'px' }"
    ></div>
    <div 
      class="virtual-grid-content" 
      :style="{ 
        transform: `translateY(${offset}px)`,
        display: 'grid',
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gap: gap + 'px'
      }"
    >
      <div
        v-for="item in visibleItems"
        :key="getItemKey(item)"
        class="virtual-grid-item"
      >
        <slot :item="item.data" :index="item.index"></slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  // 列表数据
  items: {
    type: Array,
    required: true
  },
  // 列数
  columns: {
    type: Number,
    default: 2
  },
  // 每行高度
  rowHeight: {
    type: Number,
    default: 220
  },
  // 间距
  gap: {
    type: Number,
    default: 12
  },
  // 缓冲区行数
  buffer: {
    type: Number,
    default: 2
  },
  // key字段
  keyField: {
    type: String,
    default: 'id'
  }
})

const emit = defineEmits(['scroll-end'])

const containerRef = ref(null)
const scrollTop = ref(0)
const containerHeight = ref(0)

// 总行数
const totalRows = computed(() => Math.ceil(props.items.length / props.columns))

// 总高度
const totalHeight = computed(() => 
  totalRows.value * props.rowHeight + (totalRows.value - 1) * props.gap
)

// 可见行数
const visibleRows = computed(() => 
  Math.ceil(containerHeight.value / (props.rowHeight + props.gap)) + props.buffer * 2
)

// 起始行
const startRow = computed(() => {
  const row = Math.floor(scrollTop.value / (props.rowHeight + props.gap)) - props.buffer
  return Math.max(0, row)
})

// 结束行
const endRow = computed(() => {
  const row = startRow.value + visibleRows.value
  return Math.min(totalRows.value, row)
})

// 起始索引
const startIndex = computed(() => startRow.value * props.columns)

// 结束索引
const endIndex = computed(() => Math.min(props.items.length, endRow.value * props.columns))

// 偏移量
const offset = computed(() => startRow.value * (props.rowHeight + props.gap))

// 可见项
const visibleItems = computed(() => {
  return props.items.slice(startIndex.value, endIndex.value).map((data, i) => ({
    data,
    index: startIndex.value + i
  }))
})

// 获取项的key
const getItemKey = (item) => {
  return item.data[props.keyField] ?? item.index
}

// 处理滚动
const handleScroll = (e) => {
  scrollTop.value = e.target.scrollTop
  
  // 检测是否滚动到底部
  const { scrollHeight, clientHeight } = e.target
  if (scrollTop.value + clientHeight >= scrollHeight - 100) {
    emit('scroll-end')
  }
}

// 滚动到顶部
const scrollToTop = () => {
  if (containerRef.value) {
    containerRef.value.scrollTop = 0
  }
}

// 初始化
onMounted(() => {
  if (containerRef.value) {
    containerHeight.value = containerRef.value.clientHeight
    
    const resizeObserver = new ResizeObserver((entries) => {
      containerHeight.value = entries[0].contentRect.height
    })
    resizeObserver.observe(containerRef.value)
    
    onUnmounted(() => {
      resizeObserver.disconnect()
    })
  }
})

defineExpose({ scrollToTop })
</script>

<style scoped>
.virtual-grid-container {
  height: 100%;
  overflow-y: auto;
  position: relative;
  -webkit-overflow-scrolling: touch;
}

.virtual-grid-phantom {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  z-index: -1;
}

.virtual-grid-content {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  padding: 0 12px;
}

.virtual-grid-item {
  box-sizing: border-box;
}
</style>
