"""Acceso a datos del inventario: materiales y kardex."""

# Tipos fecha y duración
from datetime import date, timedelta
# Decimal = número decimal exacto
from decimal import Decimal

# and_ = AND; case = CASE WHEN; exists = EXISTS; or_ = OR; select = SELECT
from sqlalchemy import and_, case, exists, or_, select
# Sesión de base de datos
from sqlalchemy.orm import Session

# Modelos de las tablas usadas
from app.models import Material, MovimientoInventario, Receta, RecetaIngrediente
# Funciones para contar y paginar
from app.repositories.paginacion import contar, paginar
# Estados del stock y filtros
from app.schemas.inventario import EstadoStock, FiltrosKardex, FiltrosMaterial


# Construye la expresión SQL que calcula el estado del stock de cada material
def expresion_estado(limite_vencimiento: date, factor_critico: Decimal):
    """Estado del stock calculado por PostgreSQL (RF32). El orden importa:
    primero vencimiento, luego crítico, luego bajo; si no, bueno."""
    # CASE WHEN ... THEN ... ELSE ... END
    return case(
        # WHEN tiene fecha de vencimiento Y vence antes o en la fecha límite...
        (and_(Material.fecha_vencimiento.is_not(None), Material.fecha_vencimiento <= limite_vencimiento),
         # ...THEN 'VENCIENDO'
         EstadoStock.VENCIENDO.value),
        # WHEN stock <= mínimo x 0.5 THEN 'CRITICO'
        (Material.stock <= Material.stock_minimo * factor_critico, EstadoStock.CRITICO.value),
        # WHEN stock <= mínimo THEN 'BAJO'
        (Material.stock <= Material.stock_minimo, EstadoStock.BAJO.value),
        # ELSE 'BUENO'
        else_=EstadoStock.BUENO.value,
    )


