// Funciones para el carrito de compras
function addToCart(productId) {
  const button = event.target
  const originalText = button.innerHTML
  const originalClass = button.className

  button.innerHTML = '<span class="loading"></span> Agregando...'
  button.disabled = true

  fetch("/add_to_cart", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      producto_id: productId,
      cantidad: 1,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        button.innerHTML = '<i class="fas fa-check"></i> ¡Agregado!'
        button.className = button.className.replace("btn-primary", "btn-success")

        window.notifications.success(data.message, {
          title: "Producto Agregado",
          duration: 3000,
          actions: [
            {
              text: "Ver Carrito",
              type: "primary",
              onclick: "scrollToCart()",
            },
          ],
        })

        setTimeout(() => {
          button.innerHTML = originalText
          button.className = originalClass
          button.disabled = false
        }, 2000)

        setTimeout(() => {
          location.reload()
        }, 1000)
      } else {
        window.notifications.error(data.message, {
          title: "Error al Agregar",
          duration: 4000,
        })
        button.innerHTML = originalText
        button.disabled = false
      }
    })
    .catch((error) => {
      console.error("Error:", error)
      window.notifications.error("Error al agregar el producto al carrito", {
        title: "Error de Conexión",
        duration: 5000,
        persistent: true,
      })
      button.innerHTML = originalText
      button.disabled = false
    })
}

function removeFromCart(carritoId) {
  if (confirm("¿Estás seguro de que quieres remover este producto del carrito?")) {
    fetch("/remove_from_cart", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        carrito_id: carritoId,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showToast(data.message, "success")
          setTimeout(() => location.reload(), 500)
        } else {
          showToast(data.message, "danger")
        }
      })
      .catch((error) => {
        console.error("Error:", error)
        showToast("Error al remover el producto del carrito", "danger")
      })
  }
}

// Validación de formularios
document.addEventListener("DOMContentLoaded", () => {
  // Validar formulario de registro
  const registerForm = document.querySelector("#registerModal form")
  if (registerForm) {
    registerForm.addEventListener("submit", (e) => {
      const username = document.getElementById("reg_username").value.trim()
      const email = document.getElementById("reg_email").value.trim()
      const password = document.getElementById("reg_password").value

      if (username.length < 3) {
        e.preventDefault()
        showToast("El usuario debe tener al menos 3 caracteres", "warning")
        return false
      }

      if (password.length < 6) {
        e.preventDefault()
        showToast("La contraseña debe tener al menos 6 caracteres", "warning")
        return false
      }

      if (!isValidEmail(email)) {
        e.preventDefault()
        showToast("Por favor ingresa un email válido", "warning")
        return false
      }
    })
  }

  // Validar formulario de login
  const loginForm = document.querySelector("#loginModal form")
  if (loginForm) {
    loginForm.addEventListener("submit", (e) => {
      const username = document.getElementById("username").value.trim()
      const password = document.getElementById("password").value

      if (!username || !password) {
        e.preventDefault()
        showToast("Por favor completa todos los campos", "warning")
        return false
      }
    })
  }

  const productForm = document.querySelector("#addProductModal form")
  if (productForm) {
    productForm.addEventListener("submit", (e) => {
      const nombre = document.getElementById("nombre").value.trim()
      const precio = Number.parseFloat(document.getElementById("precio").value)
      const stock = Number.parseInt(document.getElementById("stock").value)

      if (!nombre) {
        e.preventDefault()
        showToast("El nombre del producto es obligatorio", "warning")
        return false
      }

      if (precio <= 0) {
        e.preventDefault()
        showToast("El precio debe ser mayor a 0", "warning")
        return false
      }

      if (stock < 0) {
        e.preventDefault()
        showToast("El stock no puede ser negativo", "warning")
        return false
      }
    })
  }

  // Auto-cerrar alertas después de 5 segundos
  const alerts = document.querySelectorAll(".alert")
  const bootstrap = window.bootstrap // Declare the bootstrap variable
  alerts.forEach((alert) => {
    setTimeout(() => {
      if (bootstrap && bootstrap.Alert) {
        const bsAlert = new bootstrap.Alert(alert)
        bsAlert.close()
      }
    }, 5000)
  })

  // Inicializar tooltips si existen
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  if (bootstrap && bootstrap.Tooltip) {
    tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl))
  }

  // Smooth scroll para enlaces internos
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault()
      const target = document.querySelector(this.getAttribute("href"))
      if (target) {
        target.scrollIntoView({
          behavior: "smooth",
          block: "start",
        })
      }
    })
  })
})

// Función para validar email
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

// Función para formatear precios
function formatPrice(price) {
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "USD",
  }).format(price)
}

