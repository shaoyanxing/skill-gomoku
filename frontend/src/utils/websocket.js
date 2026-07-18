// WebSocket 封装：心跳（30s Ping）+ 指数退避重连
export class GameSocket {
  constructor(url, handlers = {}) {
    this.url = url
    this.handlers = handlers
    this.ws = null
    this.heartbeatTimer = null
    this.reconnectTimer = null
    this.retries = 0
    this.maxRetries = 8
    this.closedByUser = false
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) return
    this.ws = new WebSocket(this.url)
    this.ws.onopen = () => {
      this.retries = 0
      this.handlers.onOpen && this.handlers.onOpen()
      this.startHeartbeat()
    }
    this.ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        this.handlers.onMessage && this.handlers.onMessage(msg)
      } catch (err) { /* 忽略坏包 */ }
    }
    this.ws.onclose = () => {
      this.stopHeartbeat()
      this.handlers.onClose && this.handlers.onClose()
      if (!this.closedByUser) this.scheduleReconnect()
    }
    this.ws.onerror = () => { this.ws && this.ws.close() }
  }

  send(payload) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload))
      return true
    }
    return false
  }

  startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => this.send({ type: 'ping' }), 30000)
  }

  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  scheduleReconnect() {
    if (this.retries >= this.maxRetries) return
    const delay = Math.min(1000 * 2 ** this.retries, 15000)
    this.retries += 1
    clearTimeout(this.reconnectTimer)
    this.reconnectTimer = setTimeout(() => this.connect(), delay)
  }

  close() {
    this.closedByUser = true
    clearTimeout(this.reconnectTimer)
    this.stopHeartbeat()
    if (this.ws) this.ws.close()
  }
}