# Clase con todas las consultas del inventario
class InventarioRepository:
    # Constructor: recibe la sesión de base de datos
    def __init__(self, db: Session) -> None:
        # Guarda la sesión
        self.db = db

    # ----- Materiales -----

    # Busca un material por su id
    def obtener_material(self, material_id: int) -> Material | None:
        # SELECT por llave primaria
        return self.db.get(Material, material_id)

    # Busca un material junto con su estado de stock
    def obtener_con_estado(self, material_id: int, limite: date, factor: Decimal) -> tuple[Material, str] | None:
        # Ejecuta la consulta y toma la primera fila (o None)
        fila = self.db.execute(
            # SELECT materiales.*, CASE ... AS estado WHERE id = :id
            select(Material, expresion_estado(limite, factor)).where(Material.id == material_id)
        ).first()  # .first(): primera fila o None si no hay resultados
        # Devuelve (material, estado) o None si no existe
        return (fila[0], fila[1]) if fila else None

    # Lee un material bloqueando su fila
    def obtener_para_actualizar(self, material_id: int) -> Material | None:
        """SELECT ... FOR UPDATE: dos salidas simultáneas no dejan el stock negativo."""
        # Arma la consulta
        consulta = (
            # SELECT * FROM materiales
            select(Material)
            # WHERE id = :id
            .where(Material.id == material_id)
            # FOR UPDATE: bloquea la fila hasta el commit
            .with_for_update()
            # Lee el stock real de la base de datos, no el que estaba en memoria
            .execution_options(populate_existing=True)
        )
        # Ejecuta y devuelve el material (o None)
        return self.db.scalar(consulta)

    # Indica si ya existe un material con ese código de barras
    def existe_codigo(self, codigo_barras: str) -> bool:
        # SELECT EXISTS (... WHERE codigo_barras = :codigo)
        return self.db.scalar(select(exists().where(Material.codigo_barras == codigo_barras)))

    # Lista materiales con su estado, filtros y paginación
    def listar_materiales(self, filtros: FiltrosMaterial, limite: date, factor: Decimal) -> tuple[list[tuple[Material, str]], int]:
        # Expresión CASE del estado
        estado = expresion_estado(limite, factor)
        # Consulta base: materiales con su estado, con el estado activo pedido, ordenados por nombre
        consulta = select(Material, estado).where(Material.activo == filtros.activo).order_by(Material.nombre)
        # Si se envió texto para buscar...
        if filtros.buscar:
            # Patrón para coincidencia parcial
            patron = f"%{filtros.buscar}%"
            # Busca en el nombre O en el código de barras
            consulta = consulta.where(or_(Material.nombre.ilike(patron), Material.codigo_barras.ilike(patron)))
        # Si se filtró por categoría...
        if filtros.categoria:
            # ...WHERE categoria = :categoria
            consulta = consulta.where(Material.categoria == filtros.categoria)
        # Si se filtró por estado...
        if filtros.estado:
            # ...WHERE (CASE ...) = :estado
            consulta = consulta.where(estado == filtros.estado.value)
        # Ejecuta la página pedida (OFFSET y LIMIT); cada fila es (material, estado)
        filas = self.db.execute(consulta.offset((filtros.pagina - 1) * filtros.tamano).limit(filtros.tamano)).all()
        # Devuelve la lista de (material, estado) y el total
        return [(fila[0], fila[1]) for fila in filas], contar(self.db, consulta)

    # Indica si el material tiene movimientos en el kardex
    def tiene_movimientos(self, material_id: int) -> bool:
        # SELECT EXISTS (SELECT ... FROM movimientos_inventario WHERE material_id = :id)
        return self.db.scalar(select(exists().where(MovimientoInventario.material_id == material_id)))

    # Indica si el material está en alguna receta
    def usado_en_recetas(self, material_id: int) -> bool:
        """True si alguna receta (activa o no) tiene el material en su fórmula."""
        # SELECT EXISTS (SELECT ... FROM receta_ingredientes WHERE material_id = :id)
        return self.db.scalar(select(exists().where(RecetaIngrediente.material_id == material_id)))

    # Devuelve los nombres de las recetas activas que usan el material
    def recetas_activas_que_usan(self, material_id: int) -> list[str]:
        # Arma la consulta
        consulta = (
            # SELECT recetas.nombre
            select(Receta.nombre)
            # JOIN receta_ingredientes
            .join(RecetaIngrediente, RecetaIngrediente.receta_id == Receta.id)
            # Que usen el material y estén activas
            .where(RecetaIngrediente.material_id == material_id, Receta.activo)
            # Ordenadas por nombre
            .order_by(Receta.nombre)
        )
        # Ejecuta y devuelve la lista de nombres
        return list(self.db.scalars(consulta))

    # Crea un material y, si trae stock inicial, su primera ENTRADA
    def crear_material(self, material: Material, movimiento: MovimientoInventario | None) -> Material:
        """Crea el material y, si trae stock inicial, su primera ENTRADA del kardex."""
        # INSERT del material
        self.db.add(material)
        self.db.flush()  # obtiene el id del material antes del commit
        # Si hay movimiento inicial...
        if movimiento is not None:
            # ...le asigna el id del material recién creado
            movimiento.material_id = material.id
            # INSERT del movimiento
            self.db.add(movimiento)
        # Confirma el material y su movimiento juntos
        self.db.commit()
        # Vuelve a leer el material
        self.db.refresh(material)
        # Devuelve el material creado
        return material

    # Guarda un material modificado
    def guardar(self, material: Material) -> Material:
        # UPDATE
        self.db.add(material)
        # Confirma
        self.db.commit()
        # Vuelve a leer la fila
        self.db.refresh(material)
        # Devuelve el material
        return material

    # Borra un material definitivamente
    def eliminar(self, material: Material) -> None:
        # Marca la fila para DELETE
        self.db.delete(material)
        # Confirma el borrado
        self.db.commit()

    # ----- Kardex -----

    # Guarda un movimiento del kardex
    def registrar_movimiento(self, movimiento: MovimientoInventario) -> MovimientoInventario:
        """Guarda el movimiento y el nuevo stock del material en una sola transacción."""
        # INSERT del movimiento (el UPDATE del stock ya está pendiente en la sesión)
        self.db.add(movimiento)
        # Confirma los dos cambios juntos
        self.db.commit()
        # Vuelve a leer el movimiento
        self.db.refresh(movimiento)
        # Devuelve el movimiento guardado
        return movimiento

    # Lista el kardex con filtros y paginación
    def listar_kardex(self, filtros: FiltrosKardex) -> tuple[list[MovimientoInventario], int]:
        # Consulta base: movimientos del más reciente al más antiguo
        consulta = select(MovimientoInventario).order_by(
            # Por fecha descendente y luego por id descendente
            MovimientoInventario.creado_en.desc(), MovimientoInventario.id.desc()
        )
        # Si se filtró por material...
        if filtros.material_id is not None:
            # ...WHERE material_id = :id
            consulta = consulta.where(MovimientoInventario.material_id == filtros.material_id)
        # Si se filtró por tipo...
        if filtros.tipo:
            # ...WHERE tipo = :tipo
            consulta = consulta.where(MovimientoInventario.tipo == filtros.tipo)
        # Si se envió fecha inicial...
        if filtros.desde:
            # ...WHERE creado_en >= :desde
            consulta = consulta.where(MovimientoInventario.creado_en >= filtros.desde)
        # Si se envió fecha final...
        if filtros.hasta:
            # "hasta" incluye todo ese día
            # WHERE creado_en < (hasta + 1 día)
            consulta = consulta.where(MovimientoInventario.creado_en < filtros.hasta + timedelta(days=1))
        # Ejecuta la consulta paginada
        return paginar(self.db, consulta, filtros.pagina, filtros.tamano)
