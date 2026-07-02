from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
import random
from collections import defaultdict, Counter
import json
import calendar
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import pandas as pd
import base64
from io import BytesIO
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'cafetin_secreto_2024_muy_seguro'

DATABASE = 'cafetin.db'

def init_db():
    """Inicializar la base de datos"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio REAL NOT NULL,
            imagen TEXT,
            categoria TEXT,
            stock INTEGER DEFAULT 0,
            popularidad INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de carrito
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carrito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            producto_id INTEGER,
            cantidad INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES usuarios (id),
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    ''')
    
    # Tabla de pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total REAL NOT NULL,
            estado TEXT DEFAULT 'completado',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES usuarios (id)
        )
    ''')
    
    # Tabla de detalles de pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedido_detalles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            producto_id INTEGER,
            cantidad INTEGER,
            precio_unitario REAL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id),
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    ''')
    
    # Tabla de historial de compras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            producto_id INTEGER,
            cantidad INTEGER,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES usuarios (id),
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    ''')
    
    # Insertar usuario administrador por defecto
    cursor.execute('SELECT * FROM usuarios WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute('''
            INSERT INTO usuarios (username, email, password, role)
            VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin@cafetin.com', admin_password, 'admin'))
        print("Usuario admin creado: admin/admin123")
    
    # Insertar productos de ejemplo
    cursor.execute('SELECT COUNT(*) FROM productos')
    if cursor.fetchone()[0] == 0:
        productos_ejemplo = [
            ('Café Americano', 'Café negro tradicional preparado con granos selectos de Colombia', 2.50, '/static/images/americano.jpg', 'Bebidas Calientes', 50, 85),
            ('Cappuccino', 'Café espresso con leche espumosa perfectamente texturizada', 3.50, '/static/images/cappuccino.jpg', 'Bebidas Calientes', 30, 92),
            ('Latte', 'Café con leche cremosa y arte latte personalizado', 4.00, '/static/images/latte.jpg', 'Bebidas Calientes', 25, 88),
            ('Mocha', 'Café con chocolate belga y crema batida', 4.25, '/static/images/mocha.jpg', 'Bebidas Calientes', 20, 78),
            ('Frappé de Vainilla', 'Bebida fría refrescante con café, hielo y vainilla natural', 4.50, '/static/images/frappe.jpg', 'Bebidas Frías', 20, 82),
            ('Smoothie de Frutas', 'Batido natural con frutas de temporada y yogurt', 3.75, '/static/images/smoothie.jpg', 'Bebidas Frías', 15, 75),
            ('Té Chai Latte', 'Té especiado con leche y canela', 3.25, '/static/images/chai.jpg', 'Bebidas Calientes', 18, 70),
            ('Croissant Simple', 'Croissant francés recién horneado y mantequilloso', 2.00, '/static/images/croissant.jpg', 'Panadería', 15, 65),
            ('Croissant de Chocolate', 'Croissant relleno de chocolate belga premium', 2.50, '/static/images/croissant-chocolate.jpg', 'Panadería', 12, 80),
            ('Muffin de Arándanos', 'Muffin esponjoso con arándanos frescos orgánicos', 2.75, '/static/images/muffin-arandanos.jpg', 'Panadería', 18, 72),
            ('Cheesecake', 'Porción de cheesecake cremoso con frutos rojos', 4.50, '/static/images/cheesecake.jpg', 'Postres', 8, 90),
            ('Tiramisu', 'Postre italiano tradicional con café y mascarpone', 5.00, '/static/images/tiramisu.jpg', 'Postres', 6, 95),
            ('Sandwich Club', 'Sandwich gourmet con pollo, tocino, aguacate y vegetales', 6.50, '/static/images/sandwich-club.jpg', 'Comida', 10, 85),
            ('Wrap Vegetariano', 'Wrap integral con hummus, vegetales frescos y queso', 5.50, '/static/images/wrap-veggie.jpg', 'Comida', 8, 68),
            ('Ensalada César', 'Ensalada fresca con pollo a la parrilla y aderezo casero', 7.00, '/static/images/ensalada-cesar.jpg', 'Comida', 8, 77),
            ('Bagel con Salmón', 'Bagel tostado con salmón ahumado, queso crema y alcaparras', 7.50, '/static/images/bagel-salmon.jpg', 'Comida', 5, 88)
        ]
        
        cursor.executemany('''
            INSERT INTO productos (nombre, descripcion, precio, imagen, categoria, stock, popularidad)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', productos_ejemplo)
        print("Productos de ejemplo insertados")
    
    # Insertar datos de ejemplo para el historial de compras (para probar la IA)
    cursor.execute('SELECT COUNT(*) FROM historial_compras')
    if cursor.fetchone()[0] == 0:
        historial_ejemplo = []
        for user_id in range(1, 6): 
            for _ in range(random.randint(5, 15)): 
                producto_id = random.randint(1, 16)
                cantidad = random.randint(1, 3)
                fecha = datetime.now() - timedelta(days=random.randint(1, 90))
                historial_ejemplo.append((user_id, producto_id, cantidad, fecha))
        
        cursor.executemany('''
            INSERT INTO historial_compras (user_id, producto_id, cantidad, fecha)
            VALUES (?, ?, ?, ?)
        ''', historial_ejemplo)
        print("Historial de compras de ejemplo creado")
    
    cursor.execute('SELECT * FROM usuarios WHERE username = ?', ('cliente_demo',))
    if not cursor.fetchone():
        demo_password = hashlib.sha256('demo123'.encode()).hexdigest()
        cursor.execute('''
            INSERT INTO usuarios (username, email, password, role)
            VALUES (?, ?, ?, ?)
        ''', ('cliente_demo', 'demo@cafetin.com', demo_password, 'user'))
        demo_user_id = cursor.lastrowid
        
        productos_demo = [1, 2, 3, 5, 8, 9, 11, 12] 
        for producto_id in productos_demo:
            for _ in range(random.randint(2, 8)):
                cantidad = random.randint(1, 3)
                fecha = datetime.now() - timedelta(days=random.randint(1, 60))
                cursor.execute('''
                    INSERT INTO historial_compras (user_id, producto_id, cantidad, fecha)
                    VALUES (?, ?, ?, ?)
                ''', (demo_user_id, producto_id, cantidad, fecha))
        
        print("Usuario demo creado: cliente_demo/demo123")
    
    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente")

def get_db_connection():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash de contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verificar contraseña"""
    return hash_password(password) == hashed

