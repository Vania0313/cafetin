// Sistema de notificaciones mejorado
class NotificationSystem {
  constructor() {
    this.container = null
    this.notifications = []
    this.maxNotifications = 5
    this.init()
  }

  init() {
    // Crear contenedor de notificaciones
    this.container = document.createElement("div")
    this.container.id = "notification-container"
    this.container.className = "notification-container"
    document.body.appendChild(this.container)

    // Estilos CSS
    this.addStyles()
  }

  addStyles() {
    const style = document.createElement("style")
    style.textContent = `
            .notification-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
                pointer-events: none;
            }

            .notification {
                background: white;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
                margin-bottom: 12px;
                padding: 16px 20px;
                border-left: 4px solid;
                transform: translateX(100%);
                opacity: 0;
                transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                pointer-events: auto;
                position: relative;
                overflow: hidden;
                max-width: 100%;
                word-wrap: break-word;
            }

            .notification.show {
                transform: translateX(0);
                opacity: 1;
            }

            .notification.hide {
                transform: translateX(100%);
                opacity: 0;
                margin-bottom: 0;
                padding-top: 0;
                padding-bottom: 0;
                max-height: 0;
            }

            .notification-success {
                border-left-color: #10b981;
                background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
            }

            .notification-error {
                border-left-color: #ef4444;
                background: linear-gradient(135deg, #fef2f2 0%, #fef1f1 100%);
            }

            .notification-warning {
                border-left-color: #f59e0b;
                background: linear-gradient(135deg, #fffbeb 0%, #fefce8 100%);
            }

            .notification-info {
                border-left-color: #3b82f6;
                background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%);
            }

            .notification-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 8px;
            }

            .notification-title {
                display: flex;
                align-items: center;
                font-weight: 600;
                font-size: 14px;
                margin: 0;
            }

            .notification-icon {
                margin-right: 8px;
                font-size: 16px;
            }

            .notification-success .notification-icon {
                color: #10b981;
            }

            .notification-error .notification-icon {
                color: #ef4444;
            }

            .notification-warning .notification-icon {
                color: #f59e0b;
            }

            .notification-info .notification-icon {
                color: #3b82f6;
            }

            .notification-close {
                background: none;
                border: none;
                font-size: 18px;
                cursor: pointer;
                color: #6b7280;
                padding: 0;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: all 0.2s;
            }

            .notification-close:hover {
                background: rgba(0, 0, 0, 0.1);
                color: #374151;
            }

            .notification-message {
                font-size: 13px;
                color: #374151;
                line-height: 1.4;
                margin: 0;
            }

            .notification-progress {
                position: absolute;
                bottom: 0;
                left: 0;
                height: 3px;
                background: rgba(0, 0, 0, 0.1);
                border-radius: 0 0 12px 12px;
                overflow: hidden;
            }

            .notification-progress-bar {
                height: 100%;
                width: 100%;
                transform: translateX(-100%);
                transition: transform linear;
            }

            .notification-success .notification-progress-bar {
                background: #10b981;
            }

            .notification-error .notification-progress-bar {
                background: #ef4444;
            }

            .notification-warning .notification-progress-bar {
                background: #f59e0b;
            }

            .notification-info .notification-progress-bar {
                background: #3b82f6;
            }

            .notification-actions {
                margin-top: 12px;
                display: flex;
                gap: 8px;
            }

            .notification-btn {
                padding: 6px 12px;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }

            .notification-btn-primary {
                background: #3b82f6;
                color: white;
            }

            .notification-btn-primary:hover {
                background: #2563eb;
            }

            .notification-btn-secondary {
                background: #f3f4f6;
                color: #374151;
            }

            .notification-btn-secondary:hover {
                background: #e5e7eb;
            }

            @media (max-width: 480px) {
                .notification-container {
                    left: 20px;
                    right: 20px;
                    max-width: none;
                }
            }

            /* Animación de entrada */
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            /* Animación de salida */
            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }

            /* Efecto de shake para errores */
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
                20%, 40%, 60%, 80% { transform: translateX(5px); }
            }

            .notification-error.shake {
                animation: shake 0.5s ease-in-out;
            }
        `
    document.head.appendChild(style)
  }

  show(options) {
    const {
      type = "info",
      title = "",
      message = "",
      duration = 5000,
      actions = [],
      persistent = false,
      sound = true,
    } = options

    // Limitar número de notificaciones
    if (this.notifications.length >= this.maxNotifications) {
      this.notifications[0].remove()
    }

    const notification = this.createNotification({
      type,
      title,
      message,
      duration,
      actions,
      persistent,
    })

    this.container.appendChild(notification.element)
    this.notifications.push(notification)

    // Reproducir sonido
    if (sound) {
      this.playSound(type)
    }

    // Mostrar notificación
    setTimeout(() => {
      notification.element.classList.add("show")
    }, 100)

    // Auto-ocultar si no es persistente
    if (!persistent && duration > 0) {
      notification.startProgress(duration)
      setTimeout(() => {
        notification.remove()
      }, duration)
    }

    return notification
  }

