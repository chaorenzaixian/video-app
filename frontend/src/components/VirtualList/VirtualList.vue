<template>
  <div 
    ref="containerRef" 
    class="virtual-list-container" 
    @scroll="handleScroll"
  >
    <div 
      class="virtual-list-phantom" 
      :style="{ height: totalHeight + 'px' }"
    ></div>
    <div 
      class="virtual-list-content" 
      :style="{ transform: `translateY(${offset}px)` }"
    >
      <div
        v-for="item in visibleItems"
        :key="getItemKey(item)"
        class="virtual-list-item"
        :style="{ height: itemHeight + 'px' }"
      >
        <slot :item="item.data" :index="item.index"></slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  // 列表数据
  items: {
    type: Array,
    required: true
  },
  // 每项高度
  itemHeight: {
    type: Number,
    default: 200
  },
  // 缓冲区大小（前后各渲染多少项）
  buffer: {
    type: Number,
    default: 3
  },
  // 获取唯一key的函数
  keyField: {
    type: String,
    default: 'id'
  }
})

const emit = defineEmits(['scroll-end'])

const containerRef = ref(null)
const scrollTop = ref(0)
const containerHeight = ref(0)

// 总高度
const totalHeight = computed(() => props.items.length * props.itemHeight)

// 可见项数量
const visibleCount = computed(() => 
  Math.ceil(containerHeight.value / props.itemHeight) + props.buffer * 2
)

// 起始索引
const startIndex = computed(() => {
  const index = Math.floor(scrollTop.value / props.itemHeight) - props.buffer
  return Math.max(0, index)
})

// 结束索引
const endIndex = computed(() => {
  const index = startIndex.value + visibleCount.value
  return Math.min(props.items.length, index)
})

// 偏移量
const offset = computed(() => startIndex.value * props.itemHeight)

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
  if (scrollTop.value + clientHeight >= scrollHeight - 50) {
    emit('scroll-end')
  }
}

// 滚动到指定索引
const scrollToIndex = (index) => {
  if (containerRef.value) {
    containerRef.value.scrollTop = index * props.itemHeight
  }
}

// 滚动到顶部
const scrollToTop = () => {
  if (containerRef.value) {
    containerRef.value.scrollTop = 0
  }
}

// 初始化容器高度
onMounted(() => {
  if (containerRef.value) {
    containerHeight.value = containerRef.value.clientHeight
    
    // 监听容器大小变化
    const resizeObserver = new ResizeObserver((entries) => {
      containerHeight.value = entries[0].contentRect.height
    })
    resizeObserver.observe(containerRef.value)
    
    onUnmounted(() => {
      resizeObserver.disconnect()
    })
  }
})

// 暴露方法
defineExpose({
  scrollToIndex,
  scrollToTop
})
</script>

<style scoped>
.virtual-list-container {
  height: 100%;
  overflow-y: auto;
  position: relative;
  -webkit-overflow-scrolling: touch;
}

.virtual-list-phantom {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  z-index: -1;
}

.virtual-list-content {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
}

.virtual-list-item {
  box-sizing: border-box;
}
</style>