def get_user_recommendations(user_id, limit=6):
    """Obtener recomendaciones personalizadas usando algoritmos de IA"""
    conn = get_db_connection()
    
    user_history = conn.execute('''
        SELECT producto_id, SUM(cantidad) as total_comprado
        FROM historial_compras 
        WHERE user_id = ?
        GROUP BY producto_id
        ORDER BY total_comprado DESC
    ''', (user_id,)).fetchall()
    
    user_products = {row['producto_id']: row['total_comprado'] for row in user_history}
    
    # Algoritmo 2: Filtrado colaborativo simple
    # Encontrar usuarios similares basado en productos comprados
    similar_users = conn.execute('''
        SELECT DISTINCT h2.user_id, COUNT(*) as productos_comunes
        FROM historial_compras h1
        JOIN historial_compras h2 ON h1.producto_id = h2.producto_id
        WHERE h1.user_id = ? AND h2.user_id != ?
        GROUP BY h2.user_id
        ORDER BY productos_comunes DESC
        LIMIT 5
    ''', (user_id, user_id)).fetchall()
    
    # Algoritmo 3: Recomendaciones basadas en categorías preferidas
    category_preferences = conn.execute('''
        SELECT p.categoria, SUM(h.cantidad) as total_categoria
        FROM historial_compras h
        JOIN productos p ON h.producto_id = p.id
        WHERE h.user_id = ?
        GROUP BY p.categoria
        ORDER BY total_categoria DESC
    ''', (user_id,)).fetchall()
    
    # Calcular puntuaciones de recomendación
    recommendations = defaultdict(float)
    
    # Puntuación por historial personal (peso: 0.4)
    for producto_id, cantidad in user_products.items():
        # Recomendar productos similares de la misma categoría
        similar_products = conn.execute('''
            SELECT p2.id, p2.popularidad
            FROM productos p1
            JOIN productos p2 ON p1.categoria = p2.categoria
            WHERE p1.id = ? AND p2.id != ? AND p2.stock > 0
        ''', (producto_id, producto_id)).fetchall()
        
        for similar in similar_products:
            recommendations[similar['id']] += (cantidad * 0.4) + (similar['popularidad'] * 0.01)
    
    # Puntuación por usuarios similares (peso: 0.3)
    for similar_user in similar_users:
        similar_user_products = conn.execute('''
            SELECT producto_id, SUM(cantidad) as total
            FROM historial_compras
            WHERE user_id = ? AND producto_id NOT IN (
                SELECT producto_id FROM historial_compras WHERE user_id = ?
            )
            GROUP BY producto_id
        ''', (similar_user['user_id'], user_id)).fetchall()
        
        for product in similar_user_products:
            recommendations[product['producto_id']] += product['total'] * 0.3
    
    # Puntuación por popularidad general (peso: 0.2)
    popular_products = conn.execute('''
        SELECT id, popularidad
        FROM productos
        WHERE stock > 0 AND id NOT IN (
            SELECT DISTINCT producto_id FROM historial_compras WHERE user_id = ?
        )
        ORDER BY popularidad DESC
    ''', (user_id,)).fetchall()
    
    for product in popular_products:
        recommendations[product['id']] += product['popularidad'] * 0.002
    
    # Puntuación por categorías preferidas (peso: 0.1)
    if category_preferences:
        top_category = category_preferences[0]['categoria']
        category_products = conn.execute('''
            SELECT id, popularidad
            FROM productos
            WHERE categoria = ? AND stock > 0 AND id NOT IN (
                SELECT DISTINCT producto_id FROM historial_compras WHERE user_id = ?
            )
        ''', (top_category, user_id)).fetchall()
        
        for product in category_products:
            recommendations[product['id']] += product['popularidad'] * 0.001
    
    # Obtener los productos recomendados con mayor puntuación
    sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
    recommended_ids = [str(prod_id) for prod_id, score in sorted_recommendations[:limit]]
    
    if not recommended_ids:
        # Si no hay recomendaciones, mostrar productos populares
        recommended_ids = [str(row['id']) for row in popular_products[:limit]]
    
    # Obtener información completa de los productos recomendados
    if recommended_ids:
        placeholders = ','.join(['?' for _ in recommended_ids])
        recommended_products = conn.execute(f'''
            SELECT * FROM productos 
            WHERE id IN ({placeholders}) AND stock > 0
            ORDER BY popularidad DESC
        ''', recommended_ids).fetchall()
    else:
        recommended_products = []
    
    conn.close()
    return recommended_products

# Algoritmos de IA para análisis de ventas y demanda
def predict_demand(producto_id, days_ahead=7):
    """Predecir demanda usando regresión lineal simple"""
    conn = get_db_connection()
    
    # Obtener historial de ventas de los últimos 30 días
    ventas_historicas = conn.execute('''
        SELECT DATE(h.fecha) as fecha, SUM(h.cantidad) as total_vendido
        FROM historial_compras h
        WHERE h.producto_id = ? AND h.fecha >= date('now', '-30 days')
        GROUP BY DATE(h.fecha)
        ORDER BY fecha
    ''', (producto_id,)).fetchall()
    
    if len(ventas_historicas) < 3:
        conn.close()
        return 0
    
    # Preparar datos para regresión
    x_values = list(range(len(ventas_historicas)))
    y_values = [row['total_vendido'] for row in ventas_historicas]
    
    # Regresión lineal simple
    n = len(x_values)
    sum_x = sum(x_values)
    sum_y = sum(y_values)
    sum_xy = sum(x * y for x, y in zip(x_values, y_values))
    sum_x2 = sum(x * x for x in x_values)
    
    if n * sum_x2 - sum_x * sum_x == 0:
        conn.close()
        return sum_y / n if n > 0 else 0
    
    # Calcular pendiente y intercepto
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
    intercept = (sum_y - slope * sum_x) / n
    
    # Predecir demanda futura
    future_point = len(x_values) + days_ahead
    predicted_demand = max(0, slope * future_point + intercept)
    
    conn.close()
    return round(predicted_demand, 2)

