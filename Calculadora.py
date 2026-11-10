import ast
import math
import operator
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk


# FASE 4: CLASE PERSISTENCIA DE DATOS (SQLite)
class GestorHistorial:
    """Clase encargada de la persistencia en SQLite (DAO)."""

    def __init__(self, db_name="historial_calculadora.db"):
        self.db_name = db_name
        self._crear_tabla()

    def _conectar(self):
        return sqlite3.connect(self.db_name)

    def _crear_tabla(self):
        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS historial (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        expresion TEXT NOT NULL,
                        resultado TEXT NOT NULL,
                        fecha_hora TEXT NOT NULL
                    )
                """
                )
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error al inicializar la base de datos: {e}")

    def guardar_operacion(self, expresion: str, resultado: str):
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO historial (expresion, resultado, fecha_hora)
                    VALUES (?, ?, ?)
                """,
                    (expresion, str(resultado), fecha_hora),
                )
                conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Error al guardar en el historial: {e}") from e

    def obtener_historial(self):
        try:
            with self._conectar() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT expresion, resultado, fecha_hora FROM historial ORDER BY id DESC"
                )
                return cursor.fetchall()
        except sqlite3.Error as e:
            raise RuntimeError(f"Error al consultar el historial: {e}") from e


# FASE 2 & 4: CLASE MODELO (Lógica Matemática, Memoria y Funciones Avanzadas)
class ModeloCalculadora:
    """Lógica matemática avanzada, gestión de memoria y evaluación segura con AST."""

    def __init__(self, gestor_historial: GestorHistorial):
        self.gestor_historial = gestor_historial
        self.memoria = 0.0  # FASE 2: Memoria de operaciones

    _BIN_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,  # 1. Módulo (%)
        ast.Pow: operator.pow,  # 2. Exponencial (**)
    }

    _UNARY_OPS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    _FUNCS = {
        "abs": abs,  # 3. Valor absoluto
        "log": math.log10,  # 4. Logaritmo en base 10
    }

    def _eval_ast(self, node):
        if isinstance(node, ast.Expression):
            return self._eval_ast(node.body)

        if isinstance(node, ast.Constant) and isinstance(
            node.value, (int, float)
        ):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in self._BIN_OPS:
            left = self._eval_ast(node.left)
            right = self._eval_ast(node.right)
            if isinstance(node.op, ast.Div) and right == 0:
                raise ZeroDivisionError("No se puede dividir entre cero.")
            if isinstance(node.op, ast.Mod) and right == 0:
                raise ZeroDivisionError("Módulo entre cero no permitido.")
            return self._BIN_OPS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in self._UNARY_OPS:
            operand = self._eval_ast(node.operand)
            return self._UNARY_OPS[type(node.op)](operand)

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self._FUNCS and len(node.args) == 1:
                arg_val = self._eval_ast(node.args[0])
                if func_name == "log" and arg_val <= 0:
                    raise ValueError("Logaritmo requiere valor positivo.")
                return self._FUNCS[func_name](arg_val)

        raise ValueError("Expresión no permitida o sintaxis errónea.")

    def calcular(self, expresion: str):
        expresion_limpia = (expresion or "").strip()

        if not expresion_limpia:
            raise ValueError("La expresión está vacía.")

        try:
            tree = ast.parse(expresion_limpia, mode="eval")
            resultado = self._eval_ast(tree)
        except ZeroDivisionError:
            raise
        except ValueError:
            raise
        except Exception as e:
            raise ValueError("Sintaxis de expresión incorrecta.") from e

        if isinstance(resultado, float) and resultado.is_integer():
            resultado = int(resultado)

        self.gestor_historial.guardar_operacion(expresion_limpia, resultado)
        return resultado

    # Métodos de Memoria de Operaciones
    def memoria_limpiar(self):
        self.memoria = 0.0

    def memoria_recuperar(self):
        return self.memoria

    def memoria_sumar(self, valor: float):
        self.memoria += valor

    def memoria_restar(self, valor: float):
        self.memoria -= valor

    def consultar_historial(self):
        return self.gestor_historial.obtener_historial()


