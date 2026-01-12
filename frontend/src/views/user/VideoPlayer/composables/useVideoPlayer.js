/**
 * 视频播放器核心逻辑
 */
import { ref, computed, onUnmounted } from 'vue'
import Artplayer from 'artplayer'
import Hls from 'hls.js'

export function useVideoPlayer(options = {}) {
  const artPlayerRef = ref(null)
  const videoRef = ref(null)
  const isPlaying = ref(false)
  const currentPlayTime = ref(0)
  
  let artInstance = null
  
  const getVideoUrl = (video) => {
    if (video.hls_url) return video.hls_url
    return video.original_url || ''
  }
  
  const getCoverUrl = (url) => {
    if (!url) return '/placeholder.webp'
    if (url.startsWith('http') || url.startsWith('/')) return url
    return '/' + url
  }
  
  const initArtPlayer = (video, callbacks = {}) => {
    if (!artPlayerRef.value) return null
    
    const videoUrl = getVideoUrl(video)
    if (!videoUrl) return null
    
    // 销毁旧实例
    if (artInstance) {
      artInstance.destroy()
      artInstance = null
    }
    
    artInstance = new Artplayer({
      container: artPlayerRef.value,
      url: videoUrl,
      poster: getCoverUrl(video.cover_url),
      volume: 0.7,
      isLive: false,
      muted: false,
      autoplay: false,
      pip: true,
      autoSize: false,
      autoMini: true,
      screenshot: false,
      setting: true,
      loop: false,
      flip: true,
      playbackRate: true,
      aspectRatio: true,
      fullscreen: true,
      fullscreenWeb: true,
      subtitleOffset: false,
      miniProgressBar: true,
      mutex: true,
      backdrop: true,
      playsInline: true,
      autoPlayback: true,
      airplay: true,
      theme: '#ec4899',
      lang: 'zh-cn',
      moreVideoAttr: {
        crossOrigin: 'anonymous',
      },
      customType: {
        m3u8: function playM3u8(video, url, art) {
          if (Hls.isSupported()) {
            if (art.hls) art.hls.destroy()
            const hls = new Hls({
              maxBufferLength: 30,
              maxMaxBufferLength: 60,
              maxBufferSize: 60 * 1000 * 1000,
              maxBufferHole: 0.5,
              lowLatencyMode: false,
              startLevel: -1,
              abrEwmaDefaultEstimate: 5000000,
              abrBandWidthFactor: 0.95,
              abrBandWidthUpFactor: 0.7,
              backBufferLength: 30,
            })
            hls.loadSource(url)
            hls.attachMedia(video)
            art.hls = hls
            art.on('destroy', () => hls.destroy())
          } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
            video.src = url
          } else {
            art.notice.show = '不支持播放格式: m3u8'
          }
        },
      },
      controls: [
        {
          name: 'fast-rewind',
          position: 'right',
          html: '<svg viewBox="0 0 24 24" width="22" height="22" fill="white"><path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z"/></svg>',
          tooltip: '快退10秒',
          click: function() {
            if (artInstance) {
              artInstance.currentTime = Math.max(0, artInstance.currentTime - 10)
            }
          },
        },
        {
          name: 'fast-forward',
          position: 'right',
          html: '<svg viewBox="0 0 24 24" width="22" height="22" fill="white"><path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6L13 6z"/></svg>',
          tooltip: '快进10秒',
          click: function() {
            if (artInstance) {
              artInstance.currentTime = Math.min(artInstance.duration, artInstance.currentTime + 10)
            }
          },
        },
      ],
    })
    
    videoRef.value = artInstance.video
    
    // 事件监听
    artInstance.on('play', () => {
      isPlaying.value = true
      callbacks.onPlay?.()
    })
    
    artInstance.on('pause', () => {
      isPlaying.value = false
      callbacks.onPause?.()
    })
    
    artInstance.on('video:ended', () => {
      isPlaying.value = false
      callbacks.onEnded?.()
    })
    
    artInstance.on('video:timeupdate', () => {
      currentPlayTime.value = artInstance.currentTime
      callbacks.onTimeUpdate?.(artInstance.currentTime)
    })
    
    artInstance.on('video:waiting', () => {
      artInstance.loading.show = true
    })
    
    artInstance.on('video:canplay', () => {
      artInstance.loading.show = false
    })
    
    return artInstance
  }
  
  const play = () => {
    artInstance?.play()
  }
  
  const pause = () => {
    artInstance?.pause()
  }
  
  const togglePlay = () => {
    if (artInstance) {
      if (artInstance.playing) {
        artInstance.pause()
      } else {
        artInstance.play()
      }
    }
  }
  
  const seekTo = (time) => {
    if (artInstance) {
      artInstance.currentTime = time
    }
  }
  
  const destroy = () => {
    if (artInstance) {
      artInstance.destroy()
      artInstance = null
    }
  }
  
  onUnmounted(() => {
    destroy()
  })
  
  return {
    artPlayerRef,
    videoRef,
    isPlaying,
    currentPlayTime,
    initArtPlayer,
    play,
    pause,
    togglePlay,
    seekTo,
    destroy,
    getVideoUrl,
    getCoverUrl,
    getInstance: () => artInstance
  }
}
