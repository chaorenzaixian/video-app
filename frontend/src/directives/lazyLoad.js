/**
 * 图片懒加载指令
 * 使用 IntersectionObserver 实现
 * 
 * 用法：
 * <img v-lazy="imageUrl" />
 * <img v-lazy="{ src: imageUrl, placeholder: '/placeholder.webp' }" />
 */

const DEFAULT_PLACEHOLDER = '/images/placeholder.webp'

// 创建 IntersectionObserver 实例
let observer = null

const getObserver = () => {
  if (observer) return observer
  
  observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target
        const src = img.dataset.src
        
        if (src) {
          // 预加载图片
          const tempImg = new Image()
          tempImg.onload = () => {
            img.src = src
            img.classList.add('lazy-loaded')
            img.classList.remove('lazy-loading')
          }
          tempImg.onerror = () => {
            img.classList.add('lazy-error')
            img.classList.remove('lazy-loading')
          }
          tempImg.src = src
        }
        
        // 停止观察
        observer.unobserve(img)
      }
    })
  }, {
    rootMargin: '50px 0px', // 提前50px开始加载
    threshold: 0.01
  })
  
  return observer
}

export const lazyLoad = {
  mounted(el, binding) {
    const value = binding.value
    let src, placeholder
    
    if (typeof value === 'string') {
      src = value
      placeholder = DEFAULT_PLACEHOLDER
    } else if (typeof value === 'object') {
      src = value.src
      placeholder = value.placeholder || DEFAULT_PLACEHOLDER
    }
    
    if (!src) return
    
    // 设置占位图
    el.src = placeholder
    el.dataset.src = src
    el.classList.add('lazy-loading')
    
    // 开始观察
    getObserver().observe(el)
  },
  
  updated(el, binding) {
    const value = binding.value
    const newSrc = typeof value === 'string' ? value : value?.src
    
    if (newSrc && newSrc !== el.dataset.src) {
      el.dataset.src = newSrc
      el.classList.remove('lazy-loaded', 'lazy-error')
      el.classList.add('lazy-loading')
      getObserver().observe(el)
    }
  },
  
  unmounted(el) {
    if (observer) {
      observer.unobserve(el)
    }
  }
}

// 注册全局指令
export function setupLazyLoad(app) {
  app.directive('lazy', lazyLoad)
}

export default lazyLoad