def analyze_sales_trends():
    """Analizar tendencias de ventas usando IA"""
    conn = get_db_connection()
    
    # Ventas por semana de los últimos 2 meses
    ventas_semanales = conn.execute('''
        SELECT 
            strftime('%Y-%W', h.fecha) as semana,
            strftime('%Y-%m-%d', h.fecha) as fecha,
            SUM(h.cantidad * p.precio) as ingresos,
            SUM(h.cantidad) as productos_vendidos,
            COUNT(DISTINCT h.user_id) as clientes_unicos
        FROM historial_compras h
        JOIN productos p ON h.producto_id = p.id
        WHERE h.fecha >= date('now', '-60 days')
        GROUP BY strftime('%Y-%W', h.fecha)
        ORDER BY semana DESC
        LIMIT 8
    ''').fetchall()
    
    # Productos más vendidos por categoría
    productos_categoria = conn.execute('''
        SELECT 
            p.categoria,
            p.nombre,
            SUM(h.cantidad) as total_vendido,
            SUM(h.cantidad * p.precio) as ingresos_generados,
            AVG(h.cantidad) as promedio_por_compra
        FROM historial_compras h
        JOIN productos p ON h.producto_id = p.id
        WHERE h.fecha >= date('now', '-30 days')
        GROUP BY p.categoria, p.id, p.nombre
        ORDER BY p.categoria, total_vendido DESC
    ''').fetchall()
    
    # Análisis de patrones de compra por día de la semana
    patrones_semanales = conn.execute('''
        SELECT 
            CASE strftime('%w', h.fecha)
                WHEN '0' THEN 'Domingo'
                WHEN '1' THEN 'Lunes'
                WHEN '2' THEN 'Martes'
                WHEN '3' THEN 'Miércoles'
                WHEN '4' THEN 'Jueves'
                WHEN '5' THEN 'Viernes'
                WHEN '6' THEN 'Sábado'
            END as dia_semana,
            strftime('%w', h.fecha) as dia_numero,
            COUNT(*) as total_compras,
            SUM(h.cantidad * p.precio) as ingresos,
            AVG(h.cantidad * p.precio) as ticket_promedio
        FROM historial_compras h
        JOIN productos p ON h.producto_id = p.id
        WHERE h.fecha >= date('now', '-30 days')
        GROUP BY strftime('%w', h.fecha)
        ORDER BY dia_numero
    ''').fetchall()
    
    # Detección de productos con baja rotación
    productos_baja_rotacion = conn.execute('''
        SELECT 
            p.id,
            p.nombre,
            p.stock,
            p.precio,
            COALESCE(SUM(h.cantidad), 0) as vendidos_30_dias,
            p.stock / NULLIF(COALESCE(SUM(h.cantidad), 0), 0) as ratio_stock_ventas
        FROM productos p
        LEFT JOIN historial_compras h ON p.id = h.producto_id 
            AND h.fecha >= date('now', '-30 days')
        GROUP BY p.id, p.nombre, p.stock, p.precio
        HAVING vendidos_30_dias < 5 OR ratio_stock_ventas > 10
        ORDER BY ratio_stock_ventas DESC
    ''').fetchall()
    
    conn.close()
    
    return {
        'ventas_semanales': ventas_semanales,
        'productos_categoria': productos_categoria,
        'patrones_semanales': patrones_semanales,
        'productos_baja_rotacion': productos_baja_rotacion
    }

def generate_stock_recommendations():
    """Generar recomendaciones de stock usando IA"""
    conn = get_db_connection()
    
    recomendaciones = []
    productos = conn.execute('SELECT * FROM productos').fetchall()
    
    for producto in productos:
        # Predecir demanda para los próximos 7 días
        demanda_predicha = predict_demand(producto['id'], 7)
        
        # Calcular velocidad de venta (productos vendidos por día)
        velocidad_venta = conn.execute('''
            SELECT AVG(daily_sales) as velocidad
            FROM (
                SELECT DATE(fecha) as dia, SUM(cantidad) as daily_sales
                FROM historial_compras
                WHERE producto_id = ? AND fecha >= date('now', '-14 days')
                GROUP BY DATE(fecha)
            )
        ''', (producto['id'],)).fetchone()
        
        velocidad = velocidad_venta['velocidad'] if velocidad_venta['velocidad'] else 0
        
        # Calcular días de stock restante
        dias_stock = producto['stock'] / velocidad if velocidad > 0 else float('inf')
        
        # Generar recomendación
        if dias_stock < 3:
            urgencia = "CRÍTICO"
            accion = f"Reabastecer inmediatamente. Stock para {dias_stock:.1f} días"
            cantidad_sugerida = max(int(demanda_predicha * 2), 10)
        elif dias_stock < 7:
            urgencia = "ALTO"
            accion = f"Reabastecer pronto. Stock para {dias_stock:.1f} días"
            cantidad_sugerida = max(int(demanda_predicha * 1.5), 5)
        elif dias_stock > 30:
            urgencia = "EXCESO"
            accion = "Considerar promoción para reducir stock"
            cantidad_sugerida = 0
        else:
            urgencia = "NORMAL"
            accion = "Stock adecuado"
            cantidad_sugerida = 0
        
        recomendaciones.append({
            'producto': producto,
            'demanda_predicha': demanda_predicha,
            'velocidad_venta': round(velocidad, 2),
            'dias_stock': round(dias_stock, 1) if dias_stock != float('inf') else 'Infinito',
            'urgencia': urgencia,
            'accion': accion,
            'cantidad_sugerida': cantidad_sugerida
        })
    
    conn.close()
    
    # Ordenar por urgencia
    orden_urgencia = {'CRÍTICO': 0, 'ALTO': 1, 'NORMAL': 2, 'EXCESO': 3}
    recomendaciones.sort(key=lambda x: orden_urgencia.get(x['urgencia'], 4))
    
    return recomendaciones