# FASE 3 & 4: CLASE VISTA (Interfaz Gráfica, Temas y Atajos)
class VistaCalculadora(tk.Tk):
    """Interfaz gráfica dinámica con soporte de modo oscuro/claro y atajos de teclado."""

    # Paletas de color para Temas
    TEMAS = {
        "oscuro": {
            "bg_ventana": "#1e272e",
            "bg_pantalla": "#2f3640",
            "fg_pantalla": "#f5f6fa",
            "btn_num": "#34495e",
            "btn_op": "#f39c12",
            "btn_mem": "#27ae60",
            "btn_clear": "#e74c3c",
            "btn_hist": "#8e44ad",
            "fg_texto": "#ffffff",
        },
        "claro": {
            "bg_ventana": "#dcdde1",
            "bg_pantalla": "#f5f6fa",
            "fg_pantalla": "#2f3640",
            "btn_num": "#f5f6fa",
            "btn_op": "#e67e22",
            "btn_mem": "#2ecc71",
            "btn_clear": "#e74c3c",
            "btn_hist": "#9b59b6",
            "fg_texto": "#2f3640",
        },
    }

    def __init__(self, modelo: ModeloCalculadora):
        super().__init__()
        self.modelo = modelo
        self.modo_actual = "oscuro"

        self.title("Calculadora Avanzada POO")
        self.geometry("450x650")

        # Pantalla Principal
        self.pantalla_var = tk.StringVar()
        self.pantalla = tk.Entry(
            self,
            textvariable=self.pantalla_var,
            font=("Arial", 26, "bold"),
            bd=0,
            justify="right",
            insertwidth=4,
        )
        self.pantalla.grid(
            row=0,
            column=0,
            columnspan=4,
            ipady=15,
            padx=10,
            pady=(15, 5),
            sticky="nsew",
        )

        self.botones_dict = {}
        self.inicializar_botones()
        self.aplicar_tema()
        self.configurar_atajos_teclado()

    def inicializar_botones(self):
        """Genera el grid de botones incluyendo memoria, funciones avanzadas e historial."""
        botones_config = [
            # Fila 1: Gestión de Memoria
            ("MC", 1, 0, "mem"),
            ("MR", 1, 1, "mem"),
            ("M+", 1, 2, "mem"),
            ("M-", 1, 3, "mem"),
            # Fila 2: Funciones Extras (Módulo, Exponencial, Logaritmo, Valor Absoluto)
            ("mod", 2, 0, "op"),
            ("^", 2, 1, "op"),
            ("log", 2, 2, "op"),
            ("abs", 2, 3, "op"),
            # Fila 3: Control y División
            ("C", 3, 0, "clear"),
            ("(", 3, 1, "op"),
            (")", 3, 2, "op"),
            ("/", 3, 3, "op"),
            # Fila 4: Números y Multiplicación
            ("7", 4, 0, "num"),
            ("8", 4, 1, "num"),
            ("9", 4, 2, "num"),
            ("*", 4, 3, "op"),
            # Fila 5: Números y Resta
            ("4", 5, 0, "num"),
            ("5", 5, 1, "num"),
            ("6", 5, 2, "num"),
            ("-", 5, 3, "op"),
            # Fila 6: Números y Suma
            ("1", 6, 0, "num"),
            ("2", 6, 1, "num"),
            ("3", 6, 2, "num"),
            ("+", 6, 3, "op"),
            # Fila 7: Cero, Punto, Negativo, Igual
            ("0", 7, 0, "num"),
            (".", 7, 1, "num"),
            ("+/-", 7, 2, "num"),
            ("=", 7, 3, "op"),
            # Fila 8: Controles Extras (Historial y Cambiar Tema)
            ("HISTORIAL", 8, 0, "hist"),
            ("TEMA", 8, 2, "hist"),
        ]

        for texto, fila, col, cat in botones_config:
            if texto in ["HISTORIAL", "TEMA"]:
                cmd = (
                    self.mostrar_ventana_historial
                    if texto == "HISTORIAL"
                    else self.alternar_tema
                )
                label = "📋 Historial" if texto == "HISTORIAL" else "🌓 Tema"
                btn = tk.Button(
                    self,
                    text=label,
                    font=("Arial", 10, "bold"),
                    bd=0,
                    command=cmd,
                )
                btn.grid(
                    row=fila,
                    column=col,
                    columnspan=2,
                    padx=3,
                    pady=4,
                    sticky="nsew",
                )
                self.botones_dict[texto] = (btn, "hist")
                continue

            btn = tk.Button(
                self,
                text=texto,
                font=("Arial", 12, "bold"),
                bd=0,
                command=lambda t=texto: self.gestionar_clic(t),
            )
            btn.grid(row=fila, column=col, padx=3, pady=3, sticky="nsew")
            self.botones_dict[texto] = (btn, cat)

        for i in range(9):
            self.grid_rowconfigure(i, weight=1)
        for j in range(4):
            self.grid_columnconfigure(j, weight=1)

    def aplicar_tema(self):
        """Aplica la paleta de colores activa a la ventana y controles."""
        colors = self.TEMAS[self.modo_actual]
        self.configure(bg=colors["bg_ventana"])
        self.pantalla.configure(
            bg=colors["bg_pantalla"], fg=colors["fg_pantalla"]
        )

        for texto, (btn, cat) in self.botones_dict.items():
            if cat == "num":
                bg = colors["btn_num"]
                fg = colors["fg_texto"]
            elif cat == "op":
                bg = colors["btn_op"]
                fg = "white"
            elif cat == "mem":
                bg = colors["btn_mem"]
                fg = "white"
            elif cat == "clear":
                bg = colors["btn_clear"]
                fg = "white"
            else:
                bg = colors["btn_hist"]
                fg = "white"

            btn.configure(
                bg=bg, fg=fg, activebackground=bg, activeforeground=fg
            )

    def alternar_tema(self):
        """Cambia dinámicamente entre Modo Claro y Oscuro."""
        self.modo_actual = (
            "claro" if self.modo_actual == "oscuro" else "oscuro"
        )
        self.aplicar_tema()

    def configurar_atajos_teclado(self):
        """Eventos: Captura de entradas físicas del teclado."""
        self.bind("<Key>", self._manejar_tecla_fisica)
        self.bind("<Return>", lambda e: self.gestionar_clic("="))
        self.bind("<BackSpace>", lambda e: self._borrar_ultimo_caracter())
        self.bind("<Escape>", lambda e: self.gestionar_clic("C"))

    def _borrar_ultimo_caracter(self):
        self.pantalla_var.set(self.pantalla_var.get()[:-1])

    def _manejar_tecla_fisica(self, event):
        ch = event.char
        if ch in "0123456789.+-*/()":
            self.pantalla_var.set(self.pantalla_var.get() + ch)

    def gestionar_clic(self, tecla):
        """Manejador centralizado de lógica de interfaz y memoria."""
        texto_actual = self.pantalla_var.get()

        if tecla == "C":
            self.pantalla_var.set("")

        elif tecla in ["MC", "MR", "M+", "M-"]:
            self._gestionar_memoria(tecla, texto_actual)

        elif tecla == "mod":
            self.pantalla_var.set(texto_actual + "%")

        elif tecla == "^":
            self.pantalla_var.set(texto_actual + "**")

        elif tecla in ["log", "abs"]:
            self.pantalla_var.set(f"{tecla}({texto_actual})")

        elif tecla == "=":
            if not texto_actual.strip():
                messagebox.showwarning(
                    "Campo Vacío", "Por favor ingresa una expresión."
                )
                return

            try:
                resultado = self.modelo.calcular(texto_actual)
                self.pantalla_var.set(str(resultado))
            except (ZeroDivisionError, ValueError) as e:
                messagebox.showerror("Error", str(e))
                self.pantalla_var.set("")
            except Exception as e:
                messagebox.showerror(
                    "Error Inesperado", f"Ocurrió un error: {e}"
                )
                self.pantalla_var.set("")

        elif tecla == "+/-":
            if texto_actual:
                if texto_actual.startswith("-"):
                    self.pantalla_var.set(texto_actual[1:])
                else:
                    self.pantalla_var.set("-" + texto_actual)

        else:
            self.pantalla_var.set(texto_actual + tecla)

    def _gestionar_memoria(self, accion, texto):
        """Maneja las operaciones de la memoria (MC, MR, M+, M-)."""
        try:
            val = float(texto) if texto else 0.0
            if accion == "MC":
                self.modelo.memoria_limpiar()
                messagebox.showinfo("Memoria", "Memoria borrada (MC).")
            elif accion == "MR":
                res = self.modelo.memoria_recuperar()
                self.pantalla_var.set(str(int(res) if res.is_integer() else res))
            elif accion == "M+":
                self.modelo.memoria_sumar(val)
                messagebox.showinfo("Memoria", f"Sumado {val} a la memoria.")
            elif accion == "M-":
                self.modelo.memoria_restar(val)
                messagebox.showinfo("Memoria", f"Restado {val} a la memoria.")
        except ValueError:
            messagebox.showerror(
                "Error Memoria", "Ingrese un número válido para operar con la memoria."
            )

    def mostrar_ventana_historial(self):
        try:
            registros = self.modelo.consultar_historial()
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo cargar el historial: {e}"
            )
            return

        ventana_h = tk.Toplevel(self)
        ventana_h.title("Historial de Operaciones")
        ventana_h.geometry("450x300")

        columnas = ("expresion", "resultado", "fecha")
        tabla = ttk.Treeview(
            ventana_h, columns=columnas, show="headings", height=10
        )

        tabla.heading("expresion", text="Operación")
        tabla.heading("resultado", text="Resultado")
        tabla.heading("fecha", text="Fecha y Hora")

        tabla.column("expresion", width=140, anchor="center")
        tabla.column("resultado", width=110, anchor="center")
        tabla.column("fecha", width=160, anchor="center")

        for reg in registros:
            tabla.insert("", tk.END, values=reg)

        scrollbar = ttk.Scrollbar(
            ventana_h, orient=tk.VERTICAL, command=tabla.yview
        )
        tabla.configure(yscroll=scrollbar.set)

        tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)


# ARRANQUE DEL SISTEMA
if __name__ == "__main__":
    gestor_db = GestorHistorial()
    modelo = ModeloCalculadora(gestor_db)
    app = VistaCalculadora(modelo)
    app.mainloop()
