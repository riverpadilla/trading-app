import tkinter as tk
from tkinter import ttk
import pandas as pd
import estrategia2

def mostrar_tabla_estadisticas(df):
    # Calcula las estadísticas usando estrategia2
    stats_df = estrategia2.calcular_estadisticas(df)

    # Crea ventana principal
    root = tk.Tk()
    root.title("Estadísticas de Variación")

    # Frame para la tabla
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Columnas de la tabla (incluye RSI, MACD y MA50)
    columns = ("Estadística", "Valor", "Fecha/Hora", "Apertura", "Cierre", "High", "Low", "RSI", "MACD", "MA50")
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=len(stats_df))
    
    # Configura encabezados y columnas
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor=tk.CENTER, width=100)

    # Inserta los datos
    for _, row in stats_df.iterrows():
        tree.insert(
            "", tk.END,
            values=(
                row.get("Estadística", ""),
                f"{row.get('Valor', 0):.6f}",
                row.get("Fecha/Hora", ""),
                f"{row.get('Apertura', '')}" if row.get('Apertura', '') != '' else '',
                f"{row.get('Cierre', '')}" if row.get('Cierre', '') != '' else '',
                f"{row.get('High', '')}" if row.get('High', '') != '' else '',
                f"{row.get('Low', '')}" if row.get('Low', '') != '' else '',
                f"{row.get('RSI', '')}" if row.get('RSI', '') != '' else '',
                f"{row.get('MACD', '')}" if row.get('MACD', '') != '' else '',
                f"{row.get('MA50', '')}" if row.get('MA50', '') != '' else ''
            )
        )

    tree.pack(fill=tk.BOTH, expand=True)

    # Botón para cerrar
    ttk.Button(root, text="Cerrar", command=root.destroy).pack(pady=10)

    root.mainloop()

# Ejemplo de uso:
if __name__ == "__main__":
    # Simulación: carga de datos desde chart_ui.py
    import chart_ui
    symbol = chart_ui.SYMBOLS[0]
    interval = chart_ui.INTERVALS[5]
    df = chart_ui.obtener_historico_binance(symbol, interval)
    df = chart_ui.procesar_indicadores(df)
    mostrar_tabla_estadisticas(df)