  createNotification(options) {
    const { type, title, message, actions } = options

    const element = document.createElement("div")
    element.className = `notification notification-${type}`

    const icons = {
      success: "fas fa-check-circle",
      error: "fas fa-exclamation-circle",
      warning: "fas fa-exclamation-triangle",
      info: "fas fa-info-circle",
    }

    const titles = {
      success: title || "Éxito",
      error: title || "Error",
      warning: title || "Advertencia",
      info: title || "Información",
    }

    element.innerHTML = `
            <div class="notification-header">
                <h4 class="notification-title">
                    <i class="notification-icon ${icons[type]}"></i>
                    ${titles[type]}
                </h4>
                <button class="notification-close" onclick="this.closest('.notification').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <p class="notification-message">${message}</p>
            ${
              actions.length > 0
                ? `
                <div class="notification-actions">
                    ${actions
                      .map(
                        (action) => `
                        <button class="notification-btn notification-btn-${action.type || "secondary"}" 
                                onclick="${action.onclick}">
                            ${action.text}
                        </button>
                    `,
                      )
                      .join("")}
                </div>
            `
                : ""
            }
            <div class="notification-progress">
                <div class="notification-progress-bar"></div>
            </div>
        `

    const notificationObj = {
      element,
      remove: () => {
        element.classList.add("hide")
        setTimeout(() => {
          if (element.parentNode) {
            element.parentNode.removeChild(element)
          }
          const index = this.notifications.indexOf(notificationObj)
          if (index > -1) {
            this.notifications.splice(index, 1)
          }
        }, 400)
      },
      startProgress: (duration) => {
        const progressBar = element.querySelector(".notification-progress-bar")
        progressBar.style.transitionDuration = `${duration}ms`
        progressBar.style.transform = "translateX(0)"
      },
    }

    // Agregar efecto shake para errores
    if (type === "error") {
      setTimeout(() => {
        element.classList.add("shake")
        setTimeout(() => {
          element.classList.remove("shake")
        }, 500)
      }, 200)
    }

    return notificationObj
  }

  playSound(type) {
    // Crear contexto de audio si no existe
    if (!this.audioContext) {
      try {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
      } catch (e) {
        return // Audio no soportado
      }
    }

    const frequencies = {
      success: [523.25, 659.25, 783.99], // C5, E5, G5
      error: [220, 185, 147], // A3, F#3, D3
      warning: [440, 554.37], // A4, C#5
      info: [523.25, 659.25], // C5, E5
    }

    const freq = frequencies[type] || frequencies.info

    freq.forEach((frequency, index) => {
      setTimeout(() => {
        this.playTone(frequency, 0.1, 0.1)
      }, index * 100)
    })
  }

  playTone(frequency, duration, volume) {
    if (!this.audioContext) return

    const oscillator = this.audioContext.createOscillator()
    const gainNode = this.audioContext.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(this.audioContext.destination)

    oscillator.frequency.value = frequency
    oscillator.type = "sine"

    gainNode.gain.setValueAtTime(0, this.audioContext.currentTime)
    gainNode.gain.linearRampToValueAtTime(volume, this.audioContext.currentTime + 0.01)
    gainNode.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + duration)

    oscillator.start(this.audioContext.currentTime)
    oscillator.stop(this.audioContext.currentTime + duration)
  }

  // Métodos de conveniencia
  success(message, options = {}) {
    return this.show({ ...options, type: "success", message })
  }

  error(message, options = {}) {
    return this.show({ ...options, type: "error", message })
  }

  warning(message, options = {}) {
    return this.show({ ...options, type: "warning", message })
  }

  info(message, options = {}) {
    return this.show({ ...options, type: "info", message })
  }

  // Limpiar todas las notificaciones
  clear() {
    this.notifications.forEach((notification) => notification.remove())
    this.notifications = []
  }
}

// Crear instancia global
window.notifications = new NotificationSystem()

// Función de compatibilidad con el código existente
window.showToast = (message, type = "info", options = {}) =>
  window.notifications.show({
    type: type === "danger" ? "error" : type,
    message: message, // Declared variable
    ...options,
  })

// Notificaciones específicas para el carrito
window.showCartNotification = (action, productName) => {
  const messages = {
    added: `${productName} agregado al carrito`,
    removed: `${productName} removido del carrito`,
    updated: `Cantidad actualizada para ${productName}`,
    checkout: "Compra realizada exitosamente",
  }

  const types = {
    added: "success",
    removed: "warning",
    updated: "info",
    checkout: "success",
  }

  return window.notifications.show({
    type: types[action] || "info",
    message: messages[action] || message, // Declared variable
    duration: 3000,
    actions:
      action === "checkout"
        ? [
            {
              text: "Ver Historial",
              type: "primary",
              onclick: 'window.location.href="/user"',
            },
          ]
        : [],
  })
}

window.showAINotification = (message, data = {}) =>
  window.notifications.show({
    type: "info",
    title: "Recomendación IA",
    message: message, // Declared variable
    duration: 6000,
    actions: [
      {
        text: "Ver Promociones",
        type: "primary",
        onclick: 'window.location.href="/promociones"',
      },
    ],
  })

// Notificaciones de stock para admin
window.showStockAlert = (productName, stock) => {
  const type = stock <= 0 ? "error" : stock <= 5 ? "warning" : "info"
  const message =
    stock <= 0
      ? `${productName} está agotado`
      : stock <= 5
        ? `Stock bajo para ${productName}: ${stock} unidades`
        : `Stock actualizado para ${productName}: ${stock} unidades`

  return window.notifications.show({
    type,
    title: "Alerta de Stock",
    message: message, // Declared variable
    persistent: stock <= 0,
    actions:
      stock <= 5
        ? [
            {
              text: "Reabastecer",
              type: "primary",
              onclick: `restock('${productName}')`,
            },
          ]
        : [],
  })
}