@app.route('/')
def index():
    """Página principal mejorada"""
    conn = get_db_connection()
    
    # Productos destacados (más populares)
    productos_destacados = conn.execute('''
        SELECT * FROM productos 
        WHERE stock > 0 
        ORDER BY popularidad DESC 
        LIMIT 6
    ''').fetchall()
    
    # Estadísticas para mostrar
    total_productos = conn.execute('SELECT COUNT(*) as count FROM productos').fetchone()['count']
    total_usuarios = conn.execute('SELECT COUNT(*) as count FROM usuarios WHERE role = "user"').fetchone()['count']
    
    conn.close()
    
    return render_template('index.html', 
                         productos_destacados=productos_destacados,
                         total_productos=total_productos,
                         total_usuarios=total_usuarios)

@app.route('/login', methods=['POST'])
def login():
    """Iniciar sesión mejorado"""
    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Por favor ingresa usuario y contraseña', 'error')
            return redirect(url_for('index'))
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM usuarios WHERE username = ?',
            (username,)
        ).fetchone()
        conn.close()
        
        if user and verify_password(password, user['password']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            flash(f'¡Bienvenido {user["username"]}!', 'success')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('user'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        print(f"Error en login: {e}")
        flash('Error al iniciar sesión. Intenta nuevamente.', 'error')
        return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    """Registrar nuevo usuario mejorado"""
    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validaciones
        if not username or not email or not password:
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('index'))
        
        if len(username) < 3:
            flash('El usuario debe tener al menos 3 caracteres', 'error')
            return redirect(url_for('index'))
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return redirect(url_for('index'))
        
        conn = get_db_connection()
        
        # Verificar si el usuario ya existe
        existing_user = conn.execute(
            'SELECT * FROM usuarios WHERE username = ? OR email = ?',
            (username, email)
        ).fetchone()
        
        if existing_user:
            flash('El usuario o email ya existe', 'error')
            conn.close()
            return redirect(url_for('index'))
        
        # Crear nuevo usuario
        hashed_password = hash_password(password)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO usuarios (username, email, password) VALUES (?, ?, ?)',
            (username, email, hashed_password)
        )
        conn.commit()
        conn.close()
        
        flash('¡Usuario registrado exitosamente! Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        print(f"Error en registro: {e}")
        flash('Error al registrar usuario. Intenta nuevamente.', 'error')
        return redirect(url_for('index'))

@app.route('/user')
def user():
    """Página de usuario"""
    if 'user_id' not in session:
        flash('Debes iniciar sesión para acceder', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    productos = conn.execute('SELECT * FROM productos WHERE stock > 0 ORDER BY categoria, nombre').fetchall()
    
    # Obtener items del carrito
    carrito_items = conn.execute('''
        SELECT p.*, c.cantidad, c.id as carrito_id
        FROM carrito c 
        JOIN productos p ON c.producto_id = p.id 
        WHERE c.user_id = ?
        ORDER BY c.created_at DESC
    ''', (session['user_id'],)).fetchall()
    
    # Agrupar productos por categoría
    productos_por_categoria = defaultdict(list)
    for producto in productos:
        productos_por_categoria[producto['categoria']].append(producto)
    
    conn.close()
    
    return render_template('user.html', 
                         productos_por_categoria=productos_por_categoria,
                         carrito_items=carrito_items)

@app.route('/promociones')
def promociones():
    """Página de promociones con IA"""
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver las promociones', 'error')
        return redirect(url_for('index'))
    
    # Obtener recomendaciones personalizadas
    recomendaciones = get_user_recommendations(session['user_id'], limit=8)
    
    conn = get_db_connection()
    
    # Obtener historial del usuario para mostrar estadísticas
    historial_usuario = conn.execute('''
        SELECT p.nombre, p.categoria, SUM(h.cantidad) as total_comprado
        FROM historial_compras h
        JOIN productos p ON h.producto_id = p.id
        WHERE h.user_id = ?
        GROUP BY p.id, p.nombre, p.categoria
        ORDER BY total_comprado DESC
        LIMIT 5
    ''', (session['user_id'],)).fetchall()
    
    # Categoría más comprada
    categoria_favorita = conn.execute('''
        SELECT p.categoria, SUM(h.cantidad) as total
        FROM historial_compras h
        JOIN productos p ON h.producto_id = p.id
        WHERE h.user_id = ?
        GROUP BY p.categoria
        ORDER BY total DESC
        LIMIT 1
    ''', (session['user_id'],)).fetchone()
    
    # Ofertas especiales (productos con descuento simulado)
    ofertas_especiales = conn.execute('''
        SELECT *, ROUND(precio * 0.8, 2) as precio_oferta
        FROM productos 
        WHERE stock > 0 AND popularidad > 80
        ORDER BY RANDOM()
        LIMIT 4
    ''').fetchall()
    
    conn.close()
    
    return render_template('promociones.html',
                         recomendaciones=recomendaciones,
                         historial_usuario=historial_usuario,
                         categoria_favorita=categoria_favorita,
                         ofertas_especiales=ofertas_especiales)

@app.route('/admin')
def admin():
    """Página de administrador"""
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Acceso denegado', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    productos = conn.execute('SELECT * FROM productos ORDER BY categoria, nombre').fetchall()
    usuarios = conn.execute('SELECT id, username, email, role, created_at FROM usuarios ORDER BY created_at DESC').fetchall()
    
    # Estadísticas adicionales
    ventas_por_categoria = conn.execute('''
        SELECT p.categoria, COUNT(*) as ventas, SUM(pd.cantidad * pd.precio_unitario) as ingresos
        FROM pedido_detalles pd
        JOIN productos p ON pd.producto_id = p.id
        GROUP BY p.categoria
        ORDER BY ingresos DESC
    ''').fetchall()
    
    productos_populares = conn.execute('''
        SELECT nombre, popularidad, stock
        FROM productos
        ORDER BY popularidad DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin.html', 
                         productos=productos, 
                         usuarios=usuarios,
                         ventas_por_categoria=ventas_por_categoria,
                         productos_populares=productos_populares)

@app.route('/admin/pedidos')
def admin_pedidos():
    """Gestión de pedidos"""
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Acceso denegado', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    
    pedidos = conn.execute('''
        SELECT 
            p.*,
            u.username,
            COUNT(pd.id) as total_items,
            GROUP_CONCAT(pr.nombre || ' (x' || pd.cantidad || ')') as productos
        FROM pedidos p
        JOIN usuarios u ON p.user_id = u.id
        LEFT JOIN pedido_detalles pd ON p.id = pd.pedido_id
        LEFT JOIN productos pr ON pd.producto_id = pr.id
        GROUP BY p.id
        ORDER BY p.created_at DESC
    ''').fetchall()
    
    stats_pedidos = conn.execute('''
        SELECT 
            COUNT(*) as total_pedidos,
            SUM(total) as ingresos_totales,
            AVG(total) as ticket_promedio,
            COUNT(DISTINCT user_id) as clientes_unicos
        FROM pedidos
        WHERE created_at >= date('now', '-30 days')
    ''').fetchone()
    
    conn.close()
    
    return render_template('admin_pedidos.html', 
                         pedidos=pedidos,
                         stats_pedidos=stats_pedidos)

@app.route('/admin/ventas')
def admin_ventas():
    """Análisis de ventas con IA"""
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Acceso denegado', 'error')
        return redirect(url_for('index'))
    
    # Obtener análisis de tendencias
    analisis = analyze_sales_trends()
    
    return render_template('admin_ventas.html', **analisis)

@app.route('/admin/reportes')
def admin_reportes():
    """Reportes avanzados con IA"""
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Acceso denegado', 'error')
        return redirect(url_for('index'))
    
    # Generar recomendaciones de stock
    recomendaciones_stock = generate_stock_recommendations()
    
    conn = get_db_connection()
    
    # Métricas generales
    metricas = conn.execute('''
        SELECT 
            (SELECT COUNT(*) FROM productos WHERE stock > 0) as productos_disponibles,
            (SELECT COUNT(*) FROM productos WHERE stock <= 5) as productos_bajo_stock,
            (SELECT COUNT(*) FROM usuarios WHERE role = 'user') as total_clientes,
            (SELECT COUNT(*) FROM pedidos WHERE created_at >= date('now', '-7 days')) as pedidos_semana,
            (SELECT ROUND(AVG(total), 2) FROM pedidos WHERE created_at >= date('now', '-30 days')) as ticket_promedio,
            (SELECT SUM(total) FROM pedidos WHERE created_at >= date('now', '-30 days')) as ingresos_mes
    ''').fetchone()
    
    # Top productos por ingresos
    top_productos_ingresos = conn.execute('''
        SELECT 
            p.nombre,
            SUM(h.cantidad * p.precio) as ingresos,
            SUM(h.cantidad) as unidades_vendidas,
            COUNT(DISTINCT h.user_id) as clientes_compraron
        FROM historial_compras h
        JOIN productos p ON h.producto_id = p.id
        WHERE h.fecha >= date('now', '-30 days')
        GROUP BY p.id, p.nombre
        ORDER BY ingresos DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin_reportes.html',
                         recomendaciones_stock=recomendaciones_stock,
                         metricas=metricas,
                         top_productos_ingresos=top_productos_ingresos)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    """Agregar producto al carrito"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Debe iniciar sesión'})
    
    try:
        data = request.get_json()
        producto_id = data['producto_id']
        cantidad = data.get('cantidad', 1)
        
        conn = get_db_connection()
        
        # Verificar stock
        producto = conn.execute('SELECT * FROM productos WHERE id = ?', (producto_id,)).fetchone()
        if not producto or producto['stock'] < cantidad:
            conn.close()
            return jsonify({'success': False, 'message': 'Stock insuficiente'})
        
        # Verificar si el producto ya está en el carrito
        existing_item = conn.execute(
            'SELECT * FROM carrito WHERE user_id = ? AND producto_id = ?',
            (session['user_id'], producto_id)
        ).fetchone()
        
        if existing_item:
            # Actualizar cantidad
            nueva_cantidad = existing_item['cantidad'] + cantidad
            if nueva_cantidad > producto['stock']:
                conn.close()
                return jsonify({'success': False, 'message': 'No hay suficiente stock'})
            
            conn.execute(
                'UPDATE carrito SET cantidad = ? WHERE user_id = ? AND producto_id = ?',
                (nueva_cantidad, session['user_id'], producto_id)
            )
        else:
            # Agregar nuevo item
            conn.execute(
                'INSERT INTO carrito (user_id, producto_id, cantidad) VALUES (?, ?, ?)',
                (session['user_id'], producto_id, cantidad)
            )
        
        # Registrar en historial
        conn.execute(
            'INSERT INTO historial_compras (user_id, producto_id, cantidad) VALUES (?, ?, ?)',
            (session['user_id'], producto_id, cantidad)
        )
        
        # Actualizar popularidad del producto
        conn.execute(
            'UPDATE productos SET popularidad = popularidad + ? WHERE id = ?',
            (cantidad, producto_id)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Producto agregado al carrito'})
        
    except Exception as e:
        print(f"Error al agregar al carrito: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'})

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    """Remover producto del carrito"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Debe iniciar sesión'})
    
    try:
        data = request.get_json()
        carrito_id = data['carrito_id']
        
        conn = get_db_connection()
        conn.execute(
            'DELETE FROM carrito WHERE id = ? AND user_id = ?',
            (carrito_id, session['user_id'])
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Producto removido del carrito'})
        
    except Exception as e:
        print(f"Error al remover del carrito: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'})

@app.route('/checkout', methods=['POST'])
def checkout():
    """Procesar compra"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Debe iniciar sesión'})
    
    try:
        conn = get_db_connection()
        
        # Obtener items del carrito
        carrito_items = conn.execute('''
            SELECT c.*, p.precio, p.nombre, p.stock
            FROM carrito c
            JOIN productos p ON c.producto_id = p.id
            WHERE c.user_id = ?
        ''', (session['user_id'],)).fetchall()
        
        if not carrito_items:
            conn.close()
            return jsonify({'success': False, 'message': 'El carrito está vacío'})
        
        # Calcular total y verificar stock
        total = 0
        for item in carrito_items:
            if item['stock'] < item['cantidad']:
                conn.close()
                return jsonify({'success': False, 'message': f'Stock insuficiente para {item["nombre"]}'})
            total += item['precio'] * item['cantidad']
        
        # Crear pedido
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO pedidos (user_id, total) VALUES (?, ?)',
            (session['user_id'], total)
        )
        pedido_id = cursor.lastrowid
        
        # Crear detalles del pedido y actualizar stock
        for item in carrito_items:
            cursor.execute('''
                INSERT INTO pedido_detalles (pedido_id, producto_id, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?)
            ''', (pedido_id, item['producto_id'], item['cantidad'], item['precio']))
            
            # Actualizar stock
            cursor.execute(
                'UPDATE productos SET stock = stock - ? WHERE id = ?',
                (item['cantidad'], item['producto_id'])
            )
        
        # Limpiar carrito
        cursor.execute('DELETE FROM carrito WHERE user_id = ?', (session['user_id'],))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Compra realizada exitosamente. Total: ${total:.2f}'})
        
    except Exception as e:
        print(f"Error en checkout: {e}")
        return jsonify({'success': False, 'message': 'Error al procesar la compra'})

@app.route('/add_product', methods=['POST'])
def add_product():
    """Agregar nuevo producto (solo admin)"""
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Acceso denegado', 'error')
        return redirect(url_for('index'))
    
    try:
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = float(request.form['precio'])
        categoria = request.form['categoria']
        stock = int(request.form['stock'])
        imagen = request.form.get('imagen', '/static/images/default.jpg')
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO productos (nombre, descripcion, precio, imagen, categoria, stock, popularidad)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nombre, descripcion, precio, imagen, categoria, stock, 0))
        conn.commit()
        conn.close()
        
        flash('Producto agregado exitosamente', 'success')
        return redirect(url_for('admin'))
        
    except Exception as e:
        print(f"Error al agregar producto: {e}")
        flash('Error al agregar producto', 'error')
        return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    username = session.get('username', 'Usuario')
    session.clear()
    flash(f'¡Hasta luego {username}!', 'info')
    return redirect(url_for('index'))

# ============= ALGORITMOS DE CLUSTERING K-MEANS=============

def extract_customer_features():
    """Extraer características de los clientes para clustering"""
    conn = get_db_connection()
    
    customers_data = conn.execute('''
        SELECT 
            u.id,
            u.username,
            COUNT(DISTINCT h.id) as total_compras,
            SUM(h.cantidad * p.precio) as total_gastado,
            AVG(h.cantidad * p.precio) as monto_promedio,
            COUNT(DISTINCT h.producto_id) as productos_unicos,
            COUNT(DISTINCT p.categoria) as categorias_compradas,
            julianday('now') - julianday(MAX(h.fecha)) as dias_desde_ultima_compra,
            julianday(MAX(h.fecha)) - julianday(MIN(h.fecha)) as periodo_actividad
        FROM usuarios u
        JOIN historial_compras h ON u.id = h.user_id
        JOIN productos p ON h.producto_id = p.id
        WHERE u.role = 'user'
        GROUP BY u.id, u.username
        HAVING total_compras > 0
    ''').fetchall()
    
    if not customers_data:
        conn.close()
        return None, None
    
    features = []
    customer_info = []
    
    for customer in customers_data:
        categoria_favorita = conn.execute('''
            SELECT p.categoria, COUNT(*) as frecuencia
            FROM historial_compras h
            JOIN productos p ON h.producto_id = p.id
            WHERE h.user_id = ?
            GROUP BY p.categoria
            ORDER BY frecuencia DESC
            LIMIT 1
        ''', (customer['id'],)).fetchone()
        
        periodo_semanas = max(customer['periodo_actividad'] / 7, 1)
        frecuencia_compra = customer['total_compras'] / periodo_semanas
        
        feature_vector = [
            frecuencia_compra,
            customer['monto_promedio'],
            customer['total_gastado'],
            customer['dias_desde_ultima_compra'],
            customer['productos_unicos'],
            customer['categorias_compradas']
        ]
        
        features.append(feature_vector)
        customer_info.append({
            'id': customer['id'],
            'username': customer['username'],
            'total_compras': customer['total_compras'],
            'total_gastado': customer['total_gastado'],
            'monto_promedio': customer['monto_promedio'],
            'productos_unicos': customer['productos_unicos'],
            'dias_desde_ultima_compra': customer['dias_desde_ultima_compra'],
            'frecuencia_compra': frecuencia_compra,
            'categoria_favorita': categoria_favorita['categoria'] if categoria_favorita else 'Sin categoría'
        })
    
    conn.close()
    return np.array(features), customer_info

def assign_cluster_names_intelligently(clustering_result):
    """Asignar nombres únicos a clusters basado en características reales"""
    cluster_analysis = clustering_result['cluster_analysis']
    
    clusters_with_metrics = []
    for cluster_id, analysis in cluster_analysis.items():
        frequency_score = min(analysis['avg_frequency'] * 20, 100)  
        spending_score = min(analysis['avg_total_spent'] / 2, 100) 
        recency_score = max(0, 100 - analysis['avg_days_since_last']) 
        
        composite_score = (frequency_score * 0.4) + (spending_score * 0.4) + (recency_score * 0.2)
        
        clusters_with_metrics.append({
            'cluster_id': cluster_id,
            'composite_score': composite_score,
            'avg_frequency': analysis['avg_frequency'],
            'avg_total_spent': analysis['avg_total_spent'],
            'avg_days_since_last': analysis['avg_days_since_last'],
            'count': analysis['count']
        })

    clusters_with_metrics.sort(key=lambda x: x['composite_score'], reverse=True)
    
    cluster_names = {}
    cluster_colors = {}
    used_names = set()  
    

    for i, cluster_info in enumerate(clusters_with_metrics):
        cluster_id = cluster_info['cluster_id']
        freq = cluster_info['avg_frequency']
        spent = cluster_info['avg_total_spent']
        days = cluster_info['avg_days_since_last']
        
        if i == 0 and spent > 100:  
            name = "VIP Premium"
            color = "#FF6B6B"
        elif freq >= 4.0 and "Cliente Frecuente" not in used_names: 
            name = "Cliente Frecuente"
            color = "#4ECDC4"
        elif spent >= 80 and days <= 20 and "Cliente Valioso" not in used_names: 
            name = "Cliente Valioso"
            color = "#45B7D1"
        elif days > 30 and "Cliente Inactivo" not in used_names:  
            name = "Cliente Inactivo"
            color = "#96CEB4"
        elif freq >= 2.0 and "Cliente Regular" not in used_names: 
            name = "Cliente Regular"
            color = "#FFA726"
        elif "Cliente Casual" not in used_names:
            name = "Cliente Casual"
            color = "#FFEAA7"
        else: 
            name = f"Cluster Especial {cluster_id}"
            color = "#E0E0E0"
        
        cluster_names[cluster_id] = name
        cluster_colors[cluster_id] = color
        used_names.add(name)
    
    return cluster_names, cluster_colors

def perform_kmeans_clustering(n_clusters=4):
    """Realizar clustering K-Means de clientes"""
    features, customer_info = extract_customer_features()
    
    if features is None or len(features) < n_clusters:
        return None
    
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(features_scaled)
    
    cluster_analysis = {}
    for i in range(n_clusters):
        cluster_mask = cluster_labels == i
        cluster_features = features[cluster_mask]
        
        if len(cluster_features) > 0:
            cluster_analysis[i] = {
                'count': len(cluster_features),
                'avg_frequency': np.mean(cluster_features[:, 0]),
                'avg_amount': np.mean(cluster_features[:, 1]),
                'avg_total_spent': np.mean(cluster_features[:, 2]),
                'avg_days_since_last': np.mean(cluster_features[:, 3]),
                'avg_unique_products': np.mean(cluster_features[:, 4])
            }
    
    temp_result = {'cluster_analysis': cluster_analysis}
    cluster_names, cluster_colors = assign_cluster_names_intelligently(temp_result)
    
    for cluster_id in cluster_analysis:
        cluster_analysis[cluster_id]['name'] = cluster_names.get(cluster_id, f'Cluster {cluster_id}')
        cluster_analysis[cluster_id]['color'] = cluster_colors.get(cluster_id, '#CCCCCC')
    
    clustered_customers = []
    for i, customer in enumerate(customer_info):
        cluster_id = int(cluster_labels[i])
        customer['cluster_id'] = cluster_id
        customer['cluster_name'] = cluster_names.get(cluster_id, f'Cluster {cluster_id}')
        clustered_customers.append(customer)
    
    return {
        'customers': clustered_customers,
        'cluster_analysis': cluster_analysis,
        'cluster_names': cluster_names,
        'cluster_colors': cluster_colors,
        'features': features,
        'features_scaled': features_scaled,
        'cluster_labels': cluster_labels,
        'scaler': scaler,
        'kmeans': kmeans
    }

def save_customer_clusters():
    """Guardar clusters de clientes en la base de datos"""
    clustering_result = perform_kmeans_clustering()
    
    if not clustering_result:
        return False
    
    conn = get_db_connection()
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS customer_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            cluster_id INTEGER,
            cluster_name TEXT,
            frecuencia_compra REAL,
            monto_promedio REAL,
            total_gastado REAL,
            dias_desde_ultima_compra INTEGER,
            productos_unicos INTEGER,
            categoria_favorita TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES usuarios (id)
        )
    ''')
    
    conn.execute('DELETE FROM customer_clusters')
    
    for customer in clustering_result['customers']:
        conn.execute('''
            INSERT INTO customer_clusters 
            (user_id, cluster_id, cluster_name, frecuencia_compra, monto_promedio, 
             total_gastado, dias_desde_ultima_compra, productos_unicos, categoria_favorita)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            customer['id'],
            customer['cluster_id'],
            customer['cluster_name'],
            customer['frecuencia_compra'],
            customer['monto_promedio'],
            customer['total_gastado'],
            customer['dias_desde_ultima_compra'],
            customer['productos_unicos'],
            customer['categoria_favorita']
        ))
    
    conn.commit()
    conn.close()
    return True

def generate_cluster_visualization():
    """Generar visualizaciones de los clusters"""
    clustering_result = perform_kmeans_clustering()
    
    if not clustering_result:
        return None
    
    plt.style.use('default')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Análisis de Clusters de Clientes', fontsize=16, fontweight='bold')
    
    customers = clustering_result['customers']
    df = pd.DataFrame(customers)
    
    # Gráfico 1: Distribución de clusters
    cluster_counts = df['cluster_name'].value_counts()
    colors = [clustering_result['cluster_colors'].get(
        next(cluster_id for cluster_id, analysis in clustering_result['cluster_analysis'].items() 
             if analysis['name'] == name), '#CCCCCC'
    ) for name in cluster_counts.index]
    
    axes[0, 0].pie(cluster_counts.values, labels=cluster_counts.index, autopct='%1.1f%%', 
                   startangle=90, colors=colors)
    axes[0, 0].set_title('Distribución de Clientes por Cluster')
    
    # Gráfico 2: Frecuencia vs Monto Promedio
    for cluster_name in df['cluster_name'].unique():
        cluster_data = df[df['cluster_name'] == cluster_name]
        cluster_id = cluster_data.iloc[0]['cluster_id']
        color = clustering_result['cluster_colors'].get(cluster_id, '#CCCCCC')
        axes[0, 1].scatter(cluster_data['frecuencia_compra'], cluster_data['monto_promedio'], 
                          c=color, label=cluster_name, alpha=0.7, s=60)
    
    axes[0, 1].set_xlabel('Frecuencia de Compra (por semana)')
    axes[0, 1].set_ylabel('Monto Promedio por Compra ($)')
    axes[0, 1].set_title('Frecuencia vs Monto Promedio')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Gráfico 3: Total gastado por cluster
    cluster_spending = df.groupby('cluster_name')['total_gastado'].mean()
    colors_bar = [clustering_result['cluster_colors'].get(
        next(cluster_id for cluster_id, analysis in clustering_result['cluster_analysis'].items() 
             if analysis['name'] == name), '#CCCCCC'
    ) for name in cluster_spending.index]
    
    bars = axes[1, 0].bar(cluster_spending.index, cluster_spending.values, color=colors_bar)
    axes[1, 0].set_title('Gasto Promedio por Cluster')
    axes[1, 0].set_ylabel('Total Gastado ($)')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    for bar in bars:
        height = bar.get_height()
        axes[1, 0].text(bar.get_x() + bar.get_width()/2., height,
                       f'${height:.2f}', ha='center', va='bottom')
    
    # Gráfico 4: Días desde última compra
    cluster_recency = df.groupby('cluster_name')['dias_desde_ultima_compra'].mean()
    bars = axes[1, 1].bar(cluster_recency.index, cluster_recency.values, color=colors_bar)
    axes[1, 1].set_title('Días Promedio Desde Última Compra')
    axes[1, 1].set_ylabel('Días')
    axes[1, 1].tick_params(axis='x', rotation=45)
    
    for bar in bars:
        height = bar.get_height()
        axes[1, 1].text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}', ha='center', va='bottom')
    
    plt.tight_layout()
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    plot_data = buffer.getvalue()
    buffer.close()
    plt.close()
    
    plot_url = base64.b64encode(plot_data).decode()
    return plot_url

def get_cluster_recommendations_dynamic(cluster_id, cluster_name, cluster_analysis):
    """Obtener recomendaciones basadas en el nombre real del cluster"""
    
    analysis = cluster_analysis.get(cluster_id, {})
    avg_frequency = analysis.get('avg_frequency', 0)
    avg_total_spent = analysis.get('avg_total_spent', 0)
    avg_days_since_last = analysis.get('avg_days_since_last', 0)
    
    recommendations_map = {
        "VIP Premium": {
            'title': 'Clientes VIP Premium',
            'description': f'Clientes de máximo valor: {avg_frequency:.1f} compras/sem, ${avg_total_spent:.2f} gastado',
            'strategies': [
                'Programa de lealtad exclusivo con beneficios premium',
                'Acceso anticipado a nuevos productos',
                'Descuentos por volumen en compras grandes',
                'Servicio personalizado y atención prioritaria',
                'Eventos exclusivos y degustaciones privadas'
            ],
            'color': '#FF6B6B'
        },
        "Cliente Frecuente": {
            'title': 'Clientes Frecuentes',
            'description': f'Clientes muy activos: {avg_frequency:.1f} compras/sem, visitas regulares',
            'strategies': [
                'Tarjeta de fidelidad con sellos por visita',
                'Descuentos por frecuencia de compra',
                'Ofertas especiales en horarios de mayor visita',
                'Programa "compra 10, lleva 1 gratis"',
                'Reconocimiento como cliente preferencial'
            ],
            'color': '#4ECDC4'
        },
        "Cliente Valioso": {
            'title': 'Clientes Valiosos',
            'description': f'Clientes de alto potencial: {avg_frequency:.1f} compras/sem, ${avg_total_spent:.2f} gastado',
            'strategies': [
                'Incentivos para aumentar frecuencia de visita',
                'Ofertas personalizadas basadas en historial',
                'Programa de referidos con beneficios',
                'Promociones en categorías favoritas',
                'Comunicación regular con ofertas especiales'
            ],
            'color': '#45B7D1'
        },
        "Cliente Regular": {
            'title': 'Clientes Regulares',
            'description': f'Clientes consistentes: {avg_frequency:.1f} compras/sem, comportamiento estable',
            'strategies': [
                'Programa de puntos por compras regulares',
                'Ofertas en productos complementarios',
                'Recordatorios de productos favoritos',
                'Promociones de temporada',
                'Newsletter con novedades y ofertas'
            ],
            'color': '#FFA726'
        },
        "Cliente Casual": {
            'title': 'Clientes Casuales',
            'description': f'Clientes ocasionales: {avg_frequency:.1f} compras/sem, ${avg_total_spent:.2f} gastado',
            'strategies': [
                'Ofertas de bienvenida para incentivar retorno',
                'Promociones en productos de entrada',
                'Combos y paquetes atractivos',
                'Campañas de reactivación por email',
                'Descuentos en segunda compra'
            ],
            'color': '#FFEAA7'
        },
        "Cliente Inactivo": {
            'title': 'Clientes Inactivos',
            'description': f'Clientes sin actividad reciente: {avg_days_since_last:.0f} días desde última compra',
            'strategies': [
                'Campañas de reactivación agresivas',
                'Descuentos significativos para volver',
                'Encuestas para entender razones de inactividad',
                'Ofertas "te extrañamos" personalizadas',
                'Muestras gratuitas de nuevos productos'
            ],
            'color': '#96CEB4'
        }
    }
    
    if cluster_name in recommendations_map:
        return recommendations_map[cluster_name]
    
    return {
        'title': cluster_name,
        'description': f'Grupo específico: {avg_frequency:.1f} compras/sem, ${avg_total_spent:.2f} gastado, {avg_days_since_last:.0f} días última compra',
        'strategies': [
            'Análisis detallado del comportamiento del grupo',
            'Estrategias personalizadas basadas en características únicas',
            'Monitoreo continuo para optimizar approach'
        ],
        'color': analysis.get('color', '#CCCCCC')
    }
    

@app.route('/admin/clustering')
def admin_clustering():
    """Página de análisis de clustering de clientes"""
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Acceso denegado', 'error')
        return redirect(url_for('index'))
    
    clustering_result = perform_kmeans_clustering()
    
    if not clustering_result:
        flash('No hay suficientes datos para realizar clustering', 'warning')
        return redirect(url_for('admin'))
    
    plot_url = generate_cluster_visualization()
    
    cluster_recommendations = {}
    for cluster_id, analysis in clustering_result['cluster_analysis'].items():
        cluster_name = analysis['name']
        cluster_recommendations[cluster_id] = get_cluster_recommendations_dynamic(
            cluster_id, cluster_name, clustering_result['cluster_analysis']
        )
    
    return render_template('admin_clustering.html',
                         clustering_result=clustering_result,
                         plot_url=plot_url,
                         cluster_recommendations=cluster_recommendations)

@app.route('/admin/clustering/update', methods=['POST'])
def update_clustering():
    """Actualizar clustering de clientes"""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Acceso denegado'})
    
    try:
        success = save_customer_clusters()
        if success:
            return jsonify({'success': True, 'message': 'Clustering actualizado exitosamente'})
        else:
            return jsonify({'success': False, 'message': 'No hay suficientes datos para clustering'})
    except Exception as e:
        print(f"Error al actualizar clustering: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'})


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("Inicializando aplicación...")
    init_db()
    print("¡Aplicación lista!")
    print("Accede a: http://localhost:5000")
    print("Usuario admin: admin / admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)