// Función para calcular total del carrito
function calculateCartTotal() {
  const cartItems = document.querySelectorAll(".cart-item")
  let total = 0

  cartItems.forEach((item) => {
    const priceElement = item.querySelector(".item-price")
    const quantityElement = item.querySelector(".item-quantity")

    if (priceElement && quantityElement) {
      const price = Number.parseFloat(priceElement.textContent.replace("$", ""))
      const quantity = Number.parseInt(quantityElement.textContent)
      total += price * quantity
    }
  })

  return total
}

// Función para animar elementos
function animateElement(element, animation) {
  element.style.animation = animation
  element.addEventListener("animationend", () => {
    element.style.animation = ""
  })
}

// Función para manejar errores de imágenes
function handleImageError(img) {
  img.style.display = "none"
  const placeholder = img.nextElementSibling
  if (placeholder) {
    placeholder.style.display = "flex"
  }
}

// Función para lazy loading de imágenes
function lazyLoadImages() {
  const images = document.querySelectorAll("img[data-src]")
  const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const img = entry.target
        img.src = img.dataset.src
        img.classList.remove("lazy")
        imageObserver.unobserve(img)
      }
    })
  })

  images.forEach((img) => imageObserver.observe(img))
}

// Función para detectar dispositivo móvil
function isMobile() {
  return window.innerWidth <= 768
}

// Función para manejar el scroll suave en hero
function initSmoothScroll() {
  const scrollIndicator = document.querySelector(".scroll-indicator")
  if (scrollIndicator) {
    scrollIndicator.addEventListener("click", () => {
      const nextSection = document.querySelector(".featured-products")
      if (nextSection) {
        nextSection.scrollIntoView({ behavior: "smooth" })
      }
    })
  }
}

// Función para mostrar notificaciones toast
function showToast(message, type = "info") {
  // Crear contenedor si no existe
  let toastContainer = document.getElementById("toast-container")
  if (!toastContainer) {
    toastContainer = document.createElement("div")
    toastContainer.id = "toast-container"
    toastContainer.className = "toast-container position-fixed bottom-0 end-0 p-3"
    toastContainer.style.zIndex = "9999"
    document.body.appendChild(toastContainer)
  }

  // Crear toast
  const toastId = "toast-" + Date.now()
  const toast = document.createElement("div")
  toast.id = toastId
  toast.className = `toast align-items-center text-white bg-${type} border-0`
  toast.setAttribute("role", "alert")
  toast.setAttribute("aria-live", "assertive")
  toast.setAttribute("aria-atomic", "true")

  // Icono según el tipo
  let icon = "fas fa-info-circle"
  switch (type) {
    case "success":
      icon = "fas fa-check-circle"
      break
    case "danger":
      icon = "fas fa-exclamation-circle"
      break
    case "warning":
      icon = "fas fa-exclamation-triangle"
      break
  }

  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        <i class="${icon} me-2"></i>${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `

  toastContainer.appendChild(toast)

  const bsToast = window.bootstrap.Toast
  if (bsToast) {
    new bsToast(toast, {
      autohide: true,
      delay: 4000,
    }).show()
  }

  toast.addEventListener("hidden.bs.toast", () => {
    toast.remove()
  })
}

function setLoadingState(element, isLoading) {
  if (isLoading) {
    element.classList.add("loading")
    element.disabled = true
  } else {
    element.classList.remove("loading")
    element.disabled = false
  }
}

function copyToClipboard(text) {
  navigator.clipboard
    .writeText(text)
    .then(() => {
      showToast("Texto copiado al portapapeles", "success")
    })
    .catch(() => {
      showToast("Error al copiar texto", "danger")
    })
}

function shareOnSocial(platform, url, text) {
  const shareUrls = {
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
    twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`,
    whatsapp: `https://wa.me/?text=${encodeURIComponent(text + " " + url)}`,
  }

  if (shareUrls[platform]) {
    window.open(shareUrls[platform], "_blank", "width=600,height=400")
  }
}

function scrollToCart() {
  const cartElement = document.querySelector(".cart-card")
  if (cartElement) {
    cartElement.scrollIntoView({ behavior: "smooth", block: "center" })
    cartElement.style.animation = "pulse 1s ease-in-out"
  }
}

window.addToCart = addToCart
window.removeFromCart = removeFromCart
window.showToast = showToast
window.formatPrice = formatPrice
window.copyToClipboard = copyToClipboard
window.shareOnSocial = shareOnSocial

document.addEventListener("DOMContentLoaded", () => {
  lazyLoadImages()
  initSmoothScroll()

  document.body.classList.add("loaded")
})

window.addEventListener("resize", () => {
  if (isMobile()) {
  }
})

function preloadImages(urls) {
  urls.forEach((url) => {
    const img = new Image()
    img.src = url
  })
}
